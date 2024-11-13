from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import pytz
from datetime import timedelta

type_plan_rows = [('contracting', 'contracting')
    , ('cash', 'cash')
    , ('acceptance', 'acceptance')
    , ('margin_income', 'margin_income')
    , ('margin3_income', 'margin3_income')
    , ('ebit', 'ebit')
    , ('net_profit', 'net_profit')
                  ]

class budget_plan_kam(models.Model):
    _name = 'project_budget.budget_plan_kam'
    _description = "KAM's budget plan on year"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name_to_show'

    plan_supervisor_id = fields.Many2one('project_budget.budget_plan_supervisor', required=True, copy = True, readonly = True)

    year = fields.Integer(related='plan_supervisor_id.year')
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Account Currency',  required = True, copy = True,
                                  default=lambda self: self.env['res.currency'].search([('name', '=', 'RUB')], limit=1),tracking=True)

    budget_plan_kam_spec_ids = fields.One2many(comodel_name='project_budget.budget_plan_kam_spec',
                                                      inverse_name='budget_plan_kam_id',
                                                      string="plan kam spec", auto_join=True, copy=True)


    project_office_id = fields.Many2one(related='plan_supervisor_id.project_office_id', string='project_office')
    responsibility_center_id = fields.Many2one(related='plan_supervisor_id.responsibility_center_id', string='project_office')
    supervisor_id = fields.Many2one(related = 'plan_supervisor_id.supervisor_id', string='KAMs supervisor')  # TODO убрать после миграции на кураторов
    supervisor_user_id = fields.Many2one(related='plan_supervisor_id.supervisor_user_id', readonly=True)  # TODO убрать после миграции на кураторов
    curator_id = fields.Many2one(related='plan_supervisor_id.curator_id', string='KAMs supervisor')
    curator_user_id = fields.Many2one(related='plan_supervisor_id.curator_user_id', readonly=True)
    key_account_manager_id = fields.Many2one('hr.employee', string='Key Account Manager', check_company=True, copy=True,
                                             required=True, tracking=True)

    is_use_ebit = fields.Boolean(related='plan_supervisor_id.is_use_ebit', string="using EBIT", tracking=True)
    is_use_net_profit = fields.Boolean(related='plan_supervisor_id.is_use_net_profit', string="using Net Profit", tracking=True)

    name_to_show = fields.Char(string='name_to_show', compute='_get_name_to_show')
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

    @api.depends('budget_plan_kam_spec_ids')
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

        for row in self.budget_plan_kam_spec_ids:
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
        for plan_kam in self:
            plan_kam.name_to_show = str(
                plan_kam.year) + ' ' + plan_kam.project_office_id.name + ' ' + plan_kam.key_account_manager_id.name

    def insert_spec(self,type_row, plan_id):
        type_plan_row_vals = []
        type_plan_row_vals.append(dict(
              type_row=type_row
            , budget_plan_kam_id=plan_id
        ))
        print('insert_spec type_row = ',type_row)
        self.env['project_budget.budget_plan_kam_spec'].create(type_plan_row_vals)

    # @api.onchange('is_use_ebit', 'is_use_net_profit')
    def _check_use_ebit_use_net_profit(self):
        print('_check_changes_project')
        for row in self:
            print('row.is_use_ebit = ', row.is_use_ebit)
            print('row.is_use_net_profit = ', row.is_use_net_profit)
            if row.is_use_ebit == False:
                for budget_plan_kam_spec in row.budget_plan_kam_spec_ids:
                    if budget_plan_kam_spec.type_row == 'ebit':
                        print('ebit unlink')
                        budget_plan_kam_spec.unlink()
            else:
                isexistebit = False
                for budget_plan_kam_spec in row.budget_plan_kam_spec_ids:
                    if budget_plan_kam_spec.type_row == 'ebit':
                        isexistebit = True
                print('isexistebit=',isexistebit)
                if isexistebit == False:
                    self.insert_spec('ebit',row.id)

            if row.is_use_net_profit == False:
                for budget_plan_kam_spec in row.budget_plan_kam_spec_ids:
                    if budget_plan_kam_spec.type_row == 'net_profit':
                        print('net_profit unlink')
                        budget_plan_kam_spec.unlink()
            else:
                isexistnet_profit = False
                for budget_plan_kam_spec in row.budget_plan_kam_spec_ids:
                    if budget_plan_kam_spec.type_row == 'net_profit':
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
        budget_plan_kams = super(budget_plan_kam, self).create(vals_list)
        for spec_plan_kam in budget_plan_kams:
            for type_plan_row in type_plan_rows:
                self.insert_spec( type_plan_row[0], spec_plan_kam.id)
        budget_plan_kams._check_use_ebit_use_net_profit()
        self.env.flush_all()
        return budget_plan_kams

    class budget_plan_kam_spec(models.Model):
        _name = 'project_budget.budget_plan_kam_spec'
        budget_plan_kam_id = fields.Many2one('project_budget.budget_plan_kam', string='plan kam',
                                                    index=True, ondelete='cascade')
        currency_id = fields.Many2one(related='budget_plan_kam_id.currency_id', readonly=True)

        type_row = fields.Selection(type_plan_rows, required=True, index=True, readonly=True)

        q1_plan = fields.Monetary(string='q1_plan', tracking=True)
        q2_plan = fields.Monetary(string='q2_plan', tracking=True)
        q3_plan = fields.Monetary(string='q3_plan', tracking=True)
        q4_plan = fields.Monetary(string='q4_plan', tracking=True)
        year_plan = fields.Monetary(string='year_plan', compute='_compute_totals', store=False,
                                    tracking=True)
        q1_fact = fields.Monetary(string='q1 fact', tracking=True)
        q2_fact = fields.Monetary(string='q2 fact', tracking=True)
        q3_fact = fields.Monetary(string='q3 fact', tracking=True)
        q4_fact = fields.Monetary(string='q4 fact', tracking=True)
        year_fact = fields.Monetary(string='year fact', compute='_compute_totals', store=False, tracking=True)

        q1_plan_6_6 = fields.Monetary(string='q1_plan 6+6', tracking=True)
        q2_plan_6_6 = fields.Monetary(string='q2_plan 6+6', tracking=True)
        q3_plan_6_6 = fields.Monetary(string='q3_plan 6+6', tracking=True)
        q4_plan_6_6 = fields.Monetary(string='q4_plan 6+6', tracking=True)
        year_plan_6_6 = fields.Monetary(string='year_plan 6+6', compute='_compute_totals', store=False,
                                        tracking=True)

        @api.depends("q1_plan", "q2_plan", "q3_plan", "q4_plan",
                     "q1_plan_6_6", "q2_plan_6_6", "q3_plan_6_6", "q4_plan_6_6", )
        def _compute_totals(self):
            for row in self:
                row.year_plan = row.q1_plan + row.q2_plan + row.q3_plan + row.q4_plan
                row.year_plan_6_6 = row.q1_plan_6_6 + row.q2_plan_6_6 + row.q3_plan_6_6 + row.q4_plan_6_6 + row.q1_fact + row.q2_fact
                row.year_fact = row.q1_fact + row.q2_fact + row.q3_fact + row.q4_fact

        def calc_fact(self):
            for plan_kam in self:
                return False
