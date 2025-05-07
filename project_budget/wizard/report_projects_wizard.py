from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from io import BytesIO
from datetime import date, timedelta, datetime
import pytz


class report_projects_wizard(models.TransientModel):
    _name = 'project_budget.projects.report.wizard'
    _description = 'Projects report Wizard'

    def _get_available_type_report(self):
        type_report = [
            ('kb', _('KB')),
            ('kb_fin', _('KB fin')),
            ('forecast_v2', _('Forecast_v2')),
            ('plan_fact', _('Plan-Fact')),
            ('raw_data', _('Raw Data')),
            ('management_committee', _('Management Committee')),
            ('pds_acceptance_by_date', _('PDS, Acceptance')),
            ('pds_weekly_plan_fact', _('PDS weekly plan fact')),
            ('pds_weekly_plan_fact_sa', _('PDS weekly plan fact SA')),
            ('week_to_week', _('Week to Week')),
            ('bdds', _('BDDS report')),
        ]
        if self.env.user.has_group('base.group_no_one'):
            type_report.append(('forecast_v3', _('Forecast_v3')))
        return type_report

    def _get_last_fixed_budget(self):
        last_fixed_budget = self.env['project_budget.commercial_budget'].search(
            [('budget_state', '=', 'fixed')], order='date_actual desc', limit=1
        )
        if not last_fixed_budget:
            return self.env['project_budget.commercial_budget'].search([('budget_state', '=', 'work')], limit=1)
        return last_fixed_budget

    year = fields.Integer(string='Year of the report', required=True,default=date.today().year)
    year_end = fields.Integer(string='end Year of the report', required=True, default=date.today().year)
    type_report = fields.Selection(selection=_get_available_type_report, default='kb', required=True)
    commercial_budget_id = fields.Many2one(
        'project_budget.commercial_budget', string='commercial_budget-',required=True,
        default=lambda self: self.env['project_budget.commercial_budget'].search([('budget_state', '=', 'work')], limit=1)
    )
    past_commercial_budget_id = fields.Many2one(
        'project_budget.commercial_budget', string='past budget', required=True, default=_get_last_fixed_budget
    )
    etalon_budget_id = fields.Many2one(
        'project_budget.commercial_budget', string='etalon budget',
        default=lambda self: self.env['project_budget.commercial_budget'].search([('budget_state', '=', 'work')], limit=1)
    )
    use_koeff_reserve = fields.Boolean(string='use koefficient for reserve', default = False)
    koeff_reserve = fields.Float(string='koefficient for reserve', default=0.6)
    koeff_potential = fields.Float(string='koefficient for potential', default=0.1)
    date_start = fields.Date(string='start of report', default=date.today(), required=True)
    date_end = fields.Date(string='end of report', compute='_compute_default_end_date', required=True, readonly=False)
    pds_accept = fields.Selection([('pds', 'PDS'), ('accept', 'Acceptance')], string='PDS Accept', default='pds', required=True)
    report_with_projects = fields.Boolean(string='detailed report', default=True)
    responsibility_center_ids = fields.Many2many('account.analytic.account', relation='report_responsibility_center_rel',
                                          column1='id', column2='responsibility_center_id', string='Project offices')
    print_managers = fields.Boolean(string='print managers', default=False)
    systematica_forecast = fields.Boolean(string='systematica forecast', default=False)
    three_quarters_report = fields.Boolean(string='report for three quarters', default=True)

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for report in self:
            if report.date_end < report.date_start:
                raise_text = _("End date should be later then start date")
                raise ValidationError(raise_text)

    @api.onchange('type_report')
    def _compute_default_end_date(self):
        for report in self:
            if report.type_report == 'bdds':
                report.date_end = date.today() + timedelta(days=335)
            else:
                report.date_end = date.today() + timedelta(days=7)

    def action_print_report(self):
        self.ensure_one()
        datas ={}
        # datas['report_type'] = 'xlsx'
        # datas['report_name'] = 'project_budget.report_tender_excel'
        # datas['report_file'] = 'project_budget.report_tender_excel'
        datas['year']= self.year
        datas['year_end']= self.year_end
        datas['date_start']= self.date_start
        datas['date_end']= self.date_end
        datas['commercial_budget_id'] = self.commercial_budget_id.id
        datas['past_commercial_budget_id'] = self.past_commercial_budget_id.id
        datas['etalon_budget_id'] = self.etalon_budget_id.id
        datas['koeff_reserve'] = 1 if not self.use_koeff_reserve else self.koeff_reserve
        datas['koeff_potential'] = 1 if not self.use_koeff_reserve else self.koeff_potential
        datas['pds_accept'] = self.pds_accept
        datas['report_with_projects'] = self.report_with_projects
        datas['responsibility_center_ids'] = self.env['account.analytic.account'].search([('plan_id', '=', self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id)]).ids if not self.responsibility_center_ids.ids else self.responsibility_center_ids.ids
        datas['print_managers'] = self.print_managers
        datas['systematica_forecast'] = self.systematica_forecast
        datas['three_quarters_report'] = self.three_quarters_report

        print('data=', datas)
        report_name = 'Project_list_' + str(self.year) + '_' + self.type_report + '.xlsx'

        if self.type_report == 'kb':
            return self.env.ref('project_budget.action_projects_list_report_xlsx_kb').report_action(self, data=datas)

        if self.type_report == 'kb_fin':
            return self.env.ref('project_budget.action_projects_list_report_xlsx_kb_fin').report_action(self, data=datas)

        # if self.type_report == 'forecast':
        #     return self.env.ref('project_budget.action_projects_list_report_xlsx_forecast').report_action(self, data=datas)

        if self.type_report == 'forecast_v2':
            return self.env.ref('project_budget.action_projects_list_report_xlsx_forecast_v2').report_action(self, data=datas)

        if self.type_report == 'forecast_v3':
            return self.env.ref('project_budget.action_projects_list_report_xlsx_forecast_v3').report_action(self, data=datas)

        if self.type_report == 'plan_fact':
            return self.env.ref('project_budget.action_projects_list_report_xlsx_plan_fact').report_action(self, data=datas)

        # if self.type_report == 'svod':
        #     return self.env.ref('project_budget.action_projects_list_report_xlsx_svod').report_action(self, data=datas)

        if self.type_report == 'raw_data':
            # self.env.ref('project_budget.action_projects_list_report_xlsx_svod').report_file = report_name
            return self.env.ref('project_budget.action_projects_list_report_xlsx_raw_data').report_action(self, data=datas)

        # if self.type_report == 'overdue':
        #     # self.env.ref('project_budget.action_projects_list_report_xlsx_svod').report_file = report_name
        #     return self.env.ref('project_budget.action_projects_list_report_xlsx_overdue').report_action(self, data=datas)

        if self.type_report == 'management_committee':
            c_ids = self.env['res.company'].browse(self.env.context.get('allowed_company_ids', []))
            print_report_name = f"{'_'.join(name.strip().replace(' ', '_') for name in c_ids.mapped('name'))}_{datetime.now(pytz.timezone(self.env.user.tz)).strftime('%Y%m%d_%H%M%S')}"
            return self.env.ref('project_budget.action_projects_list_report_xlsx_management_committee').with_context(
                print_report_name=print_report_name).report_action(self, data=datas)
        
        if self.type_report == 'pds_acceptance_by_date':
            return self.env.ref('project_budget.action_projects_list_report_xlsx_pds_acceptance_by_date').report_action(self, data=datas)

        # if self.type_report == 'pds_weekly':
        #     return self.env.ref('project_budget.action_projects_list_report_xlsx_pds_weekly').report_action(self, data=datas)

        if self.type_report == 'pds_weekly_plan_fact':
            return self.env.ref('project_budget.action_projects_list_report_xlsx_pds_weekly_plan_fact').report_action(self, data=datas)

        if self.type_report == 'pds_weekly_plan_fact_sa':
            return self.env.ref('project_budget.action_projects_list_report_xlsx_pds_weekly_plan_fact_sa').report_action(self, data=datas)

        if self.type_report == 'week_to_week':
            return self.env.ref('project_budget.action_projects_list_report_xlsx_week_to_week').report_action(self, data=datas)

        if self.type_report == 'contracting_revenue_cash':
            return self.env.ref('project_budget.action_projects_list_report_xlsx_contracting_revenue_cash').report_action(self, data=datas)

        if self.type_report == 'bdds':
            return self.env.ref('project_budget.action_projects_list_report_xlsx_bdds').report_action(self, data=datas)
