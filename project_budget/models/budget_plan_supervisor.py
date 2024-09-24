from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import pytz
from datetime import timedelta

type_plan_rows = [
    ('contracting', 'contracting'),
    ('cash', 'cash'),
    ('acceptance', 'acceptance'),
    ('margin_income', 'margin_income'),
    ('margin3_income', 'margin3_income'),
    ('ebit', 'ebit'),
    ('net_profit', 'net_profit'),
]


class budget_plan_supervisor(models.Model):
    _name = 'project_budget.budget_plan_supervisor'
    _description = "Supervisors's budget plan on year"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name_to_show'

    year = fields.Integer(string="year plan", required=True, index=True,
                          default=lambda self: fields.datetime.now().year)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Account Currency', required=True, copy=True,
                                  default=lambda self: self.env['res.currency'].search([('name', '=', 'RUB')], limit=1),
                                  tracking=True)
    budget_plan_supervisor_spec_ids = fields.One2many(comodel_name='project_budget.budget_plan_supervisor_spec',
                                                      inverse_name='budget_plan_supervisor_id',
                                                      string="plan supervisor spec", auto_join=True, copy=True)

    plan_kam_ids = fields.One2many('project_budget.budget_plan_kam', 'plan_supervisor_id', string="KAM's plans")

    project_office_id = fields.Many2one('project_budget.project_office', string='project_office', copy=True,
                                        tracking=True, check_company=True)
    supervisor_id = fields.Many2one('project_budget.project_supervisor', string='KAMs supervisor', copy=True,
                                    tracking=True, check_company=True)  # TODO убрать после миграции на кураторов
    curator_id = fields.Many2one('hr.employee', string='KAMs supervisor', copy=True,
                                    tracking=True, check_company=True)
    supervisor_user_id = fields.Many2one(related='supervisor_id.user_id', readonly=True)  # TODO убрать после миграции на кураторов
    curator_user_id = fields.Many2one(related='curator_id.user_id', readonly=True)
    name_to_show = fields.Char(string='name_to_show', compute='_get_name_to_show')

    is_use_ebit = fields.Boolean(string="using EBIT", tracking=True)
    is_use_net_profit = fields.Boolean(string="using Net Profit", tracking=True)
    is_company_plan = fields.Boolean(string="Company plan", tracking=True)

    sum_contracting_year = fields.Monetary(string='contracting plan year', tracking=True, readonly=True,
                                           compute='_compute_totals_year')
    sum_contracting_year_6_6 = fields.Monetary(string='contracting plan year 6+6', tracking=True, readonly=True,
                                               compute='_compute_totals_year')
    sum_contracting_year_fact = fields.Monetary(string='contracting fact year', tracking=True, readonly=True,
                                                compute='_compute_totals_year')
    sum_cash_year = fields.Monetary(string='cash plan year', tracking=True, readonly=True,
                                    compute='_compute_totals_year')
    sum_cash_year_6_6 = fields.Monetary(string='cash plan year 6+6', tracking=True, readonly=True,
                                        compute='_compute_totals_year')
    sum_cash_year_fact = fields.Monetary(string='cash fact year', tracking=True, readonly=True,
                                         compute='_compute_totals_year')
    sum_acceptance_year = fields.Monetary(string='acceptance plan year', tracking=True, readonly=True,
                                          compute='_compute_totals_year')
    sum_acceptance_year_6_6 = fields.Monetary(string='acceptance plan year 6+6', tracking=True, readonly=True,
                                              compute='_compute_totals_year')
    sum_acceptance_year_fact = fields.Monetary(string='acceptance fact year', tracking=True, readonly=True,
                                               compute='_compute_totals_year')
    sum_margin_income_year = fields.Monetary(string='margin plan year', tracking=True, readonly=True,
                                             compute='_compute_totals_year')
    sum_margin_income_year_6_6 = fields.Monetary(string='margin plan year 6+6', tracking=True, readonly=True,
                                                 compute='_compute_totals_year')
    sum_margin_income_year_fact = fields.Monetary(string='margin fact year', tracking=True, readonly=True,
                                                  compute='_compute_totals_year')
    sum_margin3_income_year = fields.Monetary(string='margin3 plan year', tracking=True, readonly=True,
                                              compute='_compute_totals_year')
    sum_margin3_income_year_6_6 = fields.Monetary(string='margin3 plan year 6+6', tracking=True, readonly=True,
                                                  compute='_compute_totals_year')
    sum_margin3_income_year_fact = fields.Monetary(string='margin3 fact year', tracking=True, readonly=True,
                                                   compute='_compute_totals_year')
    sum_ebit_year = fields.Monetary(string='ebit plan year', tracking=True, readonly=True,
                                    compute='_compute_totals_year')
    sum_ebit_year_6_6 = fields.Monetary(string='ebit plan year 6+6', tracking=True, readonly=True,
                                        compute='_compute_totals_year')
    sum_ebit_year_fact = fields.Monetary(string='ebit fact year', tracking=True, readonly=True,
                                         compute='_compute_totals_year')
    sum_net_profit_year = fields.Monetary(string='net_profit plan year', tracking=True, readonly=True,
                                          compute='_compute_totals_year')
    sum_net_profit_year_6_6 = fields.Monetary(string='net_profit plan year 6+6', tracking=True, readonly=True,
                                              compute='_compute_totals_year')
    sum_net_profit_year_fact = fields.Monetary(string='net_profit fact year', tracking=True, readonly=True,
                                               compute='_compute_totals_year')

    @api.depends('budget_plan_supervisor_spec_ids')
    def _compute_totals_year(self):
        self.sum_contracting_year = 0
        self.sum_contracting_year_6_6 = 0
        self.sum_contracting_year_fact = 0
        self.sum_cash_year = 0
        self.sum_cash_year_6_6 = 0
        self.sum_cash_year_fact = 0
        self.sum_acceptance_year = 0
        self.sum_acceptance_year_6_6 = 0
        self.sum_acceptance_year_fact = 0
        self.sum_margin_income_year = 0
        self.sum_margin_income_year_6_6 = 0
        self.sum_margin_income_year_fact = 0
        self.sum_margin3_income_year = 0
        self.sum_margin3_income_year_6_6 = 0
        self.sum_margin3_income_year_fact = 0
        self.sum_ebit_year = 0
        self.sum_ebit_year_6_6 = 0
        self.sum_ebit_year_fact = 0
        self.sum_net_profit_year = 0
        self.sum_net_profit_year_6_6 = 0
        self.sum_net_profit_year_fact = 0

        for row in self.budget_plan_supervisor_spec_ids:
            print('row.type_row = ', row.type_row)
            print('row.year_plan = ', row.year_plan)
            print('row.year_plan_6_6 = ', row.year_plan_6_6)
            if row.type_row == 'contracting':
                self.sum_contracting_year = row.year_plan
                self.sum_contracting_year_6_6 = row.year_plan_6_6
                self.sum_contracting_year_fact = row.year_fact
            if row.type_row == 'cash':
                self.sum_cash_year = row.year_plan
                self.sum_cash_year_6_6 = row.year_plan_6_6
                self.sum_cash_year_fact = row.year_fact
            if row.type_row == 'acceptance':
                self.sum_acceptance_year = row.year_plan
                self.sum_acceptance_year_6_6 = row.year_plan_6_6
                self.sum_acceptance_year_fact = row.year_fact
            if row.type_row == 'margin_income':
                self.sum_margin_income_year = row.year_plan
                self.sum_margin_income_year_6_6 = row.year_plan_6_6
                self.sum_margin_income_year_fact = row.year_fact
            if row.type_row == 'margin3_income':
                self.sum_margin3_income_year = row.year_plan
                self.sum_margin3_income_year_6_6 = row.year_plan_6_6
                self.sum_margin3_income_year_fact = row.year_fact
            if row.type_row == 'ebit':
                self.sum_ebit_year = row.year_plan
                self.sum_ebit_year_6_6 = row.year_plan_6_6
                self.sum_ebit_year_fact = row.year_fact
            if row.type_row == 'net_profit':
                self.sum_net_profit_year = row.year_plan
                self.sum_net_profit_year_6_6 = row.year_plan_6_6
                self.sum_net_profit_year_fact = row.year_fact

    @api.depends('curator_id', 'year')
    def _get_name_to_show(self):
        for plan_supervisor in self:
            plan_supervisor.name_to_show = (
                    str(plan_supervisor.year)
                    + ' '
                    + (plan_supervisor.project_office_id.name or plan_supervisor.company_id.name)
                    + ' '
                    + (plan_supervisor.curator_id.name or '')
            )

    def insert_spec(self, type_row, plan_id):
        type_plan_row_vals = []
        type_plan_row_vals.append(dict(
            type_row=type_row
            , budget_plan_supervisor_id=plan_id
        ))
        print('insert_spec type_row = ', type_row)
        self.env['project_budget.budget_plan_supervisor_spec'].create(type_plan_row_vals)

    # @api.onchange('is_use_ebit', 'is_use_net_profit')
    def _check_use_ebit_use_net_profit(self):
        print('_check_changes_project')
        for row in self:
            print('row.is_use_ebit = ', row.is_use_ebit)
            print('row.is_use_net_profit = ', row.is_use_net_profit)
            if row.is_use_ebit == False:
                for budget_plan_supervisor_spec in row.budget_plan_supervisor_spec_ids:
                    if budget_plan_supervisor_spec.type_row == 'ebit':
                        print('ebit unlink')
                        budget_plan_supervisor_spec.unlink()
            else:
                isexistebit = False
                for budget_plan_supervisor_spec in row.budget_plan_supervisor_spec_ids:
                    if budget_plan_supervisor_spec.type_row == 'ebit':
                        isexistebit = True
                print('isexistebit=', isexistebit)
                if isexistebit == False:
                    self.insert_spec('ebit', row.id)

            if row.is_use_net_profit == False:
                for budget_plan_supervisor_spec in row.budget_plan_supervisor_spec_ids:
                    if budget_plan_supervisor_spec.type_row == 'net_profit':
                        print('net_profit unlink')
                        budget_plan_supervisor_spec.unlink()
            else:
                isexistnet_profit = False
                for budget_plan_supervisor_spec in row.budget_plan_supervisor_spec_ids:
                    if budget_plan_supervisor_spec.type_row == 'net_profit':
                        isexistnet_profit = True
                print('isexistnet_profit=', isexistnet_profit)
                if isexistnet_profit == False:
                    self.insert_spec('net_profit', row.id)

    def write(self, vals_list):
        res = super().write(vals_list)
        self._check_use_ebit_use_net_profit()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        budget_plan_supervisors = super(budget_plan_supervisor, self).create(vals_list)
        for spec_plan_supervisor in budget_plan_supervisors:
            for type_plan_row in type_plan_rows:
                self.insert_spec(type_plan_row[0], spec_plan_supervisor.id)
        budget_plan_supervisors._check_use_ebit_use_net_profit()
        self.env.flush_all()
        return budget_plan_supervisors


