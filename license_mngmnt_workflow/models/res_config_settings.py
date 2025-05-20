from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    license_workflow_id = fields.Many2one(related='company_id.license_workflow_id', readonly=False)
