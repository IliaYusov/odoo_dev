from odoo import models
from datetime import date, datetime, timedelta
from dateutil.relativedelta import *
from xlsxwriter.utility import xl_col_to_name
from collections import OrderedDict
import logging

isdebug = False
logger = logging.getLogger("*___forecast_report___*")

class ReportPdsWeeklyPlanFactExcel(models.AbstractModel):
    _name = 'report.project_budget.report_pds_weekly_plan_fact_excel'
    _description = 'project_budget.report_pds_weekly_plan_fact_excel'
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

    def get_currency_rate_by_project(self,project):
        project_currency_rates = self.env['project_budget.project_currency_rates']
        return project_currency_rates._get_currency_rate_for_project_in_company_currency(project)

    def offices_with_parents(self, ids, max_level):
        if not ids:
            return max_level
        max_level += 1
        new_ids = [office.id for office in self.env['project_budget.project_office'].search([('parent_id', 'in', ids)])]
        return self.offices_with_parents(new_ids, max_level)

    def calculate_periods_dict(self, workbook, actual_date):
        commitment_format = workbook.add_format({
            'border': 1,
            'font_size': 8,
            'num_format': '#,##0',
            'fg_color': '#d9d9d9',
        })
        fact_format = workbook.add_format({
            'border': 1,
            'font_size': 8,
            'num_format': '#,##0',
            'fg_color': '#E2EFDA',
        })
        plan_fact_format = workbook.add_format({
            'border': 1,
            'font_size': 8,
            'num_format': '#,##0',
            'fg_color': '#FFF2CC',
        })
        difference_format = workbook.add_format({
            'border': 1,
            'font_size': 8,
            'num_format': '#,##0',
            'fg_color': '#BDD7EE',
        })
        commitment_head_format = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "font_size": 10,
            'fg_color': '#d9d9d9',
        })
        fact_head_format = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "font_size": 10,
            'fg_color': '#E2EFDA',
        })
        plan_fact_head_format = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "font_size": 10,
            'fg_color': '#FFF2CC',
        })
        difference_head_format = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "font_size": 10,
            'fg_color': '#BDD7EE',
        })
        commitment_office_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            'bold': True,
            'num_format': '#,##0',
            'fg_color': '#d9d9d9',
        })
        fact_office_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            'bold': True,
            'num_format': '#,##0',
            'fg_color': '#E2EFDA',
        })
        plan_fact_office_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            'bold': True,
            'num_format': '#,##0',
            'fg_color': '#FFF2CC',
        })
        difference_office_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            'bold': True,
            'num_format': '#,##0',
            'fg_color': '#BDD7EE',
        })
        commitment_company_format = workbook.add_format({
            'top': 2,
            'bottom': 2,
            'left': 1,
            'right': 1,
            'font_size': 12,
            'bold': True,
            'num_format': '#,##0',
            'fg_color': '#d9d9d9',
        })
        fact_company_format = workbook.add_format({
            'top': 2,
            'bottom': 2,
            'left': 1,
            'right': 1,
            'font_size': 12,
            'bold': True,
            'num_format': '#,##0',
            'fg_color': '#E2EFDA',
        })
        plan_fact_company_format = workbook.add_format({
            'top': 2,
            'bottom': 2,
            'left': 1,
            'right': 1,
            'font_size': 12,
            'bold': True,
            'num_format': '#,##0',
            'fg_color': '#FFF2CC',
        })
        difference_company_format = workbook.add_format({
            'top': 2,
            'bottom': 2,
            'left': 1,
            'right': 1,
            'font_size': 12,
            'bold': True,
            'num_format': '#,##0',
            'fg_color': '#BDD7EE',
        })
        periods_dict = OrderedDict()
        period_limits = []
        col = 0
        month_cols = []
        week_cols = []
        actual_quarter_start = date(actual_date.year, (actual_date.month - 1) // 3 * 3 + 1, 1)
        for month_delta in (-3, -2, -1, 0, 1, 2, 3, 4, 5):  # месяцы от начала текущего квартала
            month_start = actual_quarter_start + relativedelta(months=month_delta)
            month_end = actual_quarter_start + relativedelta(months=month_delta + 1) - timedelta(days=1)

            if month_delta in (0, 1, 2):
                col_format = (10, None)
            else:
                col_format = (10, None, {'hidden': 1, 'level': 1})

            if month_start.month == actual_date.month:
                actual_week = month_start
                actual_week_number = actual_week.isocalendar()[1]
                actual_week_year = actual_week.isocalendar()[0]
                week_start = month_start
                week_end = self.get_dates_from_week(actual_week_number, actual_week_year)[1]
                while week_start.month < actual_date.month + 2:  # недели в течение двух месяцев
                    if week_start.month >= actual_date.month + 1:
                        col_format = (10, None, {'hidden': 1, 'level': 1})
                    periods_dict[(week_start, week_end)] = {
                        'type': 'week',
                        'cols': [
                            {
                                'print': 'commitment',
                                'print_head': 'прогноз',
                                'format': commitment_format,
                                'format_head': commitment_head_format,
                                'format_office': commitment_office_format,
                                'format_company': commitment_company_format,
                                'col_format': col_format,
                            },
                            {
                                'print': 'fact',
                                'print_head': 'факт',
                                'format': fact_format,
                                'format_head': fact_head_format,
                                'format_office': fact_office_format,
                                'format_company': fact_company_format,
                                'col_format': col_format,
                            }
                        ],
                    }
                    col += 2
                    if week_start.isocalendar()[1] > actual_date.isocalendar()[1]:
                        week_cols.append(col - 1)
                    else:
                        week_cols.append(col)
                    actual_week = actual_week + timedelta(weeks=1)
                    actual_week_number = actual_week.isocalendar()[1]
                    actual_week_year = actual_week.isocalendar()[0]
                    week_start, week_end = self.get_dates_from_week(actual_week_number, actual_week_year)
                    if week_start.month != week_end.month:  # учитываем разбиение недель по месяцам
                        week_month_end = week_end.replace(day=1) - timedelta(days=1)
                        week_month_start = week_end.replace(day=1)
                        periods_dict[(week_start, week_month_end)] = {
                            'type': 'week',
                            'cols': [
                                {
                                    'print': 'commitment',
                                    'print_head': 'прогноз',
                                    'format': commitment_format,
                                    'format_head': commitment_head_format,
                                    'format_office': commitment_office_format,
                                    'format_company': commitment_company_format,
                                    'col_format': col_format,
                                },
                                {
                                    'print': 'fact',
                                    'print_head': 'факт',
                                    'format': fact_format,
                                    'format_head': fact_head_format,
                                    'format_office': fact_office_format,
                                    'format_company': fact_company_format,
                                    'col_format': col_format,
                                }
                            ],
                        }
                        col += 2
                        if week_start.isocalendar()[1] > actual_date.isocalendar()[1]:
                            week_cols.append(col - 1)
                        else:
                            week_cols.append(col)
                        formula = week_cols
                        week_cols = []

                        if week_start < actual_date.date():
                            month_format = fact_format
                            month_head_format = fact_head_format
                            month_office_format = fact_office_format
                            month_company_format = fact_company_format
                        else:
                            month_format = commitment_format
                            month_head_format = commitment_head_format
                            month_office_format = commitment_office_format
                            month_company_format = commitment_company_format

                        periods_dict['sum_month_' + str(week_start.month)] = {
                            'type': 'sum_month',
                            'date': week_start,
                            'formula': formula,
                            'cols': [
                                {
                                    'print': 'commitment',
                                    'print_head': 'прогноз',
                                    'format': month_format,
                                    'format_head': month_head_format,
                                    'format_office': month_office_format,
                                    'format_company': month_company_format,
                                    'col_format': col_format,
                                },
                            ],
                        }
                        col += 1
                        month_cols.append(col)
                        if week_start.month % 3 == 0:
                            formula = month_cols
                            month_cols = []

                            if month_end < actual_date.date():
                                quater_format = fact_format
                                quater_head_format = fact_head_format
                                quater_office_format = fact_office_format
                                quater_company_format = fact_company_format
                            else:
                                quater_format = commitment_format
                                quater_head_format = commitment_head_format
                                quater_office_format = commitment_office_format
                                quater_company_format = commitment_company_format

                            periods_dict['sum_quarter_' + str((month_start.month - 1) // 3 + 1)] = {
                                'type': 'sum_quarter',
                                'date': month_end,
                                'formula': formula,
                                'cols': [
                                    {
                                        'print': 'commitment',
                                        'print_head': 'прогноз',
                                        'format': quater_format,
                                        'format_head': quater_head_format,
                                        'format_office': quater_office_format,
                                        'format_company': quater_company_format,
                                        'col_format': col_format,
                                    },
                                ],
                            }
                            col += 1
                        week_start = week_month_start
            elif month_start.month == actual_date.month + 1:  # пропускаем следующий за текущим месяц
                pass
            else:
                if month_end < actual_date.date():  # в прошлом печатаем прогноз и факт, в будущем - только прогноз
                    periods_dict[(month_start, month_end)] = {
                        'type': 'month',
                        'cols': [
                            {
                                'print': 'commitment',
                                'print_head': 'план-прогноз на начало месяца',
                                'format': plan_fact_format,
                                'format_head': plan_fact_head_format,
                                'format_office': plan_fact_office_format,
                                'format_company': plan_fact_company_format,
                                'col_format': col_format,
                            },
                            {
                                'print': 'fact',
                                'print_head': 'факт',
                                'format': fact_format,
                                'format_head': fact_head_format,
                                'format_office': fact_office_format,
                                'format_company': fact_company_format,
                                'col_format': col_format,
                            },
                            {
                                'print': 'difference',
                                'print_head': 'разница',
                                'format': difference_format,
                                'format_head': difference_head_format,
                                'format_office': difference_office_format,
                                'format_company': difference_company_format,
                                'col_format': col_format,
                            }
                        ]
                    }
                    col += 3
                    month_cols.append(col - 1)
                else:
                    periods_dict[(month_start, month_end)] = {
                        'type': 'month',
                        'cols': [
                            {
                                'print': 'commitment',
                                'print_head': 'прогноз на текущую дату',
                                'format': commitment_format,
                                'format_head': commitment_head_format,
                                'format_office': commitment_office_format,
                                'format_company': commitment_company_format,
                                'col_format': col_format,
                            }
                        ]
                    }
                    col += 1
                    month_cols.append(col)
                if month_start.month % 3 == 0:  # добавляем суммы и формулы по кварталам
                    formula = month_cols
                    month_cols = []

                    if month_start < actual_date.date():
                        quater_format = fact_format
                        quater_head_format = fact_head_format
                        quater_office_format = fact_office_format
                        quater_company_format = fact_company_format
                    else:
                        quater_format = commitment_format
                        quater_head_format = commitment_head_format
                        quater_office_format = commitment_office_format
                        quater_company_format = commitment_company_format

                    periods_dict['sum_quarter_' + str((month_start.month - 1) // 3 + 1)] = {
                        'type': 'sum_quarter',
                        'date': month_end,
                        'formula': formula,
                        'cols': [
                            {
                                'print': 'commitment',
                                'print_head': 'прогноз',
                                'format': quater_format,
                                'format_head': quater_head_format,
                                'format_office': quater_office_format,
                                'format_company': quater_company_format,
                                'col_format': col_format,
                            },
                        ],
                    }
                    col += 1
                if month_delta == -3:  # начало и конец всего переода
                    period_limits.append(month_start)
                elif month_delta == 5:
                    period_limits.append(month_end)

        return periods_dict, period_limits

    def calculate_budget_ids(self, budget, periods_dict):
        budget_ids = set()
        actual_budget_date = budget.date_actual or date.today()
        actual_budget_week = actual_budget_date.isocalendar()[1]
        actual_budget_month = actual_budget_date.month
        for period, options in periods_dict.items():
            if 'sum' not in period:
                if options['type'] == 'month' and period[1].month <= actual_budget_month:
                    budget_id = self.env['project_budget.commercial_budget'].search([
                        ('date_actual', '<=', period[0]),
                        ('date_actual', '>=', period[0] - relativedelta(months=1)),
                    ], limit=1, order='date_actual desc').id
                    options['budget_id'] = budget_id
                    if budget_id:
                        budget_ids.add(budget_id)
                elif options['type'] == 'week' and period[1].isocalendar()[1] <= actual_budget_week:
                    previous_week_number = (period[0] - timedelta(weeks=1)).isocalendar()[1]
                    previous_week_year= (period[0] - timedelta(weeks=1)).isocalendar()[0]
                    previous_week_start, previous_week_end = self.get_dates_from_week(previous_week_number, previous_week_year)
                    budget_id = self.env['project_budget.commercial_budget'].search([
                        ('date_actual', '<=', previous_week_end),
                        ('date_actual', '>=', previous_week_start),
                    ], limit=1, order='date_actual desc').id
                    options['budget_id'] = budget_id
                    if budget_id:
                        budget_ids.add(budget_id)
                else:
                    options['budget_id'] = budget.id
                    budget_ids.add(budget.id)
        return (periods_dict, list(budget_ids))

    def get_data_from_projects(self, projects, periods_dict, budget):
        project_project_ids = set(projects.mapped('project_id'))
        data = {}
        for project_project_id in sorted(project_project_ids):
            pds_is_present = False
            project_data = {}
            for period, options in periods_dict.items():
                if 'sum' not in period:
                    for project in projects.filtered(lambda pr: pr.project_id == project_project_id):
                        project_data.setdefault(period, {'commitment': 0, 'fact': 0})

                        if project.step_status == 'project':
                            pds_fact_list = project.fact_cash_flow_ids
                            pds_plan_list = project.planned_cash_flow_ids
                            project_id = (project.step_project_number or '') + ' | ' + (project.project_id or '')
                        elif project.step_status == 'step':
                            pds_fact_list = project.fact_step_cash_flow_ids
                            pds_plan_list = project.planned_step_cash_flow_ids
                            project_id = (project.step_project_number or '') + ' | ' + project.step_project_parent_id.project_id + " | " + project.project_id

                        for pds_fact in pds_fact_list:
                            if period[0] <= pds_fact.date_cash <= period[1] and project.commercial_budget_id.id == budget.id:
                                pds_is_present = True
                                project_data[period]['fact'] += pds_fact.sum_cash

                        for pds_plan in pds_plan_list:
                            if (period[0] <= pds_plan.date_cash <= period[1]
                                    and project.commercial_budget_id.id == options['budget_id']
                                    and (pds_plan.forecast == 'commitment'
                                         or (pds_plan.forecast == 'from_project'
                                             and project.stage_id.code in ('100(done)', '100', '75')))):
                                pds_is_present = True
                                project_data[period]['commitment'] += pds_plan.distribution_sum_with_vat_ostatok

            if pds_is_present:
                current_project = projects.filtered(lambda pr: pr.project_id == project_project_id and pr.commercial_budget_id.id == budget.id)
                data.setdefault(current_project.company_id.name, {}).setdefault(current_project.project_office_id.name, {}).setdefault(
                    current_project.project_id, {})

                currency_rate = self.get_currency_rate_by_project(current_project)
                if current_project.step_status == 'project':
                    project_step_id = (current_project.step_project_number or '') + ' | ' + (current_project.project_id or '')
                elif current_project.step_status == 'step':
                    project_step_id = (current_project.step_project_number or '') + ' | ' + current_project.step_project_parent_id.project_id + " | " + current_project.project_id

                data[current_project.company_id.name][current_project.project_office_id.name][current_project.project_id]['info'] = {
                    'key_account_manager_id': current_project.key_account_manager_id.name,
                    'partner_id': current_project.partner_id.name,
                    'essence_project': current_project.essence_project,
                    'project_id': project_step_id,
                    'probability': self.get_estimated_probability_name_forecast(current_project.stage_id.code),
                    'total_amount_of_revenue_with_vat': current_project.total_amount_of_revenue_with_vat * currency_rate,
                    'margin_income': current_project.margin_income * currency_rate,
                    'profitability': current_project.profitability,
                    'dogovor_number': current_project.dogovor_number or '',
                    'vat_attribute_id': current_project.vat_attribute_id.name,
                }

                data[current_project.company_id.name][current_project.project_office_id.name][current_project.project_id]['periods'] = project_data
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

    def get_dates_from_week(self, week_number, year):

        first_day_of_year = date(year, 1, 1)

        for day in range(1, 8):
            day_of_year = date(year, 1, day)
            if day_of_year.weekday() == 5:  # четверг
                first_day_of_year = day_of_year
        first_week_begin = first_day_of_year - timedelta(days=first_day_of_year.weekday())
        first_week_end = first_week_begin + timedelta(days=6)
        delta = timedelta(days=(week_number - 1) * 7)
        return first_week_begin + delta, first_week_end + delta

    def print_head(self, workbook, sheet, row, column, periods_dict, actual_budget_date):
        sheet.set_row(row, 16)
        sheet.set_row(row + 1, 65)

        head_format_month = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "fg_color": '#D096BF',
            "font_size": 10,
        })

        for period, options in periods_dict.items():
            if options['type'] == 'month':
                for col in options['cols']:
                    string = self.month_rus_name[period[0].month - 1] + '\n' + col['print_head']
                    sheet.set_column(column, column, *(col['col_format']))
                    sheet.merge_range(row + 1, column, row + 2, column, string, col['format_head'])
                    column += 1
            elif options['type'] == 'week':
                for col in options['cols']:
                    string = self.month_rus_name[period[0].month - 1] + ' ' + period[0].strftime("%d") + '-' + period[1].strftime("%d") + '\n' + col['print_head']
                    sheet.set_column(column, column, *(col['col_format']))
                    sheet.merge_range(row + 1, column, row + 2, column, string, col['format_head'])
                    column += 1
            elif options['type'] == 'sum_month':
                string = self.month_rus_name[options['date'].month - 1]  + '\n прогноз на текущую дату'
                sheet.set_column(column, column, *(options['cols'][0]['col_format']))
                sheet.merge_range(row + 1, column, row + 2, column, string, options['cols'][0]['format_head'])
                column += 1
            elif options['type'] == 'sum_quarter':
                if options['date'] < actual_budget_date.date():
                    string = ('ИТОГО \nПДС Q' + str((options['date'].month - 1) // 3 + 1) + '/' +
                              options['date'].strftime("%Y") + '\nФакт')
                else:
                    string = ('ИТОГО \nПДС Q' + str((options['date'].month - 1) // 3 + 1) + '/' +
                              options['date'].strftime("%Y") + '\nПрогноз')
                sheet.set_column(column, column, *(options['cols'][0]['col_format']))
                sheet.merge_range(row + 1, column, row + 2, column, string, options['cols'][0]['format_head'])
                column += 1
            else:
                string = period
                sheet.set_column(column, column, *(options['cols'][0]['col_format']))
                sheet.merge_range(row + 1, column, row + 2, column, string,  options['cols'][0]['format_head'])
                column += 1
        return column

    def print_row_values(self, workbook, sheet, row, column, periods_data, periods_dict):

        row_format_number = workbook.add_format({
            'border': 1,
            'font_size': 8,
            'num_format': '#,##0',
        })

        for period in periods_dict:
            if 'sum' not in period:
                for col in periods_dict[period]['cols']:
                    if col['print'] != 'difference':
                        sheet.write_number(row, column, periods_data[period][col['print']], col['format'])
                    else:
                        formula = '={1}{0}-{2}{0}'.format(
                            row + 1,
                            xl_col_to_name(column - 1),
                            xl_col_to_name(column - 2)
                        )
                        sheet.write_formula(row, column, formula, col['format'])
                    column += 1
            else:
                for col in periods_dict[period]['cols']:
                    if 'sum_quarter' in period:
                        formula = 'sum({1}{0},{2}{0},{3}{0})'.format(
                                row + 1,
                                xl_col_to_name(11 + periods_dict[period]['formula'][0]),
                                xl_col_to_name(11 + periods_dict[period]['formula'][1]),
                                xl_col_to_name(11 + periods_dict[period]['formula'][2]),
                            )
                        sheet.write_formula(row, column, formula, col['format'])
                        column += 1
                    elif 'sum_month' in period:
                        if len(periods_dict[period]['formula']) == 4:  # учитываем разное количество недель в месяце
                            formula = 'sum({1}{0},{2}{0},{3}{0},{4}{0})'.format(
                                row + 1,
                                xl_col_to_name(11 + periods_dict[period]['formula'][0]),
                                xl_col_to_name(11 + periods_dict[period]['formula'][1]),
                                xl_col_to_name(11 + periods_dict[period]['formula'][2]),
                                xl_col_to_name(11 + periods_dict[period]['formula'][3]),
                            )
                            sheet.write_formula(row, column, formula, col['format'])
                        elif len(periods_dict[period]['formula']) == 5:
                            formula = 'sum({1}{0},{2}{0},{3}{0},{4}{0},{5}{0})'.format(
                                row + 1,
                                xl_col_to_name(11 + periods_dict[period]['formula'][0]),
                                xl_col_to_name(11 + periods_dict[period]['formula'][1]),
                                xl_col_to_name(11 + periods_dict[period]['formula'][2]),
                                xl_col_to_name(11 + periods_dict[period]['formula'][3]),
                                xl_col_to_name(11 + periods_dict[period]['formula'][4]),
                            )
                            sheet.write_formula(row, column, formula, col['format'])
                        elif len(periods_dict[period]['formula']) == 6:
                            formula = 'sum({1}{0},{2}{0},{3}{0},{4}{0},{5}{0},{6}{0})'.format(
                                row + 1,
                                xl_col_to_name(11 + periods_dict[period]['formula'][0]),
                                xl_col_to_name(11 + periods_dict[period]['formula'][1]),
                                xl_col_to_name(11 + periods_dict[period]['formula'][2]),
                                xl_col_to_name(11 + periods_dict[period]['formula'][3]),
                                xl_col_to_name(11 + periods_dict[period]['formula'][4]),
                                xl_col_to_name(11 + periods_dict[period]['formula'][5]),
                            )
                            sheet.write_formula(row, column, formula, col['format'])
                        column += 1
                    else:
                        sheet.write_string(row, column, period, row_format_number)
                        column += 1

    def print_row(self, sheet, workbook, companies, project_offices, actual_office_ids, row, data, periods_dict, level, max_level, dict_formula):
        row_format = workbook.add_format({
            'border': 1,
            'font_size': 8
        })
        office_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            'bold': True,
        })
        company_format = workbook.add_format({
            'top': 2,
            'bottom': 2,
            'left': 1,
            'right': 1,
            'font_size': 12,
            'bold': True,
        })
        row_format_number = workbook.add_format({
            'border': 1,
            'font_size': 9,
            'num_format': '#,##0',
        })
        office_format_number = workbook.add_format({
            'border': 1,
            'font_size': 10,
            'bold': True,
            'num_format': '#,##0',
        })
        company_format_number = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'bold': True,
            'num_format': '#,##0',
        })
        for company in companies:
            if company.id not in dict_formula['company_ids']:
                row += 1
                dict_formula['company_ids'][company.id] = row
                sheet.merge_range(row, 0, row, 11, company.name, company_format)
            office_lines = list()

            for office in project_offices.filtered(lambda r: r.company_id == company):
                if office.id in actual_office_ids:
                    if office.id not in dict_formula['company_ids']:
                        row += 1
                        dict_formula['office_ids'][office.id] = row
                        sheet.set_row(row, False, False, {'hidden': 1, 'level': level})
                        sheet.merge_range(row, 0, row, 11, office.name, office_format)
                    project_lines = list()
                    office_lines.append(row)
                    if office.name in data[company.name]:
                        for project, content in data[company.name][office.name].items():
                            # печатаем строки проектов
                            row += 1
                            sheet.set_row(row, False, False, {'hidden': 1, 'level': max_level + 1})
                            cur_row_format = row_format
                            cur_row_format_number = row_format_number
                            column = 0
                            sheet.write_string(row, column, office.name, cur_row_format)
                            column += 1
                            sheet.write_string(row, column, content['info']['key_account_manager_id'], cur_row_format)
                            column += 1
                            sheet.write_string(row, column, content['info']['partner_id'], cur_row_format)
                            column += 1
                            sheet.write_string(row, column, content['info']['essence_project'], cur_row_format)
                            column += 1
                            sheet.write_string(row, column, content['info']['project_id'], cur_row_format)
                            column += 1
                            sheet.write_string(row, column, content['info']['probability'], cur_row_format)
                            column += 1
                            sheet.write_number(row, column, content['info']['total_amount_of_revenue_with_vat'], cur_row_format_number)
                            column += 1
                            sheet.write_number(row, column, content['info']['margin_income'], cur_row_format_number)
                            column += 1
                            sheet.write_number(row, column, content['info']['profitability'], cur_row_format_number)
                            column += 1
                            sheet.write_string(row, column, content['info']['dogovor_number'], cur_row_format)
                            column += 1
                            sheet.write_string(row, column, content['info']['vat_attribute_id'], cur_row_format)
                            column += 1
                            sheet.write_string(row, column, '', cur_row_format)
                            column += 1
                            self.print_row_values(workbook, sheet, row, column, content['periods'], periods_dict)
                            project_lines.append(row)

                    child_offices = self.env['project_budget.project_office'].search(
                        [('parent_id', '=', office.id)], order='report_sort')

                    if child_offices:
                        row, formula_itogo = self.print_row(sheet, workbook, company, child_offices,
                                                            actual_office_ids, row, data, periods_dict,
                                                            level + 1, max_level, dict_formula)
                        for child_office in child_offices:
                            if child_office.id in actual_office_ids:
                                project_lines.append(dict_formula['office_ids'][child_office.id])

                    self.print_vertical_sum_formula(sheet, dict_formula['office_ids'][office.id], project_lines, periods_dict, 12, 'format_office')

                if level == 1:
                    self.print_vertical_sum_formula(sheet, dict_formula['company_ids'][company.id], office_lines, periods_dict, 12, 'format_company')

        return row, dict_formula

    def print_vertical_sum_formula(self, sheet, row, sum_lines, periods_dict, start_col, format):
        formula = '=sum('
        for n in range(len(sum_lines)):
            formula += '{0}{' + str(n + 1) + '},'
        formula += ')'
        col_counter = start_col
        for period, options in periods_dict.items():
            for col in options['cols']:
                result_formula = formula.format(xl_col_to_name(col_counter), *[line + 1 for line in sum_lines])
                sheet.write_formula(row, col_counter, result_formula, col[format])
                col_counter += 1

    def printworksheet(self, workbook, budget, namesheet, project_office_ids, max_level, multipliers, dict_formula):
        report_name = budget.name
        sheet = workbook.add_worksheet(namesheet)
        sheet.set_zoom(85)

        bold = workbook.add_format({'bold': True})
        money_format = workbook.add_format({'num_format': '#,##0'})
        head_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_size': 11,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#FFFF00'
        })
        head_format_grey = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "bold": False,
            "fg_color": '#d9d9d9',
            "font_size": 10,
        })
        row_format_date_month = workbook.add_format({
            'border': 1,
            'font_size': 9,
        })

        row_format_manager = workbook.add_format({
            'border': 1,
            'font_size': 9,
            "bold": True,
            "fg_color": '#D9D9D9',
        })
        row_format_manager.set_num_format('#,##0')

        row_format_office = workbook.add_format({
            'border': 1,
            'font_size': 9,
            "bold": True,
            "fg_color": '#8497B0',
        })
        row_format_office.set_num_format('#,##0')

        row_format_date_month.set_num_format('mmm yyyy')

        row_format = workbook.add_format({
            'border': 1,
            'font_size': 9
        })

        row_format_canceled_project = workbook.add_format({
            'border': 1,
            'font_size': 9
        })
        row_format_canceled_project.set_font_color('red')

        row_format_number = workbook.add_format({
            'border': 1,
            'font_size': 9,
        })
        row_format_number.set_num_format('#,##0')

        row_format_number_canceled_project = workbook.add_format({
            'border': 1,
            'font_size': 9,
        })
        row_format_number_canceled_project.set_num_format('#,##0')
        row_format_number_canceled_project.set_font_color('red')

        row_format_number_itogo = workbook.add_format({
            'top': 2,
            'bottom': 2,
            'left': 1,
            'right': 1,
            'font_size': 12,
            "bold": True,
            "num_format": '#,##0',
        })
        row_format_number_itogo_percent = workbook.add_format({
            'top': 2,
            'bottom': 2,
            'left': 1,
            'right': 1,
            'font_size': 12,
            "bold": True,
            "fg_color": '#BFBFBF',
            'num_format': '0.00%',
        })
        head_format_month_itogo = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "bold": True,
            "fg_color": '#D9E1F2',
            "font_size": 12,
            "num_format": '#,##0',
        })

        actual_budget_date = budget.date_actual or datetime.now()

        date_format = workbook.add_format({'num_format': 'd mmmm yyyy'})
        row = 0
        sheet.write_string(row, 0, budget.name + ' ' + str(actual_budget_date.date()), bold)
        column = 0
        sheet.merge_range(row + 1, 0, row + 2, 0, "БЮ/Проектный офис", head_format_grey)
        sheet.set_column(column, column, 16)
        column += 1
        sheet.merge_range(row + 1, column, row + 2, column, "КАМ", head_format_grey)
        sheet.set_column(column, column, 16)
        column += 1
        sheet.merge_range(row + 1, column, row + 2, column, "Заказчик", head_format_grey)
        sheet.set_column(column, column, 25)
        column += 1
        sheet.merge_range(row + 1, column, row + 2, column, "Наименование Проекта", head_format_grey)
        sheet.set_column(column, column, 25, False, {'hidden': 1, 'level': 2})
        column += 1
        sheet.merge_range(row + 1, column, row + 2, column, "Номер этапа проекта", head_format_grey)
        sheet.set_column(column, column, 16, False, {'hidden': 1, 'level': 2})
        column += 1
        sheet.merge_range(row + 1, column, row + 2, column, "Стадия продажи", head_format_grey)
        sheet.set_column(column, column, 10, False, {'hidden': 1, 'level': 2})
        column += 1
        sheet.merge_range(row + 1, column, row + 2, column, "Сумма проекта, руб.", head_format_grey)
        sheet.set_column(column, column, 14, False, {'hidden': 1, 'level': 2})
        column += 1
        sheet.merge_range(row + 1, column, row + 2, column, "Валовая прибыль экспертно, руб.", head_format_grey)
        sheet.set_column(column, column, 14, False, {'hidden': 1, 'level': 2})
        column += 1
        sheet.merge_range(row + 1, column, row + 2, column, "Прибыльность экспертно, %", head_format_grey)
        sheet.set_column(column, column, 9, False, {'hidden': 1, 'level': 2})
        column += 1
        sheet.merge_range(row + 1, column, row + 2, column, "Номер договора", head_format_grey)
        sheet.set_column(column, column, 11.88, False, {'hidden': 1, 'level': 2})
        column += 1
        sheet.merge_range(row + 1, column, row + 2, column, "НДС", head_format_grey)
        sheet.set_column(column, column, 4, False, {'hidden': 1, 'level': 2})
        column += 1
        sheet.merge_range(row + 1, column, row + 2, column, "", head_format_grey)
        sheet.set_column(column, column, 2)

        sheet.freeze_panes(3, 12)
        column += 1

        periods_dict, period_limits = self.calculate_periods_dict(workbook, actual_budget_date)
        periods_dict, budget_ids = self.calculate_budget_ids(budget, periods_dict)

        projects = self.env['project_budget.projects'].search([
            '&','&',
            ('commercial_budget_id', 'in', budget_ids),
            '|', '&', ('step_status', '=', 'step'),
            ('step_project_parent_id.project_have_steps', '=', True),
            '&', ('step_status', '=', 'project'),
            ('project_have_steps', '=', False),
            '|','|','|',
            ('id', 'in', [fact.projects_id.id for fact in self.env['project_budget.fact_cash_flow'].search([]) if fact.date_cash >= period_limits[0] and fact.date_cash <= period_limits[1]]),
            ('id', 'in', [plan.projects_id.id for plan in self.env['project_budget.planned_cash_flow'].search([]) if plan.date_cash >= period_limits[0] and plan.date_cash <= period_limits[1]]),
            ('id', 'in', [fact.step_project_child_id.id for fact in self.env['project_budget.fact_cash_flow'].search([]) if fact.date_cash >= period_limits[0] and fact.date_cash <= period_limits[1]]),
            ('id', 'in', [plan.step_project_child_id.id for plan in self.env['project_budget.planned_cash_flow'].search([]) if plan.date_cash >= period_limits[0] and plan.date_cash <= period_limits[1]]),
        ], order='project_id')

        print()

        data = self.get_data_from_projects(projects, periods_dict, budget)

        actual_office_ids_set = set()
        for company in data:
            for office_name in data[company]:
                office = self.env['project_budget.project_office'].search([('name', '=', office_name)])
                actual_office_ids_set.add(office.id)
                while office.parent_id:
                    office = office.parent_id
                    actual_office_ids_set.add(office.id)

        actual_office_ids = list(actual_office_ids_set)

        column = self.print_head(workbook, sheet, row, column, periods_dict, actual_budget_date)
        row += 2

        companies = self.env['res.company'].search([('name', 'in', list(data.keys()))], order='name')

        if project_office_ids:
            project_offices = self.env['project_budget.project_office'].search([
                ('id','in',project_office_ids), ('parent_id', 'not in', project_office_ids)], order='report_sort')  # для сортировки так делаем + не берем дочерние оффисы, если выбраны их материнские
        else:
            project_offices = self.env['project_budget.project_office'].search([
                ('parent_id', '=', False)], order='report_sort')  # для сортировки так делаем + берем сначала только верхние элементы

        row, dict_formula = self.print_row(sheet, workbook, companies, project_offices, actual_office_ids, row, data, periods_dict, 1, max_level, dict_formula)

        if set(self.env['project_budget.project_office'].search([]).ids) == set(project_office_ids):
            row += 1

            sheet.merge_range(row, 0, row, 11, 'ИТОГО по отчету', row_format_number_itogo)

            self.print_vertical_sum_formula(sheet, row, dict_formula['company_ids'].values(), periods_dict, 12, 'format_company')

    def generate_xlsx_report(self, workbook, data, budgets):

        dict_formula = {'company_ids': {}, 'office_ids': {}, 'office_ids_not_empty': {}}

        project_office_ids = data['project_office_ids']

        ids = [office.id for office in self.env['project_budget.project_office'].search([('parent_id', '=', False), ('id', 'in', project_office_ids)])]
        max_level = self.offices_with_parents(ids, 0)

        if set(self.env['project_budget.project_office'].search([]).ids) != set(project_office_ids):
            max_level -= 1

        multipliers = {'50': data['koeff_reserve'], '30': data['koeff_potential']}

        commercial_budget_id = data['commercial_budget_id']
        print('commercial_budget_id', commercial_budget_id)
        budget = self.env['project_budget.commercial_budget'].search([('id', '=', commercial_budget_id)])
        self.printworksheet(workbook, budget, 'ПДС', project_office_ids, max_level, multipliers, dict_formula)
