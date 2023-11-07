from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import pytz
from datetime import timedelta
import datetime

class project_budget_project_currency_rates(models.Model):

    def _get_domain_currency(self):
        domain = [('id', '!=', self.env.company.currency_id.id)]
        return domain

    _name = 'project_budget.project_currency_rates'
    _description = "projects currency rates"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    projects_id = fields.Many2one('project_budget.projects', string='projects_id', index=True, ondelete='cascade')
    currency_id = fields.Many2one('res.currency', string="Project's currency",  required = True, copy = True
                                  ,tracking=True, domain=_get_domain_currency)
    name = fields.Char(string='name',tracking=True)
    rate = fields.Float(string='currency rate',tracking=True)

    _sql_constraints = [
                        ("project_currency_unique", "unique (projects_id, currency_id)", "Project cant get currency duplicate")
                       ]


    def write(self, vals_list):
        print('project_currency_rates write = ', self)
        res = super().write(vals_list)
        for row in self:
            try:
                print('project_currency_rates row.project_id.id = ', row.projects_id.id)
                cur_idstr = str(row.projects_id.id)
                cur_idstr = cur_idstr.replace('NewId_', '')
                cur_id = int(cur_idstr)
                print('project_currency_rates cur_id = ', cur_id)
                curprj = self.env['project_budget.projects'].search([('id', '=', cur_id)], limit=1)
                print('project_currency_rates curprj = ',curprj)
                if curprj:
                    curprj._compute_spec_totals()
            except:
                return False
        return res

    def _get_currency_rate_for_project_currency(self,cur_project, currency_id):
        # cur_project = self.env['project_budget.projects'].search([('id', '=', projects_id)])
        rate = 0
        if cur_project:
            project_currency_rate = 1
            current_currency_rate = 1
            project_currency = cur_project.currency_id.id
            for each in cur_project.project_currency_rates_ids:
                if each.currency_id.id == project_currency:
                    project_currency_rate = each.rate
                if each.currency_id.id == currency_id:
                    current_currency_rate = each.rate
            rate = current_currency_rate/project_currency_rate
        return rate

    def _get_currency_rate_for_project_in_company_currency(self,cur_project):
        # cur_project = self.env['project_budget.projects'].search([('id', '=', projects_id)])
        rate = 0
        if cur_project:
            project_currency_rate = 1
            project_currency = cur_project.currency_id.id
            for each in cur_project.project_currency_rates_ids:
                if each.currency_id.id == project_currency:
                    project_currency_rate = each.rate
            rate = project_currency_rate
        return rate

    def _get_sum_by_project_in_company_currency(self, cur_project, sum):
        return self._get_currency_rate_for_project_in_company_currency(cur_project)*sum
