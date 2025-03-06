from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    opportunity_id = fields.Many2one(related='order_id.opportunity_id', index=True, readonly=True)
