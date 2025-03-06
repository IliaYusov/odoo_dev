from odoo import fields, models, _

PRICE_INCLUDE_TYPES = [
    ('tax_included', _('Tax Included')),
    ('tax_excluded', _('Tax Excluded'))
]


class ResCompany(models.Model):
    _inherit = 'res.company'

    account_price_include = fields.Selection(selection=PRICE_INCLUDE_TYPES, string='Default Sales Price Include',
                                             default='tax_excluded', required=True,
                                             help='Default on whether the sales price used on the product and invoices with this Company includes its taxes.')
