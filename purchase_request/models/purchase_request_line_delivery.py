from odoo import fields, models, _


class PurchaseRequestLineDelivery(models.Model):
    _name = 'purchase.request.line.delivery'
    _description = "Purchase Request Line Delivery"
    _order = 'request_id, request_line_id, id'

    request_id = fields.Many2one('purchase.request', string='Request', ondelete='cascade', copy=True, index=True,
                                 required=True)
    request_line_id = fields.Many2one('purchase.request.line', string='Request Line', ondelete='cascade',
                                      copy=True, index=True, required=True)
    product_id = fields.Many2one(related='request_line_id.product_id', string='Product', copy=False,
                                 depends=['request_line_id'], index='btree_not_null', readonly=True, store=True)
    product_uom_qty = fields.Float(related='request_line_id.product_uom_qty', string='Quantity', copy=False,
                                   depends=['product_id'], digits='Product Unit of Measure', readonly=True, store=True)
    delivery_address_id = fields.Many2one('res.partner', copy=False,
                                          domain="[('parent_id', '=', parent.customer_id), ('type', '=', 'delivery')]")
    cargo_insurance_service = fields.Boolean(string='Cargo Insurance', copy=False, default=False)
    unloading_service = fields.Boolean(string='Unloading Service', copy=False, default=False)
    rise_floor_service = fields.Boolean(string='Rise Floor Service', copy=False, default=False)
    comment = fields.Char(string='Comment', copy=False)
