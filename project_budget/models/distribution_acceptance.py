from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import pytz
from datetime import timedelta


class distribution_acceptance(models.Model):

    @api.onchange("planned_acceptance_flow_id")
    def _compute_default_sum(self):
        pass
        # if self.planned_acceptance_flow_id.ids:
        #     distribution = {}
        #     print('self.fact_acceptance_flow_id.distribution_acceptance_ids', self.fact_acceptance_flow_id.distribution_acceptance_ids)
        #     distr_list = [distribution for distribution in self.fact_acceptance_flow_id.distribution_acceptance_ids if
        #                   hasattr(distribution.id, 'origin') and distribution.id.origin is not False]
        #     for distr in distr_list[:-1]:
        #         distribution['total'] = distribution.get('total', 0) + distr.sum_cash_without_vat
        #         if distr.id.origin is None:
        #             distribution[distr.planned_acceptance_flow_id] = distribution.get(distr.planned_acceptance_flow_id,
        #                                                                               0) + distr.sum_cash_without_vat
        #     return {'value': {'sum_cash_without_vat': min(
        #         self.distribution_sum_without_vat_ostatok - distribution.get(self.planned_acceptance_flow_id, 0),
        #         self.fact_acceptance_flow_id.sum_cash_without_vat - distribution.get('total', 0))}}

    _name = 'project_budget.distribution_acceptance'
    _description = "distribution acceptance fact by plan"
    # _inherit = ['mail.thread', 'mail.activity.mixin']

    fact_acceptance_flow_id = fields.Many2one('project_budget.fact_acceptance_flow', string='fact_acceptance_flow', index=True,
                                        ondelete='cascade',
                                        domain='[("projects_id", "=", parent.projects_id)]', required=True, copy=True)
    planned_acceptance_flow_id = fields.Many2one('project_budget.planned_acceptance_flow', string='planned_acceptance_flow',
                                           index=True, ondelete='cascade',
                                           domain='[("projects_id", "=", parent.projects_id)]', required=True,copy=True)

    date_acceptance_fact = fields.Date(related='fact_acceptance_flow_id.date_cash', readonly=True)
    date_acceptance_plan = fields.Date(related='planned_acceptance_flow_id.date_cash', readonly=True)
    currency_id = fields.Many2one(related='fact_acceptance_flow_id.currency_id', readonly=True)
    sum_cash_without_vat_fact = fields.Monetary(related='fact_acceptance_flow_id.sum_cash_without_vat',
                                                string="sum_acceptance_without_vat fact", readonly=True)
    sum_cash_fact = fields.Monetary(related='fact_acceptance_flow_id.sum_cash', string="sum_cash_fact", readonly=True)
    sum_cash_without_vat_plan = fields.Monetary(related='planned_acceptance_flow_id.sum_cash_without_vat',
                                                string="sum_acceptance_without_vat_plan", readonly=True)
    sum_cash_plan = fields.Monetary(related='planned_acceptance_flow_id.sum_cash', string="sum_acceptance_plan", readonly=True)
    distribution_sum_with_vat = fields.Monetary(related='planned_acceptance_flow_id.distribution_sum_with_vat',
                                                string="distribution_sum_with_vat", readonly=True)
    distribution_sum_without_vat = fields.Monetary(related='planned_acceptance_flow_id.distribution_sum_without_vat',
                                                   string="distribution_sum_without_vat", readonly=True)
    distribution_sum_without_vat_ostatok = fields.Monetary(
        related='planned_acceptance_flow_id.distribution_sum_without_vat_ostatok',
        string="distribution_sum_without_vat_ostatok", readonly=True)
    distribution_sum_with_vat_ostatok = fields.Monetary(
        related='planned_acceptance_flow_id.distribution_sum_with_vat_ostatok',
        string="distribution_sum_with_vat_ostatok", readonly=True)

    sum_cash_without_vat = fields.Monetary(string="fact sum_cash_without_vat", required=True, copy=True, default=_compute_default_sum)
    sum_cash = fields.Monetary(string="fact sum_cash", required=True, copy=True,compute='_compute_sum', readonly=True)

    @api.depends("sum_cash_without_vat")
    def _compute_sum(self):
        for row in self:
            if row.fact_acceptance_flow_id.project_steps_id:
                row.sum_cash = row.sum_cash_without_vat * (1 + row.fact_acceptance_flow_id.project_steps_id.vat_attribute_id.percent / 100)
            else:
                row.sum_cash = row.sum_cash_without_vat * (1 + row.fact_acceptance_flow_id.projects_id.vat_attribute_id.percent / 100)
