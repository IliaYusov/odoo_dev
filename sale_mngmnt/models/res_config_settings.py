from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    quotation_validity_days = fields.Integer(related='company_id.quotation_validity_days', readonly=False)

    module_sale_mngmnt_margin = fields.Boolean(string='Margins')

    # ------------------------------------------------------
    # ONCHANGE METHODS
    # ------------------------------------------------------

    @api.onchange('quotation_validity_days')
    def _onchange_quotation_validity_days(self):
        if self.quotation_validity_days < 0:
            self.quotation_validity_days = self.env['res.company'].default_get(
                ['quotation_validity_days']
            )['quotation_validity_days']
            return {
                'warning': {
                    'title': _('Warning'),
                    'message': _('Quotation Validity is required and must be greater or equal to 0.'),
                }
            }
