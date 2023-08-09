from odoo import models, fields, api, exceptions, _

DEFAULT_BG_COLOR = 'rgba(120,120,120,1)'


class TicketStage(models.Model):
    _name = "helpdesk.ticket.stage"
    _description = "Ticket Stage"
    _order = "sequence"

    name = fields.Char(required=True, string='Name', translate=True)
    code = fields.Char(required=True, string='Code')

    type_id = fields.Many2one('helpdesk.ticket.stage.type', string="Stage Type", required=True, index=True,
                              ondelete="restrict")
    ticket_type_id = fields.Many2one('helpdesk.ticket.type', string='Ticket Type', ondelete='cascade', required=True,
                                     index=True)

    active = fields.Boolean(default=True, index=True)
    sequence = fields.Integer(default=5, index=True)

    description = fields.Text()
    bg_color = fields.Char(default=DEFAULT_BG_COLOR, string="Background Color")

    use_custom_colors = fields.Boolean()
    res_bg_color = fields.Char(string="Background Color", compute='_compute_custom_colors', readonly=True)

    route_in_ids = fields.One2many('helpdesk.ticket.stage.route', 'stage_to_id', string='Incoming Routes')
    route_out_ids = fields.One2many('helpdesk.ticket.stage.route', 'stage_from_id', string='Outgoing Routes')

    previous_stage_ids = fields.Many2many('helpdesk.ticket.stage', 'ticket_stage_prev_stage_ids_rel',
                                          string='Previous stages', column1='stage_id', column2='prev_stage_id',
                                          compute='_compute_previous_stage_ids', store=True)

    closed = fields.Boolean(index=True)
    diagram_position = fields.Char(readonly=True)

    _sql_constraints = [
        ('stage_name_uniq',
         'UNIQUE (ticket_type_id, name)',
         'Stage name must be uniq for ticket type'),
        ('stage_code_uniq',
         'UNIQUE (ticket_type_id, code)',
         'Stage code must be uniq for ticket type')
    ]

    @api.depends('ticket_type_id', 'ticket_type_id.stage_ids',
                 'ticket_type_id.route_ids',
                 'ticket_type_id.route_ids.stage_from_id',
                 'ticket_type_id.route_ids.stage_to_id')
    def _compute_previous_stage_ids(self):
        for stage in self:
            route_ids = stage.ticket_type_id.route_ids.filtered(lambda r: r.stage_to_id == stage)

            stage_ids = route_ids.mapped('stage_from_id')
            stage.previous_stage_ids = stage_ids
            stage.invalidate_recordset()

    @api.depends('bg_color', 'type_id', 'use_custom_colors')
    def _compute_custom_colors(self):
        for rec in self:
            if rec.use_custom_colors:
                rec.res_bg_color = rec.bg_color
            elif rec.type_id:
                rec.res_bg_color = rec.type_id.bg_color
            else:
                rec.res_bg_color = DEFAULT_BG_COLOR
