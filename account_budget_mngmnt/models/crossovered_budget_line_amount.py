from odoo import fields, models


class CrossoveredBudgetLineAmount(models.Model):
    _name = 'crossovered.budget.line.amount'
    _description = 'Budget Line Amount'

    crossovered_budget_line_id = fields.Many2one('crossovered.budget.line', 'Budget Line', index=True,
                                                 ondelete='cascade', required=True)
    crossovered_budget_id = fields.Many2one(related='crossovered_budget_line_id.crossovered_budget_id', readonly=True,
                                            store=True)
    company_id = fields.Many2one(related='crossovered_budget_line_id.company_id', readonly=True,
                                 store=True)
    currency_id = fields.Many2one(related='crossovered_budget_line_id.currency_id', readonly=True)
    paid_date = fields.Date(string='Paid Date', copy=True, required=True)
    planned_amount = fields.Monetary(string='Planned Amount', copy=True, required=True,
                                     help='Amount you plan to earn/spend.')
