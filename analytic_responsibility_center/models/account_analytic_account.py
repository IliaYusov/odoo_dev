from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.account'

    sequence = fields.Integer(string='Sequence', default=1)

    head_id = fields.Many2one('res.users', string='The Head', copy=False, domain="[('company_ids', 'in', company_id)]")

    print_name = fields.Char(string='Printed Name', copy=False)
