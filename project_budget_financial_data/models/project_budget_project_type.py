from odoo import models, fields


class ProjectType(models.Model):
    _inherit = 'project_budget.project_type'

    is_revenue_from_the_sale_of_works = fields.Boolean(string='is_revenue_from_the_sale_of_works(services)',tracking=True, default=True)
    is_revenue_from_the_sale_of_goods = fields.Boolean(string='is_revenue_from the sale of goods',tracking=True, default=True)
    is_cost_of_goods = fields.Boolean(string='is_cost_of_goods', tracking=True, default=True)
    is_own_works_fot = fields.Boolean(string='is_own_works_fot', tracking=True, default=True)
    is_third_party_works = fields.Boolean(string='is_third_party_works(subcontracting)', tracking=True, default=True)
    is_awards_on_results_project = fields.Boolean(string='is_Awards based on the results of the project', tracking=True, default=True)
    is_transportation_expenses = fields.Boolean(string='is_transportation_expenses', tracking=True, default=True)
    is_travel_expenses = fields.Boolean(string='is_travel_expenses', tracking=True, default=True)
    is_representation_expenses = fields.Boolean(string='is_representation_expenses', tracking=True, default=True)
    is_warranty_service_costs = fields.Boolean(string='is_Warranty service costs', tracking=True, default=True)
    is_rko_other = fields.Boolean(string='is_rko_other', tracking=True, default=True)
    is_other_expenses = fields.Boolean(string='is_other_expenses', tracking=True, default=True)
