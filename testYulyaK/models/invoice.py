from odoo import api, fields, models


class InvoiceModel(models.Model):
    _name = "invoice.test"
    _description = "Приходная накладная"

    organization_id = fields.Many2one('res.partner', string="Организация", required=True)
    total_amount = fields.Float(string="Сумма документа", compute='_compute_total_amount', required=True)
    warehouse_id = fields.Many2one('stock.warehouse', string="Склад поступления", required=True)
    invoice_date = fields.Date(string="Дата накладной", required=True)
    order_date = fields.Date(string="Дата ордера", readonly=True)
    invoice_lines = fields.One2many("invoice_line.test", "invoice_id", string="Спецификация", required=True)
    is_received = fields.Boolean(string="Оприходовано", default=False, readonly=True)
    stock_order_id = fields.Many2one("order.test", string="Складской ордер", readonly=True)

    @api.depends('invoice_lines.amount')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = sum(record.invoice_lines.mapped('amount'))

    def action_confirm(self):
        if not self.is_received:
            # Оприходовать документ
            self.is_received = True
            self.create_stock_order()
        pass

    def action_cancel(self):
        if self.is_received:
            # Отменить приход
            self.is_received = False
            self.delete_stock_order()
        pass

    def create_stock_order(self):
        print("Создание складского ордера")
        stock_order = self.env['order.test'].create({
            'order_date': fields.Date.today(),
            'warehouse': self.warehouse_id.id,
            'total_amount': self.total_amount
        })
        order_lines = []
        for invoice_line in self.invoice_lines:
            order_line = self.env['order_line.test'].create({
                'product': invoice_line.product.id,
                'quantity': invoice_line.quantity,
                'price': invoice_line.price,
                'amount': invoice_line.amount,
                'order_id': stock_order.id
            })
            order_lines.append(order_line.id)
        stock_order.order_lines = [(6, 0, order_lines)]
        self.stock_order_id = stock_order.id
        self.order_date = fields.Date.today()

    def delete_stock_order(self):
        print("Удаление складского ордера")
        if self.stock_order_id:
            self.stock_order_id.order_lines.unlink()
            self.stock_order_id.unlink()
            self.stock_order_id = False
            self.order_date = None


class InvoiceLineModel(models.Model):
    _name = "invoice_line.test"
    _description = ""

    invoice_id = fields.Many2one("invoice.test", string="ID", required=True)
    product = fields.Many2one('product.product', string="Продукт", required=True)
    quantity = fields.Float(string="Количество", required=True)
    price = fields.Float(string="Цена", required=True)
    amount = fields.Float(string="Сумма", compute="_compute_amount", required=True)

    @api.depends('quantity', 'price')
    def _compute_amount(self):
        for record in self:
            record.amount = record.quantity * record.price
