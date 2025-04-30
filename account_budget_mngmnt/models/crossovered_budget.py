from odoo import api, fields, models, _

BUDGET_STATES = [
    ('draft', _('Draft')),
    ('confirm', _('Confirmed')),
    ('validate', _('Validated')),
    ('done', _('Done')),
    ('cancel', _('Cancelled'))
]


class CrossoveredBudget(models.Model):
    _name = 'crossovered.budget'
    _description = 'Budget'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Budget Name', required=True)
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user)
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    state = fields.Selection(selection=BUDGET_STATES, string='Status', copy=False, default='draft', index=True,
                             readonly=True, required=True, tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', copy=True,
                                  default=lambda self: self.env.company.currency_id, tracking=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', copy=True,
                                          groups='analytic.group_analytic_accounting')
    line_ids = fields.One2many('crossovered.budget.line', 'crossovered_budget_id', string='Budget Lines', copy=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)

    amount_total_income = fields.Monetary(string='Total Income', compute='_compute_amount', tracking=True, store=True)
    amount_total_expense = fields.Monetary(string='Total Expenses', compute='_compute_amount', tracking=True,
                                           store=True)
    gross_margin = fields.Monetary(string='Gross Margin', compute='_compute_amount', tracking=True, store=True)
    gross_profitability = fields.Float(string='Gross Profitability', compute='_compute_amount', tracking=True,
                                       store=True)

    # ------------------------------------------------------
    # COMPUTE METHODS
    # ------------------------------------------------------

    @api.depends('line_ids.planned_amount_in_budget_currency')
    def _compute_amount(self):
        for rec in self:
            rec.amount_total_income = sum(
                rec.line_ids.filtered(lambda l: l.general_budget_id.direction == 'income').mapped(
                    'planned_amount_in_budget_currency'))
            rec.amount_total_expense = sum(
                rec.line_ids.filtered(lambda l: l.general_budget_id.direction == 'expense').mapped(
                    'planned_amount_in_budget_currency'))
            rec.gross_margin = rec.amount_total_income - rec.amount_total_expense
            rec.gross_profitability = 0 if rec.amount_total_income == 0 else rec.gross_margin / rec.amount_total_income

    # ------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------

    def action_budget_confirm(self):
        self.write({'state': 'confirm'})

    def action_budget_draft(self):
        self.write({'state': 'draft'})

    def action_budget_validate(self):
        self.write({'state': 'validate'})

    def action_budget_cancel(self):
        self.write({'state': 'cancel'})

    def action_budget_done(self):
        self.write({'state': 'done'})
