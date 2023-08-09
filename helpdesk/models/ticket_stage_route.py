from odoo import models, fields, api, exceptions, _


class TicketStageRoute(models.Model):
    _name = "helpdesk.ticket.stage.route"
    _description = "Ticket Stage Route"
    _order = "sequence"

    name = fields.Char(translate=True)
    sequence = fields.Integer(default=5, index=True, required=True, tracking=True)
    stage_from_id = fields.Many2one('helpdesk.ticket.stage', string='From', ondelete='restrict', required=True, index=True,
                                    tracking=True)
    stage_to_id = fields.Many2one('helpdesk.ticket.stage', string='To', ondelete='restrict', required=True, index=True,
                                  tracking=True)
    ticket_type_id = fields.Many2one('helpdesk.ticket.type', 'Ticket Type', ondelete='cascade', required=True, index=True,
                                     tracking=True)
    close = fields.Boolean(related='stage_to_id.closed', store=True, index=True, readonly=True)

    require_comment = fields.Boolean(store=True, help="If set, then user will be asked for comment on this route")

    button_style = fields.Selection([
        ('primary', 'Primary'),
        ('secondary', 'Secondary'),
        ('success', 'Success'),
        ('danger', 'Danger'),
        ('warning', 'Warning'),
        ('info', 'Info'),
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('link', 'Link'),
    ], required=True, default='primary', string='Button style')

    _sql_constraints = [
        ('stage_stage_from_to_type_uniq',
         'UNIQUE (ticket_type_id, stage_from_id, stage_to_id)',
         'Such route already present in this ticket type')
    ]

    def name_get(self):
        res = []
        for record in self:
            name = "%s -> %s" % (record.stage_from_id.name, record.stage_to_id.name)
            if record.name:
                name = "%s [%s]" % (name, record.name)

            if self.env.context.get('name_only', False) and record.name:
                name = record.name

            res += [(record.id, name)]
        return res

    # todo: по идее, нужно проверять имеет ли пользователь права двигать таску, пока заглушка
    def _check_can_move(self, ticket):
        pass

    @api.model
    def check_route(self, ticket, to_stage_id):
        route = self.search([
            ('ticket_type_id', '=', ticket.type_id.id),
            ('stage_from_id', '=', ticket.stage_id.id),
            ('stage_to_id', '=', to_stage_id)
        ])
        if not route:
            TicketStage = self.env['ticket.stage']
            stage = TicketStage.browse(to_stage_id) if to_stage_id else None
            raise exceptions.ValidationError(_(
                "Cannot move ticket to this stage: no route.\n"
                "\tTicket: %(ticket)s\n"
                "\tTo stage id: %(to_stage_id)s\n"
                "\tTo stage name: %(to_stage_name)s\n"
                "\tFrom stage name: %(from_stage_name)s\n"
            ) % {
                'ticket': ticket.name,
                'to_stage_id': to_stage_id,
                'to_stage_name': stage.name if stage else None,
                'from_stage_name': (ticket.stage_id.name if ticket.stage_id else None)
            })

        return route
