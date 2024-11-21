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

            quater_col_format = (10, None)
            blank_quater_col_format = (2, None)
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
                            }
                        ],
                    }
                    col += 2
                    if date_utils.start_of(week_start, 'week') > date_utils.start_of(actual_date, 'week').date():
                        week_cols.append(col - 2)
                    else:
                        week_cols.append(col - 1)
                    actual_week = actual_week + timedelta(weeks=1)
                    actual_week_number = actual_week.isocalendar()[1]
                    actual_week_year = actual_week.isocalendar()[0]
                    week_start, week_end = self.get_dates_from_week(actual_week_number, actual_week_year)
                    if week_start.month != week_end.month:  # учитываем разбиение недель по месяцам
                        week_month_end = week_end.replace(day=1) - timedelta(days=1)
                        week_month_start = week_end.replace(day=1)
                        periods_dict[(week_start, week_month_end)] = {
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
                                }
                            ],
                        }
                        col += 2
                        if date_utils.start_of(week_start, 'week') > date_utils.start_of(actual_date, 'week').date():
                            week_cols.append(col - 2)
                        else:
                            week_cols.append(col - 1)
                        formula = week_cols
                        week_cols = []

                        if week_start < actual_date.date():
                            month_format = fact_format
                            month_head_format = fact_head_format
                            month_center_format = fact_center_format
                            month_company_format = fact_company_format
                        else:
                            month_format = commitment_format
                            month_head_format = commitment_head_format
                            month_center_format = commitment_center_format
                            month_company_format = commitment_company_format

                        periods_dict['sum_month_' + str(week_start.month)] = {
                            'type': 'sum_month',
                            'difference': False,
                            'date': week_start,
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
                        if week_start.month % 3 == 0:
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
                                'difference': False,
                                'date': month_end,
                                'formula': formula,
                                'cols': [
                                    {
                                        'print': 'commitment',
                                        'print_head': 'прогноз',
                                        'format': quater_format,
                                        'format_head': quater_head_format,
                                        'format_center': quater_center_format,
                                        'format_company': quater_company_format,
                                        'col_format': quater_col_format,
                                    },
                                    {
                                        'print': 'blank',
                                        'print_head': 'разница',
                                        'format': blank_format,
                                        'format_head': blank_head_format,
                                        'format_center': blank_center_format,
                                        'format_company': blank_company_format,
                                        'col_format': blank_quater_col_format,
                                    },
                                ],
                            }
                            col += 2
                        week_start = week_month_start
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
                        col += 2
                    month_cols.append(col - 1)
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
                        'difference': False,
                        'date': month_end,
                        'formula': formula,
                        'cols': [
                            {
                                'print': 'commitment',
                                'print_head': 'прогноз',
                                'format': quater_format,
                                'format_head': quater_head_format,
                                'format_center': quater_center_format,
                                'format_company': quater_company_format,
                                'col_format': quater_col_format,
                            },
                            {
                                'print': 'blank',
                                'print_head': 'разница',
                                'format': blank_format,
                                'format_head': blank_head_format,
                                'format_center': blank_center_format,
                                'format_company': blank_company_format,
                                'col_format': blank_quater_col_format,
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
                        ('date_actual', '<=', period[0]),
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
        return (periods_dict, list(budget_ids))

    # def get_data_from_projects(self, projects, periods_dict, budget, budget_ids):
    #     project_project_ids = set(projects.mapped('project_id'))
    #     data = {}
    #     for project_project_id in sorted(project_project_ids):
    #         pds_is_present = False
    #         factoring_is_present = False
    #         project_data = {}
    #         for project in projects.filtered(lambda pr: pr.project_id == project_project_id):
    #             if project.step_status == 'project':
    #                 pds_fact_list = project.fact_cash_flow_ids
    #                 pds_plan_list = project.planned_cash_flow_ids
    #             elif project.step_status == 'step':
    #                 pds_fact_list = project.fact_step_cash_flow_ids
    #                 pds_plan_list = project.planned_step_cash_flow_ids
    #
    #             for period, options in periods_dict.items():
    #                 if 'sum' not in period:
    #                     project_data.setdefault(period, {'commitment': 0, 'fact': 0})
    #
    #                     for pds_fact in pds_fact_list:
    #                         if period[0] <= pds_fact.date_cash <= period[1] and project.commercial_budget_id.id == budget.id:
    #                             pds_is_present = True
    #                             factoring_is_present = any(d.factoring for d in pds_fact.distribution_cash_ids)
    #                             project_data[period]['fact'] += pds_fact.sum_cash
    #
    #                     for pds_plan in pds_plan_list:
    #                         if (period[0] <= pds_plan.date_cash <= period[1]
    #                                 and project.commercial_budget_id.id == options['budget_id']
    #                                 and (pds_plan.forecast == 'commitment'
    #                                      or (pds_plan.forecast == 'from_project'
    #                                          and project.stage_id.code in ('100(done)', '100', '75')))):
    #                             if pds_plan.distribution_sum_with_vat_ostatok > 0:
    #                                 pds_is_present = True
    #                                 project_data[period]['commitment'] += pds_plan.distribution_sum_with_vat_ostatok
    #
    #         if pds_is_present:
    #             current_project = projects.filtered(lambda pr: pr.project_id == project_project_id and pr.commercial_budget_id.id == budget.id)
    #
    #             if not current_project:  # если в текущем бюджете проекта нет, ищем самый последний и берем info из него
    #                 for budget_id in sorted(budget_ids, reverse=True):
    #                     if budget_id != budget.id:
    #                         current_project = projects.filtered(lambda pr: pr.project_id == project_project_id and pr.commercial_budget_id.id == budget_id)
    #                         if current_project:
    #                             break
    #
    #             data.setdefault(current_project.company_id.name, {}).setdefault(current_project.responsibility_center_id.name, {}).setdefault(
    #                 current_project.project_id, {})
    #
    #             project_step_id = ''
    #
    #             currency_rate = self.get_currency_rate_by_project(current_project)
    #             if current_project.step_status == 'project':
    #                 project_step_id = (current_project.step_project_number or '') + ' | ' + (current_project.project_id or '')
    #             elif current_project.step_status == 'step':
    #                 project_step_id = (current_project.step_project_number or '') + ' | ' + current_project.step_project_parent_id.project_id + " | " + current_project.project_id
    #
    #             data[current_project.company_id.name][current_project.responsibility_center_id.name][current_project.project_id]['info'] = {
    #                 'factoring': factoring_is_present,
    #                 'key_account_manager_id': current_project.key_account_manager_id.name,
    #                 'partner_id': current_project.partner_id.name,
    #                 'essence_project': current_project.essence_project,
    #                 'project_id': project_step_id,
    #                 'probability': self.get_estimated_probability_name_forecast(current_project.stage_id.code),
    #                 'total_amount_of_revenue_with_vat': current_project.total_amount_of_revenue_with_vat * currency_rate,
    #                 'margin_income': current_project.margin_income * currency_rate,
    #                 'profitability': current_project.profitability,
    #                 'dogovor_number': current_project.dogovor_number or '',
    #                 'vat_attribute_id': current_project.vat_attribute_id.name,
    #             }
    #
    #             data[current_project.company_id.name][current_project.responsibility_center_id.name][current_project.project_id]['periods'] = project_data
    #     return data

    def get_data_from_indicators(self, indicators, periods_dict, budget, budget_ids):
        data = {}
        for prj_id in indicators.prj_id:
            pds_is_present = False
            factoring_is_present = False
            project_data = {}
            for period, options in periods_dict.items():
                if 'sum' not in period:
                    current_indicators = indicators.filtered(
                        lambda i: i.prj_id == prj_id and (
                            i.commercial_budget_id.id == budget.id and not i.forecast_probability_id or
                            i.commercial_budget_id.id == options['budget_id'] and
                            i.forecast_probability_id.id == self.env.ref('project_budget_nkk.project_budget_forecast_probability_commitment').id
                        ) and
                        period[0] <= i.date <= period[1]
                    )
                    res = self.env['project.budget.report.sales.forecast']._get_cash_flow_data(period[0], period[1], current_indicators)
                    fact = res.get('fact', 0)
                    commitment = res.get(self.env.ref('project_budget_nkk.project_budget_forecast_probability_commitment').id, 0)
                    project_data.setdefault(period, {'commitment': commitment, 'fact': fact})
                    pds_is_present = any((fact, commitment))
                    factoring_is_present = any(d.factoring for d in current_indicators.fact_cash_flow_id.distribution_cash_ids)

                if pds_is_present:
                    data.setdefault(prj_id.company_id.name, {}).setdefault(prj_id.responsibility_center_id.name, {}).setdefault(
                        prj_id.project_id, {})

                    project_step_id = ''

                    currency_rate = self.get_currency_rate_by_project(prj_id)
                    if prj_id.step_status == 'project':
                        project_step_id = (prj_id.step_project_number or '') + ' | ' + (prj_id.project_id or '')
                    elif prj_id.step_status == 'step':
                        project_step_id = (prj_id.step_project_number or '') + ' | ' + prj_id.step_project_parent_id.project_id + " | " + prj_id.project_id

                    data[prj_id.company_id.name][prj_id.responsibility_center_id.name][prj_id.project_id]['info'] = {
                        'factoring': factoring_is_present,
                        'key_account_manager_id': prj_id.key_account_manager_id.name,
                        'partner_id': prj_id.partner_id.name,
                        'essence_project': prj_id.essence_project,
                        'project_id': project_step_id,
                        # 'probability': self.get_estimated_probability_name_forecast(prj_id.stage_id.code),
                        # 'total_amount_of_revenue_with_vat': prj_id.total_amount_of_revenue_with_vat * currency_rate,
                        # 'margin_income': prj_id.margin_income * currency_rate,
                        # 'profitability': prj_id.profitability,
                        # 'dogovor_number': prj_id.dogovor_number or '',
                        # 'vat_attribute_id': prj_id.vat_attribute_id.name,
                    }
                    data[prj_id.company_id.name][prj_id.responsibility_center_id.name][prj_id.project_id]['periods'] = project_data
        return data

    # def get_estimated_probability_name_forecast(self, name):
    #     result = name
    #     if name == '0': result = 'Отменен'
    #     if name == '30': result = 'Идентификация проекта'
    #     if name == '50': result = 'Подготовка ТКП'
    #     if name == '75': result = 'Подписание договора'
    #     if name == '100': result = 'Исполнение'
    #     if name == '100(done)': result = 'Исполнен/закрыт'
    #     return result

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

    def print_row(self, sheet, workbook, companies, responsibility_centers, actual_center_ids, row, data, periods_dict, level, max_level, dict_formula, start_column):
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
            'bold': True,
            'fg_color': '#FFFF00',
            'num_format': '#,##0;[red]-#,##0',
            'valign': 'center',
        })

        for company in companies:
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
                        row, formula_itogo = self.print_row(sheet, workbook, company, child_centers,
                                                            actual_center_ids, row, data, periods_dict,
                                                            level + 1, max_level, dict_formula, start_column)
                        for child_center in child_centers:
                            if child_center.id in actual_center_ids:
                                project_lines.append(dict_formula['center_ids'][child_center.id])

                    self.print_vertical_sum_formula(sheet, dict_formula['center_ids'][center.id], project_lines, periods_dict, start_column, 'format_center')

            if level == 1:
                row += 1
                sheet.merge_range(row, 0, row, start_column - 1, 'ИТОГО ' + company.name, company_format)
                self.print_vertical_sum_formula(sheet, row, center_lines, periods_dict, start_column, 'format_company')
                row += 1
                column = start_column
                for period, options in periods_dict.items():
                    period_len = len(options['cols'])
                    if options['difference']:
                        formula = f'={xl_col_to_name(column + 1)}{row}-{xl_col_to_name(column)}{row}'
                        sheet.merge_range(row, column, row, column + 1, formula, difference_format)
                    column += period_len

        return row, dict_formula

    def print_vertical_sum_formula(self, sheet, row, sum_lines, periods_dict, start_col, format):
        formula = '=sum('
        for n in range(len(sum_lines)):
            formula += '{0}{' + str(n + 1) + '},'
        formula += ')'
        col_counter = start_col
        for period, options in periods_dict.items():
            for col in options['cols']:
                if col['print'] != 'blank':
                    result_formula = formula.format(xl_col_to_name(col_counter), *[line + 1 for line in sum_lines])
                    sheet.write_formula(row, col_counter, result_formula, col[format])
                    col_counter += 1
                else:
                    sheet.write(row, col_counter, '', col[format])
                    col_counter += 1

    def printworksheet(self, workbook, budget, namesheet, responsibility_center_ids, max_level, multipliers, dict_formula, start_column):
        sheet = workbook.add_worksheet(namesheet)
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
        row_format_number_itogo = workbook.add_format({
            'top': 2,
            'bottom': 2,
            'left': 1,
            'right': 1,
            'font_size': 12,
            "bold": True,
            "num_format": '#,##0',
        })

        actual_budget_date = budget.date_actual or datetime.now()

        row = 0
        sheet.write_string(row, 0, budget.name + ' ' + str(actual_budget_date.date()), bold)
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

        periods_dict, period_limits = self.calculate_periods_dict(workbook, actual_budget_date)
        periods_dict, budget_ids = self.calculate_budget_ids(budget, periods_dict)

        # projects = self.env['project_budget.projects'].search([
        #     '&','&',
        #     ('commercial_budget_id', 'in', budget_ids),
        #     '|', '&', ('step_status', '=', 'step'),
        #     ('step_project_parent_id.project_have_steps', '=', True),
        #     '&', ('step_status', '=', 'project'),
        #     ('project_have_steps', '=', False),
        #     '|','|','|',
        #     ('id', 'in', [fact.projects_id.id for fact in self.env['project_budget.fact_cash_flow'].search([]) if fact.date_cash >= period_limits[0] and fact.date_cash <= period_limits[1]]),
        #     ('id', 'in', [plan.projects_id.id for plan in self.env['project_budget.planned_cash_flow'].search([]) if plan.date_cash >= period_limits[0] and plan.date_cash <= period_limits[1]]),
        #     ('id', 'in', [fact.step_project_child_id.id for fact in self.env['project_budget.fact_cash_flow'].search([]) if fact.date_cash >= period_limits[0] and fact.date_cash <= period_limits[1]]),
        #     ('id', 'in', [plan.step_project_child_id.id for plan in self.env['project_budget.planned_cash_flow'].search([]) if plan.date_cash >= period_limits[0] and plan.date_cash <= period_limits[1]]),
        # ], order='project_id')

        financial_indicators = self.env['project.budget.financial.indicator'].search([
            ('commercial_budget_id', 'in', budget_ids),
            ('type', '=', 'cash_flow'),
            ('date', '>=', period_limits[0]),
            ('date', '<=', period_limits[1]),
        ], order='project_id')

        # data = self.get_data_from_projects(projects, periods_dict, budget, budget_ids)
        data = self.get_data_from_indicators(financial_indicators, periods_dict, budget, budget_ids)

        actual_center_ids_set = set()
        for company in data:
            for center_name in data[company]:
                center = self.env['account.analytic.account'].search([
                    ('name', '=', center_name),
                    ('company_id.name', '=', company),
                    ('plan_id', '=', self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
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
                ('id','in',responsibility_center_ids),
                ('parent_id', 'not in', responsibility_center_ids),
                ('plan_id', '=', self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
            ], order='sequence')  # для сортировки так делаем + не берем дочерние оффисы, если выбраны их материнские
        else:
            responsibility_centers = self.env['account.analytic.account'].search([
                ('parent_id', '=', False),
                ('plan_id', '=', self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
            ], order='sequence')  # для сортировки так делаем + берем сначала только верхние элементы

        row, dict_formula = self.print_row(sheet, workbook, companies, responsibility_centers, actual_center_ids, row, data, periods_dict, 1, max_level, dict_formula, start_column)

    def generate_xlsx_report(self, workbook, data, budgets):

        START_COLUMN = 6

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

        multipliers = {'50': data['koeff_reserve'], '30': data['koeff_potential']}

        commercial_budget_id = data['commercial_budget_id']
        budget = self.env['project_budget.commercial_budget'].search([('id', '=', commercial_budget_id)])
        self.printworksheet(workbook, budget, 'ПДС', responsibility_center_ids, max_level, multipliers, dict_formula, START_COLUMN)
