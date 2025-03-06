from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    auto_create_sale_order = fields.Boolean(string='Creation sale order', default=False)
