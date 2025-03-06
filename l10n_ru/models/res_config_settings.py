from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    account_price_include = fields.Selection(related='company_id.account_price_include',
                                             string='Default Sales Price Include', readonly=False, required=True,
                                             help='Default on whether the sales price used on the product and invoices with this Company includes its taxes.')
