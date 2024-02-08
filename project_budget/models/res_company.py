from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    is_vendor = fields.Boolean(string="Is Vendor")
