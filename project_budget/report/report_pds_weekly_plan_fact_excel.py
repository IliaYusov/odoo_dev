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

    strYEAR = '2023'
    YEARint = int(strYEAR)

    month_rus_name = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь',
                      'Ноябрь', 'Декабрь',]

    def get_currency_rate_by_project(self,project):
        project_currency_rates = self.env['project_budget.project_currency_rates']
        return project_currency_rates._get_currency_rate_for_project_in_company_currency(project)

    def offices_with_parents(self, ids, max_level):
        if not ids:
            return max_level
        max_level += 1
        new_ids = [office.id for office in self.env['project_budget.project_office'].search([('parent_id', 'in', ids)])]
        return self.offices_with_parents(new_ids, max_level)

    def calculate_periods_dict(self, actual_date):
        periods_dict = OrderedDict()
        period_limits = []
        col = 0
        month_cols = []
        week_cols = []
        actual_quarter_start = date(actual_date.year, (actual_date.month - 1) // 3 * 3 + 1, 1)
        for month_delta in (-3, -2, -1, 0, 1, 2, 3, 4, 5):  # месяцы от начала текущего квартала
            month_start = actual_quarter_start + relativedelta(months=month_delta)
            month_end = actual_quarter_start + relativedelta(months=month_delta + 1) - timedelta(days=1)
            if month_start.month == actual_date.month:
                actual_week = month_start
                actual_week_number = actual_week.isocalendar()[1]
                actual_week_year = actual_week.isocalendar()[0]
                week_start = month_start
                week_end = self.get_dates_from_week(actual_week_number, actual_week_year)[1]
                while week_start.month < actual_date.month + 2:  # недели в течение двух месяцев
                    periods_dict[(week_start, week_end)] = {
                        'type': 'week',
                        'cols': [
                            {
                                'print': 'commitment',
                                'print_head': 'прогноз'
                            },
                            {
                                'print': 'fact',
                                'print_head': 'факт'
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
                                    'print_head': 'прогноз'
                                },
                                {
                                    'print': 'fact',
                                    'print_head': 'факт'
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
                        periods_dict['sum_month_' + str(week_start.month)] = {
                            'type': 'sum_month',
                            'date': week_start,
                            'formula': formula,
                        }
                        col += 1
                        month_cols.append(col)
                        if week_start.month % 3 == 0:
                            formula = month_cols
                            month_cols = []
                            periods_dict['sum_quarter_' + str((month_start.month - 1) // 3 + 1)] = {
                                'type': 'sum_quarter',
                                'date': month_end,
                                'formula': formula,
                            }
                            col += 1
                        week_start = week_month_start
            elif month_start.month == actual_date.month + 1:  # пропускаем следующий за текущим месяц
                pass
            else:
                if month_end < actual_date:  # в прошлом печатаем прогноз и факт, в будущем - только прогноз
                    periods_dict[(month_start, month_end)] = {
                        'type': 'month',
                        'cols': [
                            {
                                'print': 'commitment',
                                'print_head': 'план-прогноз на начало месяца'
                            },
                            {
                                'print': 'fact',
                                'print_head': 'факт'
                            },
                            {
                                'print': 'difference',
                                'print_head': 'разница'
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
                                'print_head': 'прогноз на текущую дату'
                            }
                        ]
                    }
                    col += 1
                    month_cols.append(col)
                if month_start.month % 3 == 0:  # добавляем суммы и формулы по кварталам
                    formula = month_cols
                    month_cols = []
                    periods_dict['sum_quarter_' + str((month_start.month - 1) // 3 + 1)] = {
                        'type': 'sum_quarter',
                        'date': month_end,
                        'formula': formula,
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
        data = {}
        for project in projects:
            pds_is_present = False
            project_data = {}
            for period, options in periods_dict.items():
                if 'sum' not in period:
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
                        if period[0] <= pds_fact.date_cash <= period[1] and project.commercial_budget_id == budget:
                            pds_is_present = True
                            project_data[period]['fact'] += pds_fact.sum_cash

                    for pds_plan in pds_plan_list:
                        if (period[0] <= pds_plan.date_cash <= period[1]
                                and project.commercial_budget_id.id == options['budget_id']
                                and (pds_plan.forecast == 'commitment'
                                     or (pds_plan.forecast == 'from_project'
                                         and project.stage_id.code in ('100(done)', '100', '75')))):
                            pds_is_present = True
                            project_data[period]['commitment'] += pds_plan.sum_cash

            if pds_is_present:
                data.setdefault(project.company_id.name, {}).setdefault(project.project_office_id.name, {}).setdefault(
                    project.project_id, {})

                currency_rate = self.get_currency_rate_by_project(project)

                data[project.company_id.name][project.project_office_id.name][project.project_id]['info'] = {
                    'key_account_manager_id': project.key_account_manager_id.name,
                    'partner_id': project.partner_id.name,
                    'essence_project': project.essence_project,
                    'project_id': project_id,
                    'probability': self.get_estimated_probability_name_forecast(project.stage_id.code),
                    'total_amount_of_revenue_with_vat': project.total_amount_of_revenue_with_vat * currency_rate,
                    'margin_income': project.margin_income * currency_rate,
                    'profitability': project.profitability,
                    'dogovor_number': project.dogovor_number or '',
                    'vat_attribute_id': project.vat_attribute_id.name,
                }

                data[project.company_id.name][project.project_office_id.name][project.project_id]['periods'] = project_data
        return data

    def is_project_in_year(self, project):
        global strYEAR
        global YEARint

        years = (YEARint, YEARint + 1, YEARint + 2)

        if project:
            if project.stage_id.code == '0':  # проверяем последний зафиксированный бюджет в предыдущих годах
                last_fixed_project = self.env['project_budget.projects'].search(
                    [('date_actual', '<', date(YEARint,1,1)),
                     ('budget_state', '=', 'fixed'),
                     ('project_id', '=', project.project_id),
                     ], limit=1, order='date_actual desc')
                if last_fixed_project and last_fixed_project.stage_id.code == '0':
                    return False

            if project.end_presale_project_month.year in years or project.end_sale_project_month.year in years:
                return True
            for pds in project.planned_cash_flow_ids:
                if pds.date_cash.year in years:
                    return True
            for pds in project.fact_cash_flow_ids:
                if pds.date_cash.year in years:
                    return True
            for act in project.planned_acceptance_flow_ids:
                if act.date_cash.year in years:
                    return True
            for act in project.fact_acceptance_flow_ids:
                if act.date_cash.year in years:
                    return True
            for pds in project.planned_step_cash_flow_ids:
                if pds.date_cash.year in years:
                    return True
            for pds in project.fact_step_cash_flow_ids:
                if pds.date_cash.year in years:
                    return True
            for act in project.planned_step_acceptance_flow_ids:
                if act.date_cash.year in years:
                    return True
            for act in project.fact_step_acceptance_flow_ids:
                if act.date_cash.year in years:
                    return True
        return False

    quarter_rus_name = ['Q1', 'Q2', 'HY1/YEAR', 'Q3', 'Q4', 'HY2/YEAR', 'YEAR', 'NEXT', 'AFTER NEXT']

    dict_formula = {}

    dict_contract_pds = {
        # 1: {'name': 'Контрактование, с НДС', 'color': '#FFD966'},
        2: {'name': 'Поступление денежных средств, с НДС', 'color': '#D096BF'},
        # 3: {'name': 'Валовая Выручка, без НДС', 'color': '#B4C6E7'},
        # 4: {'name': 'Валовая прибыль (Маржа 1), без НДС', 'color': '#F4FD9F'},
    }

    def get_estimated_probability_name_forecast(self, name):
        result = name
        if name == '0': result = 'Отменен'
        if name == '30': result = 'Идентификация проекта'
        if name == '50': result = 'Подготовка ТКП'
        if name == '75': result = 'Подписание договора'
        if name == '100': result = 'Исполнение'
        if name == '100(done)': result = 'Исполнен/закрыт'
        return result

    def get_quarter_from_month(self, month):
        if month in (1, 2, 3):
            return 'Q1'
        if month in (4, 5, 6):
            return 'Q2'
        if month in (7, 8, 9):
            return 'Q3'
        if month in (10, 11, 12):
            return 'Q4'
        return False

    def get_months_from_quarter(self, quarter_name):
        months = False
        if 'Q1' in quarter_name:
            months = (1, 2, 3)
        if 'Q2' in quarter_name:
            months = (4, 5, 6)
        if 'Q3' in quarter_name:
            months = (7, 8, 9)
        if 'Q4' in quarter_name:
            months = (10, 11, 12)
        return months

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

    def get_sum_fact_pds_project_quarter(self, project, quarter):
        global strYEAR
        global YEARint

        sum_cash = 0
        
        months = self.get_months_from_quarter(quarter)
        
        if project.step_status == 'project':
            pds_list = project.fact_cash_flow_ids
        elif project.step_status == 'step':
            pds_list = project.fact_step_cash_flow_ids

        for pds in pds_list:

            if pds.date_cash.month in months and pds.date_cash.year == YEARint:
                sum_cash += pds.sum_cash
                
        return sum_cash

    def get_sum_fact_pds_project_week(self, project, week_number):
        global strYEAR
        global YEARint

        sum_cash = 0

        if project.step_status == 'project':
            pds_list = project.fact_cash_flow_ids
        elif project.step_status == 'step':
            pds_list = project.fact_step_cash_flow_ids

        for pds in pds_list:

            if pds.date_cash.isocalendar()[1] == week_number and pds.date_cash.isocalendar()[0] == YEARint:
                sum_cash += pds.sum_cash

        return sum_cash

    def get_sum_fact_pds_project_year(self, project, year):

        sum_cash = 0

        if project.step_status == 'project':
            pds_list = project.fact_cash_flow_ids
        elif project.step_status == 'step':
            pds_list = project.fact_step_cash_flow_ids

        for pds in pds_list:

            if pds.date_cash.year == year:
                sum_cash += pds.sum_cash

        return sum_cash

    def get_sum_plan_pds_project_quarter(self, project, quarter):
        global strYEAR
        global YEARint

        sum_cash = {'commitment': 0, 'reserve': 0, 'potential': 0}

        months = self.get_months_from_quarter(quarter)

        if project.step_status == 'project':
            pds_list = project.planned_cash_flow_ids
        elif project.step_status == 'step':
            pds_list = project.planned_step_cash_flow_ids

        for pds in pds_list:
            if pds.date_cash.month in months and pds.date_cash.year == YEARint:
                stage_id_code = project.stage_id.code

                if pds.forecast == 'from_project':
                    if stage_id_code in ('100(done)', '100', '75'):
                        sum_cash['commitment'] += pds.sum_cash
                    elif stage_id_code == '50':
                        sum_cash['reserve'] += pds.sum_cash
                else:
                    if stage_id_code != '0':
                        sum_cash[pds.forecast] += pds.sum_cash
        return sum_cash

    def get_sum_plan_pds_project_week(self, project, week_number):
        global strYEAR
        global YEARint

        sum_cash = {'commitment': 0, 'reserve': 0, 'potential': 0}

        if project.step_status == 'project':
            pds_list = project.planned_cash_flow_ids
        elif project.step_status == 'step':
            pds_list = project.planned_step_cash_flow_ids

        for pds in pds_list:
            if pds.date_cash.isocalendar()[1] == week_number and pds.date_cash.isocalendar()[0] == YEARint:
                stage_id_code = project.stage_id.code
                if pds.forecast == 'from_project':
                    if stage_id_code in ('100(done)', '100', '75'):
                        sum_cash['commitment'] += pds.sum_cash
                    elif stage_id_code == '50':
                        sum_cash['reserve'] += pds.sum_cash
                else:
                    if stage_id_code != '0':
                        sum_cash[pds.forecast] += pds.sum_cash
        return sum_cash

    def get_sum_plan_pds_project_year(self, project, year):
        global strYEAR
        global YEARint

        sum_cash = {'commitment': 0, 'reserve': 0, 'potential': 0}

        if project.step_status == 'project':
            pds_list = project.planned_cash_flow_ids
        elif project.step_status == 'step':
            pds_list = project.planned_step_cash_flow_ids

        for pds in pds_list:
            if pds.date_cash.year == year:
                stage_id_code = project.stage_id.code
                if pds.forecast == 'from_project':
                    if stage_id_code in ('100(done)', '100', '75'):
                        sum_cash['commitment'] += pds.sum_cash
                    elif stage_id_code == '50':
                        sum_cash['reserve'] += pds.sum_cash
                else:
                    if stage_id_code != '0':
                        sum_cash[pds.forecast] += pds.sum_cash
        return sum_cash

    def print_week_head(self, workbook, sheet, row, column, YEAR):
        global strYEAR
        global YEARint

        for x in self.dict_contract_pds.items():
            y = list(x[1].values())
            head_format_month = workbook.add_format({
                'border': 1,
                'text_wrap': True,
                'align': 'center',
                'valign': 'vcenter',
                "fg_color": y[1],
                "font_size": 10,
            })
            head_format_month_current = workbook.add_format({
                'border': 1,
                'text_wrap': True,
                'align': 'center',
                'valign': 'vcenter',
                "bold": True,
                "fg_color": '#00AA00',
                "font_size": 10,
            })
            head_format_month_next = workbook.add_format({
                'border': 1,
                'text_wrap': True,
                'align': 'center',
                'valign': 'vcenter',
                "bold": True,
                "fg_color": '#ffa500',
                "font_size": 10,
            })
            head_format_month_itogo = workbook.add_format({
                'border': 1,
                'text_wrap': True,
                'align': 'center',
                'valign': 'vcenter',
                "bold": True,
                "fg_color": '#D9E1F2',
                "font_size": 12,
            })
            head_format_month_itogo_6_plus_6 = workbook.add_format({
                'border': 1,
                'text_wrap': True,
                'align': 'center',
                'valign': 'vcenter',
                "bold": True,
                "fg_color": '#00b0f0',
                "font_size": 12,
            })
            head_format_month_itogo_percent = workbook.add_format({
                'border': 1,
                'text_wrap': True,
                'align': 'center',
                'valign': 'vcenter',
                "bold": False,
                "fg_color": '#ffff99',
                "font_size": 9,
            })
            head_format_month_detail = workbook.add_format({
                'border': 1,
                'text_wrap': True,
                'align': 'center',
                'valign': 'vcenter',
                "bold": False,
                "fg_color": '#E2EFDA',
                "font_size": 9,
            })
            head_format_month_detail_fact = workbook.add_format({
                'border': 1,
                'text_wrap': True,
                'align': 'center',
                'valign': 'vcenter',
                "bold": True,
                "fg_color": '#C6E0B4',
                "font_size": 9,
            })

            colbeg = column

            for week_number in range(1, date(YEARint, 12, 28).isocalendar()[1] + 1):

                sheet.set_row(row, 30)
                sheet.set_row(row + 1, 25)
                sheet.set_row(row + 2, 25)

                current_week = date.today().isocalendar()[1]

                if week_number == current_week:
                    str_format = head_format_month_current
                elif week_number in (current_week + 1, current_week + 2):
                    str_format = head_format_month_next
                else:
                    str_format = head_format_month
                    sheet.set_column(column, column + 2, False, False, {'hidden': 1, 'level': 1})

                week_begin, week_end = self.get_dates_from_week(week_number, YEARint)

                sheet.merge_range(row, column, row, column + 2,
                                  'WEEK ' +
                                  str(week_number) +
                                  '\n(' +
                                  week_begin.strftime('%d.%m.%Y') +
                                  ' - ' +
                                  week_end.strftime('%d.%m.%Y') +
                                  ')',
                                  str_format)

                sheet.merge_range(row+1, column, row+2, column, 'Факт', head_format_month_detail_fact)
                column += 1
                sheet.merge_range(row + 1, column, row + 1, column + 1, 'Прогноз до конца недели', head_format_month_detail)
                sheet.write_string(row + 2, column, 'Обязательство', head_format_month_detail)
                column += 1
                sheet.write_string(row + 2, column, 'Резерв', head_format_month_detail)
                column += 1

            sheet.merge_range(row-1, colbeg, row-1, column - 1, y[0], head_format_month)

        return column

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
                    string = period[0].strftime("%B") + '\n' + col['print_head']
                    sheet.merge_range(row + 1, column, row + 2, column, string, head_format_month)
                    column += 1
            elif options['type'] == 'week':
                for col in options['cols']:
                    string = period[0].strftime("%B") + ' ' + period[0].strftime("%d") + '-' + period[1].strftime("%d") + '\n' + col['print_head']
                    sheet.merge_range(row + 1, column, row + 2, column, string, head_format_month)
                    column += 1
            elif options['type'] == 'sum_month':
                string = options['date'].strftime("%B")  + '\n прогноз на текущую дату'
                sheet.merge_range(row + 1, column, row + 2, column, string, head_format_month)
                column += 1
            elif options['type'] == 'sum_quarter':
                if options['date'] < actual_budget_date:
                    string = ('ИТОГО \nПДС Q' + str((options['date'].month - 1) // 3 + 1) + '/' +
                              options['date'].strftime("%Y") + '\nФакт')
                else:
                    string = ('ИТОГО \nПДС Q' + str((options['date'].month - 1) // 3 + 1) + '/' +
                              options['date'].strftime("%Y") + '\nПрогноз')
                sheet.merge_range(row + 1, column, row + 2, column, string, head_format_month)
                column += 1
            else:
                string = period
                sheet.merge_range(row + 1, column, row + 2, column, string, head_format_month)
                column += 1
        return column

    # def print_week_pds_project(self, sheet, row, column, week_number, project, row_format_number, row_format_number_color_fact):
    #     global strYEAR
    #     global YEARint
    #
    #     sum75tmpetalon = sum50tmpetalon = sum100tmp = sum75tmp = sum50tmp = 0
    #
    #     sum100tmp = self.get_sum_fact_pds_project_week(project, week_number)
    #     if sum100tmp:
    #         sheet.write_number(row, column, sum100tmp, row_format_number_color_fact)
    #
    #     sum = self.get_sum_plan_pds_project_week(project, week_number)
    #
    #     if sum100tmp >= sum['commitment']:
    #         sum100tmp_ostatok = sum100tmp - sum['commitment']
    #         sum['commitment'] = 0
    #         sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
    #     else:
    #         sum['commitment'] = sum['commitment'] - sum100tmp
    #
    #     # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
    #     sum_distribution_pds = 0
    #     sum_ostatok_pds = {'commitment': 0, 'reserve': 0, 'potential': 0}
    #
    #     if project.step_status == 'project':
    #         pds_list = project.planned_cash_flow_ids
    #     elif project.step_status == 'step':
    #         pds_list = project.planned_step_cash_flow_ids
    #
    #     stage_id_code = project.stage_id.code
    #
    #     for planned_cash_flow in pds_list:
    #         if planned_cash_flow.date_cash.isocalendar()[1] == week_number and planned_cash_flow.date_cash.isocalendar()[0] == YEARint:
    #             if planned_cash_flow.forecast == 'from_project':
    #                 if stage_id_code in ('100(done)', '100', '75'):
    #                     sum_ostatok_pds['commitment'] += planned_cash_flow.distribution_sum_with_vat_ostatok
    #                 elif stage_id_code == '50':
    #                     sum_ostatok_pds['reserve'] += planned_cash_flow.distribution_sum_with_vat_ostatok
    #             else:
    #                 if stage_id_code != '0':
    #                     sum_ostatok_pds[planned_cash_flow.forecast] += planned_cash_flow.distribution_sum_with_vat_ostatok
    #
    #             sum_distribution_pds += planned_cash_flow.distribution_sum_without_vat
    #
    #     if sum_distribution_pds != 0 : # если есть распределение, то остаток = остатку распределения
    #         sum = sum_ostatok_pds
    #         for key in sum:
    #             if sum[key] < 0:
    #                 sum[key] = 0
    #
    #     sheet.write_number(row, column + 1, sum['commitment'], row_format_number)
    #     sum75tmp += sum['commitment']
    #     sheet.write_number(row, column + 2, sum['reserve'], row_format_number)
    #     sum50tmp += sum['reserve']
    #
    #     return sum75tmpetalon, sum50tmpetalon, sum100tmp, sum75tmp, sum50tmp

    def calculate_quarter_pds(self, element, project, multipliers):
        global strYEAR
        global YEARint

        sum75tmpetalon = 0
        sum50tmpetalon = 0
        sum100tmp = 0
        sum75tmp = 0
        sum50tmp = 0
        sum_next_75_tmp = 0
        sum_next_50_tmp = 0
        sum_next_30_tmp = 0
        sum_after_next_tmp = 0

        if 'Q' in element:

            months = self.get_months_from_quarter(element)

            project_etalon = self.get_etalon_project(project, element)

            sum = self.get_sum_plan_pds_project_quarter(project_etalon, element)

            stage_id_code = project_etalon.stage_id.code

            if sum:
                if stage_id_code in ('75', '100', '100(done)'):
                    sum75tmpetalon += sum['commitment']
                if stage_id_code == '50':
                    sum50tmpetalon += sum['reserve']

            sum100tmp = self.get_sum_fact_pds_project_quarter(project, element)
            sum = self.get_sum_plan_pds_project_quarter(project, element)

            if sum100tmp >= sum['commitment']:
                sum100tmp_ostatok = sum100tmp - sum['commitment']
                sum['commitment'] = 0
                sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
            else:
                sum['commitment'] = sum['commitment'] - sum100tmp

            # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
            sum_distribution_pds = 0
            sum_ostatok_pds = {'commitment': 0, 'reserve': 0, 'potential': 0}
            for planned_cash_flow in project.planned_cash_flow_ids:
                if planned_cash_flow.date_cash.month in months and planned_cash_flow.date_cash.year == YEARint:
                    sum_distribution_pds += planned_cash_flow.distribution_sum_without_vat
                    if planned_cash_flow.forecast == 'from_project':
                        if project.stage_id.code in ('100(done)', '100', '75'):
                            sum_ostatok_pds['commitment'] += planned_cash_flow.distribution_sum_with_vat_ostatok
                        elif project.stage_id.code == '50':
                            sum_ostatok_pds['reserve'] += planned_cash_flow.distribution_sum_with_vat_ostatok
                    else:
                        if project.stage_id.code != '0':
                            sum_ostatok_pds[
                                planned_cash_flow.forecast] += planned_cash_flow.distribution_sum_with_vat_ostatok

            if sum_distribution_pds != 0:  # если есть распределение, то остаток = остатку распределения
                sum = sum_ostatok_pds
                for key in sum:
                    if sum[key] < 0:
                        sum[key] = 0

            sum75tmp += sum['commitment']
            sum50tmp += sum['reserve']

        elif element == 'NEXT':
            sum100tmp = self.get_sum_fact_pds_project_year(project, YEARint + 1)
            sum = self.get_sum_plan_pds_project_year(project, YEARint + 1)

            if sum100tmp >= sum['commitment']:
                sum100tmp_ostatok = sum100tmp - sum['commitment']
                sum['commitment'] = 0
                sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
            else:
                sum['commitment'] = sum['commitment'] - sum100tmp

            # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
            sum_distribution_pds = 0
            sum_ostatok_pds = {'commitment': 0, 'reserve': 0, 'potential': 0}
            stage_id_code = project.stage_id.code

            for planned_cash_flow in project.planned_cash_flow_ids:
                if planned_cash_flow.date_cash.year == YEARint + 1:
                    sum_distribution_pds += planned_cash_flow.distribution_sum_without_vat
                    if planned_cash_flow.forecast == 'from_project':
                        if project.stage_id.code in ('100(done)', '100', '75'):
                            sum_ostatok_pds['commitment'] += planned_cash_flow.distribution_sum_with_vat_ostatok
                        elif project.stage_id.code == '50':
                            sum_ostatok_pds['reserve'] += planned_cash_flow.distribution_sum_with_vat_ostatok
                        elif project.stage_id.code == '30':
                            sum_ostatok_pds['potential'] += planned_cash_flow.distribution_sum_with_vat_ostatok
                    else:
                        if project.stage_id.code != '0':
                            sum_ostatok_pds[
                                planned_cash_flow.forecast] += planned_cash_flow.distribution_sum_with_vat_ostatok

            if sum_distribution_pds != 0:  # если есть распределение, то остаток = остатку распределения
                sum = sum_ostatok_pds
                for key in sum:
                    if sum[key] < 0:
                        sum[key] = 0

            sum_next_75_tmp += sum['commitment']
            sum_next_50_tmp += sum['reserve'] * multipliers['50']
            sum_next_30_tmp += sum['potential'] * multipliers['30']

        elif element == 'AFTER NEXT':

            sum100tmp = self.get_sum_fact_pds_project_year(project, YEARint + 2)
            sum = self.get_sum_plan_pds_project_year(project, YEARint + 2)

            if sum100tmp >= sum['commitment']:
                sum100tmp_ostatok = sum100tmp - sum['commitment']
                sum['commitment'] = 0
                sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
            else:
                sum['commitment'] = sum['commitment'] - sum100tmp

            # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
            sum_distribution_pds = 0
            sum_ostatok_pds = {'commitment': 0, 'reserve': 0, 'potential': 0}
            stage_id_code = project.stage_id.code

            for planned_cash_flow in project.planned_cash_flow_ids:
                if planned_cash_flow.date_cash.year == YEARint + 2:
                    sum_distribution_pds += planned_cash_flow.distribution_sum_without_vat
                    if planned_cash_flow.forecast == 'from_project':
                        if project.stage_id.code in ('100(done)', '100', '75'):
                            sum_ostatok_pds['commitment'] += planned_cash_flow.distribution_sum_with_vat_ostatok
                        elif project.stage_id.code == '50':
                            sum_ostatok_pds['reserve'] += planned_cash_flow.distribution_sum_with_vat_ostatok
                        elif project.stage_id.code == '30':
                            sum_ostatok_pds['potential'] += planned_cash_flow.distribution_sum_with_vat_ostatok
                    else:
                        if project.stage_id.code != '0':
                            sum_ostatok_pds[
                                planned_cash_flow.forecast] += planned_cash_flow.distribution_sum_with_vat_ostatok

            if sum_distribution_pds != 0:  # если есть распределение, то остаток = остатку распределения
                sum = sum_ostatok_pds
                for key in sum:
                    if sum[key] < 0:
                        sum[key] = 0

            sum_after_next_tmp += sum['commitment']
            sum_after_next_tmp += sum['reserve'] * multipliers['50']
            sum_after_next_tmp += sum['potential'] * multipliers['30']

        return (sum75tmpetalon, sum50tmpetalon,
                sum100tmp, sum75tmp, sum50tmp,
                sum_next_75_tmp, sum_next_50_tmp, sum_next_30_tmp,
                sum_after_next_tmp)

    def calculate_weekly_pds(self, week_number, project, project_office, multipliers):
        global strYEAR
        global YEARint

        sum75tmpetalon = 0
        sum50tmpetalon = 0
        sum100tmp = 0
        sum75tmp = 0
        sum50tmp = 0
        sum_next_75_tmp = 0
        sum_next_50_tmp = 0
        sum_next_30_tmp = 0
        sum_after_next_tmp = 0

        sum100tmp = self.get_sum_fact_pds_project_week(project, week_number)
        sum = self.get_sum_plan_pds_project_week(project, week_number)

        if sum100tmp >= sum['commitment']:
            sum100tmp_ostatok = sum100tmp - sum['commitment']
            sum['commitment'] = 0
            sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
        else:
            sum['commitment'] = sum['commitment'] - sum100tmp

        # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
        sum_distribution_pds = 0
        sum_ostatok_pds = {'commitment': 0, 'reserve': 0, 'potential': 0}

        if project.step_status == 'project':
            pds_list = project.planned_cash_flow_ids
        elif project.step_status == 'step':
            pds_list = project.planned_step_cash_flow_ids

        for planned_cash_flow in pds_list:
            if planned_cash_flow.date_cash.isocalendar()[1] == week_number and planned_cash_flow.date_cash.isocalendar()[0] == YEARint:
                sum_distribution_pds += planned_cash_flow.distribution_sum_without_vat
                if planned_cash_flow.forecast == 'from_project':
                    if project.stage_id.code in ('100(done)', '100', '75'):
                        sum_ostatok_pds['commitment'] += planned_cash_flow.distribution_sum_with_vat_ostatok
                    elif project.stage_id.code == '50':
                        sum_ostatok_pds['reserve'] += planned_cash_flow.distribution_sum_with_vat_ostatok
                else:
                    if project.stage_id.code != '0':
                        sum_ostatok_pds[
                            planned_cash_flow.forecast] += planned_cash_flow.distribution_sum_with_vat_ostatok

        if sum_distribution_pds != 0:  # если есть распределение, то остаток = остатку распределения
            sum = sum_ostatok_pds
            for key in sum:
                if sum[key] < 0:
                    sum[key] = 0

        sum75tmp += sum['commitment']
        sum50tmp += sum['reserve']

        return (
            sum75tmpetalon, sum50tmpetalon, sum100tmp, sum75tmp, sum50tmp, sum_next_75_tmp, sum_next_50_tmp,
            sum_next_30_tmp, sum_after_next_tmp
        )

    def get_month_number_rus(self, monthNameRus):
        if monthNameRus == 'Январь': return 1
        if monthNameRus == 'Февраль': return 2
        if monthNameRus == 'Март': return 3
        if monthNameRus == 'Апрель': return 4
        if monthNameRus == 'Май': return 5
        if monthNameRus == 'Июнь': return 6
        if monthNameRus == 'Июль': return 7
        if monthNameRus == 'Август': return 8
        if monthNameRus == 'Сентябрь': return 9
        if monthNameRus == 'Октябрь': return 10
        if monthNameRus == 'Ноябрь': return 11
        if monthNameRus == 'Декабрь': return 12
        return False

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
                        sheet.write_number(row, column, periods_data[period][col['print']], row_format_number)
                    else:
                        formula = '={1}{0}-{2}{0}'.format(
                            row + 1,
                            xl_col_to_name(column - 2),
                            xl_col_to_name(column - 1)
                        )
                        sheet.write_formula(row, column, formula, row_format_number)
                    column += 1
            else:
                if 'sum_quarter' in period:
                    formula = 'sum({1}{0},{2}{0},{3}{0})'.format(
                            row + 1,
                            xl_col_to_name(11 + periods_dict[period]['formula'][0]),
                            xl_col_to_name(11 + periods_dict[period]['formula'][1]),
                            xl_col_to_name(11 + periods_dict[period]['formula'][2]),
                        )
                    sheet.write_formula(row, column, formula, row_format_number)
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
                        sheet.write_formula(row, column, formula, row_format_number)
                    elif len(periods_dict[period]['formula']) == 5:
                        formula = 'sum({1}{0},{2}{0},{3}{0},{4}{0},{5}{0})'.format(
                            row + 1,
                            xl_col_to_name(11 + periods_dict[period]['formula'][0]),
                            xl_col_to_name(11 + periods_dict[period]['formula'][1]),
                            xl_col_to_name(11 + periods_dict[period]['formula'][2]),
                            xl_col_to_name(11 + periods_dict[period]['formula'][3]),
                            xl_col_to_name(11 + periods_dict[period]['formula'][4]),
                        )
                        sheet.write_formula(row, column, formula, row_format_number)
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
                        sheet.write_formula(row, column, formula, row_format_number)
                    column += 1
                else:
                    sheet.write_string(row, column, period, row_format_number)
                    column += 1
        #
        # # Поступление денежных средсв, с НДС
        # sumYear100etalon = sumYear75etalon = sumYear50etalon = sumYear100 = sumYear75 = sumYear50 = 0
        # sumQ100etalon = sumQ75etalon = sumQ50etalon = sumQ100 = sumQ75 = sumQ50 = 0
        # sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0
        #
        # for week_number in range(1, date(YEARint, 12, 28).isocalendar()[1] + 1):
        #
        #     sumQ100 = sumQ75 = sumQ50 = 0
        #
        #     sumQ75tmpetalon, sumQ50tmpetalon, sumQ100tmp, sumQ75tmp, sumQ50tmp = self.print_week_pds_project(sheet, row, column, week_number,
        #                                                                                 project, row_format_number, row_format_number_color_fact)
        #
        #     if sumQ100tmp == 0:
        #         sheet.write_number(row, column, 0, row_format_number_color_fact)
        #     if sumQ75tmp == 0:
        #         sheet.write_number(row, column + 1, 0, row_format_number)
        #     if sumQ50tmp == 0:
        #         sheet.write_number(row, column + 2, 0, row_format_number)
        #
        #     column += 3

    def print_row_values_office(self, workbook, sheet, row, column, YEAR, projects, project_office, formula_offices, multipliers):
        global strYEAR
        global YEARint

        row_format_number = workbook.add_format({
            'border': 1,
            'font_size': 10,
            'num_format': '#,##0',
            "fg_color": '#DDDDDD',
        })
        row_format_number_color_fact = workbook.add_format({
            "fg_color": '#A4BE92',
            'border': 1,
            'font_size': 10,
            'num_format': '#,##0',
        })
        row_format_number_color_percent = workbook.add_format({
            "fg_color": '#ffff99',
            'border': 1,
            'font_size': 10,
            'num_format': '0.00%',
        })
        row_format_number_color_forecast = workbook.add_format({
            "fg_color": '#D9E1F2',
            'border': 1,
            'font_size': 10,
            'num_format': '#,##0',
        })
        row_format_number_color_next = workbook.add_format({
            "fg_color": '#E2EFDA',
            'border': 1,
            'font_size': 10,
            'num_format': '#,##0',
        })
        head_format_month_itogo = workbook.add_format({
            'border': 1,
            "fg_color": '#D9E1F2',
            'diag_type': 3
        })

        column += 11

# Поступление денежных средств, с НДС

        for week_number in range(1, date(YEARint, 12, 28).isocalendar()[1] + 1):
            column += 1

            sumM100 = 0
            sumM75 = 0
            sumM50 = 0

            for project in projects:
                (sumM75tmpetalon, sumM50tmpetalon,
                 sumM100tmp, sumM75tmp, sumM50tmp,
                 sum_next_75_tmp, sum_next_50_tmp, sum_next_30_tmp,
                 sum_after_next_tmp) = self.calculate_weekly_pds(week_number, project, project_office, multipliers)

                sumM100 += sumM100tmp
                sumM75 += sumM75tmp
                sumM50 += sumM50tmp

            child_offices_rows = formula_offices.get('project_office_' + str(project_office.id)) or ''

            f_Q100 = 'sum(' + str(sumM100) + child_offices_rows.format(xl_col_to_name(column)) + ')'
            f_Q75 = 'sum(' + str(sumM75) + child_offices_rows.format(xl_col_to_name(column + 1)) + ')'
            f_Q50 = 'sum(' + str(sumM50) + child_offices_rows.format(xl_col_to_name(column + 2)) + ')'

            sheet.write_formula(row, column, f_Q100, row_format_number_color_fact)
            sheet.write_formula(row, column + 1, f_Q75, row_format_number)
            sheet.write_formula(row, column + 2, f_Q50, row_format_number)

            column += 2

# end Поступление денежных средсв, с НДС

    def print_row(self, sheet, workbook, row, data, periods_dict, max_level, formula_itogo):

        row_format = workbook.add_format({
            'border': 1,
            'font_size': 8
        })

        row_format_canceled_project = workbook.add_format({
            'border': 1,
            'font_size': 8
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

        for company in data:
            for office in data[company]:
                for project, content in data[company][office].items():
                    # печатаем строки проектов
                    row += 1
                    sheet.set_row(row, False, False, {'hidden': 1, 'level': max_level + 1})
                    cur_row_format = row_format
                    cur_row_format_number = row_format_number
                    column = 0
                    sheet.write_string(row, column, office, cur_row_format)
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

        return row, formula_itogo

    def printrow(self, sheet, workbook, companies, project_offices, budget, budget_ids, row, formula_itogo, level, multipliers):
        global strYEAR
        global YEARint
        global dict_formula, max_level

        head_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_size': 11,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#FFFF00'
        })
        head_format_1 = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "bold": False,
            "fg_color": '#C6E0B4',
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
            'font_size': 10,
            "bold": False,
            "num_format": '#,##0',
            "fg_color": '#DDDDDD',
        })

        row_format_company = workbook.add_format({
            'border': 1,
            'font_size': 12,
            "bold": True,
            "num_format": '#,##0',
            "top": 2,
            "fg_color": '#BBBBBB',
        })
        row_format_company_forecast = workbook.add_format({
            'border': 1,
            'font_size': 12,
            "bold": True,
            "num_format": '#,##0',
            "top": 2,
            'fg_color': '#D9E1F2',
        })
        row_format_company_fact = workbook.add_format({
            'border': 1,
            'font_size': 12,
            "bold": True,
            "num_format": '#,##0',
            "top": 2,
            "fg_color": '#829C70',
        })
        row_format_company_percent = workbook.add_format({
            'border': 1,
            'font_size': 12,
            "bold": True,
            'num_format': '0.00%',
            "top": 2,
            "fg_color": '#ffff99',
        })
        row_format_company_next = workbook.add_format({
            'border': 1,
            'font_size': 12,
            "bold": True,
            "num_format": '#,##0',
            "top": 2,
            "fg_color": '#E2EFDA',
        })

        row_format_date_month.set_num_format('mmm yyyy')

        row_format = workbook.add_format({
            'border': 1,
            'font_size': 8
        })

        row_format_canceled_project = workbook.add_format({
            'border': 1,
            'font_size': 8
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
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#A9D08E',
            "num_format": '#,##0',
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


        #project_offices = self.env['project_budget.project_office'].search([],order='name')  # для сортировки так делаем + берем сначала только верхние элементы

        isFoundProjectsByOffice = False
        isFoundProjectsByManager = False
        begRowProjectsByOffice = 0

        cur_budget_projects = self.env['project_budget.projects'].search([
            '&','&',
            ('commercial_budget_id', '=', budget.id),
            '|', '&', ('step_status', '=', 'step'),
            ('step_project_parent_id.project_have_steps', '=', True),
            '&', ('step_status', '=', 'project'),
            ('project_have_steps', '=', False),
            '|','|','|',
            ('id', 'in', [fact.projects_id.id for fact in self.env['project_budget.fact_cash_flow'].search([]) if fact.date_cash.year == YEARint]),
            ('id', 'in', [plan.projects_id.id for plan in self.env['project_budget.planned_cash_flow'].search([]) if plan.date_cash.year == YEARint]),
            ('id', 'in', [fact.step_project_child_id.id for fact in self.env['project_budget.fact_cash_flow'].search([]) if fact.date_cash.year == YEARint]),
            ('id', 'in', [plan.step_project_child_id.id for plan in self.env['project_budget.planned_cash_flow'].search([]) if plan.date_cash.year == YEARint]),
        ])

        # cur_project_offices = project_offices.filtered(lambda r: r in cur_budget_projects.project_office_id or r in {office.parent_id for office in cur_budget_projects.project_office_id if office.parent_id in project_offices})
        # cur_project_managers = project_managers.filtered(lambda r: r in cur_budget_projects.project_manager_id)
        cur_companies = companies.filtered(lambda r: r in cur_budget_projects.project_office_id.company_id)

        for company in cur_companies:
            print('company = ', company.name)
            isFoundProjectsByCompany = False
            formulaProjectCompany = '=sum(0'

            dict_formula['office_ids_not_empty'] = {}

            if company.id not in dict_formula['company_ids'] and set(self.env['project_budget.project_office'].search([]).ids) == set(project_office_ids):
                row += 1
                dict_formula['company_ids'][company.id] = row

            for project_office in project_offices.filtered(lambda r: r.company_id == company):

                print('project_office.name = ', project_office.name)

                begRowProjectsByOffice = 0

                if project_office.id not in dict_formula['office_ids']:
                    row += 1
                    dict_formula['office_ids'][project_office.id] = row

                row0 = row

                child_project_offices = self.env['project_budget.project_office'].search([('parent_id', '=', project_office.id)], order='report_sort')

                if project_office.child_ids:
                    dict_formula['office_ids'][project_office.id] = row
                    row0, formula_itogo = self.printrow(sheet, workbook, company, child_project_offices, budget, budget_ids, row, formula_itogo, level + 1, multipliers)

                isFoundProjectsByOffice = False
                if row0 != row:
                    isFoundProjectsByOffice = True

                row = row0

                formulaProjectOffice = '=sum(0'

                for spec in cur_budget_projects.filtered(lambda r: r.project_office_id == project_office or (r.different_project_offices_in_steps and r.project_have_steps)):

                    if spec.vgo == '-':

                        if begRowProjectsByOffice == 0:
                            begRowProjectsByOffice = row

                        if (spec.project_office_id == project_office
                            and spec.company_id == company
                            and spec.stage_id.code in ['100(done)', '100', '75', '50']
                            and self.is_project_in_year(spec)
                        ):
                            currency_rate = self.get_currency_rate_by_project(spec)
                            isFoundProjectsByOffice = True
                            isFoundProjectsByCompany = True

                            # печатаем строки проектов
                            row += 1
                            sheet.set_row(row, False, False, {'hidden': 1, 'level': max_level + 1})
                            cur_row_format = row_format
                            cur_row_format_number = row_format_number
                            if spec.stage_id.code == '0':
                                cur_row_format = row_format_canceled_project
                                cur_row_format_number = row_format_number_canceled_project
                            column = 0
                            sheet.write_string(row, column, spec.project_office_id.name, cur_row_format)
                            column += 1
                            sheet.write_string(row, column, spec.key_account_manager_id.name, cur_row_format)
                            column += 1
                            sheet.write_string(row, column, spec.partner_id.name, cur_row_format)
                            column += 1
                            sheet.write_string(row, column, spec.essence_project, cur_row_format)
                            column += 1
                            if spec.step_status == 'project':
                                sheet.write_string(row, column, (spec.step_project_number or '') + ' | ' + (spec.project_id or ''), cur_row_format)
                            elif spec.step_status == 'step':
                                sheet.write_string(row, column, (spec.step_project_number or '') + ' | ' + spec.step_project_parent_id.project_id + " | " + spec.project_id, cur_row_format)
                            column += 1
                            sheet.write_string(row, column, self.get_estimated_probability_name_forecast(spec.stage_id.code), cur_row_format)
                            column += 1
                            sheet.write_number(row, column, spec.total_amount_of_revenue_with_vat*currency_rate, cur_row_format_number)
                            column += 1
                            sheet.write_number(row, column, spec.margin_income*currency_rate, cur_row_format_number)
                            column += 1
                            sheet.write_number(row, column, spec.profitability, cur_row_format_number)
                            column += 1
                            sheet.write_string(row, column, spec.dogovor_number or '', cur_row_format)
                            column += 1
                            sheet.write_string(row, column, spec.vat_attribute_id.name, cur_row_format)
                            column += 1
                            sheet.write_string(row, column, '', cur_row_format)
                            column += 1
                            self.print_row_Values(workbook, sheet, row, column,  strYEAR, spec)

                if project_office.parent_id or set(self.env['project_budget.project_office'].search([]).ids) != set(project_office_ids):
                    isFoundProjectsByCompany = False

                if isFoundProjectsByOffice:

                    dict_formula['office_ids_not_empty'][project_office.id] = row

                    column = 0

                    office_row = dict_formula['office_ids'].get(project_office.id)

                    office_name = project_office.report_name or project_office.name

                    sheet.merge_range(office_row, column, office_row, column + 11, '       ' * level + office_name, row_format_office)

                    if set(self.env['project_budget.project_office'].search([]).ids) == set(project_office_ids):
                        sheet.set_row(office_row, False, False, {'level': level})
                    elif level > 1:
                        sheet.set_row(office_row, False, False, {'level': level - 1})

                    str_project_office_id = 'project_office_' + str(int(project_office.parent_id))
                    if str_project_office_id in dict_formula:
                        dict_formula[str_project_office_id] = dict_formula[str_project_office_id] + ',{0}' + str(office_row + 1)
                    else:
                        dict_formula[str_project_office_id] = ',{0}'+str(office_row+1)

                    formulaProjectOffice += ',{0}' + f'{begRowProjectsByOffice + 2}' + ':{0}' + f'{office_row}'

                    str_project_office_id = 'project_office_' + str(int(project_office.id))
                    if str_project_office_id in dict_formula:
                        formulaProjectOffice = formulaProjectOffice + dict_formula[str_project_office_id] + ')'
                    else:
                        formulaProjectOffice = formulaProjectOffice + ')'

                    projects = self.env['project_budget.projects'].search([
                        ('commercial_budget_id', '=', budget.id),
                        ('project_office_id', '=', project_office.id),
                        '|', '&', ('step_status', '=', 'step'),
                        ('step_project_parent_id.project_have_steps', '=', True),
                        '&', ('step_status', '=', 'project'),
                        ('project_have_steps', '=', False),
                        ])

                    self.print_row_values_office(
                        workbook,
                        sheet,
                        office_row,
                        column,
                        strYEAR,
                        projects,
                        project_office,
                        dict_formula,
                        multipliers,
                        )

                    if not project_office.parent_id:
                        formulaProjectCompany += ',{0}' + f'{office_row + 1}'
                else:
                    if all(child.id not in dict_formula['office_ids_not_empty'] for child in project_office.child_ids):
                        row -= 1

            if isFoundProjectsByCompany:
                column = 0

                company_row = dict_formula['company_ids'][company.id]

                sheet.merge_range(company_row, column, company_row, column + 11, company.name, row_format_company)

                column += 11

                formulaProjectCompany += ')'

                for colFormula in range(0, date(YEARint, 12, 28).isocalendar()[1]):
                    formula = formulaProjectCompany.format(xl_col_to_name(colFormula * 3 + column + 1))
                    sheet.write_formula(company_row,colFormula * 3 + column + 1, formula, row_format_company_fact)
                    formula = formulaProjectCompany.format(xl_col_to_name(colFormula * 3 + column + 2))
                    sheet.write_formula(company_row,colFormula * 3 + column + 2, formula, row_format_company)
                    formula = formulaProjectCompany.format(xl_col_to_name(colFormula * 3 + column + 3))
                    sheet.write_formula(company_row, colFormula * 3 + column + 3, formula, row_format_company)

        return row, formula_itogo

    def printworksheet(self, workbook, budget, namesheet, max_level, multipliers):
        global strYEAR
        global YEARint
        global project_office_ids

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
            "fg_color": '#95B3D7',
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

        date_format = workbook.add_format({'num_format': 'd mmmm yyyy'})
        row = 0
        sheet.write_string(row, 0, budget.name + ' ' + str(date.today()), bold)
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

        actual_budget_date = budget.date_actual or date.today()
        periods_dict, period_limits = self.calculate_periods_dict(actual_budget_date)
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

        data = self.get_data_from_projects(projects, periods_dict, budget)

        column = self.print_head(workbook, sheet, row, column, periods_dict, actual_budget_date)
        row += 2

        companies = self.env['res.company'].search([], order='name')

        if project_office_ids:
            project_offices = self.env['project_budget.project_office'].search([
                ('id','in',project_office_ids), ('parent_id', 'not in', project_office_ids)], order='report_sort')  # для сортировки так делаем + не берем дочерние оффисы, если выбраны их материнские
        else:
            project_offices = self.env['project_budget.project_office'].search([
                ('parent_id', '=', False)], order='report_sort')  # для сортировки так делаем + берем сначала только верхние элементы

        formula_itogo = '=sum(0'

        row, formula_itogo = self.print_row(sheet, workbook, row, data, periods_dict, max_level, formula_itogo)

        if set(self.env['project_budget.project_office'].search([]).ids) == set(project_office_ids):
            row += 1
            column = 0
            sheet.merge_range(row, column, row, column + 11, 'ИТОГО по отчету', row_format_number_itogo)
            for company_row in dict_formula['company_ids'].values():
                formula_itogo += ',{0}' + str(company_row + 1)
            formula_itogo = formula_itogo + ')'
            for colFormula in range(12, date(YEARint, 12, 28).isocalendar()[1] * 3 + 12):
                formula = formula_itogo.format(xl_col_to_name(colFormula))
                sheet.write_formula(row, colFormula, formula, row_format_number_itogo)
            print('dict_formula = ', dict_formula)

    def generate_xlsx_report(self, workbook, data, budgets):

        # год не нужен
        global strYEAR
        strYEAR = str(data['year'])
        global YEARint
        YEARint = int(strYEAR)
        # ---

        global dict_formula, max_level
        dict_formula = {'company_ids': {}, 'office_ids': {}, 'office_ids_not_empty': {}}

        global project_office_ids
        project_office_ids = data['project_office_ids']

        ids = [office.id for office in self.env['project_budget.project_office'].search([('parent_id', '=', False), ('id', 'in', project_office_ids)])]

        max_level = self.offices_with_parents(ids, 0)

        if set(self.env['project_budget.project_office'].search([]).ids) != set(project_office_ids):
            max_level -= 1

        multipliers = {'50': data['koeff_reserve'], '30': data['koeff_potential']}

        commercial_budget_id = data['commercial_budget_id']
        print('commercial_budget_id', commercial_budget_id)
        budget = self.env['project_budget.commercial_budget'].search([('id', '=', commercial_budget_id)])
        self.printworksheet(workbook, budget, 'ПДС', max_level, multipliers)
