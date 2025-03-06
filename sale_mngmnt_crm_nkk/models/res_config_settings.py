from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    auto_create_sale_order = fields.Boolean(related='company_id.auto_create_sale_order', readonly=False)
