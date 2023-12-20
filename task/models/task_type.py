import logging

from odoo import api, fields, models, _
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class TaskType(models.Model):
    _name = 'task.type'
    _description = 'Task Type'
    _order = 'name, id'

    name = fields.Char(required=True, copy=True, translate=True)
    code = fields.Char(required=True, copy=True)
    active = fields.Boolean(default=True, index=True)
    description = fields.Text()

    stage_ids = fields.One2many('task.stage', 'task_type_id', string='Stages', copy=True)
    stage_count = fields.Integer(compute='_compute_stage_count', readonly=True)
    start_stage_id = fields.Many2one('task.stage', ondelete='set null', compute='_compute_start_stage_id',
                                     readonly=True, store=True)
    color = fields.Char(default='rgba(240,240,240,1)')

    route_ids = fields.One2many('task.stage.route', 'task_type_id', string='Stage Routes')
    route_count = fields.Integer(string='Routes', compute='_compute_route_count', readonly=True)

    model_id = fields.Many2one('ir.model', string='Model')
    access_group_ids = fields.Many2many('res.groups', relation='task_type_group_rel', column1='task_type_id',
                                        column2='group_id', string='Access groups',
                                        help="""If user belongs to one of groups specified in this field,
                                        then he will be able to select this type during task creation.""")

    employee_overdue_reminder = fields.Boolean(string='Employee Reminder', default=False)
    days_before = fields.Integer(string='Days Before', default=1)

    _sql_constraints = [
        ('code_uniq',
         'UNIQUE (code)',
         'Code must be unique.')
    ]

    @api.model
    def _cron_deadline_reminder(self):
        template = self.env.ref('task.mail_template_task_deadline_reminder', raise_if_not_found=False)
        if not template:
            _logger.warning(
                'Cannot sent deadline reminder mail, because Mail Scheduler has reference to non-existent template')
            return True

        today = datetime.now().date()
        types = self.search([('employee_overdue_reminder', '=', True)])
        tasks = self.env['task.task'].search([
            ('is_closed', '=', False),
            ('date_deadline', '!=', False),
            ('type_id', 'in', types.ids),
            ('user_ids', '!=', False)
        ])

        users = set(tasks.user_ids)
        for user in users:
            overdue_tasks = tasks.filtered(lambda t: user in t.user_ids and t.date_deadline < today)
            expiration_tasks = tasks.filtered(
                lambda t: user in t.user_ids and today <= t.date_deadline <= today + timedelta(
                    days=t.type_id.days_before))
            render_ctx = {
                'user_id': user,
                'overdue_tasks': overdue_tasks,
                'expiration_tasks': expiration_tasks
            }
            template.sudo().with_context(render_ctx).send_mail(self.id,
                                                               email_layout_xmlid='mail.mail_notification_layout',
                                                               force_send=True)
        return True

    @api.model_create_multi
    def create(self, vals):
        task_types = super().create(vals)

        if self.env.context.get('create_default_stages'):
            for task_type in task_types:
                if not task_type.start_stage_id:
                    task_type._create_default_stages_and_routes()

        return task_types

    @api.depends('stage_ids')
    def _compute_stage_count(self):
        for task_type in self:
            task_type.stage_count = self.env['task.stage'].search_count([
                ('task_type_id', '=', task_type.id)
            ])

    @api.depends('route_ids')
    def _compute_route_count(self):
        for task_type in self:
            task_type.route_count = self.env['task.stage.route'].search_count([
                ('task_type_id', '=', task_type.id)
            ])

    @api.depends('stage_ids', 'stage_ids.sequence', 'stage_ids.task_type_id')
    def _compute_start_stage_id(self):
        for task_type in self:
            if task_type.stage_ids:
                task_type.start_stage_id = task_type.stage_ids.sorted(key=lambda r: r.sequence)[0]
            else:
                task_type.start_stage_id = False

    def _create_default_stages_and_routes(self):
        self.ensure_one()
        stage_to_do = self.env['task.stage'].create({
            'name': _('To Do'),
            'code': 'to_do',
            'task_type_id': self.id,
            'sequence': 1,
            'type_id': self.env.ref('task.task_stage_type_to_do').id
        })
        stage_done = self.env['task.stage'].create({
            'name': _('Done'),
            'code': 'done',
            'task_type_id': self.id,
            'sequence': 100,
            'closed': True,
            'type_id': self.env.ref('task.task_stage_type_done').id
        })
        self.env['task.stage.route'].create({
            'name': _('Done'),
            'stage_from_id': stage_to_do.id,
            'stage_to_id': stage_done.id,
            'task_type_id': self.id,
        })

    def action_create_default_stage_and_routes(self):
        self._create_default_stages_and_routes()

    def action_task_type_diagram(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('task.action_task_type')
        action['context'] = {'default_task_type_id': self.id}
        action.update({
            'res_model': 'task.type',
            'res_id': self.id,
            'views': [(False, 'diagram_plus'), (False, 'form')],
        })
        return action
