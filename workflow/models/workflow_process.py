from datetime import timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

import logging

_logger = logging.getLogger(__name__)

PROCESS_STATES = [
    ('in_progress', _('In Progress')),
    ('completed', _('Completed')),
    ('canceled', _('Canceled')),
    ('break', _('Break'))
]


class WorkflowProcess(models.Model):
    _name = 'workflow.process'
    _description = 'Workflow Process'
    _order = 'id'

    @api.model
    def _selection_resource_model(self):
        return [(model.model, model.name) for model in self.env['ir.model'].sudo().search([])]

    workflow_id = fields.Many2one('workflow.workflow', string='Workflow', index=True)
    code = fields.Char(string='Code', copy=False, default=lambda self: _('New'), readonly=True, required=True)
    name = fields.Char(string='Name', copy=True, required=True)
    description = fields.Html(string='Description', copy=False)
    res_ref = fields.Reference(string='Resource', selection=_selection_resource_model, compute='_compute_res_ref')
    res_model = fields.Char(string='Resource Model', copy=False, index=True, required=True)
    res_id = fields.Integer(string='Resource ID', copy=False, index=True, required=True)
    state = fields.Selection(PROCESS_STATES, string='State')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)

    date_start = fields.Datetime(string='Date Start', copy=False, readonly=True)
    date_end = fields.Datetime(string='Date End', copy=False, readonly=True)
    duration = fields.Float(string='Duration', compute='_compute_duration', copy=False)

    activity_ids = fields.One2many('workflow.process.activity', 'workflow_process_id', string='Activities', copy=True)
    last_activity_id = fields.Many2one('workflow.process.activity', string='Last Activity', copy=False, readonly=True)
    activity_history_ids = fields.One2many('workflow.process.activity.history', 'workflow_process_id', string='History',
                                           readonly=True)
    task_ids = fields.One2many('task.task', string='Tasks', compute='_compute_task_ids', compute_sudo=True)

    @api.constrains('activity_ids')
    def check_activities(self):
        for process in self:
            if len(process.activity_ids.filtered(lambda act: act.flow_start)) > 1:
                raise ValidationError(_('Workflow process must have only one start activity.'))

    @api.depends('res_model', 'res_id')
    def _compute_res_ref(self):
        for process in self:
            process.res_ref = '%s,%d' % (
                process.res_model, process.res_id) if process.res_model else False

    @api.depends('date_start', 'date_end')
    def _compute_duration(self):
        for process in self:
            duration = (process.date_end - process.date_start).total_seconds() if process.date_end else False
            process.duration = duration / timedelta(hours=1).total_seconds() if duration else False

    @api.depends('activity_ids')
    def _compute_task_ids(self):
        for process in self:
            process.task_ids = self.env['task.task'].with_context(active_test=False).search([
                ('activity_id', 'in', process.activity_ids.ids)
            ]).ids or False

    # ------------------------------------------------------
    # CRUD
    # ------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('workflow.process') or _('New')
        records = super(WorkflowProcess, self).create(vals_list)
        return records

    def unlink(self):
        for process in self:
            if any(process.activity_ids.filtered(
                    lambda act: not act.flow_start and not act.flow_stop and act.state == 'completed')):
                raise UserError(_('You cannot delete this process because some activities were completed.'))
        self.mapped('task_ids').unlink()
        result = super(WorkflowProcess, self).unlink()
        return result

    # ------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------

    def run(self):
        self.ensure_one()
        activity = self.activity_ids.filtered(lambda act: act.flow_start)[:1]
        if not activity:
            raise UserError(_('Workflow process must have at least one start activity.'))
        activity.process()

    def run_from_last_activity(self):
        for process in self:
            copy_activity = process.last_activity_id.copy()
            process.last_activity_id.write({'active': False})
            copy_activity.process()
            process.write({'state': 'in_progress'})

    def pause(self):
        pass

    def stop(self, cancel_reason):
        self.ensure_one()
        activities = self.activity_ids.filtered(lambda act: act.state != 'completed')
        if activities:
            [task.write({'active': False, 'execution_result': cancel_reason}) for task in
             self.env['task.task'].sudo().search([('activity_id', 'in', activities.ids)])]
            [activity.write({'state': 'canceled'}) for activity in activities]
        self.write({'state': 'canceled'})

    def open_resource(self):
        self.ensure_one()
        if self.res_model and self.res_id:
            view_id = self.env[self.res_model].get_formview_id(self.res_id)
            return {
                'type': 'ir.actions.act_window',
                'res_id': self.res_id,
                'res_model': self.res_model,
                'views': [[view_id, 'form']],
                'target': 'current'
            }
