from odoo import api, Command, fields, models, _
from odoo.tools import groupby


class PurchaseRequestLineEstimation(models.Model):
    _name = 'purchase.request.line.estimation'
    _description = "Purchase Request Line Estimation"
    _order = 'request_id, request_line_id, id'
    _check_company_auto = True

    request_id = fields.Many2one('purchase.request', string='Request', ondelete='cascade', copy=True, index=True)
    request_line_id = fields.Many2one('purchase.request.line', string='Request Line', ondelete='cascade', copy=True,
                                      index=True, required=True)
    request_state = fields.Selection(related='request_id.state', string='Request State', store=True)
    company_id = fields.Many2one(related='request_line_id.company_id', string='Company', copy=False, index=True,
                                 precompute=True, store=True)
    is_favorite = fields.Boolean(string='Is Favorite', copy=False, default=False)
    vendor_id = fields.Many2one('res.partner', string='Vendor', copy=False, domain="[('is_company', '=', True)]")
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict', copy=False,
                                 change_default=True, check_company=True, index='btree_not_null',
                                 domain="[('purchase_ok', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', copy=False,
                                              depends=['product_id'], readonly=True)
    product_barcode = fields.Char(related='product_id.barcode', string='Barcode', copy=False, depends=['product_id'],
                                  readonly=True)
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure', compute='_compute_product_uom',
                                     ondelete='restrict', copy=False, readonly=False, precompute=True, store=True,
                                     domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_qty = fields.Float(string='Quantity', copy=False, digits='Product Unit of Measure', default=1.0,
                                   precompute=True, readonly=False, required=True, store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', copy=False, precompute=True,
                                  default=lambda self: self.company_id.currency_id)
    # tax_id = fields.Many2many('account.tax', string='Taxes', compute='_compute_tax_id', check_company=True,
    #                           context={'active_test': False}, precompute=True, readonly=False, store=True)
    price_unit = fields.Float(string='Unit Price', digits='Product Price', compute='_compute_price_unit',
                              inverse='_inverse_price_unit', precompute=True, readonly=False, required=True, store=True,
                              default=0.0)
    price_subtotal = fields.Monetary(string='Subtotal', compute='_compute_amount', store=True)

    delivery_time = fields.Integer(string='Delivery Time', copy=False)
    vendor_guarantee = fields.Integer(string='Vendor Guarantee', copy=False)
    supplier_id = fields.Many2one('res.partner', string='Supplier', copy=False, domain="[('is_company', '=', True)]")
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms', copy=False,
                                      check_company=True, required=True, tracking=True, precompute=True,
                                      store=True, default=lambda self: self.supplier_id.property_payment_term_id)
    comment = fields.Char(string='Comment', copy=False)

    technical_requirements = fields.Boolean(string='Only Technical Requirements', default=False)
    position_type = fields.Char(string='Type', copy=False, default='estimation', store=False)
    component_ids = fields.One2many('purchase.request.line.component', 'request_line_estimation_id',
                                    string='Components')
    characteristic_ids = fields.One2many('purchase.request.line.characteristic', 'request_line_estimation_id',
                                         string='Characteristics')

    @api.depends('product_id')
    def _compute_product_uom(self):
        for line in self:
            if not line.product_uom_id or (line.product_id.uom_id.id != line.product_uom.id):
                line.product_uom_id = line.product_id.uom_id

    @api.depends('component_ids')
    def _compute_price_unit(self):
        self.price_unit = sum(self.component_ids.mapped('price_unit'))

    def _inverse_price_unit(self):
        if self.price_unit != sum(self.component_ids.mapped('price_unit')):
            for component in self.component_ids:
                component.price_unit = 0.0

    @api.depends('product_uom_qty', 'price_unit')
    def _compute_amount(self):
        for line in self:
            tax_results = self.env['account.tax']._compute_taxes([line._convert_to_tax_base_line_dict()])
            totals = list(tax_results['totals'].values())[0]
            amount_untaxed = totals['amount_untaxed']
            amount_tax = totals['amount_tax']

            line.update({'price_subtotal': amount_untaxed})

    def _convert_to_tax_base_line_dict(self):
        self.ensure_one()
        return self.env['account.tax']._convert_to_tax_base_line_dict(
            self,
            partner=self.supplier_id,
            currency=self.currency_id,
            product=self.product_id,
            taxes=False,
            price_unit=self.price_unit,
            quantity=self.product_uom_qty,
            price_subtotal=self.price_subtotal,
        )

    def action_create_quotation(self):
        active_ids = self.env.context.get('active_ids', [])
        active_records = self.env[self._name].browse(active_ids)
        group_records = groupby(active_records, lambda f: f.request_line_id)

        order_lines = []
        for record in active_records:
            # components = []
            # for component in line.component_ids:
            #     cmp = component.copy({'request_line_id': False})
            #     components.append(cmp.id)

            order_line = dict(
                vendor_id=record.vendor_id.id,
                purchase_request_line_id=record.id,
                product_id=record.product_id.id,
                product_uom=record.product_uom_id.id,
                product_uom_qty=record.product_uom_qty,
                currency_id=record.currency_id.id,
                price_unit=record.price_unit,
                delivery_time=record.delivery_time,
                vendor_guarantee=record.vendor_guarantee,
                supplier_id=record.supplier_id.id,
                payment_term_id=record.payment_term_id.id,
                comment=record.comment
                # component_ids=[Command.link(cmp_id) for cmp_id in components]
            )
            order_lines.append((Command.CREATE, 0, order_line))
        return {
            'name': _('Quotation'),
            'view_mode': 'form',
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'context': {
                'default_company_id': self.request_id.company_id.id,
                'default_currency_id': self.request_id.company_id.currency_id.id,
                'default_partner_id': self.request_id.partner_id.id,
                'default_purchase_request_id': self.request_id.id,
                'default_deal_id': self.request_id.project_id.id,
                'default_payment_term_id': self.request_id.partner_payment_term_id.id,
                'default_user_id': self.request_id.project_id.project_manager_id.user_id.id,
                'default_note': self.request_id.special_conditions,
                'default_require_signature': False,
                'default_require_payment': False,
                'default_order_line': order_lines
            },
            'target': 'new'
        }
