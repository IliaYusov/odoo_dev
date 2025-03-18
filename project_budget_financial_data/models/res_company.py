from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    use_financial_data = fields.Boolean(string='Use financial data', default=True)
