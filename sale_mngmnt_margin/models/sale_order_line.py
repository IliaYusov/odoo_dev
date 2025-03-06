from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    margin = fields.Float(string='Margin', compute='_compute_margin', digits='Product Price', precompute=True,
                          store=True)
    margin_percent = fields.Float(string='Margin (%)', compute='_compute_margin', precompute=True, store=True)
    purchase_price = fields.Monetary(string='Cost', copy=True)
    purchase_price_subtotal = fields.Monetary(string='Subtotal Cost', compute='_compute_purchase_price_subtotal',
                                              store=True)

    @api.depends('price_subtotal', 'product_uom_qty', 'purchase_price')
    def _compute_margin(self):
        for rec in self:
            rec.margin = rec.price_subtotal - (rec.purchase_price * rec.product_uom_qty)
            rec.margin_percent = rec.price_subtotal and rec.margin / rec.price_subtotal

    @api.depends('purchase_price', 'product_uom_qty')
    def _compute_purchase_price_subtotal(self):
        for rec in self:
            rec.purchase_price_subtotal = rec.purchase_price * rec.product_uom_qty