class budget_plan_supervisor_spec(models.Model):
    _name = 'project_budget.budget_plan_supervisor_spec'

    budget_plan_supervisor_id = fields.Many2one('project_budget.budget_plan_supervisor', string='plan supervisor',
                                                index=True, ondelete='cascade')
    company_id = fields.Many2one(related='budget_plan_supervisor_id.company_id', readonly=True, store=True)
    currency_id = fields.Many2one(related='budget_plan_supervisor_id.currency_id', readonly=True)

    type_row = fields.Selection(type_plan_rows, index=True, readonly=True, required=True)

    q1_plan = fields.Monetary(string='q1_plan')
    q2_plan = fields.Monetary(string='q2_plan')
    q3_plan = fields.Monetary(string='q3_plan')
    q4_plan = fields.Monetary(string='q4_plan')
    year_plan = fields.Monetary(string='year_plan', compute='_compute_totals', store=False)

    q1_fact = fields.Monetary(string='q1 fact')
    q2_fact = fields.Monetary(string='q2 fact')
    q3_fact = fields.Monetary(string='q3 fact')
    q4_fact = fields.Monetary(string='q4 fact')
    year_fact = fields.Monetary(string='year fact', compute='_compute_totals', store=False)

    q1_plan_6_6 = fields.Monetary(string='q1_plan 6+6')
    q2_plan_6_6 = fields.Monetary(string='q2_plan 6+6')
    q3_plan_6_6 = fields.Monetary(string='q3_plan 6+6')
    q4_plan_6_6 = fields.Monetary(string='q4_plan 6+6')
    year_plan_6_6 = fields.Monetary(string='year_plan 6+6', compute='_compute_totals', store=False)

    @api.depends("q1_plan", "q2_plan", "q3_plan", "q4_plan",
                 "q1_plan_6_6", "q2_plan_6_6", "q3_plan_6_6", "q4_plan_6_6",
                 "q1_fact", "q2_fact", "q3_fact", "q4_fact")
    def _compute_totals(self):
        for row in self:
            row.year_plan = row.q1_plan + row.q2_plan + row.q3_plan + row.q4_plan
            row.year_plan_6_6 = row.q1_plan_6_6 + row.q2_plan_6_6 + row.q3_plan_6_6 + row.q4_plan_6_6 + row.q1_fact + row.q2_fact
            row.year_fact = row.q1_fact + row.q2_fact + row.q3_fact + row.q4_fact
