from odoo import models, fields, _
from odoo.exceptions import UserError
from io import BytesIO
from datetime import date

class report_projects_wizard(models.TransientModel):
    _name = 'project_budget.projects.report.wizard'
    _description = 'Projects report Wizard'
    year = fields.Integer(string='Year of the report', required=True,default=date.today().year)
    year_end = fields.Integer(string='end Year of the report', required=True, default=date.today().year)
    type_report = fields.Selection([
        ('kb', 'KB'),
        ('forecast', 'Forecast'),
        ('svod', 'Svod'),
        ('raw_data', 'Raw Data'),
        ('overdue', 'Overdue'),
        ('management_committee', 'Management Committee'),
    ],
        required=True, default='kb')
    commercial_budget_id = fields.Many2one('project_budget.commercial_budget', string='commercial_budget-',required=True
                                           ,default=lambda self: self.env['project_budget.commercial_budget'].search([('budget_state', '=', 'work')], limit=1)
                                          )
    use_koeff_reserve = fields.Boolean(string='use koefficient for reserve', default = False)
    koeff_reserve = fields.Float(string='koefficient for reserve', default=0.6)
    koeff_potential = fields.Float(string='koefficient for potential', default=0.1)


    def action_print_report(self):
        self.ensure_one()
        datas ={}
        # datas['report_type'] = 'xlsx'
        # datas['report_name'] = 'project_budget.report_tender_excel'
        # datas['report_file'] = 'project_budget.report_tender_excel'
        datas['year']= self.year
        datas['year_end']= self.year_end
        datas['commercial_budget_id'] = self.commercial_budget_id.id
        datas['koeff_reserve'] = 1 if not self.use_koeff_reserve else self.koeff_reserve
        datas['koeff_potential'] = 1 if not self.use_koeff_reserve else self.koeff_potential

        print('data=',datas)
        report_name = 'Project_list_' + str(self.year) + '_' + self.type_report + '.xlsx'

        if self.type_report == 'kb':
            return self.env.ref('project_budget.action_projects_list_report_xlsx_kb').report_action(self, data=datas)

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
            return self.env.ref('project_budget.action_projects_list_report_xlsx_management_committee').report_action(self, data=datas)
