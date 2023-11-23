from odoo import models
from xlsxwriter.utility import xl_col_to_name
from datetime import date, datetime


class report_pds_acceptance_by_date_excel(models.AbstractModel):
    _name = 'report.project_budget.report_pds_acceptance_by_date_excel'
    _description = 'project_budget.report_pds_acceptance_by_date_excel'
    _inherit = 'report.report_xlsx.abstract'

    pds_accept_str = {'pds': 'ПДС', 'accept': 'валовая выручка'}

    def get_sum_plan_pds_project_step(self, project, step, date_start, date_end):

        sum_cash = 0

        pds_list = project.planned_cash_flow_ids

        if pds_list:
            for pds in pds_list:
                if step:
                    if pds.project_steps_id.id != step.id:
                        continue
                if date_start <= pds.date_cash <= date_end and pds.forecast in ('commitment', 'reserve', 'from_project'):
                    sum_cash += pds.distribution_sum_with_vat_ostatok

        return sum_cash

    def get_sum_plan_acceptance_project_step(self, project, step, date_start, date_end):

        sum_cash = 0

        acceptance_list = project.planned_acceptance_flow_ids

        if acceptance_list:
            for acceptance in acceptance_list:
                if step:
                    if acceptance.project_steps_id.id != step.id:
                        continue
                if date_start <= acceptance.date_cash <= date_end and acceptance.forecast in ('commitment', 'reserve', 'from_project'):
                    sum_cash += acceptance.distribution_sum_without_vat_ostatok

        return sum_cash

    def print_worksheet(self, workbook, budget, sheet_name, date_start, date_end, pds_accept):

        sheet = workbook.add_worksheet(sheet_name)

        head_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_name': 'Calibri',
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#EBDCFE',
        })
        title_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_name': 'Calibri',
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#D9E1F2',
        })
        total_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_name': 'Calibri',
            'font_size': 11,
            'text_wrap': True,
            'align': 'left',
            'valign': 'vcenter',
            'fg_color': '#C6E0B4',
            'num_format': '#,##0',
        })
        total_num_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_name': 'Calibri',
            'font_size': 11,
            'text_wrap': True,
            'align': 'right',
            'valign': 'vcenter',
            'fg_color': '#C6E0B4',
            'num_format': '#,##0',
        })
        row_format = workbook.add_format({
            'border': 1,
            'font_size': 11,
            'font_name': 'Calibri',
            'num_format': '#,##0',
        })

        row = 0
        column = 0

        sheet.merge_range(row, column, row, column + 10, 'Прогноз: ' + self.pds_accept_str[pds_accept] + ' (' +
                          date.strftime(date_start, '%d.%m.%y') + '-' +
                          date.strftime(date_end, '%d.%m.%y') + ')', head_format)

        row += 1

        sheet.write_string(row, column, 'Компания', title_format)
        sheet.set_column(column, column, 23)
        column += 1
        sheet.write_string(row, column, 'Проектный офис', title_format)
        sheet.set_column(column, column, 23)
        column += 1
        sheet.write_string(row, column, 'КАМ', title_format)
        sheet.set_column(column, column, 23)
        column += 1
        sheet.write_string(row, column, 'Вероятность', title_format)
        sheet.set_column(column, column, 23)
        column += 1
        sheet.write_string(row, column, 'Заказчик', title_format)
        sheet.set_column(column, column, 23)
        column += 1
        sheet.write_string(row, column, 'ID проекта', title_format)
        sheet.set_column(column, column, 23)
        column += 1
        sheet.write_string(row, column, 'ID этапа проекта', title_format)
        sheet.set_column(column, column, 23)
        column += 1
        sheet.write_string(row, column, 'Код этапа проекта', title_format)
        sheet.set_column(column, column, 23)
        column += 1
        sheet.write_string(row, column, 'Наименование сделки', title_format)
        sheet.set_column(column, column, 23)
        column += 1
        sheet.write_string(row, column, 'Юрлицо, подписывающее договор', title_format)
        sheet.set_column(column, column, 35)
        column += 1
        sheet.write_string(row, column, 'Сумма, ' + self.pds_accept_str[pds_accept], title_format)
        sheet.set_column(column, column, 25)

        sheet.freeze_panes(2, 0)

        if pds_accept == 'pds':
            cur_budget_projects = self.env[
                'project_budget.projects'].search(
                ['&',
                 ('commercial_budget_id', '=', budget.id),
                 ('id', 'in', [pds.projects_id.id for pds in self.env['project_budget.planned_cash_flow'].search([]) if date_start <= pds.date_cash <= date_end]),
                 ]
            )
        else:
            cur_budget_projects = self.env[
                'project_budget.projects'].search(
                ['&',
                 ('commercial_budget_id', '=', budget.id),
                 ('id', 'in', [acc.projects_id.id for acc in self.env['project_budget.planned_acceptance_flow'].search([]) if date_start <= acc.date_cash <= date_end]),
                 ]
            )

        for project in cur_budget_projects:
            if project.project_steps_ids:
                for step in project.project_steps_ids:

                    if pds_accept == 'pds':
                        summ = self.get_sum_plan_pds_project_step(project, step, date_start, date_end)
                    else:
                        summ = self.get_sum_plan_acceptance_project_step(project, step, date_start,date_end)

                    if summ == 0:
                        continue

                    row += 1
                    column = 0

                    sheet.write_string(row, column, project.company_id.name, row_format)
                    column += 1
                    if project.legal_entity_signing_id.different_project_offices_in_steps and step.project_office_id:
                        sheet.write_string(row, column, step.project_office_id.name, row_format)
                    else:
                        sheet.write_string(row, column, project.project_office_id.name, row_format)
                    column += 1
                    sheet.write_string(row, column, project.project_manager_id.name, row_format)
                    column += 1
                    sheet.write_string(row, column, step.estimated_probability_id.name, row_format)
                    column += 1
                    sheet.write_string(row, column, project.customer_organization_id.name, row_format)
                    column += 1
                    sheet.write_string(row, column, project.project_id, row_format)
                    column += 1
                    sheet.write_string(row, column, step.step_id, row_format)
                    column += 1
                    sheet.write_string(row, column, (step.code or ''), row_format)
                    column += 1
                    sheet.write_string(row, column, step.essence_project , row_format)
                    column += 1
                    sheet.write_string(row, column, step.legal_entity_signing_id.name, row_format)
                    column += 1
                    sheet.write_number(row, column, summ, row_format)

            else:
                if pds_accept == 'pds':
                    summ = self.get_sum_plan_pds_project_step(project, False, date_start, date_end)
                else:
                    summ = self.get_sum_plan_acceptance_project_step(project, False, date_start, date_end)

                if summ == 0:
                    continue

                row += 1
                column = 0

                sheet.write_string(row, column, project.company_id.name, row_format)
                column += 1
                sheet.write_string(row, column, project.project_office_id.name, row_format)
                column += 1
                sheet.write_string(row, column, project.project_manager_id.name, row_format)
                column += 1
                sheet.write_string(row, column, project.estimated_probability_id.name, row_format)
                column += 1
                sheet.write_string(row, column, project.customer_organization_id.name, row_format)
                column += 1
                sheet.write_string(row, column, project.project_id, row_format)
                column += 1
                sheet.write_string(row, column, '', row_format)
                column += 1
                sheet.write_string(row, column, '', row_format)
                column += 1
                sheet.write_string(row, column, project.essence_project, row_format)
                column += 1
                sheet.write_string(row, column, project.legal_entity_signing_id.name, row_format)
                column += 1
                sheet.write_number(row, column, summ, row_format)

        row += 1
        sheet.merge_range(row, 0, row, 9, 'ИТОГО', total_format)
        sheet.write_formula(row, column, '=sum({0}{1}:{0}{2})'.format(xl_col_to_name(column), 3, row), total_num_format)

    def generate_xlsx_report(self, workbook, data, budgets):

        commercial_budget_id = data['commercial_budget_id']
        date_start = datetime.strptime(data['date_start'], '%Y-%m-%d').date()
        date_end = datetime.strptime(data['date_end'], '%Y-%m-%d').date()
        pds_accept = data['pds_accept']

        budget = self.env['project_budget.commercial_budget'].search([('id', '=', commercial_budget_id)])

        self.print_worksheet(workbook, budget, self.pds_accept_str[pds_accept], date_start, date_end, pds_accept)
