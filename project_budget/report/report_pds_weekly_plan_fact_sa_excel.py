import logging

from odoo import models
from odoo.tools import date_utils
from datetime import date, datetime, timedelta
from dateutil.relativedelta import *
from xlsxwriter.utility import xl_col_to_name
from collections import OrderedDict

isdebug = False
logger = logging.getLogger("*___forecast_report___*")

class ReportPdsWeeklyPlanFactExcelSA(models.AbstractModel):
    _name = 'report.project_budget.report_pds_weekly_plan_fact_sa_excel'
    _description = 'project_budget.report_pds_weekly_plan_fact_sa_excel'
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

    def centers_with_parents(self, ids, max_level):
        if not ids:
            return max_level
        max_level += 1
        new_ids = [center.id for center in self.env['account.analytic.account'].search([
            ('parent_id', 'in', ids),
            ('plan_id', '=', self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
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
        blank_format = workbook.add_format({
            'font_size': 8,
            'num_format': '#,##0',
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
        blank_head_format = workbook.add_format({
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "font_size": 10,
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
        blank_center_format = workbook.add_format({
            'font_size': 10,
            'bold': True,
            'num_format': '#,##0',
        })
        commitment_company_format = workbook.add_format({
            'top': 2,
            'bottom': 2,
            'left': 1,
            'right': 1,
            'font_size': 12,
            'bold': True,
            'num_format': '#,##0',
            'fg_color': '#C4D79B',
        })
        fact_company_format = workbook.add_format({
            'top': 2,
            'bottom': 2,
            'left': 1,
            'right': 1,
            'font_size': 12,
            'bold': True,
            'num_format': '#,##0',
            'fg_color': '#C4D79B',
        })
        plan_fact_company_format = workbook.add_format({
            'top': 2,
            'bottom': 2,
            'left': 1,
            'right': 1,
            'font_size': 12,
            'bold': True,
            'num_format': '#,##0',
            'fg_color': '#C4D79B',
        })
        blank_company_format = workbook.add_format({
            'font_size': 12,
            'bold': True,
            'num_format': '#,##0',
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

            quarter_col_format = (10, None)
            blank_quarter_col_format = (2, None)
            if month_delta in (0, 1, 2):
                month_col_format = (10, None)
                blank_month_col_format = (2, None)
            else:
                month_col_format = (10, None, {'hidden': 1, 'level': 1})
                blank_month_col_format = (2, None, {'hidden': 1, 'level': 1})

            if date_utils.start_of(month_start, 'month') == date_utils.start_of(actual_date, 'month').date():

                periods_dict[(month_start, month_end)] = {
                    'type': 'month',
                    'difference': False,
                    'cols': [
                        {
                            'print': 'commitment',
                            'print_head': 'план-прогноз на начало месяца',
                            'format': plan_fact_format,
                            'format_head': plan_fact_head_format,
                            'format_center': plan_fact_center_format,
                            'format_company': plan_fact_company_format,
                            'col_format': month_col_format,
                            'link': 'month_plan',
                        },
                    ]
                }
                col += 1
                
                actual_week = month_start
                actual_week_number = actual_week.isocalendar()[1]
                actual_week_year = actual_week.isocalendar()[0]
                week_start = month_start
                week_end = self.get_dates_from_week(actual_week_number, actual_week_year)[1]
                while week_start < date_utils.start_of(actual_date + relativedelta(months=2), 'month').date():  # недели в течение двух месяцев

                    week_col_format = (10, None, {'hidden': 1, 'level': 1})

                    if date_utils.start_of(week_start, 'month') >= date_utils.start_of(actual_date + relativedelta(months=1), 'month').date():
                        if month_delta in (0, 1,):
                            week_month_col_format = (10, None)
                            blank_week_month_col_format = (2, None)
                        else:
                            week_month_col_format = (10, None, {'hidden': 1, 'level': 1})
                            blank_week_month_col_format = (2, None, {'hidden': 1, 'level': 1})
                    else:
                        if month_delta in (0, 1, 2):
                            week_month_col_format = (10, None)
                            blank_week_month_col_format = (2, None)
                        else:
                            week_month_col_format = (10, None, {'hidden': 1, 'level': 1})
                            blank_week_month_col_format = (2, None, {'hidden': 1, 'level': 1})

                    periods_dict[(week_start, week_end)] = {
                        'type': 'week',
                        'difference': True,
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
                                'link': 'month_fact',
                            }
                        ],
                    }
                    col += 2
                    if date_utils.start_of(week_start, 'week') > date_utils.start_of(actual_date, 'week').date():
                        week_cols.append(col - 2)
                    else:
                        week_cols.append(col - 1)

                    next_week = actual_week + timedelta(weeks=1)
                    next_week_number = next_week.isocalendar()[1]
                    next_week_year = next_week.isocalendar()[0]
                    next_week_start, next_week_end = self.get_dates_from_week(next_week_number, next_week_year)
                    # actual_week = actual_week + timedelta(weeks=1)
                    # actual_week_number = actual_week.isocalendar()[1]
                    # actual_week_year = actual_week.isocalendar()[0]
                    # week_start, week_end = self.get_dates_from_week(actual_week_number, actual_week_year)
                    if next_week_start.month != next_week_end.month:  # учитываем разбиение недель по месяцам
                        week_month_end = next_week_end.replace(day=1) - timedelta(days=1)
                        week_month_start = next_week_end.replace(day=1)
                        periods_dict[(next_week_start, week_month_end)] = {
                            'type': 'week',
                            'difference': True,
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
                                    'link': 'month_fact',
                                }
                            ],
                        }
                        col += 2
                        if date_utils.start_of(week_start, 'week') > date_utils.start_of(actual_date, 'week').date():
                            week_cols.append(col - 2)
                        else:
                            week_cols.append(col - 1)

                        week_start = week_month_start
                    else:
                        week_start = next_week_start
                    if week_end.month != week_start.month:
                        formula = week_cols
                        week_cols = []

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

                        periods_dict['sum_month_' + str(week_end.month)] = {
                            'type': 'sum_month',
                            'difference': False,
                            'date': week_end,
                            'formula': formula,
                            'cols': [
                                {
                                    'print': 'commitment',
                                    'print_head': 'прогноз',
                                    'format': month_format,
                                    'format_head': month_head_format,
                                    'format_center': month_center_format,
                                    'format_company': month_company_format,
                                    'col_format': week_month_col_format,
                                    'link': 'month_forecast',
                                },
                                {
                                    'print': 'blank',
                                    'print_head': 'разница',
                                    'format': blank_format,
                                    'format_head': blank_head_format,
                                    'format_center': blank_center_format,
                                    'format_company': blank_company_format,
                                    'col_format': blank_week_month_col_format,
                                },
                            ],
                        }
                        col += 2
                        month_cols.append(col - 2)
                        if week_end.month % 3 == 0:
                            formula = month_cols
                            month_cols = []

                            if month_end < actual_date.date():
                                quarter_format = fact_format
                                quarter_head_format = fact_head_format
                                quarter_center_format = fact_center_format
                                quarter_company_format = fact_company_format
                            else:
                                quarter_format = commitment_format
                                quarter_head_format = commitment_head_format
                                quarter_center_format = commitment_center_format
                                quarter_company_format = commitment_company_format

                            periods_dict['sum_quarter_' + str((month_start.month - 1) // 3 + 1)] = {
                                'type': 'sum_quarter',
                                'difference': False,
                                'date': month_end,
                                'formula': formula,
                                'cols': [
                                    {
                                        'print': 'commitment',
                                        'print_head': 'прогноз',
                                        'format': quarter_format,
                                        'format_head': quarter_head_format,
                                        'format_center': quarter_center_format,
                                        'format_company': quarter_company_format,
                                        'col_format': quarter_col_format,
                                        'link': 'year_forecast'
                                    },
                                    {
                                        'print': 'blank',
                                        'print_head': 'разница',
                                        'format': blank_format,
                                        'format_head': blank_head_format,
                                        'format_center': blank_center_format,
                                        'format_company': blank_company_format,
                                        'col_format': blank_quarter_col_format,
                                    },
                                ],
                            }
                            col += 2
                    week_end = next_week_end
                    actual_week = next_week
            elif date_utils.start_of(month_start, 'month') == date_utils.start_of(actual_date + relativedelta(months=1), 'month').date():  # пропускаем следующий за текущим месяц
                continue
            else:
                if month_end < actual_date.date():  # в прошлом печатаем прогноз и факт, в будущем - только прогноз
                    periods_dict[(month_start, month_end)] = {
                        'type': 'month',
                        'difference': True,
                        'cols': [
                            {
                                'print': 'commitment',
                                'print_head': 'план-прогноз на начало месяца',
                                'format': plan_fact_format,
                                'format_head': plan_fact_head_format,
                                'format_center': plan_fact_center_format,
                                'format_company': plan_fact_company_format,
                                'col_format': month_col_format,
                            },
                            {
                                'print': 'fact',
                                'print_head': 'факт',
                                'format': fact_format,
                                'format_head': fact_head_format,
                                'format_center': fact_center_format,
                                'format_company': fact_company_format,
                                'col_format': month_col_format,
                                'link': 'quarter_fact',
                            },
                            {
                                'print': 'blank',
                                'print_head': 'разница',
                                'format': blank_format,
                                'format_head': blank_head_format,
                                'format_center': blank_center_format,
                                'format_company': blank_company_format,
                                'col_format': blank_month_col_format,
                            },
                        ]
                    }
                    col += 3
                    month_cols.append(col - 2)
                else:
                    if month_delta != 2:
                        periods_dict[(month_start, month_end)] = {
                            'type': 'month',
                            'difference': False,
                            'cols': [
                                {
                                    'print': 'commitment',
                                    'print_head': 'прогноз на текущую дату',
                                    'format': commitment_format,
                                    'format_head': commitment_head_format,
                                    'format_center': commitment_center_format,
                                    'format_company': commitment_company_format,
                                    'col_format': month_col_format,
                                },
                            ]
                        }
                        month_cols.append(col)
                        col += 1
                    else:
                        periods_dict[(month_start, month_end)] = {
                            'type': 'month',
                            'difference': False,
                            'cols': [
                                {
                                    'print': 'commitment',
                                    'print_head': 'прогноз на текущую дату',
                                    'format': commitment_format,
                                    'format_head': commitment_head_format,
                                    'format_center': commitment_center_format,
                                    'format_company': commitment_company_format,
                                    'col_format': month_col_format,
                                },
                                {
                                    'print': 'blank',
                                    'print_head': 'разница',
                                    'format': blank_format,
                                    'format_head': blank_head_format,
                                    'format_center': blank_center_format,
                                    'format_company': blank_company_format,
                                    'col_format': blank_month_col_format,
                                },
                            ]
                        }
                        month_cols.append(col)
                        col += 2
                if month_start.month % 3 == 0:  # добавляем суммы и формулы по кварталам
                    formula = month_cols
                    month_cols = []

                    if month_start < actual_date.date():
                        quarter_format = fact_format
                        quarter_head_format = fact_head_format
                        quarter_center_format = fact_center_format
                        quarter_company_format = fact_company_format
                    else:
                        quarter_format = commitment_format
                        quarter_head_format = commitment_head_format
                        quarter_center_format = commitment_center_format
                        quarter_company_format = commitment_company_format

                    periods_dict['sum_quarter_' + str((month_start.month - 1) // 3 + 1)] = {
                        'type': 'sum_quarter',
                        'difference': False,
                        'date': month_end,
                        'formula': formula,
                        'cols': [
                            {
                                'print': 'commitment',
                                'print_head': 'прогноз',
                                'format': quarter_format,
                                'format_head': quarter_head_format,
                                'format_center': quarter_center_format,
                                'format_company': quarter_company_format,
                                'col_format': quarter_col_format,
                                'link': 'year_forecast'
                            },
                            {
                                'print': 'blank',
                                'print_head': 'разница',
                                'format': blank_format,
                                'format_head': blank_head_format,
                                'format_center': blank_center_format,
                                'format_company': blank_company_format,
                                'col_format': blank_quarter_col_format,
                            },
                        ],
                    }
                    col += 2
                if month_delta == -3:  # начало и конец всего периода
                    period_limits.append(month_start)
                elif month_delta == 5:
                    period_limits.append(month_end)

        return periods_dict, period_limits

    def calculate_budget_ids(self, budget, periods_dict):
        budget_ids = set()
        actual_budget_date = date.today() if not budget.date_actual else budget.date_actual.date()
        for period, options in periods_dict.items():
            if 'sum' not in period:
                if options['type'] == 'month' and date_utils.start_of(period[1], 'month') <= date_utils.start_of(actual_budget_date, 'month'):
                    budget_id = self.env['project_budget.commercial_budget'].search([
                        ('date_actual', '<', period[0]),
                        ('date_actual', '>=', period[0] - relativedelta(months=1)),
                    ], limit=1, order='date_actual desc').id
                    options['budget_id'] = budget_id
                    if budget_id:
                        budget_ids.add(budget_id)
                elif options['type'] == 'week' and date_utils.start_of(period[1], 'week') <= date_utils.start_of(actual_budget_date, 'week'):
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
        return periods_dict, list(budget_ids)

    def get_data_from_indicators(self, indicators, periods_dict, budget, budget_ids):
        project_project_ids = set(indicators.prj_id.mapped('project_id'))
        data = {}
        commitment_id = self.env.ref('project_budget_nkk.project_budget_forecast_probability_commitment').id
        for project_project_id in project_project_ids:
            project_indicators = indicators.filtered(lambda i: i.prj_id.project_id == project_project_id)
            pds_is_present = False
            factoring_is_present = False
            project_data = {}
            for period, options in periods_dict.items():
                if 'sum' not in period:
                    fact = commitment = 0
                    for i in project_indicators:
                        if period[0] <= i.date <= period[1]:
                            if i.commercial_budget_id.id == budget.id and not i.forecast_probability_id:
                                fact += i.amount
                                factoring_is_present = any(d.factoring for d in i.fact_cash_flow_id.distribution_cash_ids)
                                pds_is_present = True
                            elif i.commercial_budget_id.id == options['budget_id'] and i.forecast_probability_id.id == commitment_id:
                                commitment += i.amount - i.distribution
                                pds_is_present = True
                    project_data.setdefault(period, {'commitment': commitment, 'fact': fact})

                if pds_is_present:
                    current_project = indicators.prj_id.filtered(
                        lambda pr: pr.project_id == project_project_id and pr.commercial_budget_id.id == budget.id)

                    if not current_project:  # если в текущем бюджете проекта нет, ищем самый последний и берем info из него
                        for budget_id in sorted(budget_ids, reverse=True):
                            if budget_id != budget.id:
                                current_project = indicators.prj_id.filtered(lambda
                                                                        pr: pr.project_id == project_project_id and
                                                                            pr.commercial_budget_id.id == budget_id)
                                if current_project:
                                    break

                    data.setdefault(current_project.company_id.name, {}).setdefault(
                        current_project.responsibility_center_id.name, {}).setdefault(
                        current_project.project_id, {})

                    project_step_id = ''

                    currency_rate = self.get_currency_rate_by_project(current_project)
                    if current_project.step_status == 'project':
                        project_step_id = (current_project.step_project_number or '') + ' | ' + (current_project.project_id or '')
                    elif current_project.step_status == 'step':
                        project_step_id = (current_project.step_project_number or '') + ' | ' + current_project.step_project_parent_id.project_id + " | " + current_project.project_id

                    data[current_project.company_id.name][current_project.responsibility_center_id.name][current_project.project_id]['info'] = {
                        'factoring': factoring_is_present,
                        'key_account_manager_id': current_project.key_account_manager_id.name,
                        'partner_id': current_project.partner_id.name,
                        'essence_project': current_project.essence_project,
                        'project_id': project_step_id,
                    }
                    data[current_project.company_id.name][current_project.responsibility_center_id.name][current_project.project_id]['periods'] = project_data
        return data

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

    def get_previous_budget(self, actual_budget_date):
        previous_week_number = (actual_budget_date - timedelta(weeks=1)).isocalendar()[1]
        previous_week_year = (actual_budget_date - timedelta(weeks=1)).isocalendar()[0]
        previous_week_start, previous_week_end = self.get_dates_from_week(previous_week_number, previous_week_year)
        previous_budget = self.env['project_budget.commercial_budget'].search([
            ('date_actual', '<=', previous_week_end),
        ], limit=1, order='date_actual desc')
        return previous_budget

    def get_company_plans(self, actual_date, company, centers_to_exclude):
        center_plans = self.env['project_budget.budget_plan_supervisor_spec'].search([
            ('budget_plan_supervisor_id.is_company_plan', '=', False),
            ('budget_plan_supervisor_id.year', '=', actual_date.year),
            ('budget_plan_supervisor_id.company_id', '=', company.id),
            ('budget_plan_supervisor_id.responsibility_center_id', 'not in', centers_to_exclude.ids),
            ('type_row', '=', 'cash'),
        ])

        use_6_6_plan = False
        for plan in center_plans:
            if plan.q3_plan_6_6 != 0 or plan.q4_plan_6_6 != 0:
                use_6_6_plan = True
                continue

        actual_quarter_number = (actual_date.month - 1) // 3 + 1
        quarter_plan = 0
        year_plan = 0
        hy1_fact = 0
        for plan in center_plans:
            if actual_quarter_number in (1, 2):
                quarter_plan += plan['q' + str(actual_quarter_number) + '_plan']
            else:
                quarter_plan += plan['q' + str(actual_quarter_number) + '_plan' + ('_6_6' if use_6_6_plan else '')]
            hy1_fact += plan.q1_fact + plan.q2_fact
            if use_6_6_plan:
                year_plan += hy1_fact + plan.q3_plan_6_6 + plan.q4_plan_6_6
            else:
                year_plan += plan.q1_plan + plan.q2_plan + plan.q3_plan + plan.q4_plan

        plans = {
            'quarter_plan': {'name': 'План' + (' 6+6' if use_6_6_plan else ''), 'amount': quarter_plan},
            'year_plan': {'name': 'План' + (' 6+6' if use_6_6_plan else ''), 'amount': year_plan},
            'hy1_fact': {'name': '', 'amount': hy1_fact}
        }
        return plans, use_6_6_plan

    def get_year_forecast(self, budget, year):
        financial_indicators = self.env['project.budget.financial.indicator'].search_read([
            ('commercial_budget_id', '=', budget.id),
            ('type', '=', 'cash_flow'),
            ('date', '>=', datetime(day=1, month=1, year=year)),
            ('date', '<=', datetime(day=31, month=12, year=year)),
            ('forecast_probability_id.id', '=', self.env.ref('project_budget_nkk.project_budget_forecast_probability_commitment').id),
        ],['amount'])
        year_forecast = sum(fi['amount'] for fi in financial_indicators)
        return year_forecast

    def get_vgo_fact_sum(self, indicators, company, budget, period):
        filtered_indicators = indicators.filtered(
            lambda i: not i.forecast_probability_id
            and i.commercial_budget_id.id == budget.id
            and period[0].date() >= i.date >= period[1].date()
            and i.project_id.signer_id != company.id
        )
        return sum(fi.amount for fi in filtered_indicators)

    def print_head(self, workbook, sheet, row, column, periods_dict, actual_budget_date):
        sheet.set_row(row, 16)
        sheet.set_row(row + 1, 65)

        for period, options in periods_dict.items():
            for col in options['cols']:
                if col['print'] == 'blank':
                    sheet.set_column(column, column, *(col['col_format']))
                    sheet.write(row + 1, column, '', col['format_head'])
                elif options['type'] == 'month':
                    string = self.month_rus_name[period[0].month - 1] + '\n' + col['print_head']
                    sheet.set_column(column, column, *(col['col_format']))
                    sheet.merge_range(row + 1, column, row + 2, column, string, col['format_head'])
                elif options['type'] == 'week':
                    string = self.month_rus_name[period[0].month - 1] + ' ' + period[0].strftime("%d") + '-' + period[1].strftime("%d") + '\n' + col['print_head']
                    sheet.set_column(column, column, *(col['col_format']))
                    sheet.merge_range(row + 1, column, row + 2, column, string, col['format_head'])
                elif options['type'] == 'sum_month':
                    string = self.month_rus_name[options['date'].month - 1]  + '\n прогноз на текущую дату'
                    sheet.set_column(column, column, *(col['col_format']))
                    sheet.merge_range(row + 1, column, row + 2, column, string, col['format_head'])
                elif options['type'] == 'sum_quarter':
                    if options['date'] < actual_budget_date.date():
                        string = ('ИТОГО \nПДС Q' + str((options['date'].month - 1) // 3 + 1) + '/' +
                                  options['date'].strftime("%Y") + '\nФакт')
                    else:
                        string = ('ИТОГО \nПДС Q' + str((options['date'].month - 1) // 3 + 1) + '/' +
                                  options['date'].strftime("%Y") + '\nПрогноз')
                    sheet.set_column(column, column, *(col['col_format']))
                    sheet.merge_range(row + 1, column, row + 2, column, string, col['format_head'])
                else:
                    string = period
                    sheet.set_column(column, column, *(col['col_format']))
                    sheet.merge_range(row + 1, column, row + 2, column, string, col['format_head'])
                column += 1
        return column

    def print_summary_head(self, workbook, sheet, row, column, period):
        head_format = workbook.add_format({
            'border': 2,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "bold": False,
            "font_size": 12,
        })
        head_format_grey = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "bold": False,
            "fg_color": '#f2f2f2',
            "font_size": 8,
        })
        left_border_1 = workbook.add_format({
            'left': 1,
        })
        left_border_2 = workbook.add_format({
            'left': 2,
        })
        sheet.merge_range(row, column, row, column + 5, period[0].strftime('%d.%m') + '-' + period[1].strftime('%d.%m'), head_format)
        sheet.write(row, column + 6, "", left_border_2)
        row += 1
        sheet.set_row(row, False, False, {'level': 1})
        sheet.write(row, column, "Факторинг", head_format_grey)
        sheet.set_column(column, column, 16)
        column += 1
        sheet.write(row, column, "Сумма", head_format_grey)
        sheet.set_column(column, column, 16)
        column += 1
        sheet.write(row, column, "Продавец", head_format_grey)
        sheet.set_column(column, column, 16)
        column += 1
        sheet.write(row, column, "Заказчик", head_format_grey)
        sheet.set_column(column, column, 25, False, {'hidden': 1, 'level': 1})
        column += 1
        sheet.write(row, column, "Проект", head_format_grey)
        sheet.set_column(column, column, 25, False, {'hidden': 1, 'level': 1})
        column += 1
        sheet.write(row, column, "Комментарий", head_format_grey)
        sheet.set_column(column, column, 25, False, {'hidden': 1, 'level': 1})
        sheet.write(row, column + 1, "", left_border_1)
        row += 1
        return row

    def print_row_values(self, workbook, sheet, row, column, periods_data, periods_dict, start_column):

        row_format_number = workbook.add_format({
            'border': 1,
            'font_size': 8,
            'num_format': '#,##0',
        })

        for period in periods_dict:
            if 'sum' not in period:
                for col in periods_dict[period]['cols']:
                    if col['print'] == 'blank':
                        sheet.write(row, column, '', col['format'])
                    else:
                        sheet.write_number(row, column, periods_data[period][col['print']], col['format'])
                    column += 1
            else:
                for col in periods_dict[period]['cols']:
                    if col['print'] == 'blank':
                        sheet.write(row, column, '', col['format'])
                    elif 'sum_quarter' in period:
                        formula = 'sum({1}{0},{2}{0},{3}{0})'.format(
                                row + 1,
                                xl_col_to_name(start_column + periods_dict[period]['formula'][0]),
                                xl_col_to_name(start_column + periods_dict[period]['formula'][1]),
                                xl_col_to_name(start_column + periods_dict[period]['formula'][2]),
                            )
                        sheet.write_formula(row, column, formula, col['format'])
                    elif 'sum_month' in period:
                        if len(periods_dict[period]['formula']) == 4:  # учитываем разное количество недель в месяце
                            formula = 'sum({1}{0},{2}{0},{3}{0},{4}{0})'.format(
                                row + 1,
                                xl_col_to_name(start_column + periods_dict[period]['formula'][0]),
                                xl_col_to_name(start_column + periods_dict[period]['formula'][1]),
                                xl_col_to_name(start_column + periods_dict[period]['formula'][2]),
                                xl_col_to_name(start_column + periods_dict[period]['formula'][3]),
                            )
                            sheet.write_formula(row, column, formula, col['format'])
                        elif len(periods_dict[period]['formula']) == 5:
                            formula = 'sum({1}{0},{2}{0},{3}{0},{4}{0},{5}{0})'.format(
                                row + 1,
                                xl_col_to_name(start_column + periods_dict[period]['formula'][0]),
                                xl_col_to_name(start_column + periods_dict[period]['formula'][1]),
                                xl_col_to_name(start_column + periods_dict[period]['formula'][2]),
                                xl_col_to_name(start_column + periods_dict[period]['formula'][3]),
                                xl_col_to_name(start_column + periods_dict[period]['formula'][4]),
                            )
                            sheet.write_formula(row, column, formula, col['format'])
                        elif len(periods_dict[period]['formula']) == 6:
                            formula = 'sum({1}{0},{2}{0},{3}{0},{4}{0},{5}{0},{6}{0})'.format(
                                row + 1,
                                xl_col_to_name(start_column + periods_dict[period]['formula'][0]),
                                xl_col_to_name(start_column + periods_dict[period]['formula'][1]),
                                xl_col_to_name(start_column + periods_dict[period]['formula'][2]),
                                xl_col_to_name(start_column + periods_dict[period]['formula'][3]),
                                xl_col_to_name(start_column + periods_dict[period]['formula'][4]),
                                xl_col_to_name(start_column + periods_dict[period]['formula'][5]),
                            )
                            sheet.write_formula(row, column, formula, col['format'])
                    else:
                        sheet.write_string(row, column, period, row_format_number)
                    column += 1

    def print_rows(self, sheet, workbook, company, responsibility_centers, actual_center_ids, row, data, periods_dict, level, max_level, dict_formula, start_column):
        row_format = workbook.add_format({
            'border': 1,
            'font_size': 8,
        })
        row_format_number = workbook.add_format({
            'border': 1,
            'font_size': 9,
            'num_format': '#,##0',
        })
        factoring_row_format = workbook.add_format({
            'border': 1,
            'font_size': 8,
            'fg_color': '#92D050',
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
            'fg_color': '#C4D79B',
        })
        difference_format = workbook.add_format({
            'top': 1,
            'bottom': 1,
            'left': 1,
            'right': 1,
            'font_size': 12,
            'fg_color': '#FFFF00',
        })
        difference_format_number = workbook.add_format({
            'top': 1,
            'bottom': 1,
            'left': 1,
            'right': 1,
            'font_size': 12,
            'bold': True,
            'fg_color': '#FFFF00',
            'num_format': '#,##0;[red]-#,##0',
            'valign': 'center',
        })

        link = {}
        center_lines = list()
        for center in responsibility_centers.filtered(lambda r: r.company_id == company):
            if center.id in actual_center_ids:
                if center.id not in dict_formula['center_ids']:
                    row += 1
                    dict_formula['center_ids'][center.id] = row
                    sheet.set_row(row, False, False, {'hidden': 1, 'level': level})
                    sheet.merge_range(row, 0, row, start_column - 1, center.name, center_format)
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
                        if content['info']['factoring']:
                            sheet.write_string(row, column, 'да', factoring_row_format)
                        else:
                            sheet.write_string(row, column, 'нет', cur_row_format)
                        column += 1
                        sheet.write_string(row, column, content['info']['key_account_manager_id'], cur_row_format)
                        column += 1
                        sheet.write_string(row, column, content['info']['partner_id'], cur_row_format)
                        column += 1
                        sheet.write_string(row, column, content['info']['essence_project'], cur_row_format)
                        column += 1
                        sheet.write_string(row, column, content['info']['project_id'], cur_row_format)
                        column += 1
                        sheet.write_string(row, column, '', cur_row_format)
                        column += 1
                        self.print_row_values(workbook, sheet, row, column, content['periods'], periods_dict, start_column)
                        project_lines.append(row)

                child_centers = self.env['account.analytic.account'].search([
                    ('parent_id', '=', center.id),
                    ('plan_id', '=', self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
                ], order='sequence')

                if child_centers:
                    row, dict_formula, link = self.print_rows(sheet, workbook, company, child_centers,
                                                        actual_center_ids, row, data, periods_dict,
                                                        level + 1, max_level, dict_formula, start_column)
                    for child_center in child_centers:
                        if child_center.id in actual_center_ids:
                            project_lines.append(dict_formula['center_ids'][child_center.id])

                self.print_vertical_sum_formula(sheet, dict_formula['center_ids'][center.id], project_lines, periods_dict, start_column, 'format_center')

        if level == 1:
            row += 1
            sheet.merge_range(row, 0, row, start_column - 1, 'ИТОГО ' + company.name, company_format)
            link = self.print_vertical_sum_formula(sheet, row, center_lines, periods_dict, start_column, 'format_company')
            row += 1
            sheet.merge_range(row, 0, row, 2, 'Разница Факт/Прогноз (неделя)', difference_format)
            column = start_column
            for period, options in periods_dict.items():
                period_len = len(options['cols'])
                if options['difference']:
                    formula = f'={xl_col_to_name(column + 1)}{row}-{xl_col_to_name(column)}{row}'
                    sheet.merge_range(row, column, row, column + 1, formula, difference_format_number)
                column += period_len
            row += 1
        return row, dict_formula, link

    def print_rows_signer(self, sheet, workbook, signer, row, data, periods_dict, max_level, start_column):
        row_format = workbook.add_format({
            'border': 1,
            'font_size': 8,
        })
        row_format_number = workbook.add_format({
            'border': 1,
            'font_size': 9,
            'num_format': '#,##0',
        })
        factoring_row_format = workbook.add_format({
            'border': 1,
            'font_size': 8,
            'fg_color': '#92D050',
        })
        row_format_signer = workbook.add_format({
            'font_size': 11,
            'num_format': '#,##0',
        })
        row += 1
        sheet.write_string(row, 0, 'Бюджет ' + signer + ':', row_format_signer)
        for company in data:
            for center in data[company]:
                for project, content in data[company][center].items():
                    # печатаем строки проектов
                    row += 1
                    sheet.set_row(row, False, False, {'hidden': 1, 'level': max_level + 1})
                    cur_row_format = row_format
                    cur_row_format_number = row_format_number
                    column = 0
                    if content['info']['factoring']:
                        sheet.write_string(row, column, 'да', factoring_row_format)
                    else:
                        sheet.write_string(row, column, 'нет', cur_row_format)
                    column += 1
                    sheet.write_string(row, column, content['info']['key_account_manager_id'], cur_row_format)
                    column += 1
                    sheet.write_string(row, column, content['info']['partner_id'], cur_row_format)
                    column += 1
                    sheet.write_string(row, column, content['info']['essence_project'], cur_row_format)
                    column += 1
                    sheet.write_string(row, column, content['info']['project_id'], cur_row_format)
                    column += 1
                    sheet.write_string(row, column, '', cur_row_format)
                    column += 1
                    self.print_row_values(workbook, sheet, row, column, content['periods'], periods_dict, start_column)
        row += 1
        return row

    def print_rows_summary(self, sheet, workbook, row, start_column, period, data, budgets, types):

        type_rus_name = {
            'fact': 'Факт',
            'commitment': 'Прогноз',
        }

        row_format = workbook.add_format({
            'border': 1,
            'font_size': 8,
            'text_wrap': True,
        })
        row_format_number = workbook.add_format({
            'border': 1,
            'font_size': 9,
            'align': 'center',
            'num_format': '#,##0;[red]-#,##0',
        })
        factoring_row_format = workbook.add_format({
            'border': 1,
            'font_size': 8,
            'fg_color': '#92D050',
        })
        forecast_format = workbook.add_format({
            'border': 2,
            'font_size': 12,
            'fg_color': '#d9d9d9',
        })
        forecast_format_number = workbook.add_format({
            'border': 2,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#d9d9d9',
            'num_format': '#,##0;[red]-#,##0',
        })
        factoring_format = workbook.add_format({
            'border': 1,
            'font_size': 8,
            'fg_color': '#EBF1DE',
        })
        factoring_format_number = workbook.add_format({
            'border': 1,
            'font_size': 11,
            'align': 'center',
            'fg_color': '#EBF1DE',
            'num_format': '#,##0;[red]-#,##0',
        })
        fact_format = workbook.add_format({
            'border': 2,
            'font_size': 12,
            'fg_color': '#EBF1DE',
        })
        fact_format_number = workbook.add_format({
            'border': 2,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#EBF1DE',
            'num_format': '#,##0;[red]-#,##0',
        })
        difference_format = workbook.add_format({
            'border': 2,
            'font_size': 12,
            'fg_color': '#ffff00',
        })
        difference_format_number = workbook.add_format({
            'border': 2,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#ffff00',
            'num_format': '#,##0;[red]-#,##0',
        })
        left_border_1 = workbook.add_format({
            'left': 1,
        })
        left_border_2 = workbook.add_format({
            'left': 2,
        })
        difference = {}
        total = 0
        for company in data[0]:
            for center in data[0][company]:
                for project, content in data[0][company][center].items():
                    column = start_column
                    amount = content['periods'][period][types[0]]
                    if amount:
                        sheet.set_row(row, False, False, {'level': 1})
                        difference.setdefault(project, {})
                        difference[project]['info'] = content['info']
                        difference[project]['amount'] = -amount
                        cur_row_format = row_format
                        cur_row_format_number = row_format_number
                        if content['info']['factoring']:
                            sheet.write_string(row, column, 'да', factoring_row_format)
                        else:
                            sheet.write_string(row, column, 'нет', cur_row_format)
                        column += 1
                        total += amount
                        sheet.write_number(row, column, amount, row_format_number)
                        column += 1
                        sheet.write_string(row, column, content['info']['key_account_manager_id'], cur_row_format)
                        column += 1
                        sheet.write_string(row, column, content['info']['partner_id'], cur_row_format)
                        column += 1
                        sheet.write_string(row, column, content['info']['essence_project'], cur_row_format)
                        column += 1
                        sheet.write_string(row, column, '', cur_row_format)
                        sheet.write(row, column + 1, '', left_border_1)
                        row += 1
        actual_budget_date = budgets[0].date_actual if budgets[0].date_actual else datetime.now()
        sheet.write(row, start_column, type_rus_name[types[0]] + ' за ' + actual_budget_date.strftime('%d.%m'), forecast_format)
        sheet.merge_range(row, start_column + 1, row, start_column + 5, total, forecast_format_number)
        sheet.write(row, start_column + 6, '', left_border_2)
        row += 1
        total = 0
        total_w_factoring = 0
        for company in data[1]:
            for center in data[1][company]:
                for project, content in data[1][company][center].items():
                    column = start_column
                    amount = content['periods'][period][types[1]]
                    if amount:
                        sheet.set_row(row, False, False, {'level': 1})
                        if project in difference.keys():
                            difference[project]['amount'] += amount
                        else:
                            difference.setdefault(project, {})
                            difference[project]['info'] = content['info']
                            difference[project]['amount'] = amount
                        cur_row_format = row_format
                        cur_row_format_number = row_format_number
                        if content['info']['factoring']:
                            sheet.write_string(row, column, 'да', factoring_row_format)
                        else:
                            sheet.write_string(row, column, 'нет', cur_row_format)
                        column += 1
                        if content['info']['factoring']:
                            total_w_factoring += amount
                        else:
                            total += amount
                        sheet.write_number(row, column, amount, row_format_number)
                        column += 1
                        sheet.write_string(row, column, content['info']['key_account_manager_id'], cur_row_format)
                        column += 1
                        sheet.write_string(row, column, content['info']['partner_id'], cur_row_format)
                        column += 1
                        sheet.write_string(row, column, content['info']['essence_project'], cur_row_format)
                        column += 1
                        sheet.write_string(row, column, '', cur_row_format)
                        sheet.write(row, column + 1, '', left_border_1)
                        row += 1
        actual_budget_date = budgets[1].date_actual if budgets[1].date_actual else datetime.now()
        if types[1] == 'fact':
            sheet.set_row(row, False, False, {'level': 1})
            sheet.write(row, start_column, 'Факторинг', factoring_format)
            sheet.merge_range(row, start_column + 1, row, start_column + 5, total_w_factoring, factoring_format_number)
            sheet.write(row, start_column + 6, '', left_border_1)
            row += 1
            sheet.set_row(row, False, False, {'level': 1})
            sheet.write(row, start_column, 'Без факторинга', factoring_format)
            sheet.merge_range(row, start_column + 1, row, start_column + 5, total, factoring_format_number)
            sheet.write(row, start_column + 6, '', left_border_1)
            row += 1
            sheet.write(row, start_column, type_rus_name[types[1]] + ' за ' + actual_budget_date.strftime('%d.%m'), fact_format)
            sheet.merge_range(
                row,
                start_column + 1,
                row,
                start_column + 5,
                f'=({xl_col_to_name(start_column + 1)}{row}+{xl_col_to_name(start_column + 1)}{row - 1})',
                fact_format_number,)
            sheet.write(row, start_column + 6, '', left_border_2)
            row += 1
        else:
            sheet.write(row, start_column, type_rus_name[types[1]] + ' за ' + actual_budget_date.strftime('%d.%m'), forecast_format)
            sheet.merge_range(row, start_column + 1, row, start_column + 5, total, forecast_format_number)
            sheet.write(row, start_column + 6, '', left_border_2)
            row += 1
        total = 0
        for project, content in difference.items():
            column = start_column
            amount = content['amount']
            if abs(amount) > 0.1:
                sheet.set_row(row, False, False, {'level': 1})
                cur_row_format = row_format
                cur_row_format_number = row_format_number
                if content['info']['factoring']:
                    sheet.write_string(row, column, 'да', factoring_row_format)
                else:
                    sheet.write_string(row, column, 'нет', cur_row_format)
                column += 1
                sheet.write_number(row, column, amount, row_format_number)
                total += amount
                column += 1
                sheet.write_string(row, column, content['info']['key_account_manager_id'], cur_row_format)
                column += 1
                sheet.write_string(row, column, content['info']['partner_id'], cur_row_format)
                column += 1
                sheet.write_string(row, column, content['info']['essence_project'], cur_row_format)
                column += 1
                sheet.write_string(row, column, '', cur_row_format)
                sheet.write(row, column + 1, '', left_border_1)
                row += 1
        sheet.write(row, start_column, 'Разница', difference_format)
        sheet.merge_range(row, start_column + 1, row, start_column + 5, total, difference_format_number)
        sheet.write(row, start_column + 6, '', left_border_2)
        row += 1
        return row

    def print_week_summary(self, workbook, sheet, row, col, company, centers_to_exclude, actual_date, budget, period, financial_indicators, previous_budget):
        italic_format = workbook.add_format({
            'font_size': 12,
            'align': 'center',
            'italic': True,
        })
        border_format = workbook.add_format({
            'font_size': 12,
            'border': 1,
            'text_wrap': True,
        })
        bold_format = workbook.add_format({
            'font_size': 12,
            'align': 'left',
            'bold': True,
        })
        head_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
        })
        plan_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#fff2cc',
        })
        plan_format_number = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#fff2cc',
            'num_format': '#,##0;[red]-#,##0',
        })
        fact_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#EBF1DE',
        })
        fact_format_number = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#EBF1DE',
            'num_format': '#,##0;[red]-#,##0',
        })
        fact_format_percent = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#EBF1DE',
            'color': '#ff0000',
            'num_format': '0%',
        })
        forecast_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'fg_color': '#d9d9d9',
        })
        forecast_format_number = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#d9d9d9',
            'num_format': '#,##0;[red]-#,##0',
        })
        commitment_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'fg_color': '#B8CCE4',
        })
        commitment_format_number = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#B8CCE4',
            'num_format': '#,##0',
        })
        percent_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'bold': True,
            'color': '#ff0000',
            'num_format': '0%',
        })
        difference_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'left',
            'bold': True,
        })
        difference_format_number = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'bold': True,
            'fg_color': '#ffff00',
            'num_format': '#,##0;[red]-#,##0',
        })
        fact_structure_head_format = workbook.add_format({
            'border': 1,
            'top': 2,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#ffff00',
        })
        fact_structure_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#EBF1DE',
            'num_format': '#,##0',
        })

        fact = commitment = 0
        for i in financial_indicators:
            if i.forecast_probability_id and i.commercial_budget_id.id == previous_budget.id:
                commitment += i.amount - i.distribution
                factoring_is_present = any(d.factoring for d in i.fact_cash_flow_id.distribution_cash_ids)
            elif not i.forecast_probability_id and i.commercial_budget_id.id == budget.id:
                fact += i.amount

        sheet.set_column(col, col, 1)
        col += 1
        sheet.set_column(col, col + 3, 18)

        sheet.merge_range(
            row,
            col,
            row,
            col + 3,
            '*Неделя',
            italic_format
        )
        row += 1
        period_str = period[0].strftime('%d.%m') + '-' + period[1].strftime('%d.%m') + ' (на ' + actual_date.strftime('%d.%m.%Y') + ')'
        sheet.merge_range(row, col, row, col + 3, period_str, head_format)
        row += 1
        sheet.merge_range(row, col, row + 1, col, 'План', plan_format)
        sheet.merge_range(row, col + 1, row + 1, col + 1, 'Факт', fact_format)
        sheet.merge_range(row, col + 2, row, col + 3, 'Прогноз', forecast_format)
        sheet.write(row + 1, col + 2, 'Обяз-во', commitment_format)
        sheet.write(row + 1, col + 3, 'Факт+Обяз-во', forecast_format)
        row += 2

        sheet.write(row, col, commitment, plan_format_number)
        sheet.write(row, col + 1, fact, fact_format_number)
        sheet.write(row, col + 2, commitment, commitment_format_number)
        sheet.write_formula(
            row,
            col + 3,
            f'=({xl_col_to_name(col + 1)}{row + 1}+{xl_col_to_name(col + 2)}{row + 1})',
            forecast_format_number
        )
        row += 1

        sheet.write_formula(
            row,
            col + 1,
            f'=IFERROR({xl_col_to_name(col + 1)}{row}/{xl_col_to_name(col)}{row}," ")',
            percent_format,
        )
        sheet.write_formula(
            row,
            col + 3,
            f'=IFERROR({xl_col_to_name(col + 3)}{row}/{xl_col_to_name(col)}{row}," ")',
            percent_format,
        )
        row += 1

        sheet.merge_range(row, col, row, col + 2, 'Разница с Планом', difference_format)
        sheet.write_formula(
            row,
            col + 3,
            f'=({xl_col_to_name(col + 1)}{row - 1}-{xl_col_to_name(col)}{row - 1})',
            difference_format_number,
        )
        row += 1

        sheet.merge_range(row, col, row, col + 3, 'Об-во состоит из:', bold_format)
        row += 1
        sheet.merge_range(row, col, row, col + 2, 'Прогноз (неделя ' + period[0].strftime('%d.%m') + '-' + period[1].strftime('%d.%m') + ') (без факта)', head_format)
        row += 3

        previous_week_start = date_utils.end_of(actual_date - timedelta(weeks=1), 'week')
        previous_week_end = date_utils.end_of(actual_date - timedelta(weeks=1), 'week')
        week_before_end = date_utils.end_of(actual_date - timedelta(weeks=2), 'week')
        budget_before_id = self.env['project_budget.commercial_budget'].search([
            ('date_actual', '<=', week_before_end),
        ], limit=1, order='date_actual desc').id

        before_financial_indicators = self.env['project.budget.financial.indicator'].search([
            ('commercial_budget_id', 'in', (budget_before_id, budget.id)),
            ('type', '=', 'cash_flow'),
            ('date', '>=', previous_week_start),
            ('date', '<=', previous_week_end),
            ('project_id.signer_id', '=', company.id),
            '|', ('forecast_probability_id', '=', False),
            ('forecast_probability_id.id', '=', self.env.ref('project_budget_nkk.project_budget_forecast_probability_commitment').id),
        ])

        fact_before = commitment_before = 0
        for i in before_financial_indicators:
            if i.forecast_probability_id and i.commercial_budget_id.id == budget_before_id:
                commitment_before += i.amount - i.distribution
                factoring_is_present = any(d.factoring for d in i.fact_cash_flow_id.distribution_cash_ids)
            elif not i.forecast_probability_id and i.commercial_budget_id.id == budget.id:
                fact_before += i.amount


        sheet.merge_range(row, col, row, col + 3,
                          'Структура ФАКТА (' + previous_week_start.strftime('%d.%m') + '-'
                          + previous_week_end.strftime('%d.%m') + ')', fact_structure_head_format)
        row += 1
        sheet.merge_range(row, col, row + 1, col + 1, 'План', plan_format)
        sheet.merge_range(row, col + 2, row + 1, col + 2, 'Факт', fact_format)
        sheet.merge_range(row, col + 3, row + 1, col + 3, '%', fact_format)
        sheet.merge_range(row + 2, col, row + 2, col + 1, commitment_before, plan_format_number)
        sheet.write(row + 2, col + 2, fact_before, fact_format_number)
        sheet.write_formula(
            row + 2,
            col + 3,
            f'=IFERROR({xl_col_to_name(col + 2)}{row + 3}/{xl_col_to_name(col)}{row + 3}," ")',
            fact_format_percent
        )
        return row

    def print_week_fact(self, workbook, sheet, row, col, company, actual_date, budget, period, financial_indicators):
        border_format = workbook.add_format({
            'font_size': 12,
            'border': 1,
            'text_wrap': True,
        })
        difference_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'left',
            'bold': True,
        })
        difference_format_number = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'bold': True,
            'fg_color': '#ffff00',
            'num_format': '#,##0;[red]-#,##0',
        })
        fact_structure_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#EBF1DE',
            'num_format': '#,##0',
        })

        sheet.merge_range(row, col, row, col + 2, 'Разница с Планом', difference_format)
        sheet.write_formula(
            row,
            col + 3,
            f'=({xl_col_to_name(col + 2)}{row}-{xl_col_to_name(col)}{row})',
            difference_format_number,
        )
        row += 2
        sheet.merge_range(row, col, row, col + 3, 'ФАКТ', fact_structure_format)
        row += 1
        sheet.merge_range(row, col, row, col + 1, 'СА', difference_format)
        sum_row = row
        row += 1
        sheet.merge_range(row, col, row, col + 1, 'ВГО', difference_format)

        vgo_fact = self.get_vgo_fact_sum(financial_indicators, company, budget, period)

        sheet.merge_range(row, col + 2, row, col + 3, vgo_fact, fact_structure_format)
        row += 1
        sheet.merge_range(row, col, row, col + 1, 'Итого:', difference_format)
        sheet.merge_range(
            row,
            col + 2,
            row,
            col + 3,
            f'=({xl_col_to_name(col + 2)}{row}+{xl_col_to_name(col + 2)}{row - 1})',
            fact_structure_format
        )
        row += 1

        fact_rows = False
        for i in financial_indicators:
            if not i.forecast_probability_id and i.commercial_budget_id.id == budget.id:
                sheet.write(row, col, i.key_account_manager_id.name, border_format)
                sheet.write(row, col + 1, i.customer_id.name, border_format)
                sheet.write(row, col + 2, i.amount, border_format)
                for d in i.fact_cash_flow_id.distribution_cash_ids:
                    if d.planned_cash_flow_id.sum_cash == i.amount:
                        sheet.set_row(row, False, False, {'hidden': 1, 'level': 1})
                        if d.planned_cash_flow_id.date_cash == i.date:
                            sheet.write(row, col + 3, 'по плану', border_format)
                        elif d.planned_cash_flow_id.date_cash > i.date:
                            sheet.write(row, col + 3, 'ранее плана', border_format)
                        elif d.planned_cash_flow_id.date_cash < i.date:
                            sheet.write(row, col + 3, 'позже плана', border_format)
                row += 1
                fact_rows = True

        if fact_rows:
            sheet.merge_range(
                sum_row,
                col + 2,
                sum_row,
                col + 3,
                f'=sum({xl_col_to_name(col + 2)}{sum_row + 4}:{xl_col_to_name(col + 2)}{row}' + ')',
                fact_structure_format
            )
        else:
            sheet.merge_range(sum_row, col + 2, sum_row, col + 3, 0, fact_structure_format)
        return row

    def print_week_changes(self, workbook, sheet, row, col, company, actual_date, budget, period, financial_indicators):
        border_format = workbook.add_format({
            'font_size': 12,
            'border': 1,
            'text_wrap': True,
        })
        difference_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'left',
            'bold': True,
        })
        difference_format_number = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'bold': True,
            'fg_color': '#ffff00',
            'num_format': '#,##0;[red]-#,##0',
        })
        fact_structure_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#EBF1DE',
            'num_format': '#,##0',
        })

        sheet.merge_range(row, col, row, col + 2, 'Разница с Планом', difference_format)
        sheet.write_formula(
            row,
            col + 3,
            f'=({xl_col_to_name(col + 2)}{row}-{xl_col_to_name(col)}{row})',
            difference_format_number,
        )
        row += 2
        sheet.merge_range(row, col, row, col + 3, 'ФАКТ', fact_structure_format)
        row += 1
        sheet.merge_range(row, col, row, col + 1, 'СА', difference_format)
        sum_row = row
        row += 1
        sheet.merge_range(row, col, row, col + 1, 'ВГО', difference_format)

        vgo_fact = self.get_vgo_fact_sum(financial_indicators, company, budget, period)

        sheet.merge_range(row, col + 2, row, col + 3, vgo_fact, fact_structure_format)
        row += 1
        sheet.merge_range(row, col, row, col + 1, 'Итого:', difference_format)
        sheet.merge_range(
            row,
            col + 2,
            row,
            col + 3,
            f'=({xl_col_to_name(col + 2)}{row}+{xl_col_to_name(col + 2)}{row - 1})',
            fact_structure_format
        )
        row += 1

        fact_rows = False
        for i in financial_indicators:
            if not i.forecast_probability_id and i.commercial_budget_id.id == budget.id:
                sheet.write(row, col, i.key_account_manager_id.name, border_format)
                sheet.write(row, col + 1, i.customer_id.name, border_format)
                sheet.write(row, col + 2, i.amount, border_format)
                for d in i.fact_cash_flow_id.distribution_cash_ids:
                    if d.planned_cash_flow_id.sum_cash == i.amount:
                        sheet.set_row(row, False, False, {'hidden': 1, 'level': 1})
                        if d.planned_cash_flow_id.date_cash == i.date:
                            sheet.write(row, col + 3, 'по плану', border_format)
                        elif d.planned_cash_flow_id.date_cash > i.date:
                            sheet.write(row, col + 3, 'ранее плана', border_format)
                        elif d.planned_cash_flow_id.date_cash < i.date:
                            sheet.write(row, col + 3, 'позже плана', border_format)
                row += 1
                fact_rows = True

        if fact_rows:
            sheet.merge_range(
                sum_row,
                col + 2,
                sum_row,
                col + 3,
                f'=sum({xl_col_to_name(col + 2)}{sum_row + 4}:{xl_col_to_name(col + 2)}{row}' + ')',
                fact_structure_format
            )
        else:
            sheet.merge_range(sum_row, col + 2, sum_row, col + 3, 0, fact_structure_format)
        return row

    def print_month_fact(self, workbook, sheet, row, col, company, actual_date, budget, period, financial_indicators):
        border_format = workbook.add_format({
            'font_size': 12,
            'border': 1,
            'text_wrap': True,
        })
        difference_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'left',
            'bold': True,
        })
        difference_format_number = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'bold': True,
            'fg_color': '#ffff00',
            'num_format': '#,##0;[red]-#,##0',
        })
        fact_structure_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#EBF1DE',
            'num_format': '#,##0',
        })
        sheet.merge_range(row, col, row, col + 2, 'Разница с Планом', difference_format)
        sheet.write_formula(
            row,
            col + 3,
            f'=({xl_col_to_name(col + 2)}{row}-{xl_col_to_name(col)}{row})',
            difference_format_number,
        )
        row += 2
        sheet.merge_range(row, col, row, col + 3, 'ФАКТ', fact_structure_format)
        row += 1
        sheet.merge_range(row, col, row, col + 1, 'СА', difference_format)
        sum_row = row
        row += 1
        sheet.merge_range(row, col, row, col + 1, 'ВГО', difference_format)

        vgo_fact = self.get_vgo_fact_sum(financial_indicators, company, budget, period)

        sheet.merge_range(row, col + 2, row, col + 3, vgo_fact, fact_structure_format)
        row += 1
        sheet.merge_range(row, col, row, col + 1, 'Итого:', difference_format)
        sheet.merge_range(
            row,
            col + 2,
            row,
            col + 3,
            f'=({xl_col_to_name(col + 2)}{row}+{xl_col_to_name(col + 2)}{row - 1})',
            fact_structure_format
        )
        row += 1

        fact_rows = False
        for i in financial_indicators:
            if not i.forecast_probability_id and i.commercial_budget_id.id == budget.id:
                sheet.write(row, col, i.key_account_manager_id.name, border_format)
                sheet.write(row, col + 1, i.customer_id.name, border_format)
                sheet.write(row, col + 2, i.amount, border_format)
                for d in i.fact_cash_flow_id.distribution_cash_ids:
                    if d.planned_cash_flow_id.sum_cash == i.amount:
                        sheet.set_row(row, False, False, {'hidden': 1, 'level': 1})
                        if d.planned_cash_flow_id.date_cash == i.date:
                            sheet.write(row, col + 3, 'по плану', border_format)
                        elif d.planned_cash_flow_id.date_cash > i.date:
                            sheet.write(row, col + 3, 'ранее плана', border_format)
                        elif d.planned_cash_flow_id.date_cash < i.date:
                            sheet.write(row, col + 3, 'позже плана', border_format)
                row += 1
                fact_rows = True

        if fact_rows:
            sheet.merge_range(
                sum_row,
                col + 2,
                sum_row,
                col + 3,
                f'=sum({xl_col_to_name(col + 2)}{sum_row + 4}:{xl_col_to_name(col + 2)}{row}' + ')',
                fact_structure_format
            )
        else:
            sheet.merge_range(sum_row, col + 2, sum_row, col + 3, 0, fact_structure_format)
        return row

    def print_month_summary(self, workbook, sheet, row, col, company, centers_to_exclude, actual_date, budget, period, financial_indicators, previous_budget):
        italic_format = workbook.add_format({
            'font_size': 12,
            'align': 'center',
            'italic': True,
        })
        border_format = workbook.add_format({
            'font_size': 12,
            'border': 1,
            'text_wrap': True,
        })
        bold_format = workbook.add_format({
            'font_size': 12,
            'align': 'left',
            'bold': True,
        })
        head_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
        })
        plan_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#fff2cc',
        })
        plan_format_number = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#fff2cc',
            'num_format': '#,##0;[red]-#,##0',
        })
        fact_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#EBF1DE',
        })
        fact_format_number = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#EBF1DE',
            'num_format': '#,##0;[red]-#,##0',
        })
        fact_format_percent = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#EBF1DE',
            'color': '#ff0000',
            'num_format': '0%',
        })
        forecast_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'fg_color': '#d9d9d9',
        })
        forecast_format_number = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#d9d9d9',
            'num_format': '#,##0;[red]-#,##0',
        })
        commitment_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'fg_color': '#B8CCE4',
        })
        commitment_format_number = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#B8CCE4',
            'num_format': '#,##0',
        })
        percent_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'bold': True,
            'color': '#ff0000',
            'num_format': '0%',
        })
        difference_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'left',
            'bold': True,
        })
        difference_format_number = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'bold': True,
            'fg_color': '#ffff00',
            'num_format': '#,##0;[red]-#,##0',
        })
        fact_structure_head_format = workbook.add_format({
            'border': 1,
            'top': 2,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#ffff00',
        })
        fact_structure_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#EBF1DE',
            'num_format': '#,##0',
        })

        current_week_start, current_week_end = self.get_dates_from_week(
            actual_date.isocalendar()[1],
            actual_date.isocalendar()[0],
        )

        fact = commitment = 0
        for i in financial_indicators:
            if i.forecast_probability_id and i.commercial_budget_id.id == previous_budget.id and current_week_start <= i.date <= current_week_end:
                commitment += i.amount - i.distribution
            if i.forecast_probability_id and i.commercial_budget_id.id == budget.id and current_week_end < i.date <= period[1].date():
                commitment += i.amount - i.distribution
            elif not i.forecast_probability_id and i.commercial_budget_id.id == budget.id:
                fact += i.amount
                factoring_is_present = any(d.factoring for d in i.fact_cash_flow_id.distribution_cash_ids)

        sheet.set_column(col, col, 1)
        col += 1
        sheet.set_column(col, col + 3, 18)

        sheet.merge_range(
            row,
            col,
            row,
            col + 3,
            '*Месяц',
            italic_format
        )
        row += 1
        period_str = self.month_rus_name[actual_date.month - 1] + ' ' + str(actual_date.year) + ' (на ' + actual_date.strftime('%d.%m.%Y') + ')'
        sheet.merge_range(row, col, row, col + 3, period_str, head_format)
        row += 1
        sheet.merge_range(row, col, row + 1, col, 'План', plan_format)
        sheet.merge_range(row, col + 1, row + 1, col + 1, 'Факт', fact_format)
        sheet.merge_range(row, col + 2, row, col + 3, 'Прогноз', forecast_format)
        sheet.write(row + 1, col + 2, 'Обяз-во', commitment_format)
        sheet.write(row + 1, col + 3, 'Факт+Обяз-во', forecast_format)
        row += 2

        sheet.write(row, col, commitment, plan_format_number)
        sheet.write(row, col + 1, fact, fact_format_number)
        sheet.write(row, col + 2, commitment, commitment_format_number)
        sheet.write_formula(
            row,
            col + 3,
            f'=({xl_col_to_name(col + 1)}{row + 1}+{xl_col_to_name(col + 2)}{row + 1})',
            forecast_format_number
        )
        row += 1

        sheet.write_formula(
            row,
            col + 1,
            f'=IFERROR({xl_col_to_name(col + 1)}{row}/{xl_col_to_name(col)}{row}," ")',
            percent_format,
        )
        sheet.write_formula(
            row,
            col + 3,
            f'=IFERROR({xl_col_to_name(col + 3)}{row}/{xl_col_to_name(col)}{row}," ")',
            percent_format,
        )
        row += 1

        sheet.merge_range(row, col, row, col + 2, 'Разница с Планом', difference_format)
        sheet.write_formula(
            row,
            col + 3,
            f'=({xl_col_to_name(col + 1)}{row - 1}-{xl_col_to_name(col)}{row - 1})',
            difference_format_number,
        )
        row += 1

        sheet.merge_range(row, col, row, col + 3, 'Об-во состоит из:', bold_format)
        row += 1
        sheet.merge_range(row, col, row, col + 2, 'Прогноз (' + self.month_rus_name[actual_date.month - 1] + ') (без факта)', head_format)

        row += 3

        previous_month_start = date_utils.start_of(actual_date.replace(day=1) - timedelta(days=1), 'month')
        previous_month_end = date_utils.end_of(actual_date.replace(day=1) - timedelta(days=1), 'month')

        budget_before_id = self.env['project_budget.commercial_budget'].search([
            ('date_actual', '<', previous_month_start),
        ], limit=1, order='date_actual desc').id

        before_financial_indicators = self.env['project.budget.financial.indicator'].search([
            ('commercial_budget_id', 'in', (budget_before_id, budget.id)),
            ('type', '=', 'cash_flow'),
            ('date', '>=', previous_month_start),
            ('date', '<=', previous_month_end),
            ('project_id.signer_id', '=', company.id),
            '|', ('forecast_probability_id', '=', False),
            ('forecast_probability_id.id', '=',
             self.env.ref('project_budget_nkk.project_budget_forecast_probability_commitment').id),
        ])

        fact_before = commitment_before = 0
        for i in before_financial_indicators:
            if i.forecast_probability_id and i.commercial_budget_id.id == budget_before_id:
                commitment_before += i.amount - i.distribution
                factoring_is_present = any(d.factoring for d in i.fact_cash_flow_id.distribution_cash_ids)
            elif not i.forecast_probability_id and i.commercial_budget_id.id == budget.id:
                fact_before += i.amount

        sheet.merge_range(row, col, row, col + 3,
                          'Структура ФАКТА (' + self.month_rus_name[previous_month_start.month - 1] + ')', fact_structure_head_format)
        row += 1
        sheet.merge_range(row, col, row + 1, col + 1, 'План', plan_format)
        sheet.merge_range(row, col + 2, row + 1, col + 2, 'Факт', fact_format)
        sheet.merge_range(row, col + 3, row + 1, col + 3, '%', fact_format)
        sheet.merge_range(row + 2, col, row + 2, col + 1, commitment_before, plan_format_number)
        sheet.write(row + 2, col + 2, fact_before, fact_format_number)
        sheet.write_formula(
            row + 2,
            col + 3,
            f'=IFERROR({xl_col_to_name(col + 2)}{row + 3}/{xl_col_to_name(col)}{row + 3}," ")',
            fact_format_percent
        )
        return row

    def print_quarter_fact(self,workbook, sheet, row, col, company, actual_date, budget, period, financial_indicators):
        border_format = workbook.add_format({
            'font_size': 12,
            'border': 1,
            'text_wrap': True,
        })
        plan_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#C5D9F1',
        })
        plan_format_number = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#C5D9F1',
            'num_format': '#,##0;[red]-#,##0',
        })
        fact_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#EBF1DE',
        })
        fact_format_number = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#EBF1DE',
            'num_format': '#,##0;[red]-#,##0',
        })
        fact_format_percent = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#EBF1DE',
            'color': '#ff0000',
            'num_format': '0%',
        })
        commitment_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#B8CCE4',
        })
        commitment_format_number = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#B8CCE4',
            'num_format': '#,##0',
        })
        difference_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'left',
            'bold': True,
        })
        difference_format_number = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'bold': True,
            'fg_color': '#ffff00',
            'num_format': '#,##0;[red]-#,##0',
        })
        fact_structure_head_format = workbook.add_format({
            'border': 1,
            'top': 2,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#ffff00',
        })
        fact_structure_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#EBF1DE',
            'num_format': '#,##0',
        })
        current_quarter_start = date_utils.start_of(actual_date, 'quarter')
        current_quarter_end = date_utils.end_of(actual_date, 'quarter')

        budget_before_id = self.env['project_budget.commercial_budget'].search([
            ('date_actual', '<', current_quarter_start),
        ], limit=1, order='date_actual desc').id

        before_financial_indicators = self.env['project.budget.financial.indicator'].search([
            ('commercial_budget_id', 'in', (budget_before_id, budget.id)),
            ('type', '=', 'cash_flow'),
            ('date', '>=', current_quarter_start),
            ('date', '<=', current_quarter_end),
            ('project_id.signer_id', '=', company.id),
            '|', ('forecast_probability_id', '=', False),
            ('forecast_probability_id.id', '=',
             self.env.ref('project_budget_nkk.project_budget_forecast_probability_commitment').id),
        ])

        fact_before = commitment_before = 0
        for i in before_financial_indicators:
            if i.forecast_probability_id and i.commercial_budget_id.id == budget_before_id:
                commitment_before += i.amount - i.distribution
                factoring_is_present = any(d.factoring for d in i.fact_cash_flow_id.distribution_cash_ids)
            elif not i.forecast_probability_id and i.commercial_budget_id.id == budget.id:
                fact_before += i.amount

        sheet.merge_range(row, col, row, col + 3,
                          'Структура ФАКТА (' + 'Q' + str((actual_date.month - 1) // 3 + 1) + ')',
                          fact_structure_head_format)
        row += 1
        sheet.merge_range(row, col, row + 1, col, f'={xl_col_to_name(col)}{3}', plan_format)
        sheet.merge_range(row, col + 1, row + 1, col + 1, 'Факт', fact_format)
        sheet.merge_range(row, col + 2, row + 1, col + 2, 'Обязательство', commitment_format)
        sheet.merge_range(row, col + 3, row + 1, col + 3, '%', fact_format)
        sheet.write_formula(row + 2, col, f'={xl_col_to_name(col)}{5}', plan_format_number)
        sheet.write_formula(row + 2, col + 1, f'={xl_col_to_name(col + 1)}{5}', fact_format_number)
        sheet.write_formula(row + 2, col + 2, f'={xl_col_to_name(col + 2)}{5}', commitment_format_number)
        sheet.write_formula(
            row + 2,
            col + 3,
            f'=IFERROR(({xl_col_to_name(col + 2)}{row + 3}+{xl_col_to_name(col + 1)}{row + 3})/{xl_col_to_name(col)}{row + 3}," ")',
            fact_format_percent
        )
        row += 3

        sheet.merge_range(row, col, row, col + 2, 'Разница с Планом', difference_format)
        sheet.write_formula(
            row,
            col + 3,
            f'=({xl_col_to_name(col + 2)}{row}+{xl_col_to_name(col + 1)}{row}-{xl_col_to_name(col)}{row})',
            difference_format_number,
        )
        row += 2
        sheet.merge_range(row, col, row, col + 3, 'ФАКТ', fact_structure_format)
        row += 1
        sheet.merge_range(row, col, row, col + 1, 'СА', difference_format)
        sum_row = row
        row += 1
        sheet.merge_range(row, col, row, col + 1, 'ВГО', difference_format)

        vgo_fact = self.get_vgo_fact_sum(financial_indicators, company, budget, period)

        sheet.merge_range(row, col + 2, row, col + 3, vgo_fact, fact_structure_format)
        row += 1
        sheet.merge_range(row, col, row, col + 1, 'Итого:', difference_format)
        sheet.merge_range(
            row,
            col + 2,
            row,
            col + 3,
            f'=({xl_col_to_name(col + 2)}{row}+{xl_col_to_name(col + 2)}{row - 1})',
            fact_structure_format
        )
        row += 1

        fact_rows = False
        for i in financial_indicators:
            if not i.forecast_probability_id and i.commercial_budget_id.id == budget.id:
                sheet.write(row, col, i.key_account_manager_id.name, border_format)
                sheet.write(row, col + 1, i.customer_id.name, border_format)
                sheet.write(row, col + 2, i.amount, border_format)
                for d in i.fact_cash_flow_id.distribution_cash_ids:
                    if d.planned_cash_flow_id.sum_cash == i.amount:
                        sheet.set_row(row, False, False, {'hidden': 1, 'level': 1})
                        if d.planned_cash_flow_id.date_cash == i.date:
                            sheet.write(row, col + 3, 'по плану', border_format)
                        elif d.planned_cash_flow_id.date_cash > i.date:
                            sheet.write(row, col + 3, 'ранее плана', border_format)
                        elif d.planned_cash_flow_id.date_cash < i.date:
                            sheet.write(row, col + 3, 'позже плана', border_format)
                row += 1
                fact_rows = True

        if fact_rows:
            sheet.merge_range(
                sum_row,
                col + 2,
                sum_row,
                col + 3,
                f'=sum({xl_col_to_name(col + 2)}{sum_row + 4}:{xl_col_to_name(col + 2)}{row}' + ')',
                fact_structure_format
            )
        else:
            sheet.merge_range(sum_row, col + 2, sum_row, col + 3, 0, fact_structure_format)
        return row

    def print_quarter_summary(self, workbook, sheet, row, col, company, centers_to_exclude, actual_date, budget, period, financial_indicators, previous_budget):
        italic_format = workbook.add_format({
            'font_size': 12,
            'align': 'center',
            'italic': True,
        })
        bold_format = workbook.add_format({
            'font_size': 12,
            'align': 'left',
            'bold': True,
        })
        border_format = workbook.add_format({
            'font_size': 12,
            'border': 1,
            'text_wrap': True,
        })
        head_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
        })
        plan_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#C5D9F1',
        })
        plan_format_number = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#C5D9F1',
            'num_format': '#,##0;[red]-#,##0',
        })
        fact_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#EBF1DE',
        })
        fact_format_number = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#EBF1DE',
            'num_format': '#,##0;[red]-#,##0',
        })
        fact_format_percent = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#EBF1DE',
            'color': '#ff0000',
            'num_format': '0%',
        })
        forecast_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'fg_color': '#d9d9d9',
        })
        forecast_format_number = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#d9d9d9',
            'num_format': '#,##0;[red]-#,##0',
        })
        commitment_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#B8CCE4',
        })
        commitment_format_number = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#B8CCE4',
            'num_format': '#,##0',
        })
        percent_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'bold': True,
            'color': '#ff0000',
            'num_format': '0%',
        })
        difference_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'left',
            'bold': True,
        })
        difference_format_number = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'bold': True,
            'fg_color': '#ffff00',
            'num_format': '#,##0;[red]-#,##0',
        })
        fact_structure_head_format = workbook.add_format({
            'border': 1,
            'top': 2,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#ffff00',
        })
        fact_structure_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#EBF1DE',
            'num_format': '#,##0',
        })

        plans, use_6_6_plan = self.get_company_plans(actual_date, company, centers_to_exclude)
        current_week_start = date_utils.start_of(actual_date, 'week')
        current_week_end = date_utils.end_of(actual_date, 'week')
        fact = commitment = 0
        for i in financial_indicators:
            if i.forecast_probability_id and i.commercial_budget_id.id == previous_budget.id and current_week_start.date() <= i.date <= current_week_end.date():
                commitment += i.amount - i.distribution
            if i.forecast_probability_id and i.commercial_budget_id.id == budget.id and current_week_end.date() < i.date <= period[1].date():
                commitment += i.amount - i.distribution
            elif not i.forecast_probability_id and i.commercial_budget_id.id == budget.id:
                fact += i.amount
                factoring_is_present = any(d.factoring for d in i.fact_cash_flow_id.distribution_cash_ids)

        sheet.set_column(col, col, 1)
        col += 1
        sheet.set_column(col, col + 3, 18)

        sheet.merge_range(
            row,
            col,
            row,
            col + 3,
            '*Квартал',
            italic_format
        )
        row += 1
        period_str = 'Q' + str((actual_date.month - 1) // 3 + 1) + ' (на ' + actual_date.strftime('%d.%m.%Y') + ')'
        sheet.merge_range(row, col, row, col + 3, period_str, head_format)
        row += 1
        sheet.merge_range(row, col, row + 1, col, plans['quarter_plan']['name'], plan_format)
        sheet.merge_range(row, col + 1, row + 1, col + 1, 'Факт', fact_format)
        sheet.merge_range(row, col + 2, row, col + 3, 'Прогноз', forecast_format)
        sheet.write(row + 1, col + 2, 'Обяз-во', commitment_format)
        sheet.write(row + 1, col + 3, 'Факт+Обяз-во', forecast_format)
        row += 2

        sheet.write(row, col, plans['quarter_plan']['amount'], plan_format_number)
        sheet.write(row, col + 1, fact, fact_format_number)
        sheet.write(row, col + 2, commitment, commitment_format_number)
        sheet.write_formula(
            row,
            col + 3,
            f'=({xl_col_to_name(col + 1)}{row + 1}+{xl_col_to_name(col + 2)}{row + 1})',
            forecast_format_number
        )
        row += 1

        sheet.write_formula(
            row,
            col + 1,
            f'=IFERROR({xl_col_to_name(col + 1)}{row}/{xl_col_to_name(col)}{row}," ")',
            percent_format,
        )
        sheet.write_formula(
            row,
            col + 3,
            f'=IFERROR({xl_col_to_name(col + 3)}{row}/{xl_col_to_name(col)}{row}," ")',
            percent_format,
        )
        row += 1

        sheet.merge_range(row, col, row, col + 2, 'Разница с Планом', difference_format)
        sheet.write_formula(
            row,
            col + 3,
            f'=({xl_col_to_name(col + 3)}{row - 1}-{xl_col_to_name(col)}{row - 1})',
            difference_format_number,
        )
        row += 1

        sheet.merge_range(row, col, row, col + 3, 'Об-во состоит из:', bold_format)
        row += 1
        sheet.merge_range(row, col, row, col + 2, 'Прогноз (Q' + str((actual_date.month - 1) // 3 + 1) + ') (без факта)', head_format)
        return row

    def print_year_summary(self, workbook, sheet, row, col, company, centers_to_exclude, actual_date, budget, period):
        italic_format = workbook.add_format({
            'font_size': 12,
            'align': 'center',
            'italic': True,
        })
        bold_format = workbook.add_format({
            'font_size': 12,
            'align': 'left',
            'bold': True,
        })
        head_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
        })
        plan_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#C5D9F1',
        })
        plan_format_number = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#C5D9F1',
            'num_format': '#,##0;[red]-#,##0',
        })
        fact_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#EBF1DE',
        })
        fact_format_number = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#EBF1DE',
            'num_format': '#,##0;[red]-#,##0',
        })
        forecast_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'fg_color': '#d9d9d9',
        })
        forecast_format_number = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#d9d9d9',
            'num_format': '#,##0;[red]-#,##0',
        })
        commitment_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'fg_color': '#B8CCE4',
        })
        commitment_format_number = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#B8CCE4',
            'num_format': '#,##0',
        })
        percent_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'bold': True,
            'color': '#ff0000',
            'num_format': '0%',
        })
        difference_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'left',
            'bold': True,
        })
        difference_format_number = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'bold': True,
            'fg_color': '#ffff00',
            'num_format': '#,##0;[red]-#,##0',
        })

        current_week_start, current_week_end = self.get_dates_from_week(
            actual_date.isocalendar()[1],
            actual_date.isocalendar()[0],
        )
        previous_week_number = (current_week_start - timedelta(weeks=1)).isocalendar()[1]
        previous_week_year = (current_week_start - timedelta(weeks=1)).isocalendar()[0]
        previous_week_start, previous_week_end = self.get_dates_from_week(previous_week_number, previous_week_year)
        previous_budget_id = self.env['project_budget.commercial_budget'].search([
            ('date_actual', '<=', previous_week_end),
        ], limit=1, order='date_actual desc').id

        financial_indicators = self.env['project.budget.financial.indicator'].search([
            ('commercial_budget_id', 'in', (previous_budget_id, budget.id)),
            ('type', '=', 'cash_flow'),
            ('date', '>=', period[0]),
            ('date', '<=', period[1]),
            ('project_id.signer_id', '=', company.id),
            '|', ('forecast_probability_id', '=', False),
            ('forecast_probability_id.id', '=', self.env.ref('project_budget_nkk.project_budget_forecast_probability_commitment').id),
        ])

        plans, use_6_6_plan = self.get_company_plans(actual_date, company, centers_to_exclude)

        fact = commitment = 0
        for i in financial_indicators:
            if i.forecast_probability_id and i.commercial_budget_id.id == previous_budget_id and current_week_start <= i.date <= current_week_end:
                commitment += i.amount - i.distribution
            if i.forecast_probability_id and i.commercial_budget_id.id == budget.id and current_week_end < i.date <= period[1].date():
                commitment += i.amount - i.distribution
            elif not i.forecast_probability_id and i.commercial_budget_id.id == budget.id:
                fact += i.amount
                factoring_is_present = any(d.factoring for d in i.fact_cash_flow_id.distribution_cash_ids)

        sheet.set_column(col, col, 1)
        col += 1
        sheet.set_column(col, col + 3, 18)

        sheet.merge_range(
            row,
            col,
            row,
            col + 3,
            '*Год',
            italic_format
        )
        row += 1
        period_str = str(actual_date.year) + ' (на ' + actual_date.strftime('%d.%m.%Y') + ')'
        sheet.merge_range(row, col, row, col + 3, period_str, head_format)
        row += 1
        sheet.merge_range(row, col, row + 1, col, plans['year_plan']['name'], plan_format)
        sheet.merge_range(row, col + 1, row + 1, col + 1, 'Факт', fact_format)
        sheet.merge_range(row, col + 2, row, col + 3, 'Прогноз', forecast_format)
        sheet.write(row + 1, col + 2, 'Обяз-во', commitment_format)
        sheet.write(row + 1, col + 3, 'Факт+Обяз-во', forecast_format)
        row += 2

        sheet.write(row, col, plans['year_plan']['amount'], plan_format_number)
        sheet.write(row, col + 1, plans['hy1_fact']['amount'] + fact, fact_format_number)
        sheet.write(row, col + 2, commitment, commitment_format_number)
        sheet.write_formula(
            row,
            col + 3,
            f'=({xl_col_to_name(col + 1)}{row + 1}+{xl_col_to_name(col + 2)}{row + 1})',
            forecast_format_number
        )
        row += 1

        sheet.write_formula(
            row,
            col + 1,
            f'=IFERROR({xl_col_to_name(col + 1)}{row}/{xl_col_to_name(col)}{row}," ")',
            percent_format,
        )
        sheet.write_formula(
            row,
            col + 3,
            f'=IFERROR({xl_col_to_name(col + 3)}{row}/{xl_col_to_name(col)}{row}," ")',
            percent_format,
        )
        row += 1

        sheet.merge_range(row, col, row, col + 2, 'Разница с Планом', difference_format)
        sheet.write_formula(
            row,
            col + 3,
            f'=({xl_col_to_name(col + 1)}{row - 1}-{xl_col_to_name(col)}{row - 1})',
            difference_format_number,
        )
        row += 1

        sheet.merge_range(row, col, row, col + 3, 'Об-во состоит из:', bold_format)
        row += 1
        sheet.merge_range(row, col, row, col + 2, 'Прогноз (' + str(actual_date.year) + ') (без факта)', head_format)
        return row

    def print_month_summary_old(self, workbook, sheet, row, start_column, company, centers_to_exclude, actual_date, budget, link):
        head_format = workbook.add_format({
            'border': 2,
            'bottom': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
        })
        plan_format = workbook.add_format({
            'border': 1,
            'left': 2,
            'font_size': 12,
            'align': 'center',
            'fg_color': '#fff2cc',
        })
        plan_format_number = workbook.add_format({
            'border': 1,
            'left': 2,
            'bottom': 2,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#fff2cc',
            'num_format': '#,##0;[red]-#,##0',
        })
        quarter_plan_format = workbook.add_format({
            'border': 1,
            'left': 2,
            'font_size': 12,
            'align': 'center',
            'fg_color': '#C5D9F1',
        })
        quarter_plan_format_number = workbook.add_format({
            'border': 1,
            'left': 2,
            'bottom': 2,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#C5D9F1',
            'num_format': '#,##0;[red]-#,##0',
        })
        fact_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'fg_color': '#EBF1DE',
        })
        fact_format_number = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#EBF1DE',
            'num_format': '#,##0;[red]-#,##0',
        })
        forecast_format = workbook.add_format({
            'border': 1,
            'right': 2,
            'font_size': 12,
            'align': 'center',
            'fg_color': '#d9d9d9',
        })
        forecast_format_number = workbook.add_format({
            'border': 1,
            'right': 2,
            'font_size': 12,
            'align': 'center',
            'bold': True,
            'fg_color': '#d9d9d9',
            'num_format': '#,##0;[red]-#,##0',
        })
        left_percent_format = workbook.add_format({
            'border': 1,
            'bottom': 2,
            'left': 2,
            'font_size': 10,
            'bold': True,
            'color': '#00B050',
            'num_format': '0%',
        })
        right_percent_format = workbook.add_format({
            'border': 1,
            'bottom': 2,
            'right': 2,
            'font_size': 10,
            'bold': True,
            'color': '#00B050',
            'num_format': '0%',
        })

        plans, use_6_6_plan = self.get_company_plans(actual_date, company, centers_to_exclude)

        # print(plans)

        # месяц
        row += 1
        sheet.merge_range(
            row,
            start_column,
            row,
            start_column + 2,
            self.month_rus_name[actual_date.month - 1] + ' ' + str(actual_date.year),
            head_format
        )
        row += 1
        sheet.write(row, start_column, 'План', plan_format)
        sheet.write(row, start_column + 1, 'Факт', fact_format)
        sheet.write(row, start_column + 2, 'Прогноз', forecast_format)
        row += 1
        sheet.write(
            row,
            start_column,
            "='{0}'!{1}".format('ПДС ' + f"{actual_date.strftime('%d.%m')}", link['month_plan'][0]),
            plan_format_number,
        )
        formula = '=sum(' + ','.join("'{0}'!{1}".format('ПДС ' + f"{actual_date.strftime('%d.%m')}", l) for l in link['month_fact']) + ')'
        sheet.write_formula(row, start_column + 1, formula, fact_format_number)
        sheet.write(
            row,
            start_column + 2,
            "='{0}'!{1}".format('ПДС ' + f"{actual_date.strftime('%d.%m')}", link['month_forecast'][0]),
            forecast_format_number,
        )
        row += 1
        sheet.write_formula(
            row,
            start_column + 1,
            f'=IFERROR({xl_col_to_name(start_column + 1)}{row}/{xl_col_to_name(start_column)}{row}," ")',
            left_percent_format,
        )
        sheet.write_formula(
            row,
            start_column + 2,
            f'=IFERROR({xl_col_to_name(start_column + 2)}{row}/{xl_col_to_name(start_column)}{row}," ")',
            right_percent_format,
        )
        row += 1

        # квартал
        row += 1
        actual_quarter_number = (actual_date.month - 1) // 3 + 1
        sheet.merge_range(
            row,
            start_column,
            row,
            start_column + 2,
            'Q' + str(actual_quarter_number),
            head_format
        )
        row += 1
        sheet.write(row, start_column, plans['quarter_plan']['name'], quarter_plan_format)
        sheet.write(row, start_column + 1, 'Факт', fact_format)
        sheet.write(row, start_column + 2, 'Прогноз', forecast_format)
        row += 1
        sheet.write(
            row,
            start_column,
            plans['quarter_plan']['amount'],
            quarter_plan_format_number,
        )
        formula = '=sum(' + ','.join(
            "'{0}'!{1}".format('ПДС ' + f"{actual_date.strftime('%d.%m')}", l) for l in link['quarter_fact'][3:]) + ',' + f'{xl_col_to_name(start_column + 1)}{row - 4}' + ')'
        sheet.write_formula(row, start_column + 1, formula, fact_format_number)
        print('link', link)
        sheet.write(
            row,
            start_column + 2,
            "='{0}'!{1}".format('ПДС ' + f"{actual_date.strftime('%d.%m')}", link['year_forecast'][1]),
            forecast_format_number,
        )
        row += 1
        sheet.write_formula(
            row,
            start_column + 1,
            f'=IFERROR({xl_col_to_name(start_column + 1)}{row}/{xl_col_to_name(start_column)}{row}," ")',
            left_percent_format,
        )
        sheet.write_formula(
            row,
            start_column + 2,
            f'=IFERROR({xl_col_to_name(start_column + 2)}{row}/{xl_col_to_name(start_column)}{row}," ")',
            right_percent_format,
        )
        row += 1

        # Год
        row += 1
        sheet.merge_range(
            row,
            start_column,
            row,
            start_column + 2,
            str(actual_date.year),
            head_format
        )
        row += 1
        sheet.write(row, start_column, plans['year_plan']['name'], quarter_plan_format)
        sheet.write(row, start_column + 1, 'Факт', fact_format)
        sheet.write(row, start_column + 2, 'Прогноз', forecast_format)
        row += 1
        sheet.write(
            row,
            start_column,
            plans['year_plan']['amount'],
            quarter_plan_format_number,
        )
        if actual_quarter_number == 1:
            fact_formula = '=sum(' + f'{xl_col_to_name(start_column + 1)}{row - 4}' + ')'
            forecast_formula = self.get_year_forecast(budget, actual_date.year)
            # forecast_formula = (
            #         '=sum('
            #         + f'{xl_col_to_name(start_column + 2)}{row - 4}'
            #         + ','
            #         + "'{0}'!{1}".format('ПДС ' + f"{actual_date.strftime('%d.%m')}", link['year_forecast'][2])
            #         + ')'
            # )
        elif actual_quarter_number == 2:
            fact_formula = (
                    "=sum("
                    + "'{0}'!{1}".format('ПДС ' + f"{actual_date.strftime('%d.%m')}", link['year_forecast'][0])
                    + ','
                    + f'{xl_col_to_name(start_column + 1)}{row - 4}'
                    + ')'
            )
            forecast_formula = self.get_year_forecast(budget, actual_date.year)
            # forecast_formula = (
            #         '=sum('
            #         + f'{xl_col_to_name(start_column + 2)}{row - 4}'
            #         + ','
            #         + "'{0}'!{1}".format('ПДС ' + f"{actual_date.strftime('%d.%m')}", link['year_forecast'][0])
            #         + ','
            #         + "'{0}'!{1}".format('ПДС ' + f"{actual_date.strftime('%d.%m')}", link['year_forecast'][2])
            #         + ')'
            # )
        elif actual_quarter_number == 3:
            fact_formula = ('=sum(' + f'{xl_col_to_name(start_column + 1)}{row - 4}' + ',' + str(plans['hy1_fact']['amount']) + ')')
            if use_6_6_plan:
                forecast_formula = (
                        '=sum('
                        + f'{xl_col_to_name(start_column + 2)}{row - 4}'
                        + ','
                        + str(plans['hy1_fact']['amount'])
                        + ','
                        + "'{0}'!{1}".format('ПДС ' + f"{actual_date.strftime('%d.%m')}", link['year_forecast'][2])
                        + ')'
                )
            else:
                forecast_formula = self.get_year_forecast(budget, actual_date.year)
        else:
            fact_formula = (
                    "=sum("
                    + "'{0}'!{1}".format('ПДС ' + f"{actual_date.strftime('%d.%m')}", link['year_forecast'][0])
                    + ','
                    + f'{xl_col_to_name(start_column + 1)}{row - 4}'
                    + ','
                    + str(plans['hy1_fact']['amount'])
                    + ')'
            )
            if use_6_6_plan:
                forecast_formula = (
                        '=sum('
                        + f'{xl_col_to_name(start_column + 2)}{row - 4}'
                        + ','
                        + str(plans['hy1_fact']['amount'])
                        + ','
                        + "'{0}'!{1}".format('ПДС ' + f"{actual_date.strftime('%d.%m')}", link['year_forecast'][0])
                        + ','
                        + "'{0}'!{1}".format('ПДС ' + f"{actual_date.strftime('%d.%m')}", link['year_forecast'][2])
                        + ')'
                )
            else:
                forecast_formula = self.get_year_forecast(budget, actual_date.year)
        # print(forecast_formula)
        sheet.write_formula(row, start_column + 1, fact_formula, fact_format_number)
        sheet.write(row, start_column + 2, forecast_formula, forecast_format_number)
        row += 1
        sheet.write_formula(
            row,
            start_column + 1,
            f'=IFERROR({xl_col_to_name(start_column + 1)}{row}/{xl_col_to_name(start_column)}{row}," ")',
            left_percent_format,
        )
        sheet.write_formula(
            row,
            start_column + 2,
            f'=IFERROR({xl_col_to_name(start_column + 2)}{row}/{xl_col_to_name(start_column)}{row}," ")',
            right_percent_format,
        )
        row += 1
        return row

    def print_vertical_sum_formula(self, sheet, row, sum_lines, periods_dict, start_col, format):
        link = {}
        formula = '=sum('
        for n in range(len(sum_lines)):
            formula += '{0}{' + str(n + 1) + '},'
        formula += ')'
        col_counter = start_col
        for period, options in periods_dict.items():
            for col in options['cols']:
                if col['print'] != 'blank':
                    if col.get('link'):
                        if not link.get('month_forecast') or 'month' not in col['link']:  # заканчиваем писать координаты ячеек месяца после первого месяца с неделями
                            link.setdefault(col['link'], [])
                            link[col['link']].append(xl_col_to_name(col_counter) + str(row + 1))
                    result_formula = formula.format(xl_col_to_name(col_counter), *[line + 1 for line in sum_lines])
                    sheet.write_formula(row, col_counter, result_formula, col[format])
                    col_counter += 1
                else:
                    sheet.write(row, col_counter, '', col[format])
                    col_counter += 1
        return link

    def print_worksheet(self, workbook, budget, name_sheet, responsibility_center_ids, max_level, dict_formula, start_column, actual_date):
        sheet = workbook.add_worksheet(name_sheet)
        sheet.set_zoom(85)

        bold = workbook.add_format({'bold': True})

        head_format_grey = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "bold": False,
            "fg_color": '#d9d9d9',
            "font_size": 10,
        })

        row = 0
        sheet.write_string(row, 0, budget.name + ' ' + str(actual_date.date()), bold)
        column = 0
        sheet.merge_range(row + 1, 0, row + 2, 0, "Факторинг", head_format_grey)
        sheet.set_column(column, column, 16)
        column += 1
        sheet.merge_range(row + 1, column, row + 2, column, "КАМ", head_format_grey)
        sheet.set_column(column, column, 16)
        column += 1
        sheet.merge_range(row + 1, column, row + 2, column, "Заказчик", head_format_grey)
        sheet.set_column(column, column, 25)
        column += 1
        sheet.merge_range(row + 1, column, row + 2, column, "Наименование Проекта", head_format_grey)
        sheet.set_column(column, column, 25)
        column += 1
        sheet.merge_range(row + 1, column, row + 2, column, "Номер этапа проекта", head_format_grey)
        sheet.set_column(column, column, 16, False, {'hidden': 1, 'level': 2})
        column += 1
        sheet.merge_range(row + 1, column, row + 2, column, "", head_format_grey)
        sheet.set_column(column, column, 2)

        sheet.freeze_panes(3, start_column)
        column += 1

        link = {}
        periods_dict, period_limits = self.calculate_periods_dict(workbook, actual_date)
        periods_dict, budget_ids = self.calculate_budget_ids(budget, periods_dict)

        column = self.print_head(workbook, sheet, row, column, periods_dict, actual_date)
        row += 2

        financial_indicators = self.env['project.budget.financial.indicator'].search([
            ('commercial_budget_id', 'in', budget_ids),
            ('type', '=', 'cash_flow'),
            ('date', '>=', period_limits[0]),
            ('date', '<=', period_limits[1]),
            '|', ('forecast_probability_id', '=', False),
            ('forecast_probability_id.id', '=', self.env.ref('project_budget_nkk.project_budget_forecast_probability_commitment').id),
        ], order='project_id')

        for company in financial_indicators.company_id:
            data = self.get_data_from_indicators(
                financial_indicators.filtered(lambda fi: fi.prj_id.signer_id == fi.company_id.partner_id and fi.company_id == company),
                periods_dict,
                budget,
                budget_ids
            )
            if data:
                actual_center_ids_set = set()
                for center_name in data[company.name]:
                    center = self.env['account.analytic.account'].search([
                        ('name', '=', center_name),
                        ('company_id', '=', company.id),
                        ('plan_id', '=', self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
                    ])
                    actual_center_ids_set.add(center.id)
                    while center.parent_id:
                        center = center.parent_id
                        actual_center_ids_set.add(center.id)

                actual_center_ids = list(actual_center_ids_set)

                if responsibility_center_ids:
                    responsibility_centers = self.env['account.analytic.account'].search([
                        ('id','in',responsibility_center_ids),
                        ('parent_id', 'not in', responsibility_center_ids),
                        ('plan_id', '=', self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
                    ], order='sequence')  # для сортировки так делаем + не берем дочерние офисы, если выбраны их материнские
                else:
                    responsibility_centers = self.env['account.analytic.account'].search([
                        ('parent_id', '=', False),
                        ('plan_id', '=', self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
                    ], order='sequence')  # для сортировки так делаем + берем сначала только верхние элементы
                row, dict_formula, link = self.print_rows(sheet, workbook, company, responsibility_centers, actual_center_ids, row, data, periods_dict, 1, max_level, dict_formula, start_column)

            signer_indicators = financial_indicators.filtered(
                    lambda fi: fi.prj_id.signer_id != fi.company_id.partner_id and fi.company_id == company)

            for signer in signer_indicators.prj_id.signer_id:

                data_signer = self.get_data_from_indicators(
                    signer_indicators.filtered(lambda fi: fi.prj_id.signer_id == signer),
                    periods_dict,
                    budget,
                    budget_ids
                )
                if data_signer:
                    row = self.print_rows_signer(sheet, workbook, signer.name, row, data_signer, periods_dict, max_level, start_column)
        return link

    def print_summary_worksheet(self, workbook, budget, name_sheet, company, centers_to_exclude, actual_date, link):
        sheet = workbook.add_worksheet(name_sheet)
        sheet.set_zoom(80)
        # commitment_format = workbook.add_format({
        #     'border': 1,
        #     'font_size': 8,
        #     'num_format': '#,##0',
        #     'fg_color': '#d9d9d9',
        # })
        #
        # current_week_start, current_week_end = self.get_dates_from_week(
        #     actual_date.isocalendar()[1],
        #     actual_date.isocalendar()[0],
        # )
        # next_week_start, next_week_end = self.get_dates_from_week(
        #     (actual_date + timedelta(weeks=1)).isocalendar()[1],
        #     (actual_date + timedelta(weeks=1)).isocalendar()[0],
        # )
        # after_next_week_start, after_next_week_end = self.get_dates_from_week(
        #     (actual_date + timedelta(weeks=2)).isocalendar()[1],
        #     (actual_date + timedelta(weeks=2)).isocalendar()[0],
        # )
        #
        # previous_budget = self.get_previous_budget(actual_date)
        #
        # previous_periods_dict = OrderedDict()
        # previous_periods_dict[(current_week_start, current_week_end)] = {
        #     'type': 'week',
        #     'budget_id': previous_budget.id,
        #     'cols': [
        #         {
        #             'print': 'commitment',
        #             'format': commitment_format,
        #         },
        #     ],
        # }
        # previous_periods_dict[(next_week_start, next_week_end)] = {
        #     'type': 'week',
        #     'budget_id': previous_budget.id,
        #     'cols': [
        #         {
        #             'print': 'commitment',
        #             'format': commitment_format,
        #         },
        #     ],
        # }
        # previous_periods_dict[(after_next_week_start, after_next_week_end)] = {
        #     'type': 'week',
        #     'budget_id': previous_budget.id,
        #     'cols': [
        #         {
        #             'print': 'commitment',
        #             'format': commitment_format,
        #         },
        #     ],
        # }
        #
        # current_periods_dict = OrderedDict()
        # current_periods_dict[(current_week_start, current_week_end)] = {
        #     'type': 'week',
        #     'budget_id': budget.id,
        #     'cols': [
        #         {
        #             'print': 'fact',
        #             'format': commitment_format,
        #         }
        #     ],
        # }
        # current_periods_dict[(next_week_start, next_week_end)] = {
        #     'type': 'week',
        #     'budget_id': budget.id,
        #     'cols': [
        #         {
        #             'print': 'commitment',
        #             'format': commitment_format,
        #         },
        #     ],
        # }
        # current_periods_dict[(after_next_week_start, after_next_week_end)] = {
        #     'type': 'week',
        #     'budget_id': budget.id,
        #     'cols': [
        #         {
        #             'print': 'commitment',
        #             'format': commitment_format,
        #         },
        #     ],
        # }
        #
        # previous_financial_indicators = self.env['project.budget.financial.indicator'].search([
        #     ('company_id', '=', company.id),
        #     ('commercial_budget_id', '=', previous_budget.id),
        #     ('prj_id.signer_id', '=', company.partner_id.id),
        #     ('type', '=', 'cash_flow'),
        #     ('date', '>=', current_week_start),
        #     ('date', '<=', after_next_week_end),
        #     ('forecast_probability_id.id', '=', self.env.ref('project_budget_nkk.project_budget_forecast_probability_commitment').id),
        # ], order='project_id')
        #
        # current_financial_indicators = self.env['project.budget.financial.indicator'].search([
        #     ('company_id', '=', company.id),
        #     ('commercial_budget_id', '=', budget.id),
        #     ('prj_id.signer_id', '=', company.partner_id.id),
        #     ('type', '=', 'cash_flow'),
        #     ('date', '>=', current_week_start),
        #     ('date', '<=', after_next_week_end),
        #     '|', ('forecast_probability_id', '=', False),
        #     ('forecast_probability_id.id', '=', self.env.ref('project_budget_nkk.project_budget_forecast_probability_commitment').id),
        # ], order='project_id')
        #
        # previous_data = self.get_data_from_indicators(
        #     previous_financial_indicators,
        #     previous_periods_dict,
        #     previous_budget,
        #     previous_budget,
        # )
        #
        # current_data = self.get_data_from_indicators(
        #     current_financial_indicators,
        #     current_periods_dict,
        #     budget,
        #     budget,
        # )
        # row = 1
        # row = self.print_summary_head(workbook, sheet, row, 1,(current_week_start, current_week_end))
        # row = self.print_rows_summary(
        #     sheet,
        #     workbook,
        #     row,
        #     start_column,
        #     (current_week_start, current_week_end),
        #     (previous_data, current_data),
        #     (previous_budget, budget),
        #     ('commitment', 'fact'),
        # )
        # row = self.print_summary_head(workbook, sheet, row, 1, (next_week_start, next_week_end))
        # row = self.print_rows_summary(
        #     sheet,
        #     workbook,
        #     row,
        #     start_column,
        #     (next_week_start, next_week_end),
        #     (previous_data, current_data),
        #     (previous_budget, budget),
        #     ('commitment', 'commitment'),
        # )
        # row = self.print_summary_head(workbook, sheet, row, 1, (after_next_week_start, after_next_week_end))
        # row = self.print_rows_summary(
        #     sheet,
        #     workbook,
        #     row,
        #     start_column,
        #     (after_next_week_start, after_next_week_end),
        #     (previous_data, current_data),
        #     (previous_budget, budget),
        #     ('commitment', 'commitment'),
        # )

        current_week_start = date_utils.start_of(actual_date, 'week')
        current_week_end = date_utils.end_of(actual_date, 'week')
        previous_week_end = date_utils.end_of(actual_date - timedelta(weeks=1), 'week')
        previous_budget = self.env['project_budget.commercial_budget'].search([
            ('date_actual', '<=', previous_week_end),
        ], limit=1, order='date_actual desc')
        financial_indicators = self.env['project.budget.financial.indicator'].search([
            ('commercial_budget_id', 'in', (previous_budget.id, budget.id)),
            ('type', '=', 'cash_flow'),
            ('date', '>=', current_week_start),
            ('date', '<=', current_week_end),
            ('project_id.signer_id', '=', company.id),
            '|', ('forecast_probability_id', '=', False),
            ('forecast_probability_id.id', '=', self.env.ref('project_budget_nkk.project_budget_forecast_probability_commitment').id),
        ])
        col = 0
        row = 0
        row = self.print_week_summary(workbook, sheet, row, col, company, centers_to_exclude, actual_date, budget,
                                      (current_week_start, current_week_end), financial_indicators, previous_budget)
        col += 1
        row += 3
        week_row = self.print_week_fact(workbook, sheet, row, col, company, actual_date, budget, (current_week_start, current_week_end), financial_indicators)

        actual_month_start = date_utils.start_of(actual_date, 'month')
        actual_month_end = date_utils.end_of(actual_date, 'month')
        financial_indicators = self.env['project.budget.financial.indicator'].search([
            ('commercial_budget_id', 'in', (previous_budget.id, budget.id)),
            ('type', '=', 'cash_flow'),
            ('date', '>=', actual_month_start),
            ('date', '<=', actual_month_end),
            ('project_id.signer_id', '=', company.id),
            '|', ('forecast_probability_id', '=', False),
            ('forecast_probability_id.id', '=', self.env.ref('project_budget_nkk.project_budget_forecast_probability_commitment').id),
        ])
        col = 5
        row = 0
        row = self.print_month_summary(workbook, sheet, row, col, company, centers_to_exclude, actual_date, budget,
                                       (actual_month_start, actual_month_end), financial_indicators, previous_budget)
        col += 1
        row += 3
        month_row = self.print_month_fact(workbook, sheet, row, col, company, actual_date, budget, (actual_month_start, actual_month_end), financial_indicators)

        actual_quarter_start = date_utils.start_of(actual_date, 'quarter')
        actual_quarter_end = date_utils.end_of(actual_date, 'quarter')
        financial_indicators = self.env['project.budget.financial.indicator'].search([
            ('commercial_budget_id', 'in', (previous_budget.id, budget.id)),
            ('type', '=', 'cash_flow'),
            ('date', '>=', actual_quarter_start),
            ('date', '<=', actual_quarter_end),
            ('project_id.signer_id', '=', company.id),
            '|', ('forecast_probability_id', '=', False),
            ('forecast_probability_id.id', '=', self.env.ref('project_budget_nkk.project_budget_forecast_probability_commitment').id),
        ])
        col = 10
        row = 0
        row = self.print_quarter_summary(workbook, sheet, row, col, company, centers_to_exclude, actual_date, budget,
                                         (actual_quarter_start, actual_quarter_end), financial_indicators, previous_budget)
        col += 1
        row += 3
        quarter_row = self.print_quarter_fact(workbook, sheet, row, col, company, actual_date, budget, (actual_quarter_start, actual_quarter_end), financial_indicators)

        col = 15
        row = 0
        actual_year_start = date_utils.start_of(actual_date, 'year')
        actual_year_end = date_utils.end_of(actual_date, 'year')
        row = self.print_year_summary(workbook, sheet, row, col, company, centers_to_exclude, actual_date, budget,
                                         (actual_year_start, actual_year_end))
        row = max(week_row, month_row, quarter_row)

        # row = self.print_week_changes(workbook, sheet, row, col, company, actual_date, budget,
        #                                       (actual_quarter_start, actual_quarter_end), financial_indicators)

    def generate_xlsx_report(self, workbook, data, budgets):

        start_column = 6

        company = self.env['res.company'].search([('name', '=', 'НКК')])

        centers_to_exclude = self.env['account.analytic.account'].search([
            ('name', 'in', ('Облако',)),
        ])

        dict_formula = {'center_ids': {}, 'center_ids_not_empty': {},}

        responsibility_center_ids = data['responsibility_center_ids']

        ids = [center.id for center in self.env['account.analytic.account'].search([
            ('parent_id', '=', False),
            ('id', 'in', responsibility_center_ids),
            ('plan_id', '=', self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
        ])]
        max_level = self.centers_with_parents(ids, 0)

        if set(self.env['account.analytic.account'].search([
            ('plan_id', '=', self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
        ]).ids) != set(responsibility_center_ids):
            max_level -= 1

        commercial_budget_id = data['commercial_budget_id']
        budget = self.env['project_budget.commercial_budget'].search([('id', '=', commercial_budget_id)])
        actual_budget_date = budget.date_actual or datetime.now()
        actual_budget_date = datetime(year=2024, month=11, day=22)  # ОТЛАДОЧНАЯ
        link = self.print_worksheet(workbook, budget, 'ПДС ' + actual_budget_date.strftime('%d.%m'), responsibility_center_ids, max_level, dict_formula, start_column, actual_budget_date)
        self.print_summary_worksheet(workbook, budget, 'Свод ' + actual_budget_date.strftime('%d.%m'), company, centers_to_exclude, actual_budget_date, link)
