import json
from odoo import _, models, fields, api, exceptions
from odoo.exceptions import ValidationError
from datetime import datetime, date

PRIORITIES = [
    ('0', 'Not set'),
    ('1', 'Lowest'),
    ('2', 'Low'),
    ('3', 'Medium'),
    ('4', 'High'),
    ('5', 'Highest'),
]

RESULT_TYPES = [
    ('ok', _('Ok')),
    ('error', _('Error'))
]


class Task(models.Model):
    _name = "task.task"
    _description = "Task"
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']

    @api.model
    def _selection_parent_model(self):
        return []

    code = fields.Char(string='Code', required=True, readonly=True, default=lambda self: _('New'))
    name = fields.Char(string='Title', tracking=True, required=True, index='trigram')
    description = fields.Html(string='Description')

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    priority = fields.Selection(PRIORITIES, string='Priority', default='3', tracking=True)
    type_id = fields.Many2one('task.type', string='Type', ondelete='restrict', required=True, index=True, copy=True,
                              tracking=True)
    stage_id = fields.Many2one('task.stage', string='Stage', ondelete='restrict', required=True, index=True,
                               tracking=True, copy=True)
    stage_type_id = fields.Many2one('task.stage.type', related="stage_id.type_id", string="Stage Type",
                                    index=True, readonly=True, store=True)
    stage_routes = fields.Char(compute='_compute_stage_routes', readonly=True)
    is_closed = fields.Boolean(related='stage_id.closed', store=True, index=True, readonly=True)

    user_id = fields.Many2one('res.users', string='Assigned', tracking=True)
    parent_ref = fields.Reference(string='Parent', ondelete='restrict', selection="_selection_parent_model",
                                  compute="_compute_parent_ref", inverse='_inverse_parent_ref', store=True)
    parent_ref_id = fields.Integer(string="Parent Id", index=True, copy=False)
    parent_ref_type = fields.Char(string="Parent Type", index=True, copy=False)

    date_deadline = fields.Date(string='Deadline', required="True", index=True, copy=False, tracking=True)
    parent_id = fields.Many2one('task.task', string='Parent Task', copy=True, tracking=True)
    child_ids = fields.One2many('task.task', 'parent_id', string="Sub-tasks")
    subtask_count = fields.Integer("Sub-task Count", compute='_compute_subtask_count')
    child_text = fields.Char(compute="_compute_child_text")
    date_closed = fields.Date(string='Date Closed', index=True, copy=False)
    execution_result = fields.Html(string='Execution Result')

    # attachment_ids = fields.One2many('ir.attachment', 'res_id', string='Attachments',
    #                                  domain=[('res_model', '=', 'task.task')])
    attachment_count = fields.Integer(compute='_compute_attachment_count', string='Attachments')

    @api.model
    def create(self, vals_list):
        if vals_list.get('parent_ref'):
            vals_list['parent_ref_type'] = vals_list['parent_ref'].split(",")[0]
            vals_list['parent_ref_id'] = int(vals_list['parent_ref'].split(",")[1])

        if vals_list.get('code', _('New')) == _('New'):
            vals_list['code'] = self.env['ir.sequence'].next_by_code('task.task') or _('New')

        if vals_list.get('type_id', False):
            type_id = self.env['task.type'].browse(vals_list['type_id'])
            if type_id and type_id.start_stage_id:
                vals_list['stage_id'] = type_id.start_stage_id.id
            else:
                raise ValidationError(
                    _("Cannot create task of type '%(type_name)s': This type have no start stage defined!") % {
                        'type_name': type_id.name})

        res = super(Task, self).create(vals_list)

        # TODO: что-то тут не так
        if res.user_id:
            res.action_create_activity()

        return res

    def write(self, vals):
        user_changed = vals.get('user_id', False) and self.user_id.id != vals['user_id']
        res = super(Task, self).write(vals)
        if user_changed:
            self.action_create_activity()
        return res

    def _compute_attachment_count(self):
        for task in self:
            task.attachment_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', self._name),
                ('res_id', '=', task.id)
            ])

    @api.depends('parent_ref_type', 'parent_ref_id')
    def _compute_parent_ref(self):
        for task in self:
            if task.parent_ref_type and task.parent_ref_type in self.env:
                task.parent_ref = '%s,%s' % (task.parent_ref_type, task.parent_ref_id or 0)
            else:
                task.parent_ref = None

    def _inverse_parent_ref(self):
        for task in self:
            if task.parent_ref:
                task.parent_ref_type = type(task.parent_ref).__name__
                task.parent_ref_id = task.parent_ref.id

    @api.depends('child_ids')
    def _compute_subtask_count(self):
        for task in self:
            task.subtask_count = self.search_count([('parent_id', '=', self.id)])

    @api.depends('child_ids')
    def _compute_child_text(self):
        for task in self:
            if not task.subtask_count:
                task.child_text = False
            elif task.subtask_count == 1:
                task.child_text = _("(+ 1 task)")
            else:
                task.child_text = _("(+ %(child_count)s tasks)", child_count=task.subtask_count)

    @api.depends('stage_id', 'type_id')
    def _compute_stage_routes(self):
        for task in self:
            routes = []
            for route in task.stage_id.route_out_ids:
                route._check_can_move(task)
                if route.name:
                    route_name = route.name
                else:
                    route_name = route.stage_to_id.name
                routes += [{
                    'id': route.id,
                    'name': route_name,
                    'stage_to_id': route.stage_to_id.id,
                    'close': route.close,
                    'btn_style': route.button_style,
                }]

            task.stage_routes = json.dumps({'routes': routes})

    def action_create_activity(self):
        return self.env['mail.activity'].create({
            'display_name': _('You have been assigned to task %s' % self.code),
            'summary': self.name,
            'date_deadline': self.date_deadline,
            'user_id': self.user_id.id,
            'res_id': self.id,
            'res_model_id': self.env['ir.model'].search([('model', '=', self._name)]).id,
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id
        })

    def _close_mail_activities(self):
        self.ensure_one()
        activities = self.env['mail.activity'].search([
            ('res_id', '=', self.id),
            ('res_model_id', '=', self.env['ir.model'].search([('model', '=', self._name)]).id),
            ('activity_type_id', '=', self.env.ref('mail.mail_activity_data_todo').id),
            ('user_id', '=', self.env.user.id)
        ])
        for activity in activities:
            activity.action_feedback(feedback=self.execution_result)

    def close_task(self, result_type):
        self.ensure_one()
        self._close_mail_activities()
        date_closed = datetime.today()
        if self.parent_ref:
            self.parent_ref.sudo().process_task_result(date_closed, result_type=result_type,
                                                       feedback=self.execution_result)
        self.write({'date_closed': date_closed})

    def action_move_task_along_route(self, route_id):
        self.ensure_one()
        route = self.env['task.stage.route'].browse(route_id)
        if route in self.stage_id.route_out_ids:
            if route.close:
                action = self.env['ir.actions.actions']._for_xml_id('task.action_task_wizard_done')
                action['name'] = _('Execution report')
                action['display_name'] = _('Execution report')
                action['context'] = {
                        'default_task_id': self.id,
                        'default_route_id': route_id
                    }
                return action
            self.stage_id = route.stage_to_id.id
            return None

        raise exceptions.UserError(_('Cannot move task (%(task)s) by this route (%(route)s)') %
                                   {
                                       'task': self.name,
                                       'route': route.display_name
                                   })

    @api.onchange('type_id')
    def _onchange_type_id(self):
        for task in self:
            if task.type_id and task.type_id.start_stage_id:
                task.stage_id = task.type_id.start_stage_id

    def action_open_task(self):
        return {
            'view_mode': 'form',
            'res_model': 'task.task',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'context': self._context
        }

    def action_open_parent_task(self):
        return {
            'name': _('Parent Task'),
            'view_mode': 'form',
            'res_model': 'task.task',
            'res_id': self.parent_id.id,
            'type': 'ir.actions.act_window',
            'context': self._context
        }

    def action_open_attachments(self):
        self.ensure_one()
        return {
            'name': _('Attachments'),
            'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,tree,form',
            'context': "{'default_res_model': '%s','default_res_id': %d}" % (self._name, self.id),
            'help': """
                <p class="o_view_nocontent_smiling_face">%s</p>
                """ % _("Add attachments for this task")
        }
