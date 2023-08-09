from odoo import models, fields
from .ticket_stage import DEFAULT_BG_COLOR


class TicketStageType(models.Model):
    _name = 'helpdesk.ticket.stage.type'
    _description = 'Stage Type'

    code = fields.Char(required=True)
    name = fields.Char(required=True, translate=True)

    active = fields.Boolean(index=True, default=True)

    bg_color = fields.Char(string="Background Color", default=DEFAULT_BG_COLOR)
