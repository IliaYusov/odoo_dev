from odoo import api, fields, models

class OrderTest(models.Model):
    _name = "order.test"
    _description = "Складские ордера"

    order_date = fields.Date(string="Дата ордера", default=fields.Date.today(), required=True)
    warehouse = fields.Many2one("stock.warehouse", string="Склад", required=True)
    total_amount = fields.Float(string="Сумма документа", required=True)
    order_lines = fields.One2many('order_line.test', 'order_id', string="Спецификация")

class OrderLine(models.Model):
    _name = "order_line.test"
    _description = ""

    product = fields.Many2one("product.product", string="Продукт", required=True)
    quantity = fields.Float(string="Количество", required=True)
    price = fields.Float(string="Цена", required=True)
    amount = fields.Float(string="Сумма", required=True)
    order_id = fields.Many2one('order.test', string="Ордер", required=True)
