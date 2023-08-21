from odoo import models, fields, api


class travel_lines(models.Model):
    _name = 'travel.lines'

    npp = fields.Integer(string="Npp")
    travel_id = fields.Many2one('travel.travel', string='Head Travel', required=True, ondelete='cascade', index=True,
                                copy=False)
    product_id = fields.Many2one('product.product', string='Delivery Product', required=True, ondelete='restrict')
    descr = fields.Char(string="Description")
    line_price = fields.Float(string='Price')
    line_quantity = fields.Float(string='Quantity')
    line_sum = fields.Float(string='line summa', store=True, compute='_compute_line_sum', tracking=5)

    @api.depends('line_quantity', 'line_price')
    def _compute_line_sum(self):
        for travel_line in self:
            travel_line.line_sum = travel_line.line_quantity * travel_line.line_price
