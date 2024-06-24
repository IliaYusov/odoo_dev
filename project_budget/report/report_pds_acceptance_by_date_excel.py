from odoo import models
from xlsxwriter.utility import xl_col_to_name
from datetime import date, datetime


class report_pds_acceptance_by_date_excel(models.AbstractModel):
    _name = 'report.project_budget.report_pds_acceptance_by_date_excel'
    _description = 'project_budget.report_pds_acceptance_by_date_excel'
    _inherit = 'report.report_xlsx.abstract'

    pds_accept_str = {'pds': 'ПДС', 'accept': 'валовая выручка'}

    def get_sum_plan_pds_project(self, project, date_start, date_end):

        sum_cash = 0

        if project.step_status == 'project':
            pds_list = project.planned_cash_flow_ids
        elif project.step_status == 'step':
            pds_list = project.planned_step_cash_flow_ids

        if pds_list:
            for pds in pds_list:
                if date_start <= pds.date_cash <= date_end and pds.forecast in ('commitment', 'reserve', 'from_project'):
                    sum_cash += max(pds.distribution_sum_with_vat_ostatok, 0)

        return sum_cash

    def get_sum_plan_acceptance_project(self, project, date_start, date_end):

        sum_cash = 0

        if project.step_status == 'project':
            acceptance_list = project.planned_acceptance_flow_ids
        elif project.step_status == 'step':
            acceptance_list = project.planned_step_acceptance_flow_ids

        if acceptance_list:
            for acceptance in acceptance_list:
                if date_start <= acceptance.date_cash <= date_end and acceptance.forecast in ('commitment', 'reserve', 'from_project'):
                    sum_cash += acceptance.distribution_sum_without_vat_ostatok

        return sum_cash

    def print_worksheet(self, workbook, budget, sheet_name, date_start, date_end, pds_accept, legal_entity_shift):

        global project_office_ids

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
        row_format_light = workbook.add_format({
            'border': 1,
            'font_size': 11,
            'font_name': 'Calibri',
            'num_format': '#,##0',
        })

        row_format_dark = workbook.add_format({
            'border': 1,
            'font_size': 11,
            'font_name': 'Calibri',
            'num_format': '#,##0',
            'fg_color': '#d9d9d9',
        })

        row = 1
        column = 0

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

        sheet.freeze_panes(2, 0)

        if project_office_ids:
            child_project_offices = self.env['project_budget.project_office'].search(
                [('id', 'in', project_office_ids)]).child_ids
            while child_project_offices:  # обходим дочерние офисы
                for child_project_office in child_project_offices:
                    if child_project_office.id not in project_office_ids:
                        project_office_ids.append(child_project_office.id)
                new_child_project_offices = child_project_offices.child_ids
                child_project_offices = new_child_project_offices

            project_offices = self.env['project_budget.project_office'].search([
                ('id', 'in', project_office_ids)], order='name')  # для сортировки так делаем
        else:
            project_offices = self.env['project_budget.project_office'].search([], order='name')

        if pds_accept == 'pds':
            cur_budget_projects = self.env[
                'project_budget.projects'].search([
                ('commercial_budget_id', '=', budget.id),
                '|', ('id', 'in', [pds.projects_id.id for pds in self.env['project_budget.planned_cash_flow'].search([]) if date_start <= pds.date_cash <= date_end]),
                ('id', 'in', [pds.step_project_child_id.id for pds in self.env['project_budget.planned_cash_flow'].search([]) if date_start <= pds.date_cash <= date_end]),
                ('stage_id.code', 'not in', ('0', '10')),
                ('project_office_id', 'in', project_offices.ids),
                '|', '&', ('step_status', '=', 'step'),
                ('step_project_parent_id.project_have_steps', '=', True),
                '&', ('step_status', '=', 'project'),
                ('project_have_steps', '=', False),
                ]).sorted(key=lambda r: (r.project_id if r.step_status == 'project' else r.step_project_parent_id.project_id + r.project_id))
        else:
            cur_budget_projects = self.env[
                'project_budget.projects'].search([
                ('commercial_budget_id', '=', budget.id),
                '|', ('id', 'in', [acc.projects_id.id for acc in self.env['project_budget.planned_acceptance_flow'].search([]) if date_start <= acc.date_cash <= date_end]),
                ('id', 'in', [acc.step_project_child_id.id for acc in self.env['project_budget.planned_acceptance_flow'].search([]) if date_start <= acc.date_cash <= date_end]),
                ('stage_id.code', 'not in', ('0', '10')),
                ('project_office_id', 'in', project_offices.ids),
                '|', '&', ('step_status', '=', 'step'),
                ('step_project_parent_id.project_have_steps', '=', True),
                '&', ('step_status', '=', 'project'),
                ('project_have_steps', '=', False),
                ]).sorted(key=lambda r: (r.project_id if r.step_status == 'project' else r.step_project_parent_id.project_id + r.project_id))

        shift = 0
        for entity_id in cur_budget_projects.legal_entity_signing_id:
            if entity_id.name not in legal_entity_shift:
                legal_entity_shift[entity_id.name] = shift
                column += 1
                sheet.write_string(row, column, self.pds_accept_str[pds_accept] + ', ' + entity_id.name, title_format)
                sheet.set_column(column, column, 15)
                shift += 1

        sheet.merge_range(0, 0, 0, column, 'Прогноз: ' + self.pds_accept_str[pds_accept] + ' (' +
                          date.strftime(date_start, '%d.%m.%y') + '-' +
                          date.strftime(date_end, '%d.%m.%y') + ')', head_format)

        for project in cur_budget_projects:
            if project.legal_entity_signing_id.name == project.company_id.name:
                row_format = row_format_light
            else:
                row_format = row_format_dark

            if pds_accept == 'pds':
                summ = self.get_sum_plan_pds_project(project, date_start, date_end)
            else:
                summ = self.get_sum_plan_acceptance_project(project, date_start, date_end)

            if summ == 0:
                continue

            row += 1
            column = 0

            sheet.write_string(row, column, project.company_id.name, row_format)
            column += 1
            sheet.write_string(row, column, project.project_office_id.name, row_format)
            column += 1
            sheet.write_string(row, column, project.key_account_manager_id.name, row_format)
            column += 1
            sheet.write_string(row, column, project.stage_id.code, row_format)
            column += 1
            sheet.write_string(row, column, project.partner_id.name, row_format)
            column += 1

            if project.step_status == 'project':
                sheet.write_string(row, column, project.project_id, row_format)
                column += 1
                sheet.write_string(row, column, '', row_format)
                column += 1
                sheet.write_string(row, column, '', row_format)
                column += 1
            elif project.step_status == 'step':
                sheet.write_string(row, column, project.step_project_parent_id.project_id, row_format)
                column += 1
                sheet.write_string(row, column, project.project_id, row_format)
                column += 1
                sheet.write_string(row, column, (project.step_project_number or ''), row_format)
                column += 1

            sheet.write_string(row, column, project.essence_project, row_format)
            column += 1
            sheet.write_string(row, column, project.legal_entity_signing_id.name, row_format)
            for shift in range(len(legal_entity_shift)):
                sheet.write_number(row, column + 1 + shift, 0, row_format)
            column += 1 + legal_entity_shift[project.legal_entity_signing_id.name]
            sheet.write_number(row, column, summ, row_format)

        row += 1
        sheet.merge_range(row, 0, row, 9, 'ИТОГО', total_format)
        for shift in range(len(legal_entity_shift)):
            sheet.write_formula(row, 10 + shift, '=sum({0}{1}:{0}{2})'.format(xl_col_to_name(10 + shift), 3, row), total_num_format)

        sheet.autofilter(1, 0, 1, 9)

    def generate_xlsx_report(self, workbook, data, budgets):

        global project_office_ids
        project_office_ids = data['project_office_ids']

        commercial_budget_id = data['commercial_budget_id']
        date_start = datetime.strptime(data['date_start'], '%Y-%m-%d').date()
        date_end = datetime.strptime(data['date_end'], '%Y-%m-%d').date()
        pds_accept = data['pds_accept']
        legal_entity_shift = {}  # таблица сдвига столбца с суммой в таблице в зависимости от юр лица

        budget = self.env['project_budget.commercial_budget'].search([('id', '=', commercial_budget_id)])

        self.print_worksheet(workbook, budget, self.pds_accept_str[pds_accept], date_start, date_end, pds_accept, legal_entity_shift)
