from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    margin = fields.Monetary(string='Margin', compute='_compute_margin', store=True)
    margin_percent = fields.Float(string='Margin (%)', compute='_compute_margin', group_operator='avg', store=True)
    amount_purchase_total = fields.Monetary(string='Cost Amount Total', compute='_compute_margin', store=True)

    @api.depends('amount_untaxed', 'line_ids.margin', 'line_ids.purchase_price_subtotal')
    def _compute_margin(self):
        if not all(self._ids):
            for rec in self:
                rec.margin = sum(rec.line_ids.mapped('margin'))
                rec.margin_percent = rec.amount_untaxed and rec.margin / rec.amount_untaxed
                rec.amount_purchase_total = sum(rec.line_ids.mapped('purchase_price_subtotal'))
        else:
            lines_data = self.env['sale.order.line'].read_group(
                domain=[('order_id', 'in', self.ids)],
                fields=['order_id', 'margin:sum', 'purchase_price_subtotal:sum'],
                groupby=['order_id']
            )
            mapped_data = {
                d['order_id'][0]: {'margin': d['margin'], 'amount_purchase_total': d['purchase_price_subtotal']}
                for d in lines_data
            }
            for rec in self:
                order_data = mapped_data.get(rec.id, {})
                rec.margin = order_data.get('margin', 0.0)
                rec.margin_percent = rec.amount_untaxed and rec.margin / rec.amount_untaxed
                rec.amount_purchase_total = order_data.get('amount_purchase_total', 0.0)
