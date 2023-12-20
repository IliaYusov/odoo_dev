from odoo import api, fields, models, _


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    purchase_request_line_id = fields.Many2one('purchase.request.line', string='Purchase Request Line', copy=False)

    vendor_id = fields.Many2one('res.partner', string='Vendor', copy=False, domain="[('is_company', '=', True)]")
    technical_requirements = fields.Boolean(string='Only Technical Requirements', default=False)
    # component_ids = fields.One2many('purchase.request.line.component', 'sale_order_line_id', string='Components',
    #                                 copy=True)

    currency_id = fields.Many2one('res.currency', string='Currency', copy=False, depends=[],
                                  readonly=False, related=False, default=False)
    currency_rate = fields.Float(string='Currency Rate', compute='_compute_currency_rate', digits=(12, 6),
                                 precompute=True, store=True)
    delivery_time = fields.Integer(string='Delivery Time', copy=False)
    vendor_guarantee = fields.Integer(string='Vendor Guarantee', copy=False)
    supplier_id = fields.Many2one('res.partner', string='Supplier', copy=False, domain="[('is_company', '=', True)]")
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms', copy=False,
                                      check_company=True, required=True, tracking=True, precompute=True,
                                      store=True, default=lambda self: self.supplier_id.property_payment_term_id)
    comment = fields.Char(string='Comment', copy=False)

    hide_characteristics = fields.Boolean(copy=False, default=False, store=False)

    @api.depends('order_id.conversion_percent', 'order_id.currency_id', 'order_id.date_order', 'currency_id', 'company_id')
    def _compute_currency_rate(self):
        cache = {}
        for line in self:
            order_date = line.order_id.date_order.date()
            if not line.company_id:
                line.currency_rate = line.currency_id.with_context(date=order_date).rate or 1.0
                continue
            elif not line.currency_id:
                line.currency_rate = 1.0
            else:
                key = (line.company_id.id, order_date, line.currency_id.id)
                if key not in cache:
                    cache[key] = self.env['res.currency']._get_conversion_rate(
                        from_currency=line.currency_id,
                        to_currency=line.company_id.currency_id,
                        company=line.company_id,
                        date=order_date
                    ) * self.env['res.currency']._get_conversion_rate(
                        from_currency=line.company_id.currency_id,
                        to_currency=line.order_id.currency_id,
                        company=line.company_id,
                        date=order_date,
                    )
                line.currency_rate = cache[key]

    def _convert_to_tax_base_line_dict(self):
        self.ensure_one()
        price_unit = self.price_unit * self.currency_rate
        return self.env['account.tax']._convert_to_tax_base_line_dict(
            self,
            partner=self.order_id.partner_id,
            currency=self.currency_id,
            product=self.product_id,
            taxes=self.tax_id,
            price_unit=price_unit if self.order_id.conversion_percent == 0 else price_unit + (
                        price_unit * self.order_id.conversion_percent / 100),
            quantity=self.product_uom_qty,
            discount=self.discount,
            price_subtotal=self.price_subtotal,
        )

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id', 'currency_rate')
    def _compute_amount(self):
        for line in self:
            tax_results = self.env['account.tax']._compute_taxes([line._convert_to_tax_base_line_dict()])
            totals = list(tax_results['totals'].values())[0]
            amount_untaxed = totals['amount_untaxed']
            amount_tax = totals['amount_tax']

            line.update({
                'price_subtotal': amount_untaxed,
                'price_tax': amount_tax,
                'price_total': amount_untaxed + amount_tax
            })
