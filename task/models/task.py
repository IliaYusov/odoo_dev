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
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _selection_parent_model(self):
        return []

    @api.model
    def _selection_parent_obj_model(self):
        return []

    def _get_type_domain(self):
        if self.parent_ref:
            return [('model_id.model', '=', type(self.parent_ref).__name__)]
        elif self.parent_ref_type:
            return [('model_id.model', 'like', self.parent_ref_type + '%')]
        else:
            return [('model_id', '=', False)]

    def _get_stage_domain(self):
        return [('task_type_id', '=', self.type_id)]

    code = fields.Char(string='Code', required=True, readonly=True, default=lambda self: _('New'))
    name = fields.Char(string='Title', tracking=True, required=True, index='trigram')
    description = fields.Html(string='Description')
    priority = fields.Selection(PRIORITIES, string='Priority', default='3', tracking=True)

    author_id = fields.Many2one('res.users', string='Author', required=True, readonly=True,
                                default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    type_id = fields.Many2one('task.type', string='Type', ondelete='restrict', required=True, index=True, copy=True,
                              tracking=True, domain=_get_type_domain)
    stage_id = fields.Many2one('task.stage', string='Stage', ondelete='restrict', required=True, index=True,
                               tracking=True, group_expand='_read_group_stage_ids', domain=_get_stage_domain)
    stage_type_id = fields.Many2one('task.stage.type', related="stage_id.type_id", string="Stage Type",
                                    index=True, readonly=True, store=True)
    stage_routes = fields.Char(compute='_compute_stage_routes', readonly=True)
    is_closed = fields.Boolean(related='stage_id.closed', store=True, index=True, readonly=True)

    user_id = fields.Many2one('res.users', string='Assigned', tracking=True)
    actual_executor_id = fields.Many2one('res.users', string='Executor', readonly=True)
    parent_ref = fields.Reference(string='Parent', ondelete='restrict', selection="_selection_parent_model",
                                  compute="_compute_parent_ref", inverse='_inverse_parent_ref', store=True)
    parent_ref_id = fields.Integer(string="Parent Id", index=True, copy=False)
    parent_ref_type = fields.Char(string="Parent Type", index=True, copy=False)

    parent_obj_ref = fields.Reference(string='Parent Object', selection='_selection_parent_obj_model',
                                      compute='_compute_parent_obj', readonly=True)

    date_deadline = fields.Date(string='Deadline', required="True", index=True, copy=False, tracking=True)
    parent_id = fields.Many2one('task.task', string='Parent Task', copy=True, tracking=True)
    child_ids = fields.One2many('task.task', 'parent_id', string="Sub-tasks")
    subtask_count = fields.Integer("Sub-task Count", compute='_compute_subtask_count')
    child_text = fields.Char(compute="_compute_child_text")
    date_closed = fields.Datetime(string='Date Closed', index=True, copy=False)
    execution_result = fields.Html(string='Execution Result')

    attachment_count = fields.Integer(compute='_compute_attachment_count', string='Attachments')
    url = fields.Char('Url', compute='_get_url')

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_('Error! You cannot create a recursive hierarchy of tasks.'))

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        search_domain = []

        if stages:
            search_domain = ['task_type_id', 'in', list(set(stages.task_type_id.ids))]

        return self.env['task.stage'].search([search_domain] if any(search_domain) else [], order=order)

    # @api.model
    # def get_view(self, view_id=None, view_type='form', **options):
    #     if view_type == 'form' and 'edit' not in self.env.context['params']:
    #         ctx = dict(self.env.context)
    #         ctx['params']['edit'] = '0'
    #         return super().with_context(ctx).get_view(view_id, view_type, **options)
    #     return super().get_view(view_id, view_type, **options)

    # @api.model
    # def fields_get(self, allfields=None, attributes=None):
    #     fields = super().fields_get(allfields=allfields, attributes=attributes)
    #
    #     public_fields = {field_name: description for field_name, description in fields.items()}
    #
    #     for field_name, description in public_fields.items():
    #         if field_name == 'description' and not description.get('readonly', False):
    #             # If the field is not in Writable fields and it is not readonly then we force the readonly to True
    #             description['readonly'] = True
    #
    #     return public_fields

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
            # res._send_message_notify(self.env.ref('task.mail_template_task_assigned_notify', raise_if_not_found=False))

        return res

    def write(self, vals):
        user_changed = vals.get('user_id', False) and self.user_id.id != vals['user_id']
        res = super(Task, self.with_context(mail_create_nolog=False)).write(vals)
        if user_changed:
            self.action_create_activity()
            # self._send_message_notify(self.env.ref('task.mail_template_task_assigned_notify', raise_if_not_found=False))
        return res

    def _compute_attachment_count(self):
        self.env.cr.execute(
            """
            WITH attachments AS (
                SELECT res_id as id, count(*) as count
                FROM ir_attachment
                WHERE res_model = 'task.task' AND res_id IN %(task_ids)s
                GROUP BY res_id
                UNION ALL
                SELECT res_id as id, count(*) as count
                FROM ir_attachment a
                INNER JOIN task_task t ON t.id = a.res_id
                INNER JOIN document_flow_process p ON p.id = t.parent_ref_id
                WHERE a.res_model = 'document_flow.process' AND a.res_id IN %(task_ids)s
                GROUP BY a.res_id                
            )
            SELECT id, sum(count)
            FROM attachments
            GROUP BY id
            """,
            {"task_ids": tuple(self.ids)}
        )
        attachments_count = dict(self.env.cr.fetchall())
        for task in self:
            task.attachment_count = attachments_count.get(task.id, 0)

    def _compute_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        return base_url

    def _compute_parent_obj(self):
        for task in self:
            task.parent_obj_ref = self.env['document_flow.process.parent_object'].search([
                ('process_id', '=', task.parent_ref_id)
            ], limit=1).parent_ref

    def _message_auto_subscribe_followers(self, updated_values, default_subtype_ids):
        return []

    # @api.constrains('type_id', 'parent_ref', 'parent_ref_type')
    # def _check_type_id(self):
    #     for task in self:
    #         if task.type_id:
    #             if task.parent_ref:
    #                 if type(task.parent_ref) != task.type_id.model_id:
    #                     raise ValidationError(_("Type '%s' of task is incorrect.", task.type_id.name))
    #             elif task.parent_ref_type:
    #                 if task.type_id.model_id.name.startswith(task.parent_ref_type):
    #                     raise ValidationError(_("Type '%s' of task is incorrect.", task.type_id.name))

    @api.depends('parent_ref_type', 'parent_ref_id')
    def _compute_parent_ref(self):
        for task in self:
            if task.parent_ref_type and task.parent_ref_type in self.env:
                task.parent_ref = '%s,%s' % (task.parent_ref_type, task.parent_ref_id or 0)
            else:
                task.parent_ref = None
            return {'domain': {'type_id': task._get_type_domain()}}

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

    @api.onchange('parent_ref')
    def _onchange_parent_ref(self):
        for task in self:
            return {'domain': {'type_id': task._get_type_domain()}}

    @api.onchange('type_id')
    def _onchange_type_id(self):
        for task in self:
            if task.type_id and task.type_id.start_stage_id:
                task.stage_id = task.type_id.start_stage_id

    def _send_message_notify(self, template):
        if not template:
            return
        template.send_mail(self.id, email_layout_xmlid='mail.mail_notification_layout', force_send=True)

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

            if not self.user_id:
                self.write({'user_id': self.env.user})

            if self.stage_id.mail_template_id:
                self._send_message_notify(self.stage_id.mail_template_id)
            return None

        raise exceptions.UserError(_('Cannot move task (%(task)s) by this route (%(route)s)') %
                                   {
                                       'task': self.name,
                                       'route': route.display_name
                                   })

    def close_task(self, result_type):
        self.ensure_one()
        self._close_mail_activities()
        date_closed = fields.Datetime.now()
        if self.parent_ref:
            self.parent_ref.sudo().process_task_result(date_closed, result_type=result_type,
                                                       feedback=self.execution_result)
        self.write({'date_closed': date_closed, 'actual_executor_id': self.env.user})

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
