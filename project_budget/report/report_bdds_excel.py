import logging

from odoo import models
from odoo.tools import date_utils
from datetime import date, datetime, timedelta
from xlsxwriter.utility import xl_col_to_name
from collections import OrderedDict
from copy import deepcopy

isdebug = False
logger = logging.getLogger("*___forecast_report___*")


class ReportBDDSExcel(models.AbstractModel):
    _name = 'report.project_budget.report_bdds_excel'
    _description = 'project_budget.report_bdds_excel'
    _inherit = 'report.report_xlsx.abstract'

    month_rus_name = [
        'Январь',
        'Февраль',
        'Март',
        'Апрель',
        'Май',
        'Июнь',
        'Июль',
        'Август',
        'Сентябрь',
        'Октябрь',
        'Ноябрь',
        'Декабрь',
    ]

    def centers_with_parents(self, ids, max_level):
        if not ids:
            return max_level
        max_level += 1
        new_ids = [center.id for center in self.env['account.analytic.account'].search([
            ('parent_id', 'in', ids),
            ('plan_id', '=',
             self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
        ])]
        return self.centers_with_parents(new_ids, max_level)

    def calculate_periods_dict(self, workbook, report_period):
        head_format = workbook.add_format({
            'border': 1,
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'bottom',
            'num_format': '#,##0',
            'fg_color': '#16365c',
            'color': '#ffffff',
        })
        center_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_size': 14,
            'align': 'center',
            'valign': 'right',
            'fg_color': '#538DD5',
            'color': '#ffffff',
            'num_format': '#,##0',
        })
        company_format = workbook.add_format({
            'top': 2,
            'bottom': 2,
            'left': 1,
            'right': 1,
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'right',
            'num_format': '#,##0',
            'fg_color': '#3E6894',
            'color': '#ffffff',
        })
        total_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_size': 14,
            'align': 'center',
            'valign': 'right',
            'num_format': '#,##0',
            'fg_color': '#FDE9D9',
        })
        project_format = workbook.add_format({
            'border': 1,
            'font_size': 11,
            'num_format': '#,##0',
        })
        project_total_format = workbook.add_format({
            'border': 1,
            'bold': True,
            'font_size': 11,
            'num_format': '#,##0',
            'fg_color': '#C5D9F1',
        })
        supplier_format = workbook.add_format({
            'border': 1,
            'font_size': 9,
            'num_format': '#,##0',
        })

        periods_dict = OrderedDict()

        month_start = date_utils.start_of(report_period[0], 'month')
        month_end = date_utils.end_of(month_start, 'month')
        last_month_start = date_utils.start_of(report_period[1], 'month')
        last_month_end = date_utils.end_of(last_month_start, 'month')
        period_limits = [month_start, last_month_end]
        col = 0
        month_cols = []

        col_format = (17, None)

        while month_start <= last_month_start:
            periods_dict[(month_start, month_end)] = {
                'type': 'month',
                'cols': [
                    {
                        'print': 'incomes',
                        'print_head': self.month_rus_name[month_start.month - 1] + ' ' + str(month_start.year),
                        'project_format': project_format,
                        'project_total_format': project_total_format,
                        'head_format': head_format,
                        'center_format': center_format,
                        'company_format': company_format,
                        'total_format': total_format,
                        'supplier_format': supplier_format,
                        'col_format': col_format,
                    },
                ]
            }
            col += 1
            month_cols.append(col)
            if month_start.month == 12:
                periods_dict['sum_year_' + str(month_start.year)] = {
                    'type': 'sum_year',
                    'date': month_end,
                    'cols': [
                        {
                            'print': 'incomes',
                            'print_head': str(month_start.year) + ' год',
                            'project_format': project_format,
                            'project_total_format': project_total_format,
                            'head_format': head_format,
                            'center_format': center_format,
                            'company_format': company_format,
                            'total_format': total_format,
                            'supplier_format': supplier_format,
                            'col_format': col_format,
                            'formula': month_cols.copy(),
                        },
                    ],
                }
                month_cols = []
            month_start = date_utils.add(month_start, months=1)
            month_end = date_utils.end_of(month_start, 'month')
        return periods_dict, period_limits

    def get_budget_items(self, company_ids, periods_dict):
        res = {}
        for company_id in company_ids.ids:
            budget_items = self.env['account.budget.item'].search([('company_id', '=', company_id)], order='sequence')
            for budget_item in budget_items:
                res.setdefault(company_id, {}).setdefault(budget_item['direction'], OrderedDict()).setdefault(budget_item['id'], {'name': budget_item['name'], 'periods': {key: 0 for key in periods_dict.keys()}, 'suppliers': {}})
        return res

    def get_data_from_projects(self, projects, periods_dict):
        data = {}
        budget_items = self.get_budget_items(projects.company_id, periods_dict)
        for project in projects:
            pds_is_present = False
            if project.step_status == 'project':
                pds_plan_list = project.planned_cash_flow_ids
                cost_plan_list = project.planned_cost_flow_ids
            elif project.step_status == 'step':
                pds_plan_list = project.planned_step_cash_flow_ids
                cost_plan_list = project.planned_step_cost_flow_ids
            else:
                continue
            if budget_items.get(project.company_id.id):
                project_data = deepcopy(budget_items[project.company_id.id])
            else:
                project_data = {
                    'income': {0: {'name': 'Поступления', 'periods': {key: 0 for key in periods_dict.keys()}, 'suppliers': {}}},
                    'expense': {0: {'name': 'Платежи (расходы)', 'periods': {key: 0 for key in periods_dict.keys()}, 'suppliers': {}}},
                }
            for period, options in periods_dict.items():
                if 'sum' not in period:
                    if budget_items.get(project.company_id.id):
                        for pds_plan in pds_plan_list:
                            if period[0] <= pds_plan.date_cash <= period[1]: # TODO
                                pds_is_present = True
                                project_data['income'][pds_plan['budget_item_id'].id]['periods'][period] += pds_plan.sum_cash  # TODO
                        for cost_plan in cost_plan_list:
                            if period[0] <= cost_plan.date <= period[1]:
                                pds_is_present = True
                                project_data['expense'][cost_plan['budget_item_id'].id]['periods'][period] -= cost_plan.amount_in_company_currency
                                if cost_plan.supplier_id:
                                    project_data['expense'][cost_plan['budget_item_id'].id]['suppliers'].setdefault(cost_plan.supplier_id.id, {'name': cost_plan.supplier_id.name, 'periods': {key: 0 for key in periods_dict.keys()}})
                                    project_data['expense'][cost_plan['budget_item_id'].id]['suppliers'][cost_plan.supplier_id.id]['periods'][period] -= cost_plan.amount_in_company_currency
                    else:
                        for pds_plan in pds_plan_list:
                            if period[0] <= pds_plan.date_cash <= period[1]:  # TODO
                                pds_is_present = True
                                project_data['income'][0]['periods'][period] += pds_plan.sum_cash  # TODO
                        for cost_plan in cost_plan_list:
                            if period[0] <= cost_plan.date <= period[1]:
                                pds_is_present = True
                                project_data['expense'][0]['periods'][period] -= cost_plan.amount_in_company_currency
                                if cost_plan.supplier_id:
                                    project_data['expense'][0]['suppliers'].setdefault(cost_plan.supplier_id.id, {'name': cost_plan.supplier_id.name,  'periods': {key: 0 for key in periods_dict.keys()}})
                                    project_data['expense'][0]['suppliers'][cost_plan.supplier_id.id]['periods'][period] -= cost_plan.amount_in_company_currency
            if pds_is_present:
                data.setdefault(project.company_id.name, {}).setdefault(
                    project.responsibility_center_id.name, {}).setdefault(
                    project.project_id, {})

                project_step_id = ''

                if project.step_status == 'project':
                    project_step_id = project.project_id
                elif project.step_status == 'step':
                    project_step_id = project.step_project_parent_id.project_id + "|" + project.project_id

                project_data['info'] = {
                    'key_account_manager_id': project.key_account_manager_id.name,
                    'partner_id': project.partner_id.name,
                    'essence_project': project.essence_project,
                    'project_id': project_step_id,
                    'probability': self.get_estimated_probability_name_forecast(project.stage_id.code),
                    'amount_total': project.amount_total_in_company_currency,
                    'margin': project.margin_in_company_currency,
                    'profitability': project.profitability,
                    'dogovor_number': project.dogovor_number or '',
                    'tax_id': project.tax_id.name,
                }

                data[project.company_id.name][project.responsibility_center_id.name][
                    project.project_id] = project_data
        return data

    def get_estimated_probability_name_forecast(self, name):
        result = name
        if name == '0': result = 'Отменен'
        if name == '30': result = 'Идентификация проекта'
        if name == '50': result = 'Подготовка ТКП'
        if name == '75': result = 'Подписание договора'
        if name == '100': result = 'Исполнение'
        if name == '100(done)': result = 'Исполнен/закрыт'
        return result

    def print_head(self, workbook, sheet, row, column, periods_dict):
        head_format = workbook.add_format({
            'border': 1,
            'bold': True,
            'font_size': 14,
            'align': 'left',
            'valign': 'bottom',
            'num_format': '#,##0',
            'fg_color': '#16365c',
            'color': '#ffffff'
        })

        sheet.set_row(row, 18)
        sheet.write(row, column, "Статьи бюджета движения денежных средств", head_format)
        column += 1
        for period, options in periods_dict.items():
            for col in options['cols']:
                string = col['print_head']
                sheet.set_column(column, column, *(col['col_format']))
                sheet.write(row, column, string, col['head_format'])
                column += 1
        return column

    def print_project_values(self, workbook, sheet, row, column, data, periods_dict, level):
        project_format = workbook.add_format({
            'border': 1,
            'font_size': 11,
            'num_format': '#,##0',
            'valign': 'left',
            'indent': 4,
        })
        project_total_format = workbook.add_format({
            'border': 1,
            'bold': True,
            'font_size': 11,
            'num_format': '#,##0',
            'fg_color': '#C5D9F1',
            'valign': 'left',
        })
        project_total_format_indent = workbook.add_format({
            'border': 1,
            'bold': True,
            'font_size': 11,
            'num_format': '#,##0',
            'fg_color': '#C5D9F1',
            'valign': 'left',
            'indent': 2,
        })
        supplier_format = workbook.add_format({
            'border': 1,
            'font_size': 9,
            'num_format': '#,##0',
            'valign': 'left',
            'indent': 6,
        })

        project_row = row + 1
        sheet.set_row(project_row, False, False, {'hidden': 1, 'level': level + 1})
        sheet.write(project_row, 0, 'Поступления', project_total_format_indent)
        income_total_row = project_row
        income_rows = []
        project_row += 1
        for income in data['income'].values():
            sheet.set_row(project_row, False, False, {'hidden': 1, 'level': level + 2})
            sheet.write(project_row, 0, income['name'], project_format)
            self.print_row_values(sheet, project_row, column, income, periods_dict, 'project_format')
            income_rows.append(project_row)
            project_row += 1
        self.print_vertical_sum_formula(sheet, income_total_row, income_rows, periods_dict, 1, 'project_total_format')

        sheet.set_row(project_row, False, False, {'hidden': 1, 'level': level + 1})
        sheet.write(project_row, 0, 'Платежи (расходы)', project_total_format_indent)
        expense_total_row = project_row
        expense_rows = []
        project_row += 1
        for expense in data['expense'].values():
            sheet.set_row(project_row, False, False, {'hidden': 1, 'level': level + 2})
            sheet.write(project_row, 0, expense['name'], project_format)
            self.print_row_values(sheet, project_row, column, expense, periods_dict, 'project_format')
            expense_rows.append(project_row)
            project_row += 1
            if expense.get('suppliers'):
                for supplier in expense['suppliers'].values():
                    sheet.set_row(project_row, False, False, {'hidden': 1, 'level': level + 3})
                    sheet.write(project_row, 0, supplier['name'], supplier_format)
                    self.print_row_values(sheet, project_row, column, supplier, periods_dict, 'supplier_format')
                    project_row += 1
        self.print_vertical_sum_formula(sheet, expense_total_row, expense_rows, periods_dict, 1, 'project_total_format')

        sheet.set_row(project_row, False, False, {'hidden': 1, 'level': level})
        sheet.write(project_row, 0, 'Итого чистые денежные средства, полученные от операционной деятельности', project_total_format)
        self.print_vertical_sum_formula(sheet, project_row, (income_total_row, expense_total_row), periods_dict, 1, 'project_total_format')
        return project_row

    def print_row_values(self, sheet, row, column, data, periods_dict, format_name):
        for period in periods_dict:
            for col in periods_dict[period]['cols']:
                if 'sum_year' in period:
                    formula = 'sum({1}{0}:{2}{0})'.format(
                        row + 1,
                        xl_col_to_name(1),
                        xl_col_to_name(column - 1),
                    )
                    sheet.write_formula(row, column, formula, col[format_name])
                    column += 1
                else:
                    sheet.write_number(row, column, data['periods'][period], col[format_name])
                    column += 1
        return row

    def print_row(self, sheet, workbook, companies, responsibility_centers, actual_center_ids, row, data, periods_dict,
                  level, max_level, dict_formula):
        project_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_size': 14,
            'align': 'center',
            'valign': 'left',
            'fg_color': '#538DD5',
            'color': '#ffffff',
        })
        center_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_size': 14,
            'align': 'center',
            'valign': 'left',
            'fg_color': '#538DD5',
            'color': '#ffffff',
        })
        company_format = workbook.add_format({
            'top': 2,
            'bottom': 2,
            'left': 1,
            'right': 1,
            'bold': True,
            'font_size': 14,
            'align': 'left',
            'valign': 'bottom',
            'num_format': '#,##0',
            'fg_color': '#3E6894',
            'color': '#ffffff'
        })

        for company in companies:
            if company.id not in dict_formula['company_ids']:
                row += 1
                dict_formula['company_ids'][company.id] = row
                sheet.write(row, 0, company.name, company_format)
            center_lines = list()

            for center in responsibility_centers.filtered(lambda r: r.company_id == company):
                if center.id in actual_center_ids:
                    if center.id not in dict_formula['center_ids']:
                        row += 1
                        dict_formula['center_ids'][center.id] = row
                        sheet.set_row(row, False, False, {'hidden': 1, 'level': level})
                        sheet.write(row, 0, center.name, center_format)
                    project_lines = list()
                    center_lines.append(row)
                    if center.name in data[company.name]:
                        for project, content in data[company.name][center.name].items():
                            # печатаем строки проектов
                            row += 1
                            sheet.set_row(row, False, False, {'hidden': 1, 'level': max_level + 1})
                            column = 0
                            sheet.write_string(
                                row, column,
                                content['info']['partner_id'] + '/'
                                + content['info']['project_id'] + '/'
                                + content['info']['key_account_manager_id'] + '/'
                                + content['info']['probability'],
                                project_format
                            )
                            for _ in range(1, len(periods_dict) + 1):
                                sheet.write_string(row, _, '', project_format)
                            column += 1
                            row = self.print_project_values(workbook, sheet, row, column, content, periods_dict, max_level + 1)
                            project_lines.append(row)

                    child_centers = self.env['account.analytic.account'].search([
                        ('parent_id', '=', center.id),
                        ('plan_id', '=', self.env.ref(
                            'analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
                    ], order='sequence')

                    if child_centers:
                        row, dict_formula = self.print_row(sheet, workbook, company, child_centers,
                                                            actual_center_ids, row, data, periods_dict,
                                                            level + 1, max_level, dict_formula)
                        for child_center in child_centers:
                            if child_center.id in actual_center_ids:
                                project_lines.append(dict_formula['center_ids'][child_center.id])

                    self.print_vertical_sum_formula(sheet, dict_formula['center_ids'][center.id], project_lines,
                                                    periods_dict, 1, 'center_format')

                if level == 1:
                    self.print_vertical_sum_formula(sheet, dict_formula['company_ids'][company.id], center_lines,
                                                    periods_dict, 1, 'company_format')

        return row, dict_formula

    def print_vertical_sum_formula(self, sheet, row, sum_lines, periods_dict, start_col, format_name):
        formula = '=sum('
        for n in range(len(sum_lines)):
            formula += '{0}{' + str(n + 1) + '},'
        formula += ')'
        col_counter = start_col
        for period, options in periods_dict.items():
            for col in options['cols']:
                result_formula = formula.format(xl_col_to_name(col_counter), *[line + 1 for line in sum_lines])
                sheet.write_formula(row, col_counter, result_formula, col[format_name])
                col_counter += 1

    def print_worksheet(self, workbook, budget, sheet_name, responsibility_center_ids, max_level, dict_formula, report_period):
        sheet = workbook.add_worksheet(sheet_name)
        sheet.set_zoom(85)

        head_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_size': 18,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#ffffff'
        })
        total_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_size': 14,
            'align': 'center',
            'valign': 'left',
            'fg_color': '#FDE9D9'
        })

        row = 0
        column = 0
        sheet.freeze_panes(3, 1)

        periods_dict, period_limits = self.calculate_periods_dict(workbook, report_period)
        sheet.merge_range(0, 0, row + 1, len(periods_dict), "Отчет о движении денежных средств", head_format)
        sheet.set_column(column, column, 55)
        row += 2

        projects = self.env['project_budget.projects'].search([
            '&','&','&',
            ('stage_id.project_state', '!=', 'cancel'),
            ('commercial_budget_id', '=', budget.id),
            '|', '&', ('step_status', '=', 'step'),
            ('step_project_parent_id.project_have_steps', '=', True),
            '&', ('step_status', '=', 'project'),
            ('project_have_steps', '=', False),
            '|', '|', '|',
            ('id', 'in', [plan.projects_id.id for plan in self.env['project_budget.planned_cash_flow'].search([]) if period_limits[0] <=  plan.date_cash <= period_limits[1]]),
            ('id', 'in', [plan.step_project_child_id.id for plan in self.env['project_budget.planned_cash_flow'].search([]) if period_limits[0] <=  plan.date_cash <= period_limits[1]]),
            ('id', 'in', [plan.projects_id.id for plan in self.env['project_budget.planned_cost_flow'].search([]) if period_limits[0] <=  plan.date <= period_limits[1]]),
            ('id', 'in', [plan.step_project_child_id.id for plan in self.env['project_budget.planned_cost_flow'].search([]) if period_limits[0] <=  plan.date <= period_limits[1]]),
        ], order='project_id')  # TODO

        data = self.get_data_from_projects(projects, periods_dict)

        actual_center_ids_set = set()
        for company in data:
            for center_name in data[company]:
                center = self.env['account.analytic.account'].search([
                    ('name', '=', center_name),
                    ('company_id.name', '=', company),
                    ('plan_id', '=',
                     self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
                ])
                actual_center_ids_set.add(center.id)
                while center.parent_id:
                    center = center.parent_id
                    actual_center_ids_set.add(center.id)

        actual_center_ids = list(actual_center_ids_set)

        column = self.print_head(workbook, sheet, row, column, periods_dict)

        companies = self.env['res.company'].search([('name', 'in', list(data.keys()))], order='name')

        if responsibility_center_ids:
            responsibility_centers = self.env['account.analytic.account'].search([
                ('id', 'in', responsibility_center_ids),
                ('parent_id', 'not in', responsibility_center_ids),
                ('plan_id', '=',
                 self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
            ], order='sequence')  # для сортировки так делаем + не берем дочерние оффисы, если выбраны их материнские
        else:
            responsibility_centers = self.env['account.analytic.account'].search([
                ('parent_id', '=', False),
                ('plan_id', '=',
                 self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
            ], order='sequence')  # для сортировки так делаем + берем сначала только верхние элементы

        row, dict_formula = self.print_row(sheet, workbook, companies, responsibility_centers, actual_center_ids, row,
                                           data, periods_dict, 1, max_level, dict_formula)

        if set(self.env['account.analytic.account'].search([
            ('plan_id', '=',
             self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
        ]).ids) == set(responsibility_center_ids):
            row += 1

            sheet.write(row, 0, 'Остаток денежных средств на конец периода', total_format)

            self.print_vertical_sum_formula(sheet, row, dict_formula['company_ids'].values(), periods_dict, 1,
                                            'total_format')

    def generate_xlsx_report(self, workbook, data, budgets):

        dict_formula = {'company_ids': {}, 'center_ids': {}, 'center_ids_not_empty': {}}

        responsibility_center_ids = data['responsibility_center_ids']

        report_period = (
            datetime.strptime(data['date_start'], "%Y-%m-%d").date(),
            datetime.strptime(data['date_end'], "%Y-%m-%d").date()
        )

        ids = [center.id for center in self.env['account.analytic.account'].search([
            ('parent_id', '=', False),
            ('id', 'in', responsibility_center_ids),
            ('plan_id', '=',
             self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
        ])]
        max_level = self.centers_with_parents(ids, 0)

        if set(self.env['account.analytic.account'].search([
            ('plan_id', '=',
             self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
        ]).ids) != set(responsibility_center_ids):
            max_level -= 1

        commercial_budget_id = data['commercial_budget_id']
        budget = self.env['project_budget.commercial_budget'].search([('id', '=', commercial_budget_id)])
        self.print_worksheet(workbook, budget, 'БДДС', responsibility_center_ids, max_level, dict_formula, report_period)
