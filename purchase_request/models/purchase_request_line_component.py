from odoo import api, fields, models, _


class PurchaseRequestLineComponent(models.Model):
    """
        Риторический вопрос, как заставить себя делать нижеидущую хрень?!
    """
    _name = 'purchase.request.line.component'
    _description = "Purchase Request Line Component"
    _order = 'request_line_id, sequence, id'
    _check_company_auto = True

    request_line_id = fields.Many2one('purchase.request.line', string='Request Line', ondelete='cascade',
                                      copy=True, index=True)
    request_line_estimation_id = fields.Many2one('purchase.request.line.estimation', string='Request Line Estimation',
                                                 ondelete='cascade', copy=True, index=True)
    company_id = fields.Many2one('res.company', string='Company', compute='_compute_company_id', copy=False, index=True,
                                 store=True)
    sequence = fields.Integer(string='Sequence', copy=True, default=1)
    vendor_id = fields.Many2one('res.partner', string='Vendor', copy=False, precompute=True,
                                domain="[('is_company', '=', True)]",
                                default=lambda self: self.request_line_id.vendor_id)
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict', copy=True,
                                 change_default=True, check_company=True, index='btree_not_null',
                                 domain="[('purchase_ok', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', copy=False,
                                              depends=['product_id'], readonly=True)
    product_barcode = fields.Char(related='product_id.barcode', string='Barcode', copy=False, depends=['product_id'],
                                  readonly=True)
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure', compute='_compute_product_uom_id',
                                     ondelete='restrict', copy=True, readonly=False, precompute=True, store=True,
                                     domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_qty = fields.Float(string='Quantity', copy=True,
                                   digits='Product Unit of Measure', default=1.0, store=True, readonly=False,
                                   required=True, precompute=True)
    currency_id = fields.Many2one(related='request_line_estimation_id.currency_id', string='Currency', copy=False,
                                  precompute=True, readonly=True)
    price_unit = fields.Float(string='Unit Price', digits='Product Price', precompute=True, readonly=False,
                              required=False, store=True, default=0.0)

    @api.depends('product_id')
    def _compute_product_uom_id(self):
        for line in self:
            if not line.product_uom_id or (line.product_id.uom_id.id != line.product_uom_id.id):
                line.product_uom_id = line.product_id.uom_id

    @api.depends('request_line_id')
    def _compute_company_id(self):
        for line in self:
            if line.request_line_id:
                line.company_id = line.request_line_id.company_id.id
            elif line.request_line_estimation_id:
                line.company_id = line.request_line_estimation_id.company_id.id
            else:
                line.company_id = self.env.company
