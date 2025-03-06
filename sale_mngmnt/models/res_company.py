from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    _sql_constraints = [
        ('check_quotation_validity_days', 'CHECK(quotation_validity_days >= 0)',
         'You cannot set a negative number for the default quotation validity.'
         ' Leave empty (or 0) to disable the automatic expiration of quotations.'),
    ]

    quotation_validity_days = fields.Integer(string='Default Quotation Validity', default=30,
                                             help='Days between quotation proposal and expiration.'
                                                  '0 days means automatic expiration is disabled')
