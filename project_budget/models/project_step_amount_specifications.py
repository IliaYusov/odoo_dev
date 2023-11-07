from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import pytz
from datetime import timedelta
import datetime

class project_budget_step_amount_spec(models.Model):

    def _get_default_amount_spec_type(self):
        context = self.env.context
        print('_get_default_amount_spec_type context = ', context)
        value = ''
        if context.get("revenue_from_the_sale_of_works") == True:
            value = 'revenue_from_the_sale_of_works'
        if context.get("revenue_from_the_sale_of_goods") == True:
            value = 'revenue_from_the_sale_of_goods'

        if context.get("cost_of_goods") == True:
            value = 'cost_of_goods'
        if context.get("travel_expenses") == True:
            value = 'travel_expenses'
        if context.get("third_party_works") == True:
            value = 'third_party_works'
        if context.get("representation_expenses") == True:
            value = 'representation_expenses'
        if context.get("rko_other") == True:
            value = 'rko_other'
        if context.get("warranty_service_costs") == True:
            value = 'warranty_service_costs'
        if context.get("other_expenses") == True:
            value = 'other_expenses'
        if context.get("transportation_expenses") == True:
            value = 'transportation_expenses'

        print('_get_default_amount_spec_type value = ', value)
        return value

    def _get_domain_currency(self):
        context = self.env.context
        print('step_amount_spec _get_domain_currency context = ',context)
        currency_list = []
        currency_list.append(self.env.company.currency_id.id)
        projects_id = -1
        if context.get("active_model") == "project_budget.project_steps":
            projects_id = context.get("projects_id")
        cur_project = self.env['project_budget.projects'].search([('id', '=', projects_id)])
        print('cur_project = ', cur_project)
        for each in cur_project.project_currency_rates_ids:
            print('each =',each)
            currency_list.append(each.currency_id.id)
        domain = [('id', 'in', currency_list)]
        return domain

    _name = 'project_budget.step_amount_spec'
    _description = "projects step amount specification"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    step_id = fields.Many2one('project_budget.project_steps', string='step_id', index=True, ondelete='cascade')
    type = fields.Selection([('revenue_from_the_sale_of_works', 'revenue_from_the_sale_of_works'), ('revenue_from_the_sale_of_goods', 'revenue_from_the_sale_of_goods'),
                             ('cost_of_goods', 'cost_of_goods'),('travel_expenses', 'travel_expenses'),('third_party_works', 'third_party_works'),
                             ('representation_expenses', 'representation_expenses'),('transportation_expenses', 'transportation_expenses'),
                             ('rko_other', 'rko_other'),('warranty_service_costs', 'warranty_service_costs'),('other_expenses', 'other_expenses'),
                            ], required=True, index=True, default= _get_default_amount_spec_type,  copy=True,)
    currency_id = fields.Many2one('res.currency', string='Account Currency',  domain = _get_domain_currency)
    # project_currency_id = fields.Many2one('project_budget.project_currency_rates', string='Projects currency',  required = True, copy = True,
    #                               tracking=True, domain=False)
    name = fields.Char(string='name',tracking=True, required = True)
    summa = fields.Monetary(string='position sum',tracking=True)

