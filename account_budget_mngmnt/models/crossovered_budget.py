from odoo import api, fields, models, _

BUDGET_STATES = [
    ('draft', _('Draft')),
    ('confirm', _('Confirmed')),
    ('done', _('Done')),
    ('cancel', _('Cancelled'))
]


class CrossoveredBudget(models.Model):
    _name = 'crossovered.budget'
    _description = 'Budget'
    _inherit = ['mail.thread']

    name = fields.Char(string='Budget Name', copy=True, required=True)
    user_id = fields.Many2one('res.users', string='Responsible', copy=False, default=lambda self: self.env.user)
    date_from = fields.Date(string='Start Date', copy=True, default=fields.Date.context_today, required=True,
                            tracking=True)
    date_to = fields.Date(string='End Date', copy=True, required=True, tracking=True)
    state = fields.Selection(selection=BUDGET_STATES, string='Status', copy=False, default='draft', index=True,
                             readonly=True, required=True, tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', copy=True,
                                  default=lambda self: self.env.company.currency_id, tracking=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', copy=True,
                                          groups='analytic.group_analytic_accounting')
    line_ids = fields.One2many('crossovered.budget.line', 'crossovered_budget_id', string='Budget Lines', copy=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)

    planned_amount_total_income = fields.Monetary(string='Planned Total Income', compute='_compute_amount',
                                                  tracking=True, store=True)
    planned_amount_total_expense = fields.Monetary(string='Planned Total Expenses', compute='_compute_amount',
                                                   tracking=True, store=True)
    practical_amount_total_expense = fields.Monetary(string='Practical Total Expenses', compute='_compute_amount',
                                                     store=True)
    can_edit = fields.Boolean(compute='_compute_can_edit', default=True)

    # ------------------------------------------------------
    # COMPUTE METHODS
    # ------------------------------------------------------

    def _compute_can_edit(self):
        for rec in self:
            rec.can_edit = rec.state == 'draft'

    @api.depends('line_ids.planned_amount_in_budget_currency', 'line_ids.practical_amount')
    def _compute_amount(self):
        for rec in self:
            rec.planned_amount_total_income = sum(
                rec.line_ids.filtered(lambda l: l.general_budget_id.direction == 'income').mapped(
                    'planned_amount_in_budget_currency'))
            expenses = rec.line_ids.filtered(lambda l: l.general_budget_id.direction == 'expense')
            rec.planned_amount_total_expense = sum(expenses.mapped('planned_amount_in_budget_currency'))
            rec.practical_amount_total_expense = sum(expenses.mapped('practical_amount'))

    # ------------------------------------------------------
    # CRUD
    # ------------------------------------------------------

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        if default is None:
            default = {}
        default['name'] = _('Copy_%s') % self.name
        return super(CrossoveredBudget, self).copy(default=default)

    # ------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------

    def action_budget_confirm(self):
        self.write({'state': 'confirm'})

    def action_budget_draft(self):
        self.write({'state': 'draft'})

    def action_budget_cancel(self):
        self.write({'state': 'cancel'})

    def action_budget_done(self):
        self.write({'state': 'done'})
