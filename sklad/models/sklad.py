from odoo import models, fields, api


class mol(models.Model):
    _name = 'sklad.mol'

    name = fields.Char(string="MOL FIO", required=True)
    code = fields.Char(string="MOL code", required=True)
    descr = fields.Char(string="MOL description")
    isArchive = fields.Boolean(string="MOL archived")

class party(models.Model):
    _name = 'sklad.party'

    name = fields.Char(string="party FIO", required=True)
    code = fields.Char(string="party code", required=True)
    descr = fields.Char(string="party description")
    isArchive = fields.Boolean(string="party archived")

class order(models.Model):
    _name = 'sklad.order'

    number = fields.Char(string="Order number",required=True)
    dord = fields.Date(string="Order date",required=True, index=True)
    typeorder = fields.Selection([('in', 'Incoming') , ('out', 'Expense')], required=True,  default='in', index=True)
    descr = fields.Char(string="Order description")
    warehouse_id = fields.Many2one('stock.location', string='Warehouse to' , company_dependent=True, check_company=True, required=True, ondelete='restrict', index=True)
    mol_id = fields.Many2one('sklad.mol', string='MOL' , index=True)
    sum = fields.Float(string="Total order summa ", store=True, compute='_compute_total_order', tracking=5)
    order_specification_ids = fields.One2many(
        comodel_name='sklad.order_spec',
        inverse_name='order_id',
        string="Order specification",
        copy=True, auto_join=True)

    @api.depends('order_specification_ids', 'order_specification_ids.price','order_specification_ids.quantity')
    def _compute_total_order(self):
        """подсчитываем итоговую сумму и количество позиций спецификации"""
        for order in self:
            order_spec = order.order_specification_ids
            order.sum = sum(order_spec.mapped('sum'))

class order_specification(models.Model):
    _name = 'sklad.order_spec'
    dord = fields.Date(string="Order date", required=True, compute='_compute_reference', index=True)
    typeorder = fields.Selection([('in', 'Incoming'), ('out', 'Expense')], required=True, index=True)
    order_id = fields.Many2one('sklad.order', string='Order', required=True, ondelete='cascade', index=True, copy=False)
    product_id = fields.Many2one('product.product', string='Delivery Product', required=True, ondelete='restrict', index=True)
    party_id = fields.Many2one('sklad.party', string='party', index=True)
    warehouse_id = fields.Many2one('stock.location', string='Warehouse to' , compute='_compute_reference', index=True)
    mol_id = fields.Many2one('sklad.mol', string='MOL' , compute='_compute_reference', index=True)
    descr = fields.Char(string="Description")
    price = fields.Float(string='Price')
    quantity = fields.Float(string='Quantity')
    sum = fields.Float(string='specification summa', store=True, compute='_compute_speec_sum', tracking=5)

    @api.depends('quantity', 'price')
    def _compute_speec_sum(self):
        for order_spec in self:
            order_spec.sum = order_spec.quantity * order_spec.price

    @api.depends('order_id.warehouse_id', 'order_id.mol_id', 'order_id.dord', 'order_id.typeorder')
    def _compute_reference(self):
        for order_spec in self:
            order_spec.warehouse_id = order_spec.order_id.warehouse_id
            order_spec.mol_id = order_spec.order_id.mol_id
            order_spec.dord = order_spec.order_id.dord
            order_spec.typeorder = order_spec.order_id.typeorder

