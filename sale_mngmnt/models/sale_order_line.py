from collections import defaultdict

from odoo import api, fields, models, _


class SaleOrderLine(models.Model):
    _name = 'sale.order.line'
    # _inherit = 'analytic.mixin'
    _description = 'Sales Order Line'
    _rec_names_search = ['name', 'order_id.name']
    _order = 'order_id, sequence, id'
    _check_company_auto = True

    order_id = fields.Many2one('sale.order', string='Sale Order', copy=False, index=True, ondelete='cascade',
                               required=True)
    date_order = fields.Date(related='order_id.date_order')
    partner_id = fields.Many2one(related='order_id.partner_id', string='Customer', index=True, precompute=True,
                                 store=True)
    salesperson_id = fields.Many2one(related='order_id.salesperson_id', string='Salesperson', precompute=True,
                                     store=True)
    currency_id = fields.Many2one(related='order_id.currency_id', readonly=True)
    currency_rate = fields.Float(related='order_id.currency_rate', readonly=True)
    account_price_include = fields.Boolean(related='order_id.account_price_include', precompute=True, readonly=True,
                                           store=True,
                                           help='Check this if the price you use on the product includes this tax.')
    company_id = fields.Many2one(related='order_id.company_id', index=True, precompute=True, store=True)
    company_currency_id = fields.Many2one(related='company_id.currency_id', readonly=True)
    sequence = fields.Integer(string='Sequence', default=1)
    product_id = fields.Many2one('product.product', string='Product',
                                 domain="[('sale_ok', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                 index='btree_not_null', ondelete='restrict')
    product_category_id = fields.Many2one(related='product_id.categ_id', string='Category', readonly=True, store=True)
    product_template_id = fields.Many2one('product.template', compute='_compute_product_template_id',
                                          string='Product Template',
                                          domain="[('sale_ok', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                          readonly=False, search='_search_product_template_id')
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', depends=['product_id'])
    name = fields.Text(compute='_compute_name', string='Description', precompute=True, readonly=False, required=True,
                       store=True)
    supplier_id = fields.Many2one('res.partner', string='Supplier', domain="[('is_company', '=', True)]")
    product_uom_id = fields.Many2one('uom.uom', compute='_compute_product_uom', string='Unit of Measure',
                                     domain="[('category_id', '=', product_uom_category_id)]", ondelete='restrict',
                                     precompute=True, readonly=False, store=True)
    product_uom_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', default=1.0, required=True)
    tax_ids = fields.Many2many('account.tax', compute='_compute_tax_ids', string='Taxes',
                               context={'active_test': False},
                               domain="[('type_tax_use', '=', 'sale'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                               precompute=True, readonly=False, required=True, store=True)
    pricelist_item_id = fields.Many2one('product.pricelist.item', compute='_compute_pricelist_item_id')
    price_unit = fields.Float(compute='_compute_price_unit', string='Unit Price', digits='Product Price',
                              precompute=True, readonly=False, required=True, store=True)
    discount = fields.Float(string='Discount (%)', digits='Discount')
    price_subtotal = fields.Monetary(string='Subtotal', compute='_compute_amount', precompute=True, store=True)
    price_tax = fields.Float(string='Total Tax', compute='_compute_amount', precompute=True, store=True)
    price_total = fields.Monetary(string='Total', compute='_compute_amount', precompute=True, store=True)

    # ------------------------------------------------------
    # COMPUTE METHODS
    # ------------------------------------------------------

    @api.depends('product_id')
    def _compute_product_template_id(self):
        for line in self:
            line.product_template_id = line.product_id.product_tmpl_id

    @api.depends('product_id')
    def _compute_product_uom_id(self):
        for rec in self:
            if not rec.product_uom_id or (rec.product_id.uom_id.id != rec.product_uom_id.id):
                rec.product_uom_id = rec.product_id.uom_id

    @api.depends('product_id')
    def _compute_name(self):
        for line in self:
            if not line.product_id:
                continue
            lang = line.order_id._get_lang()
            if lang != self.env.lang:
                line = line.with_context(lang=lang)
            name = line._get_sale_order_line_multiline_description_sale()
            line.name = name

    @api.depends('product_id', 'company_id')
    def _compute_tax_ids(self):
        taxes_by_product_company = defaultdict(lambda: self.env['account.tax'])
        lines_by_company = defaultdict(lambda: self.env['sale.order.line'])
        cached_taxes = {}
        for rec in self:
            lines_by_company[rec.company_id] += rec
        for product in self.product_id:
            for tax in product.taxes_id:
                taxes_by_product_company[(product, tax.company_id)] += tax
        for company, lines in lines_by_company.items():
            for line in lines.with_company(company):
                taxes = taxes_by_product_company[(line.product_id, company)]
                if not line.product_id or not taxes:
                    line.tax_ids = False
                    continue
                fiscal_position = line.order_id.fiscal_position_id
                cache_key = (fiscal_position.id, company.id, tuple(taxes.ids))
                cache_key += tuple()
                if cache_key in cached_taxes:
                    result = cached_taxes[cache_key]
                else:
                    result = fiscal_position.map_tax(taxes)
                    cached_taxes[cache_key] = result
                line.tax_ids = result

    @api.depends('product_id', 'product_uom_id', 'product_uom_qty')
    def _compute_pricelist_item_id(self):
        for rec in self:
            if not rec.product_id or not rec.order_id.pricelist_id:
                rec.pricelist_item_id = False
            else:
                rec.pricelist_item_id = rec.order_id.pricelist_id._get_product_rule(
                    rec.product_id,
                    quantity=rec.product_uom_qty or 1.0,
                    uom=rec.product_uom_id,
                    date=rec.order_id.date_order
                )

    @api.depends('product_id', 'product_uom_id', 'product_uom_qty')
    def _compute_price_unit(self):
        for rec in self:
            if not rec.product_uom_id or not rec.product_id:
                rec.price_unit = 0.0
            else:
                rec = rec.with_company(rec.company_id)
                price = rec._get_display_price()
                rec.price_unit = rec.product_id._get_tax_included_unit_price_from_price(
                    price,
                    rec.currency_id or rec.order_id.currency_id,
                    product_taxes=rec.product_id.taxes_id.filtered(lambda tax: tax.company_id == rec.env.company),
                    fiscal_position=rec.order_id.fiscal_position_id
                )

    @api.depends('product_uom_qty', 'price_unit', 'tax_ids', 'discount', 'account_price_include')
    def _compute_amount(self):
        for rec in self:
            tax_results = self.env['account.tax'].\
                _compute_taxes(base_lines=[rec._convert_to_tax_base_line_dict()])
            totals = list(tax_results['totals'].values())[0]
            amount_untaxed = totals['amount_untaxed']
            amount_tax = totals['amount_tax']

            rec.update({
                'price_subtotal': amount_untaxed,
                'price_tax': amount_tax,
                'price_total': amount_untaxed + amount_tax
            })

    def _search_product_template_id(self, operator, value):
        return [('product_id.product_tmpl_id', operator, value)]

    # ------------------------------------------------------
    # CORE METHODS OVERRIDES
    # ------------------------------------------------------

    def name_get(self):
        result = []
        for rec in self.sudo():
            name = '%s - %s' % (rec.order_id.name, rec.name and rec.name.split('\n')[0] or rec.product_id.name)
            if rec.partner_id.ref:
                name = '%s (%s)' % (name, rec.partner_id.ref)
            result.append((rec.id, name))
        return result

    # ------------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------------

    def _get_sale_order_line_multiline_description_sale(self):
        self.ensure_one()
        return self.product_id.get_product_multiline_description_sale()

    def _get_display_price(self):
        self.ensure_one()

        pricelist_price = self._get_pricelist_price()

        if self.order_id.pricelist_id.discount_policy == 'with_discount':
            return pricelist_price

        if not self.pricelist_item_id:
            return pricelist_price

        base_price = self._get_pricelist_price_before_discount()

        return max(base_price, pricelist_price)

    def _get_pricelist_price(self):
        self.ensure_one()
        self.product_id.ensure_one()

        price = self.pricelist_item_id._compute_price(
            product=self.product_id,
            quantity=self.product_uom_qty or 1.0,
            uom=self.product_uom_id,
            date=self.order_id.date_order,
            currency=self.currency_id
        )

        return price

    def _get_pricelist_price_before_discount(self):
        self.ensure_one()
        self.product_id.ensure_one()

        return self.pricelist_item_id._compute_price_before_discount(
            product=self.product_id,
            quantity=self.product_uom_qty or 1.0,
            uom=self.product_uom_id,
            date=self.order_id.date_order,
            currency=self.currency_id
        )

    def _convert_to_tax_base_line_dict(self):
        self.ensure_one()
        return self.env['account.tax']._convert_to_tax_base_line_dict(
            self,
            partner=self.order_id.partner_id,
            currency=self.order_id.currency_id,
            product=self.product_id,
            taxes=self.tax_ids,
            price_unit=self.price_unit,
            quantity=self.product_uom_qty,
            discount=self.discount,
            price_subtotal=self.price_subtotal,
            extra_context={
                'force_price_include': self.account_price_include
            }
        )
