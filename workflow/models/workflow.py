from odoo import api, Command, fields, models, _
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

MODEL_DOMAIN = """[
        ('transient', '=', False),
        '!',
        '|',
        '|',
        '|',
        '|',
        ('model', '=ilike', 'base_%'),
        ('model', '=ilike', 'bus.%'),
        ('model', '=ilike', 'ir.%'),        
        ('model', '=ilike', 'report.%'),
        ('model', '=ilike', 'mail.%')
    ]"""


class Workflow(models.Model):
    _name = 'workflow.workflow'
    _description = 'Workflow'
    _order = 'name, id'

    name = fields.Char(required=True, copy=True)
    active = fields.Boolean(default=True, index=True)
    description = fields.Html(string='Description', copy=False)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)

    model_id = fields.Many2one('ir.model', string='Model', domain=MODEL_DOMAIN, ondelete='cascade', required=True)
    model_name = fields.Char(related='model_id.model', string='Model Name', copy=False, readonly=True)
    activity_ids = fields.One2many('workflow.activity', 'workflow_id', string='Activities', copy=True)
    activity_count = fields.Integer(compute='_compute_activity_count')
    transition_ids = fields.One2many('workflow.transition', 'workflow_id', string='Transitions', copy=False)
    transition_count = fields.Integer(compute='_compute_transition_count')
    process_ids = fields.One2many('workflow.process', 'workflow_id', string='Processes', copy=False)
    process_count = fields.Integer(compute='_compute_process_count')

    # ------------------------------------------------------
    # CONSTRAINS
    # ------------------------------------------------------

    @api.constrains('activity_ids')
    def check_activities(self):
        for wf in self:
            if len(wf.activity_ids.filtered(lambda act: act.flow_start)) > 1:
                raise ValidationError(_('Workflow must have only one start activity.'))

    # ------------------------------------------------------
    # COMPUTE METHODS
    # ------------------------------------------------------

    @api.depends('activity_ids')
    def _compute_activity_count(self):
        for wf in self:
            wf.activity_count = len(wf.activity_ids)

    @api.depends('transition_ids')
    def _compute_transition_count(self):
        for wf in self:
            wf.transition_count = len(wf.transition_ids)

    @api.depends('process_ids')
    def _compute_process_count(self):
        for wf in self:
            wf.process_count = len(wf.process_ids)

    # ------------------------------------------------------
    # CRUD
    # ------------------------------------------------------

    @api.model_create_multi
    def create(self, vals):
        records = super().create(vals)
        if self.env.context.get('create_default_activities'):
            [rec._create_default_activities_and_routes() for rec in records.filtered(lambda wf: not wf.activity_ids)]

        return records

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        default['name'] = _('Copy_%s') % self.name
        return super(Workflow, self).copy(default=default)

    # ------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------

    def run(self, res_model, res_id):
        self.ensure_one()
        res_ref = self.env[res_model].browse(res_id)
        process_vals = dict(
            workflow_id=self.id,
            name=_('Processing "%s"') % res_ref.name,
            description=self.env.context.get('default_description', False) or res_ref.description,
            res_model=res_model,
            res_id=res_id,
            company_id=res_ref.company_id.id,
            activity_ids=[
                (Command.CREATE, 0, dict(
                    workflow_id=self.id,
                    activity_id=activity.id,
                    sequence=activity.sequence
                )) for activity in self.activity_ids
            ]
        )
        process = self.env['workflow.process'].create(process_vals)
        process.run()

    # ------------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------------

    def _create_default_activities_and_routes(self):
        self.ensure_one()
        activity_start = self.env['workflow.activity'].create({
            'name': _('Start'),
            'workflow_id': self.id,
            'flow_start': True,
            'type': False,
            'sequence': 0
        })
        activity_stop = self.env['workflow.activity'].create({
            'name': _('Stop'),
            'workflow_id': self.id,
            'flow_stop': True,
            'type': False,
            'sequence': 1000
        })
        self.env['workflow.transition'].create({
            'workflow_id': self.id,
            'name': _('Finished'),
            'activity_from_id': activity_start.id,
            'activity_to_id': activity_stop.id,
            'sequence': 0
        })
