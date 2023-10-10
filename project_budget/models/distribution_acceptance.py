from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import pytz
from datetime import timedelta


class distribution_acceptance(models.Model):
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

    sum_cash_without_vat = fields.Monetary(string="fact sum_cash_without_vat", compute='_compute_default_sum',
                                           inverse='_inverse_compute_default_sum', store=True, required=True, copy=True)
    sum_cash = fields.Monetary(string="fact sum_cash", required=True, copy=True,compute='_compute_sum', readonly=True)

    @api.depends("sum_cash_without_vat")
    def _compute_sum(self):
        for row in self:
            if row.fact_acceptance_flow_id.project_steps_id:
                row.write({'sum_cash': row.sum_cash_without_vat * (1+row.fact_acceptance_flow_id.project_steps_id.vat_attribute_id.percent / 100)})

            else:
                row.write({'sum_cash': row.sum_cash_without_vat * (1 + row.fact_acceptance_flow_id.projects_id.vat_attribute_id.percent / 100)})

    @api.depends("distribution_sum_without_vat_ostatok")
    def _compute_default_sum(self):
        for row in self:
            row.sum_cash_without_vat = min(row.distribution_sum_without_vat_ostatok, row.fact_acceptance_flow_id.sum_cash_without_vat)

    def _inverse_compute_default_sum(self):
        pass
