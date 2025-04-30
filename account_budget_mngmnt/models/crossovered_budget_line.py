from collections import defaultdict
from datetime import timedelta

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
                                          groups='analytic.group_analytic_accounting')
    analytic_plan_id = fields.Many2one(related='analytic_account_id.plan_id', string='Analytic Plan', readonly=True)
    general_budget_id = fields.Many2one('account.budget.item', string='Budget Item')
    date_from = fields.Date(string='Start Date', copy=True, required=True)
    date_to = fields.Date(string='End Date', copy=True, required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', copy=True,
                                  default=lambda self: self.env.company.currency_id)
    currency_rate = fields.Float(string='Currency Rate', compute='_compute_currency_rate', precompute=True, store=True)
    planned_amount_ids = fields.One2many('crossovered.budget.line.amount', 'crossovered_budget_line_id',
                                         string='Amounts', copy=True)
    planned_amount = fields.Monetary(string='Planned Amount', compute='_compute_planned_amount', copy=False,
                                     currency_field='currency_id', required=True,
                                     help='Amount you plan to earn/spend.')
    planned_amount_in_budget_currency = fields.Monetary(compute='_compute_planned_amount_in_budget_currency',
                                                        string='Planned Amount In Budget Currency',
                                                        currency_field='budget_currency_id', required=True)
    practical_amount = fields.Monetary(string='Practical Amount', compute='_compute_practical_amount',
                                       help='Amount really earned/spent.')

    # ------------------------------------------------------
    # CONSTRAINS
    # ------------------------------------------------------

    @api.constrains('general_budget_id', 'analytic_account_id')
    def _must_have_analytical_or_budgetary_or_both(self):
        for record in self:
            if not record.analytic_account_id and not record.general_budget_id:
                raise ValidationError(
                    _('You have to enter at least a budgetary position or analytic account on a budget line.'))

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
                        _('"Start Date" of the budget line should be included in the Period of the budget'))
            if record.date_to:
                date_to = record.date_to
                if (budget_date_from and date_to < budget_date_from) or (budget_date_to and date_to > budget_date_to):
                    raise ValidationError(
                        _('"End Date" of the budget line should be included in the Period of the budget'))

    # ------------------------------------------------------
    # COMPUTE METHODS
    # ------------------------------------------------------

    @api.depends('crossovered_budget_id', 'general_budget_id', 'analytic_account_id')
    def _compute_name(self):
        for rec in self:
            computed_name = rec.crossovered_budget_id.name
            if rec.general_budget_id:
                computed_name += ' - ' + rec.general_budget_id.name
            if rec.analytic_account_id:
                computed_name += ' - ' + rec.analytic_account_id.name
            rec.name = computed_name

    @api.depends('crossovered_budget_id', 'currency_id', 'budget_currency_id')
    def _compute_currency_rate(self):
        for rec in self:
            rec.currency_rate = self.env['res.currency']._get_conversion_rate(
                from_currency=rec.currency_id,
                to_currency=rec.budget_currency_id,
                company=rec.company_id,
                date=rec.date
            )

    @api.depends('planned_amount_ids.planned_amount')
    def _compute_planned_amount(self):
        for rec in self:
            rec.planned_amount = sum(rec.planned_amount_ids.mapped('planned_amount'))

    @api.depends('planned_amount', 'currency_rate')
    def _compute_planned_amount_in_budget_currency(self):
        for rec in self:
            if rec.currency_id == rec.budget_currency_id:
                rec.planned_amount_in_budget_currency = rec.planned_amount
            else:
                rec.planned_amount_in_budget_currency = rec.planned_amount * rec.currency_rate

    @api.depends('general_budget_id.account_ids', 'date_to', 'date_from', 'analytic_account_id')
    def _compute_practical_amount(self):
        for rec in self:
            result = 0.0
            acc_ids = rec.general_budget_id.account_ids.ids
            date_to = rec.date_to
            date_from = rec.date_from
            if rec.analytic_account_id.id and date_from and date_to:
                self.env.cr.execute(
                    """
                    SELECT SUM(amount)
                    FROM account_analytic_line
                    WHERE account_id=%s AND (date between %s AND %s) AND general_account_id=ANY(%s)""",
                    (rec.analytic_account_id.id, date_from, date_to, acc_ids),
                )
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

    # ------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------

    def action_open_budget_entries(self):
        if self.analytic_account_id:
            # if there is an analytic account, then the analytic items are loaded
            action = self.env['ir.actions.act_window']._for_xml_id('analytic.account_analytic_line_action_entries')
            action['domain'] = [
                ('auto_account_id', '=', self.analytic_account_id.id),
                ('date', '>=', self.date_from),
                ('date', '<=', self.date_to)
            ]
            if self.general_budget_id:
                action['domain'] += [('general_account_id', 'in', self.general_budget_id.account_ids.ids)]
        else:
            # otherwise the journal entries booked on the accounts of the budgetary postition are opened
            action = self.env['ir.actions.act_window']._for_xml_id('account.action_account_moves_all_a')
            action['domain'] = [
                ('account_id', 'in', self.general_budget_id.account_ids.ids),
                ('date', '>=', self.date_from),
                ('date', '<=', self.date_to)
            ]
        return action
