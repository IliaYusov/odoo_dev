from odoo import api, fields, models


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    crossovered_budget_line_ids = fields.One2many('crossovered.budget.line', 'analytic_account_id',
                                                  string='Budget Lines')
    total_planned_amount = fields.Monetary(compute='_compute_planned_amount', string='Total Planned Amount')

    @api.depends('crossovered_budget_line_ids.planned_amount')
    def _compute_planned_amount(self):
        rates = {}
        for rec in self:
            currency = rec.currency_id or self.env.company.currency_id
            company = rec.company_id or self.env.company
            total_planned_amount = 0
            for line in rec.crossovered_budget_line_ids:
                if line.currency_id == currency:
                    total_planned_amount += line.planned_amount
                    continue
                rate_key = (line.currency_id, currency, company, line.date_from)
                if rates.get(rate_key):
                    rate = rates[rate_key]
                else:
                    rate = rates[rate_key] = currency._get_conversion_rate(*rate_key)
                    rates[rate_key] = rate
                total_planned_amount += line.planned_amount * rate
            rec.total_planned_amount = currency.round(total_planned_amount)
