from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    auto_currency_update = fields.Boolean(string="Auto Currency Update")
