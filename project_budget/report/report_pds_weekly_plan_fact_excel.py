import logging

from odoo import models
from odoo.tools import date_utils
from datetime import date, datetime, timedelta
from dateutil.relativedelta import *
from xlsxwriter.utility import xl_col_to_name
from collections import OrderedDict

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

    def get_currency_rate_by_project(self, project):
        project_currency_rates = self.env['project_budget.project_currency_rates']
        return project_currency_rates._get_currency_rate_for_project_in_company_currency(project)

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
        commitment_center_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            'bold': True,
            'num_format': '#,##0',
            'fg_color': '#d9d9d9',
        })
        fact_center_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            'bold': True,
            'num_format': '#,##0',
            'fg_color': '#E2EFDA',
        })
        plan_fact_center_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            'bold': True,
            'num_format': '#,##0',
            'fg_color': '#FFF2CC',
        })
        difference_center_format = workbook.add_format({
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
        fact_week_cols = []
        actual_quarter_start = date(actual_date.year, (actual_date.month - 1) // 3 * 3 + 1, 1)
        for month_delta in (-3, -2, -1, 0, 1, 2, 3, 4, 5):  # месяцы от начала текущего квартала
            month_start = actual_quarter_start + relativedelta(months=month_delta)
            month_end = actual_quarter_start + relativedelta(months=month_delta + 1) - timedelta(days=1)

            if month_delta in (0, 1, 2):
                col_format = (10, None)
            else:
                col_format = (10, None, {'hidden': 1, 'level': 1})

            if date_utils.start_of(month_start, 'month') == date_utils.start_of(actual_date, 'month').date():

                periods_dict[(month_start, month_end)] = {
                    'type': 'month',
                    'cols': [
                        {
                            'print': 'commitment',
                            'print_head': 'план-прогноз на начало месяца',
                            'format': plan_fact_format,
                            'format_head': plan_fact_head_format,
                            'format_center': plan_fact_center_format,
                            'format_company': plan_fact_company_format,
                            'col_format': col_format,
                        },
                    ]
                }
                col += 1

                actual_week = month_start
                actual_week_number = actual_week.isocalendar()[1]
                actual_week_year = actual_week.isocalendar()[0]
                week_start = month_start
                week_end = self.get_dates_from_week(actual_week_number, actual_week_year)[1]
                while week_start < date_utils.start_of(actual_date + relativedelta(months=2),
                                                       'month').date():  # недели в течение двух месяцев
                    if date_utils.start_of(week_start, 'month') >= date_utils.start_of(
                            actual_date + relativedelta(months=1), 'month').date():
                        week_col_format = (10, None, {'hidden': 1, 'level': 1})
                    else:
                        week_col_format = (10, None)
                    periods_dict[(week_start, week_end)] = {
                        'type': 'week',
                        'cols': [
                            {
                                'print': 'commitment',
                                'print_head': 'прогноз',
                                'format': commitment_format,
                                'format_head': commitment_head_format,
                                'format_center': commitment_center_format,
                                'format_company': commitment_company_format,
                                'col_format': week_col_format,
                            },
                            {
                                'print': 'fact',
                                'print_head': 'факт',
                                'format': fact_format,
                                'format_head': fact_head_format,
                                'format_center': fact_center_format,
                                'format_company': fact_company_format,
                                'col_format': week_col_format,
                            }
                        ],
                    }
                    col += 2
                    if date_utils.start_of(week_start, 'week') > date_utils.start_of(actual_date, 'week').date():
                        week_cols.append(col - 1)
                    else:
                        week_cols.append(col)
                    fact_week_cols.append(col)
                    next_week = actual_week + timedelta(weeks=1)
                    next_week_number = next_week.isocalendar()[1]
                    next_week_year = next_week.isocalendar()[0]
                    next_week_start, next_week_end = self.get_dates_from_week(next_week_number, next_week_year)
                    if next_week_start.month != next_week_end.month:  # учитываем разбиение недель по месяцам
                        week_month_end = next_week_end.replace(day=1) - timedelta(days=1)
                        week_month_start = next_week_end.replace(day=1)
                        periods_dict[(next_week_start, week_month_end)] = {
                            'type': 'week',
                            'cols': [
                                {
                                    'print': 'commitment',
                                    'print_head': 'прогноз',
                                    'format': commitment_format,
                                    'format_head': commitment_head_format,
                                    'format_center': commitment_center_format,
                                    'format_company': commitment_company_format,
                                    'col_format': week_col_format,
                                },
                                {
                                    'print': 'fact',
                                    'print_head': 'факт',
                                    'format': fact_format,
                                    'format_head': fact_head_format,
                                    'format_center': fact_center_format,
                                    'format_company': fact_company_format,
                                    'col_format': week_col_format,
                                }
                            ],
                        }
                        col += 2
                        if date_utils.start_of(week_start, 'week') >= date_utils.start_of(actual_date, 'week').date():
                            week_cols.append(col - 1)
                        else:
                            week_cols.append(col)
                        fact_week_cols.append(col)
                        week_start = week_month_start
                    else:
                        week_start = next_week_start
                    if week_end.month != week_start.month:
                        formula = week_cols
                        fact_formula = fact_week_cols
                        week_cols = []
                        fact_week_cols = []

                        if week_end < actual_date.date():
                            month_format = fact_format
                            month_head_format = fact_head_format
                            month_center_format = fact_center_format
                            month_company_format = fact_company_format
                        else:
                            month_format = commitment_format
                            month_head_format = commitment_head_format
                            month_center_format = commitment_center_format
                            month_company_format = commitment_company_format

                        if actual_date.month == week_end.month:
                            periods_dict['sum_month_' + str(week_end.month)] = {
                                'type': 'sum_month',
                                'date': week_end,
                                'formula': formula,
                                'cols': [
                                    {
                                        'print': 'fact',
                                        'print_head': 'Факт на текущую дату',
                                        'format': fact_format,
                                        'format_head': fact_head_format,
                                        'format_center': fact_center_format,
                                        'format_company': fact_company_format,
                                        'col_format': col_format,
                                        'formula': fact_formula,
                                    },
                                    {
                                        'print': 'commitment',
                                        'print_head': 'прогноз на текущую дату',
                                        'format': month_format,
                                        'format_head': month_head_format,
                                        'format_center': month_center_format,
                                        'format_company': month_company_format,
                                        'col_format': col_format,
                                        'formula': formula,
                                    },
                                ],
                            }
                            col += 2
                        else:
                            periods_dict['sum_month_' + str(week_end.month)] = {
                                'type': 'sum_month',
                                'date': week_end,
                                'formula': formula,
                                'cols': [
                                    {
                                        'print': 'commitment',
                                        'print_head': 'прогноз на текущую дату',
                                        'format': month_format,
                                        'format_head': month_head_format,
                                        'format_center': month_center_format,
                                        'format_company': month_company_format,
                                        'col_format': col_format,
                                        'formula': formula,
                                    },
                                ],
                            }
                            col += 1
                        month_cols.append(col)
                        if week_end.month % 3 == 0:
                            formula = month_cols
                            month_cols = []

                            if month_end < actual_date.date():
                                quater_format = fact_format
                                quater_head_format = fact_head_format
                                quater_center_format = fact_center_format
                                quater_company_format = fact_company_format
                            else:
                                quater_format = commitment_format
                                quater_head_format = commitment_head_format
                                quater_center_format = commitment_center_format
                                quater_company_format = commitment_company_format

                            periods_dict['sum_quarter_' + str((month_start.month - 1) // 3 + 1)] = {
                                'type': 'sum_quarter',
                                'date': month_end,
                                'cols': [
                                    {
                                        'print': 'commitment',
                                        'print_head': 'прогноз',
                                        'format': quater_format,
                                        'format_head': quater_head_format,
                                        'format_center': quater_center_format,
                                        'format_company': quater_company_format,
                                        'col_format': col_format,
                                        'formula': formula,
                                    },
                                ],
                            }
                            col += 1
                    week_end = next_week_end
                    actual_week = next_week
            elif date_utils.start_of(month_start, 'month') == date_utils.start_of(actual_date + relativedelta(months=1),
                                                                                  'month').date():  # пропускаем следующий за текущим месяц
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
                                'format_center': plan_fact_center_format,
                                'format_company': plan_fact_company_format,
                                'col_format': col_format,
                            },
                            {
                                'print': 'fact',
                                'print_head': 'факт',
                                'format': fact_format,
                                'format_head': fact_head_format,
                                'format_center': fact_center_format,
                                'format_company': fact_company_format,
                                'col_format': col_format,
                            },
                            {
                                'print': 'difference',
                                'print_head': 'разница',
                                'format': difference_format,
                                'format_head': difference_head_format,
                                'format_center': difference_center_format,
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
                                'format_center': commitment_center_format,
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
                        quater_center_format = fact_center_format
                        quater_company_format = fact_company_format
                    else:
                        quater_format = commitment_format
                        quater_head_format = commitment_head_format
                        quater_center_format = commitment_center_format
                        quater_company_format = commitment_company_format

                    periods_dict['sum_quarter_' + str((month_start.month - 1) // 3 + 1)] = {
                        'type': 'sum_quarter',
                        'date': month_end,
                        'cols': [
                            {
                                'print': 'commitment',
                                'print_head': 'прогноз',
                                'format': quater_format,
                                'format_head': quater_head_format,
                                'format_center': quater_center_format,
                                'format_company': quater_company_format,
                                'col_format': col_format,
                                'formula': formula,
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
        actual_budget_date = date.today() if not budget.date_actual else budget.date_actual.date()
        for period, options in periods_dict.items():
            if 'sum' not in period:
                if options['type'] == 'month' and date_utils.start_of(period[1], 'month') <= date_utils.start_of(
                        actual_budget_date, 'month'):
                    budget_id = self.env['project_budget.commercial_budget'].search([
                        ('date_actual', '<=', period[0]),
                        ('date_actual', '>=', period[0] - relativedelta(months=1)),
                    ], limit=1, order='date_actual desc').id
                    options['budget_id'] = budget_id
                    if budget_id:
                        budget_ids.add(budget_id)
                elif options['type'] == 'week' and date_utils.start_of(period[1], 'week') <= date_utils.start_of(
                        actual_budget_date, 'week'):
                    previous_week_number = (period[0] - timedelta(weeks=1)).isocalendar()[1]
                    previous_week_year = (period[0] - timedelta(weeks=1)).isocalendar()[0]
                    previous_week_start, previous_week_end = self.get_dates_from_week(previous_week_number,
                                                                                      previous_week_year)
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

    def get_data_from_projects(self, projects, periods_dict, budget, budget_ids):
        project_project_ids = set(projects.mapped('project_id'))
        data = {}
        for project_project_id in sorted(project_project_ids):
            pds_is_present = False
            project_data = {}
            for project in projects.filtered(lambda pr: pr.project_id == project_project_id):
                if project.step_status == 'project':
                    pds_fact_list = project.fact_cash_flow_ids
                    pds_plan_list = project.planned_cash_flow_ids
                elif project.step_status == 'step':
                    pds_fact_list = project.fact_step_cash_flow_ids
                    pds_plan_list = project.planned_step_cash_flow_ids
                for period, options in periods_dict.items():
                    if 'sum' not in period:
                        project_data.setdefault(period, {'commitment': 0, 'fact': 0})

                        for pds_fact in pds_fact_list:
                            if period[0] <= pds_fact.date_cash <= period[
                                1] and project.commercial_budget_id.id == budget.id:
                                pds_is_present = True
                                project_data[period]['fact'] += pds_fact.sum_cash

                        for pds_plan in pds_plan_list:
                            if (period[0] <= pds_plan.date_cash <= period[1]
                                    and project.commercial_budget_id.id == options['budget_id']
                                    and (pds_plan.forecast == 'commitment'
                                         or (pds_plan.forecast == 'from_project'
                                             and project.stage_id.code in ('100(done)', '100', '75')))):
                                if pds_plan.distribution_sum_with_vat_ostatok > 0:
                                    pds_is_present = True
                                    project_data[period]['commitment'] += pds_plan.distribution_sum_with_vat_ostatok

            if pds_is_present:
                current_project = projects.filtered(
                    lambda pr: pr.project_id == project_project_id and pr.commercial_budget_id.id == budget.id)

                if not current_project:  # если в текущем бюджете проекта нет, ищем самый последний и берем info из него
                    for budget_id in sorted(budget_ids, reverse=True):
                        if budget_id != budget.id:
                            current_project = projects.filtered(lambda
                                                                    pr: pr.project_id == project_project_id and pr.commercial_budget_id.id == budget_id)
                            if current_project:
                                break

                data.setdefault(current_project.company_id.name, {}).setdefault(
                    current_project.responsibility_center_id.name, {}).setdefault(
                    current_project.project_id, {})

                project_step_id = ''

                currency_rate = self.get_currency_rate_by_project(current_project)
                if current_project.step_status == 'project':
                    project_step_id = (current_project.step_project_number or '') + ' | ' + (
                                current_project.project_id or '')
                elif current_project.step_status == 'step':
                    project_step_id = (
                                                  current_project.step_project_number or '') + ' | ' + current_project.step_project_parent_id.project_id + " | " + current_project.project_id

                data[current_project.company_id.name][current_project.responsibility_center_id.name][
                    current_project.project_id]['info'] = {
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

                data[current_project.company_id.name][current_project.responsibility_center_id.name][
                    current_project.project_id]['periods'] = project_data
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
                    string = self.month_rus_name[period[0].month - 1] + ' ' + period[0].strftime("%d") + '-' + period[
                        1].strftime("%d") + '\n' + col['print_head']
                    sheet.set_column(column, column, *(col['col_format']))
                    sheet.merge_range(row + 1, column, row + 2, column, string, col['format_head'])
                    column += 1
            elif options['type'] == 'sum_month':
                for col in options['cols']:
                    if col['print'] == 'fact':
                        string = col['print_head']
                    else:
                        string = self.month_rus_name[options['date'].month - 1] + '\n' + col['print_head']
                    sheet.set_column(column, column, *(col['col_format']))
                    sheet.merge_range(row + 1, column, row + 2, column, string, col['format_head'])
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
                sheet.merge_range(row + 1, column, row + 2, column, string, options['cols'][0]['format_head'])
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
                            xl_col_to_name(11 + col['formula'][0]),
                            xl_col_to_name(11 + col['formula'][1]),
                            xl_col_to_name(11 + col['formula'][2]),
                        )
                        sheet.write_formula(row, column, formula, col['format'])
                        column += 1
                    elif 'sum_month' in period:
                        if len(periods_dict[period]['formula']) == 4:  # учитываем разное количество недель в месяце
                            formula = 'sum({1}{0},{2}{0},{3}{0},{4}{0})'.format(
                                row + 1,
                                xl_col_to_name(11 + col['formula'][0]),
                                xl_col_to_name(11 + col['formula'][1]),
                                xl_col_to_name(11 + col['formula'][2]),
                                xl_col_to_name(11 + col['formula'][3]),
                            )
                            sheet.write_formula(row, column, formula, col['format'])
                        elif len(periods_dict[period]['formula']) == 5:
                            formula = 'sum({1}{0},{2}{0},{3}{0},{4}{0},{5}{0})'.format(
                                row + 1,
                                xl_col_to_name(11 + col['formula'][0]),
                                xl_col_to_name(11 + col['formula'][1]),
                                xl_col_to_name(11 + col['formula'][2]),
                                xl_col_to_name(11 + col['formula'][3]),
                                xl_col_to_name(11 + col['formula'][4]),
                            )
                            sheet.write_formula(row, column, formula, col['format'])
                        elif len(periods_dict[period]['formula']) == 6:
                            formula = 'sum({1}{0},{2}{0},{3}{0},{4}{0},{5}{0},{6}{0})'.format(
                                row + 1,
                                xl_col_to_name(11 + col['formula'][0]),
                                xl_col_to_name(11 + col['formula'][1]),
                                xl_col_to_name(11 + col['formula'][2]),
                                xl_col_to_name(11 + col['formula'][3]),
                                xl_col_to_name(11 + col['formula'][4]),
                                xl_col_to_name(11 + col['formula'][5]),
                            )
                            sheet.write_formula(row, column, formula, col['format'])
                        column += 1
                    else:
                        sheet.write_string(row, column, period, row_format_number)
                        column += 1

    def print_row(self, sheet, workbook, companies, responsibility_centers, actual_center_ids, row, data, periods_dict,
                  level, max_level, dict_formula):
        row_format = workbook.add_format({
            'border': 1,
            'font_size': 8
        })
        center_format = workbook.add_format({
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
        center_format_number = workbook.add_format({
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
            center_lines = list()

            for center in responsibility_centers.filtered(lambda r: r.company_id == company):
                if center.id in actual_center_ids:
                    if center.id not in dict_formula['center_ids']:
                        row += 1
                        dict_formula['center_ids'][center.id] = row
                        sheet.set_row(row, False, False, {'hidden': 1, 'level': level})
                        sheet.merge_range(row, 0, row, 11, center.name, center_format)
                    project_lines = list()
                    center_lines.append(row)
                    if center.name in data[company.name]:
                        for project, content in data[company.name][center.name].items():
                            # печатаем строки проектов
                            row += 1
                            sheet.set_row(row, False, False, {'hidden': 1, 'level': max_level + 1})
                            cur_row_format = row_format
                            cur_row_format_number = row_format_number
                            column = 0
                            sheet.write_string(row, column, center.name, cur_row_format)
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
                            sheet.write_number(row, column, content['info']['total_amount_of_revenue_with_vat'],
                                               cur_row_format_number)
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

                    child_centers = self.env['account.analytic.account'].search([
                        ('parent_id', '=', center.id),
                        ('plan_id', '=', self.env.ref(
                            'analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
                    ], order='sequence')

                    if child_centers:
                        row, formula_itogo = self.print_row(sheet, workbook, company, child_centers,
                                                            actual_center_ids, row, data, periods_dict,
                                                            level + 1, max_level, dict_formula)
                        for child_center in child_centers:
                            if child_center.id in actual_center_ids:
                                project_lines.append(dict_formula['center_ids'][child_center.id])

                    self.print_vertical_sum_formula(sheet, dict_formula['center_ids'][center.id], project_lines,
                                                    periods_dict, 12, 'format_center')

                if level == 1:
                    self.print_vertical_sum_formula(sheet, dict_formula['company_ids'][company.id], center_lines,
                                                    periods_dict, 12, 'format_company')

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

    def printworksheet(self, workbook, budget, namesheet, responsibility_center_ids, max_level, multipliers,
                       dict_formula):
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

        row_format_center = workbook.add_format({
            'border': 1,
            'font_size': 9,
            "bold": True,
            "fg_color": '#8497B0',
        })
        row_format_center.set_num_format('#,##0')

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
        # actual_budget_date = datetime(year=2024, month=6, day=6)  # для отладки

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
            '&','&','&',
            ('stage_id.project_state', '!=', 'cancel'),
            ('commercial_budget_id', 'in', budget_ids),
            '|', '&', ('step_status', '=', 'step'),
            ('step_project_parent_id.project_have_steps', '=', True),
            '&', ('step_status', '=', 'project'),
            ('project_have_steps', '=', False),
            '|', '|', '|',
            ('id', 'in', [fact.projects_id.id for fact in self.env['project_budget.fact_cash_flow'].search([]) if
                          fact.date_cash >= period_limits[0] and fact.date_cash <= period_limits[1]]),
            ('id', 'in', [plan.projects_id.id for plan in self.env['project_budget.planned_cash_flow'].search([]) if
                          plan.date_cash >= period_limits[0] and plan.date_cash <= period_limits[1]]),
            ('id', 'in',
             [fact.step_project_child_id.id for fact in self.env['project_budget.fact_cash_flow'].search([]) if
              fact.date_cash >= period_limits[0] and fact.date_cash <= period_limits[1]]),
            ('id', 'in',
             [plan.step_project_child_id.id for plan in self.env['project_budget.planned_cash_flow'].search([]) if
              plan.date_cash >= period_limits[0] and plan.date_cash <= period_limits[1]]),
        ], order='project_id')

        data = self.get_data_from_projects(projects, periods_dict, budget, budget_ids)

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

        column = self.print_head(workbook, sheet, row, column, periods_dict, actual_budget_date)
        row += 2

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

            sheet.merge_range(row, 0, row, 11, 'ИТОГО по отчету', row_format_number_itogo)

            self.print_vertical_sum_formula(sheet, row, dict_formula['company_ids'].values(), periods_dict, 12,
                                            'format_company')

    def generate_xlsx_report(self, workbook, data, budgets):

        dict_formula = {'company_ids': {}, 'center_ids': {}, 'center_ids_not_empty': {}}

        responsibility_center_ids = data['responsibility_center_ids']

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

        multipliers = {'50': data['koeff_reserve'], '30': data['koeff_potential']}

        commercial_budget_id = data['commercial_budget_id']
        budget = self.env['project_budget.commercial_budget'].search([('id', '=', commercial_budget_id)])
        self.printworksheet(workbook, budget, 'ПДС', responsibility_center_ids, max_level, multipliers, dict_formula)
