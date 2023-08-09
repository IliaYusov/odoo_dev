from odoo import models, fields, api, _


class TicketType(models.Model):
    _name = "helpdesk.ticket.type"
    _description = "Ticket Type"
    _order = 'name, id'

    name = fields.Char(required=True, copy=True, translate=True)
    code = fields.Char(required=True, copy=True)
    active = fields.Boolean(default=True, index=True)
    description = fields.Text()

    stage_ids = fields.One2many('helpdesk.ticket.stage', 'ticket_type_id', string='Stages', copy=True)
    stage_count = fields.Integer(compute='_compute_stage_count', readonly=True)
    start_stage_id = fields.Many2one('helpdesk.ticket.stage', ondelete='set null', compute='_compute_start_stage_id',
                                     readonly=True, store=True)
    color = fields.Char(default='rgba(240,240,240,1)')

    route_ids = fields.One2many('helpdesk.ticket.stage.route', 'ticket_type_id', string='Stage Routes')
    route_count = fields.Integer(string='Routes', compute='_compute_route_count', readonly=True)

    _sql_constraints = [
        ('code_uniq',
         'UNIQUE (code)',
         'Code must be unique.')
    ]

    @api.depends('stage_ids')
    def _compute_stage_count(self):
        for ticket_type in self:
            ticket_type.stage_count = self.env['helpdesk.ticket.stage'].search_count([
                ('ticket_type_id', '=', ticket_type.id)
            ])

    @api.depends('route_ids')
    def _compute_route_count(self):
        for ticket_type in self:
            ticket_type.route_count = self.env['helpdesk.ticket.stage.route'].search_count([
                ('ticket_type_id', '=', ticket_type.id)
            ])

    @api.depends('stage_ids', 'stage_ids.sequence', 'stage_ids.ticket_type_id')
    def _compute_start_stage_id(self):
        for ticket_type in self:
            if ticket_type.stage_ids:
                ticket_type.start_stage_id = ticket_type.stage_ids.sorted(key=lambda r: r.sequence)[0]
            else:
                ticket_type.start_stage_id = False

    def _create_default_stages_and_routes(self):
        self.ensure_one()
        stage_to_do = self.env['helpdesk.ticket.stage'].create({
            'name': _('To Do'),
            'code': 'to_do',
            'ticket_type_id': self.id,
            'sequence': 1,
            'type_id': self.env.ref('helpdesk.ticket_stage_type_to_do').id
        })
        stage_done = self.env['helpdesk.ticket.stage'].create({
            'name': _('Done'),
            'code': 'done',
            'ticket_type_id': self.id,
            'sequence': 100,
            'closed': True,
            'type_id': self.env.ref('helpdesk.ticket_stage_type_done').id
        })
        self.env['helpdesk.ticket.stage.route'].create({
            'name': _('Done'),
            'stage_from_id': stage_to_do.id,
            'stage_to_id': stage_done.id,
            'ticket_type_id': self.id,
        })

    @api.model_create_multi
    def create(self, vals):
        ticket_types = super().create(vals)

        if self.env.context.get('create_default_stages'):
            for ticket_type in ticket_types:
                if not ticket_type.start_stage_id:
                    ticket_type._create_default_stages_and_routes()

        return ticket_types

    def action_create_default_stage_and_routes(self):
        self._create_default_stages_and_routes()

    def action_ticket_type_diagram(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('helpdesk.action_helpdesk_ticket_type_all_types')
        action['context'] = {'default_ticket_type_id': self.id}
        action.update({
            'res_model': 'helpdesk.ticket.type',
            'res_id': self.id,
            'views': [(False, 'diagram_plus'), (False, 'form')],
        })
        return action
