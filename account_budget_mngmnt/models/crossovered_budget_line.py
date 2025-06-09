from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.osv.expression import AND


class CrossoveredBudgetLine(models.Model):
    _name = 'crossovered.budget.line'
    _description = 'Budget Line'

    name = fields.Char(compute='_compute_name')
    crossovered_budget_id = fields.Many2one('crossovered.budget', string='Budget', index=True, ondelete='cascade',
                                            required=True)
    crossovered_budget_state = fields.Selection(related='crossovered_budget_id.state', string='Budget State', copy=True,
                                                readonly=True, store=True)
    company_id = fields.Many2one(related='crossovered_budget_id.company_id', string='Company', readonly=True,
                                 store=True)
    budget_currency_id = fields.Many2one(related='crossovered_budget_id.currency_id', string='Budget Currency',
                                         readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', copy=True,
                                          domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                          groups='analytic.group_analytic_accounting')
    analytic_plan_id = fields.Many2one(related='analytic_account_id.plan_id', string='Analytic Plan',
                                       domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                       readonly=True)
    general_budget_id = fields.Many2one('account.budget.item', string='Budget Item',
                                        domain="[('child_ids', '=', False), ('company_ids', 'in', company_id)]")
    general_budget_direction = fields.Selection(related='general_budget_id.direction', readonly=True)
    date_from = fields.Date(related='crossovered_budget_id.date_from', readonly=True, store=True)
    date_to = fields.Date(related='crossovered_budget_id.date_to', readonly=True, store=True)
    planned_amount_ids = fields.One2many('crossovered.budget.line.amount', 'crossovered_budget_line_id',
                                         string='Amounts', copy=True)
    planned_amount_in_budget_currency = fields.Monetary(string='Planned Amount In Budget Currency',
                                                        compute='_compute_planned_amount',
                                                        currency_field='budget_currency_id', store=True)
    practical_amount = fields.Monetary(string='Practical Amount', compute='_compute_practical_amount',
                                       currency_field='budget_currency_id',
                                       help='Amount really earned/spent.')

    _sql_constraints = [
        (
            'budget_item_analytic_account_uniq',
            'UNIQUE NULLS NOT DISTINCT (crossovered_budget_id, general_budget_id, analytic_account_id)',
            'Budget item and analytic account must be unique for a budget line.'
        )
    ]

    # ------------------------------------------------------
    # CONSTRAINS
    # ------------------------------------------------------

    @api.constrains('general_budget_id', 'analytic_account_id')
    def _must_have_analytical_or_budgetary_or_both(self):
        for record in self:
            if not record.analytic_account_id and not record.general_budget_id:
                raise ValidationError(
                    _('You have to enter at least a budget item or analytic account on a budget line.'))

    @api.constrains('date_from', 'date_to')
    def _line_dates_between_budget_dates(self):
        for record in self:
            budget_date_from = record.crossovered_budget_id.date_from
            budget_date_to = record.crossovered_budget_id.date_to
            if record.date_from:
                date_from = record.date_from
                if (budget_date_from and date_from < budget_date_from) or (
                        budget_date_to and date_from > budget_date_to):
                    raise ValidationError(
                        _('"Start Date" of the budget line should be included in the period of the budget.'))
            if record.date_to:
                date_to = record.date_to
                if (budget_date_from and date_to < budget_date_from) or (budget_date_to and date_to > budget_date_to):
                    raise ValidationError(
                        _('"End Date" of the budget line should be included in the period of the budget.'))

    # ------------------------------------------------------
    # COMPUTE METHODS
    # ------------------------------------------------------

    @api.depends('crossovered_budget_id', 'general_budget_id', 'analytic_account_id')
    def _compute_name(self):
        for rec in self:
            name = rec.crossovered_budget_id.name
            if rec.general_budget_id:
                name += ' - ' + rec.general_budget_id.name
            if rec.analytic_account_id:
                name += ' - ' + rec.analytic_account_id.name
            rec.name = name

    @api.depends('planned_amount_ids.amount', 'planned_amount_ids.currency_rate')
    def _compute_planned_amount(self):
        for rec in self:
            rec.planned_amount_in_budget_currency = sum(rec.planned_amount_ids.mapped('amount_in_budget_currency'))

    def _compute_practical_amount(self):
        for rec in self:
            result = 0.0
            account_ids = rec.general_budget_id.account_ids.ids
            if rec.analytic_account_id.id and rec.date_from and rec.date_to:
                self.env.cr.execute("""
                    SELECT SUM(amount)
                    FROM account_analytic_line
                    WHERE account_id=%s AND (date between %s AND %s) AND general_account_id=ANY(%s)
                """, (rec.analytic_account_id.id, rec.date_from, rec.date_to, account_ids))
                result = self.env.cr.fetchone()[0] or 0.0
            rec.practical_amount = result

    # ------------------------------------------------------
    # ONCHANGE METHODS
    # ------------------------------------------------------

    @api.onchange('date_from', 'date_to')
    def _onchange_dates(self):
        domain_list = []
        if self.date_from:
            domain_list.append(['|', ('date_from', '<=', self.date_from), ('date_from', '=', False)])
        if self.date_to:
            domain_list.append(['|', ('date_to', '>=', self.date_to), ('date_to', '=', False)])
        if domain_list and not self.crossovered_budget_id.filtered_domain(AND(domain_list)):
            self.crossovered_budget_id = self.env['crossovered.budget'].search(AND(domain_list), limit=1)

    @api.onchange('crossovered_budget_id')
    def _onchange_crossovered_budget_id(self):
        if self.crossovered_budget_id:
            self.date_from = self.date_from or self.crossovered_budget_id.date_from
            self.date_to = self.date_to or self.crossovered_budget_id.date_to
