from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import pytz
from datetime import timedelta
import datetime


class ProjectBudgetAmountSpec(models.Model):
    _name = 'project_budget.amount_spec'
    _description = "projects amount specification"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _get_default_amount_spec_type(self):
        context = self.env.context
        print('_get_default_amount_spec_type context = ', context)
        value = ''
        if context.get("revenue_from_the_sale_of_works"):
            value = 'revenue_from_the_sale_of_works'
        if context.get("revenue_from_the_sale_of_goods"):
            value = 'revenue_from_the_sale_of_goods'

        if context.get("cost_of_goods"):
            value = 'cost_of_goods'
        if context.get("travel_expenses"):
            value = 'travel_expenses'
        if context.get("third_party_works"):
            value = 'third_party_works'
        if context.get("representation_expenses"):
            value = 'representation_expenses'
        if context.get("rko_other"):
            value = 'rko_other'
        if context.get("warranty_service_costs"):
            value = 'warranty_service_costs'
        if context.get("other_expenses"):
            value = 'other_expenses'
        if context.get("transportation_expenses"):
            value = 'transportation_expenses'

        print('_get_default_amount_spec_type value = ', value)
        return value

    def _get_domain_currency(self):
        context = self.env.context
        currency_list = []
        currency_list.append(self.env.company.currency_id.id)
        projects_id = -1
        if context.get("active_model") == "project_budget.projects":
            projects_id = context.get("active_id")
        cur_project = self.env['project_budget.projects'].search([('id', '=', projects_id)])
        print('cur_project = ', cur_project)
        for each in cur_project.project_currency_rates_ids:
            print('each =',each)
            currency_list.append(each.currency_id.id)
        domain = [('id', 'in', currency_list)]
        return domain

    projects_id = fields.Many2one('project_budget.projects', string='projects_id', index=True, ondelete='cascade')
    type = fields.Selection([('revenue_from_the_sale_of_works', 'revenue_from_the_sale_of_works'), ('revenue_from_the_sale_of_goods', 'revenue_from_the_sale_of_goods'),
                             ('cost_of_goods', 'cost_of_goods'),('travel_expenses', 'travel_expenses'),('third_party_works', 'third_party_works'),
                             ('representation_expenses', 'representation_expenses'),('transportation_expenses', 'transportation_expenses'),
                             ('rko_other', 'rko_other'),('warranty_service_costs', 'warranty_service_costs'),('other_expenses', 'other_expenses'),
                            ], required=True, index=True, default= _get_default_amount_spec_type,  copy=True,)
    currency_id = fields.Many2one('res.currency', string='Account Currency',  domain = _get_domain_currency)

    name = fields.Char(string='name',tracking=True, required = True)
    summa = fields.Monetary(string='position sum',tracking=True)
