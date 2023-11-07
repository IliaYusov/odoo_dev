from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    archive_previous_decisions = fields.Boolean(
        string='Archive Previous Decisions',
        config_parameter='document_flow.archive_previous_decisions'
    )
