from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    opportunity_id = fields.Many2one('project_budget.projects', string='Opportunity', check_company=True,
                                     depends=['partner_id'],
                                     domain="[('budget_state', '=', 'work'), ('step_status', '=', 'project'), ('partner_id', '=', partner_id), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                     groups='project_budget.project_budget_users,project_budget.project_budget_admin')
