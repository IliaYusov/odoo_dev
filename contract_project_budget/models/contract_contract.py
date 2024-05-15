from odoo import fields, models


class Contract(models.Model):
    _inherit = 'contract.contract'

    project_id = fields.Many2one('project_budget.projects', string='Project', copy=True,
                                 domain="[('budget_state', '=', 'work'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                 tracking=True)
