from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import pytz
from datetime import timedelta

class budget_plan_kam(models.Model):
    _name = 'project_budget.budget_plan_supervisor'
    _description = "Supervisors's budget plan on year"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name_to_show'

    year = fields.Integer(string="year plan", required=True, index=True, default=lambda self: fields.datetime.now().year)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Account Currency',  required = True, copy = True,
                                  default=lambda self: self.env['res.currency'].search([('name', '=', 'RUB')], limit=1),tracking=True)
    plan_kam_ids = fields.One2many('project_budget.budget_plan_kam', 'plan_supervisor_id', string="KAM's plans")

    project_office_id = fields.Many2one('project_budget.project_office', string='project_office', required=True,
                                        copy=True,tracking=True,  check_company=True)
    supervisor_id = fields.Many2one('project_budget.project_supervisor', string='KAMs supervisor',
                                            required=True, copy=True, tracking=True, check_company=True)
    supervisor_user_id = fields.Many2one(related='supervisor_id.user_id', readonly=True)
    contracting_q1_plan = fields.Monetary(string='contracting_q1_plan', tracking=True)
    contracting_q2_plan = fields.Monetary(string='contracting_q2_plan', tracking=True)
    contracting_q3_plan = fields.Monetary(string='contracting_q3_plan', tracking=True)
    contracting_q4_plan = fields.Monetary(string='contracting_q4_plan', tracking=True)
    contracting_year_plan = fields.Monetary(string='contracting_year_plan', compute = '_compute_totals', store = False, tracking = True )

    contracting_q1_fact = fields.Monetary(string='contracting_q1_fact', readonly = True)
    contracting_q2_fact = fields.Monetary(string='contracting_q2_fact')
    contracting_q3_fact = fields.Monetary(string='contracting_q3_fact')
    contracting_q4_fact = fields.Monetary(string='contracting_q4_fact')
    contracting_year_fact = fields.Monetary(string='contracting_year_fact', compute = '_compute_totals', store = False)


    cash_q1_plan = fields.Monetary(string='cash_q1_plan', tracking=True)
    cash_q2_plan = fields.Monetary(string='cash_q2_plan', tracking=True)
    cash_q3_plan = fields.Monetary(string='cash_q3_plan', tracking=True)
    cash_q4_plan = fields.Monetary(string='cash_q4_plan', tracking=True)
    cash_year_plan = fields.Monetary(string='cash_year_plan', compute = '_compute_totals', store = False, tracking = True )

    acceptance_q1_plan = fields.Monetary(string='acceptance_q1_plan', tracking=True)
    acceptance_q2_plan = fields.Monetary(string='acceptance_q2_plan', tracking=True)
    acceptance_q3_plan = fields.Monetary(string='acceptance_q3_plan', tracking=True)
    acceptance_q4_plan = fields.Monetary(string='acceptance_q4_plan', tracking=True)
    acceptance_year_plan = fields.Monetary(string='acceptance_year_plan', compute='_compute_totals', store=False, tracking=True)

    margin_income_q1_plan = fields.Monetary(string='margin_income_q1_plan', tracking=True)
    margin_income_q2_plan = fields.Monetary(string='margin_income_q2_plan', tracking=True)
    margin_income_q3_plan = fields.Monetary(string='margin_income_q3_plan', tracking=True)
    margin_income_q4_plan = fields.Monetary(string='margin_income_q4_plan', tracking=True)
    margin_income_year_plan = fields.Monetary(string='margin_income_year_plan', compute='_compute_totals', tracking=True)

    margin3_income_q1_plan = fields.Monetary(string='margin3_income_q1_plan', tracking=True)
    margin3_income_q2_plan = fields.Monetary(string='margin3_income_q2_plan', tracking=True)
    margin3_income_q3_plan = fields.Monetary(string='margin3_income_q3_plan', tracking=True)
    margin3_income_q4_plan = fields.Monetary(string='margin3_income_q4_plan', tracking=True)
    margin3_income_year_plan = fields.Monetary(string='margin3_income_year_plan', compute='_compute_totals', tracking=True)

    is_use_ebit = fields.Boolean(string="using EBIT", tracking = True)
    ebit_q1_plan = fields.Monetary(string='ebit_q1_plan', tracking=True)
    ebit_q2_plan = fields.Monetary(string='ebit_q2_plan', tracking=True)
    ebit_q3_plan = fields.Monetary(string='ebit_q3_plan', tracking=True)
    ebit_q4_plan = fields.Monetary(string='ebit_q4_plan', tracking=True)
    ebit_year_plan = fields.Monetary(string='ebit_year_plan', compute='_compute_totals', tracking=True)

    is_use_net_profit = fields.Boolean(string="using Net Profit", tracking=True)
    net_profit_q1_plan = fields.Monetary(string='net_profit_q1_plan', tracking=True)
    net_profit_q2_plan = fields.Monetary(string='net_profit_q2_plan', tracking=True)
    net_profit_q3_plan = fields.Monetary(string='net_profit_q3_plan', tracking=True)
    net_profit_q4_plan = fields.Monetary(string='net_profit_q4_plan', tracking=True)
    net_profit_year_plan = fields.Monetary(string='net_profit_year_plan', compute='_compute_totals', tracking=True)

    name_to_show = fields.Char(string='name_to_show', compute='_get_name_to_show')

    @api.depends('supervisor_id', 'year')
    def _get_name_to_show(self):
        for plan_supervisor in self:
            plan_supervisor.name_to_show = str(plan_supervisor.year) + ' '+plan_supervisor.supervisor_id.name + ' ' + plan_supervisor.project_office_id.name

    @api.depends("contracting_q1_plan","contracting_q2_plan","contracting_q3_plan","contracting_q4_plan",
                 "cash_q1_plan","cash_q2_plan","cash_q3_plan","cash_q4_plan",
                 "acceptance_q1_plan","acceptance_q2_plan","acceptance_q3_plan","acceptance_q4_plan",
                 "margin_income_q1_plan","margin_income_q2_plan","margin_income_q3_plan","margin_income_q4_plan",)
    def _compute_totals(self):
        for plan_kam in self:
            plan_kam.contracting_year_plan = plan_kam.contracting_q1_plan + plan_kam.contracting_q2_plan + plan_kam.contracting_q3_plan + plan_kam.contracting_q4_plan
            plan_kam.cash_year_plan = plan_kam.cash_q1_plan + plan_kam.cash_q2_plan + plan_kam.cash_q3_plan + plan_kam.cash_q4_plan
            plan_kam.acceptance_year_plan = plan_kam.acceptance_q1_plan + plan_kam.acceptance_q2_plan + plan_kam.acceptance_q3_plan + plan_kam.acceptance_q4_plan
            plan_kam.margin_income_year_plan = plan_kam.margin_income_q1_plan + plan_kam.margin_income_q2_plan + plan_kam.margin_income_q3_plan + plan_kam.margin_income_q4_plan
            plan_kam.margin3_income_year_plan = plan_kam.margin3_income_q1_plan + plan_kam.margin3_income_q2_plan + plan_kam.margin3_income_q3_plan + plan_kam.margin3_income_q4_plan
            plan_kam.ebit_year_plan = plan_kam.ebit_q1_plan + plan_kam.ebit_q2_plan + plan_kam.ebit_q3_plan + plan_kam.ebit_q4_plan
            plan_kam.net_profit_year_plan = plan_kam.net_profit_q1_plan + plan_kam.net_profit_q2_plan + plan_kam.net_profit_q3_plan + plan_kam.net_profit_q4_plan

    @api.onchange('is_use_ebit','is_use_net_profit')
    def _check_use_ebit_use_net_profit(self):
        print('_check_changes_project')
        for row in self:
            if row.is_use_ebit == False:
                row.ebit_q1_plan = 0
                row.ebit_q2_plan = 0
                row.ebit_q3_plan = 0
                row.ebit_q4_plan= 0
            if row.is_use_net_profit == False:
                row.net_profit_q1_plan = 0
                row.net_profit_q2_plan = 0
                row.net_profit_q3_plan = 0
                row.net_profit_q4_plan= 0

    def calc_fact(self):
        for plan_kam in self:
            return False