from odoo import models, fields, _
from odoo.exceptions import UserError
from io import BytesIO
from datetime import date, timedelta, datetime
import pytz

class report_projects_wizard(models.TransientModel):
    _name = 'project_budget.projects.report.wizard'
    _description = 'Projects report Wizard'
    year = fields.Integer(string='Year of the report', required=True,default=date.today().year)
    year_end = fields.Integer(string='end Year of the report', required=True, default=date.today().year)
    type_report = fields.Selection([
        ('kb', 'KB'),
        ('kb_fin', 'KB fin'),
        ('forecast', 'Forecast'),
        ('svod', 'Svod'),
        ('raw_data', 'Raw Data'),
        ('overdue', 'Overdue'),
        ('management_committee', 'Management Committee'),
        ('pds_acceptance_by_date', 'PDS, Acceptance'),
        ('pds_weekly', 'PDS weekly'),
    ],
        required=True, default='kb')
    commercial_budget_id = fields.Many2one('project_budget.commercial_budget', string='commercial_budget-',required=True
                                           ,default=lambda self: self.env['project_budget.commercial_budget'].search([('budget_state', '=', 'work')], limit=1)
                                          )
    use_koeff_reserve = fields.Boolean(string='use koefficient for reserve', default = False)
    koeff_reserve = fields.Float(string='koefficient for reserve', default=0.6)
    koeff_potential = fields.Float(string='koefficient for potential', default=0.1)
    delta = timedelta(days=7)
    date_start = fields.Date(string='start of report', default=date.today(), required=True)
    date_end = fields.Date(string='end of report', default=date.today() + delta, required=True)
    pds_accept = fields.Selection([('pds', 'PDS'), ('accept', 'Acceptance')], string='PDS Accept', default='pds', required=True)


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
        datas['koeff_reserve'] = 1 if not self.use_koeff_reserve else self.koeff_reserve
        datas['koeff_potential'] = 1 if not self.use_koeff_reserve else self.koeff_potential
        datas['pds_accept'] = self.pds_accept

        print('data=',datas)
        report_name = 'Project_list_' + str(self.year) + '_' + self.type_report + '.xlsx'

        if self.type_report == 'kb':
            return self.env.ref('project_budget.action_projects_list_report_xlsx_kb').report_action(self, data=datas)

        if self.type_report == 'kb_fin':
            return self.env.ref('project_budget.action_projects_list_report_xlsx_kb_fin').report_action(self, data=datas)

        if self.type_report == 'forecast':
            return self.env.ref('project_budget.action_projects_list_report_xlsx_forecast').report_action(self, data=datas)

        if self.type_report == 'svod':
            return self.env.ref('project_budget.action_projects_list_report_xlsx_svod').report_action(self, data=datas)

        if self.type_report == 'raw_data':
            # self.env.ref('project_budget.action_projects_list_report_xlsx_svod').report_file = report_name
            return self.env.ref('project_budget.action_projects_list_report_xlsx_raw_data').report_action(self, data=datas)

        if self.type_report == 'overdue':
            # self.env.ref('project_budget.action_projects_list_report_xlsx_svod').report_file = report_name
            return self.env.ref('project_budget.action_projects_list_report_xlsx_overdue').report_action(self, data=datas)

        if self.type_report == 'management_committee':
            report_obj = self.env.ref('project_budget.action_projects_list_report_xlsx_management_committee')
            # name = {"en_US": "Projects Report Management Committee", "ru_RU": "Отчет для УК"}  # на память
            companies = ''
            for company_id in self.env.context.get('allowed_company_ids', ''):
                companies += self.env['res.company'].search([('id', '=', company_id)]).name.strip().replace(' ', '_') + '_'
            report_obj.sudo().name = f"{companies}_{datetime.now(pytz.timezone('Europe/Moscow')).strftime('%Y%m%d_%H%M%S')}"
            return report_obj.report_action(self, data=datas)

        if self.type_report == 'pds_acceptance_by_date':
            return self.env.ref('project_budget.action_projects_list_report_xlsx_pds_acceptance_by_date').report_action(self, data=datas)

        if self.type_report == 'pds_weekly':
            return self.env.ref('project_budget.action_projects_list_report_xlsx_pds_weekly').report_action(self, data=datas)
