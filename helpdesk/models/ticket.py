import json
from odoo import models, fields, api, _, exceptions
from datetime import datetime

PRIORITIES = [
    ('0', 'Not set'),
    ('1', 'Lowest'),
    ('2', 'Low'),
    ('3', 'Medium'),
    ('4', 'High'),
    ('5', 'Highest'),
]


class HelpdeskTicket(models.Model):
    _name = 'helpdesk.ticket'
    _description = 'Helpdesk Ticket'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']

    author_id = fields.Many2one('res.users', string='Author', default=lambda self: self.env.user)
    code = fields.Char(string='Code', required=True, default=lambda self: _('New'), copy=False)
    name = fields.Text(string='Name', required=True, tracking=True)
    description = fields.Html(string='Description', required=True, tracking=True)

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    module_id = fields.Many2one('ir.model', string='Module')

    priority = fields.Selection(PRIORITIES, string='Priority', default='3', tracking=True)

    team_id = fields.Many2one('helpdesk.team', string='Helpdesk Team', tracking=True, copy=False)
    user_id = fields.Many2one('res.users', string='Assigned', check_company=True, index=True, tracking=True)
    date_closed = fields.Date(string='Date Closed', index=True, copy=False)

    type_id = fields.Many2one('helpdesk.ticket.type', string='Type', ondelete='restrict', required=True, index=True,
                              copy=True, tracking=True)
    stage_id = fields.Many2one('helpdesk.ticket.stage', string='Stage', ondelete='restrict', required=True, index=True,
                               tracking=True, copy=True)
    stage_type_id = fields.Many2one('helpdesk.ticket.stage.type', related="stage_id.type_id", string="Stage Type",
                                    index=True, readonly=True, store=True)
    is_closed = fields.Boolean(related='stage_id.closed', store=True, index=True, readonly=True)

    stage_routes = fields.Char(compute='_compute_stage_routes', readonly=True)

    attachment_count = fields.Integer(compute='_compute_attachment_count', string='Attachments')
    task_count = fields.Integer(compute='_compute_task_count', string='Tasks')

    @api.model
    def create(self, vals_list):
        if vals_list.get('code', _('New')) == _('New'):
            vals_list['code'] = self.env['ir.sequence'].next_by_code('helpdesk.ticket') or _('New')
        if vals_list.get('type_id', False):
            type_id = self.env['helpdesk.ticket.type'].browse(vals_list['type_id'])
            if type_id and type_id.start_stage_id:
                vals_list['stage_id'] = type_id.start_stage_id.id
            else:
                raise exceptions.ValidationError(
                    _("Cannot create ticket of type '%(type_name)s': This type have no start stage defined!") % {
                        'type_name': type_id.name})

        return super(HelpdeskTicket, self).create(vals_list)

    def _compute_attachment_count(self):
        for ticket in self:
            ticket.attachment_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', self._name),
                ('res_id', '=', ticket.id)
            ])

    def _compute_task_count(self):
        for ticket in self:
            ticket.task_count = self.env['task.task'].search_count([
                ('parent_id', '=', False),
                ('parent_ref_type', '=', self._name),
                ('parent_ref_id', '=', ticket.id)
            ])

    @api.depends('stage_id', 'type_id')
    def _compute_stage_routes(self):
        for ticket in self:
            routes = []
            for route in ticket.stage_id.route_out_ids:
                route._check_can_move(ticket)
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

            ticket.stage_routes = json.dumps({'routes': routes})

    @api.onchange('type_id')
    def _onchange_type_id(self):
        for ticket in self:
            if ticket.type_id and ticket.type_id.start_stage_id:
                ticket.stage_id = ticket.type_id.start_stage_id

    # TODO: настройку wf необходимо вынести в отдельный модуль, вызываемый метод прописан в js
    def action_move_task_along_route(self, route_id):
        self.ensure_one()
        route = self.env['helpdesk.ticket.stage.route'].browse(route_id)
        if route in self.stage_id.route_out_ids:
            if route.close:
                self.date_closed = datetime.today()
            self.stage_id = route.stage_to_id.id
            return None

        raise exceptions.UserError(_('Cannot move ticket (%(ticket)s) by this route (%(route)s)') %
                                   {
                                       'task': self.name,
                                       'route': route.display_name
                                   })

    # TODO: пустышка для вызова из таски при закрытии задачи. По идее тут необходимо закрывать тикет
    def process_task_result(self, date_closed, result_type='ok', feedback=False):
        pass

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
                """ % _("Add attachments for this ticket")
        }

    def action_open_tasks(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "res_model": "fleet.vehicle.assignation.log",
            "views": [[self.env.ref("hr_fleet.fleet_vehicle_assignation_log_employee_view_list").id, "tree"], [False, "form"]],
            "domain": [("driver_employee_id", "in", self.ids)],
            "context": dict(self._context, default_driver_id=self.user_id.partner_id.id, default_driver_employee_id=self.id),
            "name": "History Employee Cars",
        }

    def action_create_task(self):
        self.ensure_one()
        return {
            'name': _('Task'),
            'view_mode': 'form',
            'res_model': 'task.task',
            'type': 'ir.actions.act_window',
            'context': {
                'default_company_id': self.company_id.id,
                'default_name': self.name,
                'default_description': self.description,
                'default_parent_ref': '%s,%s' % (self._name,  self.id),
                'default_parent_ref_id': self.id,
                'default_parent_ref_type': self._name,
                'default_priority': self.priority
            },
            'target': 'new'
        }
