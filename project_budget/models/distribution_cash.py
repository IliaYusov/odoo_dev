from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import pytz
from datetime import timedelta

class distribution_cash(models.Model):
    _name = 'project_budget.distribution_cash'
    _description = "distribution cash fact by plan"
    # _inherit = ['mail.thread', 'mail.activity.mixin']

    fact_cash_flow_id = fields.Many2one('project_budget.fact_cash_flow', string='fact_cash_flow', index=True, ondelete='cascade',
                                        domain='[("projects_id", "=", parent.projects_id)]', required=True, copy=True)
    planned_cash_flow_id = fields.Many2one('project_budget.planned_cash_flow', string='planned_cash_flow', index=True, ondelete='cascade',
                                           domain='[("projects_id", "=", parent.projects_id)]',
                                           required=True,
                                           copy=True)
    date_cash_fact = fields.Date(related='fact_cash_flow_id.date_cash', readonly=True)
    date_cash_plan = fields.Date(related='planned_cash_flow_id.date_cash', readonly=True)
    currency_id = fields.Many2one(related='fact_cash_flow_id.currency_id', readonly=True)
    sum_cash_without_vat_fact = fields.Monetary(related='fact_cash_flow_id.sum_cash_without_vat', string ="sum_cash_without_vat fact", readonly=True)
    sum_cash_fact = fields.Monetary(related='fact_cash_flow_id.sum_cash', string ="sum_cash_fact", readonly=True)
    sum_cash_without_vat_plan = fields.Monetary(related='planned_cash_flow_id.sum_cash_without_vat', string ="sum_cash_without_vat_plan", readonly=True)
    sum_cash_plan = fields.Monetary(related='planned_cash_flow_id.sum_cash', string ="sum_cash_plan", readonly=True)
    distribution_sum_with_vat = fields.Monetary(related='planned_cash_flow_id.distribution_sum_with_vat', string ="distribution_sum_with_vat", readonly=True)
    distribution_sum_without_vat = fields.Monetary(related='planned_cash_flow_id.distribution_sum_without_vat', string ="distribution_sum_without_vat", readonly=True)
    distribution_sum_without_vat_ostatok = fields.Monetary(related='planned_cash_flow_id.distribution_sum_without_vat_ostatok', string ="distribution_sum_without_vat_ostatok", readonly=True)
    distribution_sum_with_vat_ostatok = fields.Monetary(related='planned_cash_flow_id.distribution_sum_with_vat_ostatok', string ="distribution_sum_with_vat_ostatok", readonly=True)

    sum_cash_without_vat = fields.Monetary(string="fact sum_cash_without_vat", required=True, copy=True, compute='_compute_sum')
    sum_cash = fields.Monetary(string="fact sum_cash", compute='_compute_default_sum',
                                           inverse='_inverse_compute_default_sum', store=True, required=True, copy=True)

    @api.depends("sum_cash")
    def _compute_sum(self):
        for row in self:
            if row.fact_cash_flow_id.project_steps_id:
                row.sum_cash_without_vat = row.sum_cash/(1+row.fact_cash_flow_id.project_steps_id.vat_attribute_id.percent / 100)
            else:
                row.sum_cash_without_vat = row.sum_cash / (1 + row.fact_cash_flow_id.projects_id.vat_attribute_id.percent / 100)
        # row.planned_cash_flow_id.compute_distribution_sum()

    @api.depends("distribution_sum_with_vat_ostatok")
    def _compute_default_sum(self):
        for row in self:
            distribution = {}
            print(row.fact_cash_flow_id.distribution_cash_ids)
            distr_list = [distribution for distribution in row.fact_cash_flow_id.distribution_cash_ids if type(distribution.id) != int and distribution.id.origin is not False]
            for distr in distr_list[:-1]:
                distribution['total'] = distribution.get('total', 0) + distr.sum_cash
                if distr.id.origin is None:
                    distribution[distr.planned_cash_flow_id] = distribution.get(distr.planned_cash_flow_id, 0) + distr.sum_cash
            row.sum_cash = min(row.distribution_sum_with_vat_ostatok - distribution.get(row.planned_cash_flow_id, 0), row.fact_cash_flow_id.sum_cash - distribution.get('total', 0))

    def _inverse_compute_default_sum(self):
        pass
