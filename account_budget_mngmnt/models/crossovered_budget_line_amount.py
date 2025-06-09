from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CrossoveredBudgetLineAmount(models.Model):
    _name = 'crossovered.budget.line.amount'
    _description = 'Budget Line Amount'

    crossovered_budget_line_id = fields.Many2one('crossovered.budget.line', 'Budget Line', index=True,
                                                 ondelete='cascade', required=True)
    crossovered_budget_id = fields.Many2one(related='crossovered_budget_line_id.crossovered_budget_id', readonly=True,
                                            store=True)
    budget_currency_id = fields.Many2one(related='crossovered_budget_line_id.budget_currency_id', readonly=True)
    company_id = fields.Many2one(related='crossovered_budget_line_id.company_id', readonly=True,
                                 store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', copy=True,
                                  default=lambda self: self.env.company.currency_id)
    date = fields.Date(string='Paid Date', copy=True, required=True)
    currency_rate = fields.Float(string='Currency Rate', compute='_compute_currency_rate', precompute=True, store=True)
    amount = fields.Monetary(string='Planned Amount', copy=True, required=True, help='Amount you plan to earn/spend')
    amount_in_budget_currency = fields.Monetary(string='Planned Amount In Budget Currency',
                                                compute='_compute_amount_in_budget_currency',
                                                currency_field='budget_currency_id', copy=True, store=True,
                                                help='Amount in budget currency you plan to earn/spend')

    # ------------------------------------------------------
    # CONSTRAINS
    # ------------------------------------------------------

    @api.constrains('crossovered_budget_line_id', 'date')
    def _line_date_between_budget_line_dates(self):
        for rec in self:
            if not rec.crossovered_budget_line_id.date_from <= rec.date <= rec.crossovered_budget_line_id.date_to:
                raise ValidationError(_('"Date" should be included in the period of the budget line.'))

    # ------------------------------------------------------
    # COMPUTE METHODS
    # ------------------------------------------------------

    @api.depends('crossovered_budget_line_id', 'currency_id', 'budget_currency_id')
    def _compute_currency_rate(self):
        for rec in self:
            rec.currency_rate = self.env['res.currency']._get_conversion_rate(
                from_currency=rec.currency_id,
                to_currency=rec.budget_currency_id,
                company=rec.company_id,
                date=rec.date or fields.Date.context_today(self.env.user)
            )

    @api.depends('amount', 'currency_rate')
    def _compute_amount_in_budget_currency(self):
        for rec in self:
            if rec.currency_id == rec.budget_currency_id:
                rec.amount_in_budget_currency = rec.amount
            else:
                rec.amount_in_budget_currency = rec.amount * rec.currency_rate
