from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    license_workflow_id = fields.Many2one('workflow.workflow', string='License Workflow', check_company=True,
                                          domain="[('model_id', '=', 'license.license')]")
