from odoo import models
from datetime import date, timedelta
import xlsxwriter
from xlsxwriter.utility import xl_col_to_name
import logging

isdebug = False
logger = logging.getLogger("*___forecast_report___*")


class VirtualCompany:

    def __init__(self, id, name):
        self.id = id
        self.name = name


class report_management_committee_excel(models.AbstractModel):
    _name = 'report.project_budget.report_management_committee_excel'
    _description = 'project_budget.report_management_committee_excel'
    _inherit = 'report.report_xlsx.abstract'

    strYEAR = '2023'
    YEARint = int(strYEAR)

    def isProjectinYear(self, project):
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
        1: {'name': 'Контрактование, с НДС', 'color': '#FFD966'},
        2: {'name': 'Поступление денежных средств, с НДС', 'color': '#D096BF'},
        3: {'name': 'Валовая Выручка, без НДС', 'color': '#B4C6E7'},
        4: {'name': 'Валовая прибыль (Маржа 1), без НДС', 'color': '#F4FD9F'},
    }

    plan_types = {
        'contraction': 'contracting',
        'cash_flow': 'cash',
        'gross_revenue': 'acceptance',
        'margin': 'margin_income',
    }

    def get_estimated_probability_name_forecast(self, name):
        result = name
        return result
        # сказали не надо словами
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

    def get_sum_fact_pds_project_year_quarter(self, project, year, quarter, without_distributions):

        sum_cash = 0

        if quarter:
            months = self.get_months_from_quarter(quarter)

        if project.step_status == 'project':
            pds_list = project.fact_cash_flow_ids
        elif project.step_status == 'step':
            pds_list = project.fact_step_cash_flow_ids

        for pds in pds_list:
            if (not quarter or pds.date_cash.month in months) and pds.date_cash.year == year:
                if without_distributions and pds.distribution_cash_ids:
                    continue
                sum_cash += pds.sum_cash

        return sum_cash

    def get_sum_plan_pds_project_year_quarter(self, project, year, quarter):
        global strYEAR
        global YEARint

        sum_cash = {'commitment': 0, 'reserve': 0, 'potential': 0}

        if quarter:
            months = self.get_months_from_quarter(quarter)

        if project.step_status == 'project':
            pds_list = project.planned_cash_flow_ids
        elif project.step_status == 'step':
            pds_list = project.planned_step_cash_flow_ids

        for pds in pds_list:
            if (not quarter or pds.date_cash.month in months) and pds.date_cash.year == year:
                stage_id_code = project.stage_id.code
                if pds.forecast == 'from_project':
                    if stage_id_code in ('75', '100', '100(done)'):
                        sum_cash['commitment'] += pds.sum_cash
                    elif stage_id_code == '50':
                        sum_cash['reserve'] += pds.sum_cash
                    elif stage_id_code == '30':
                        sum_cash['potential'] += pds.sum_cash
                else:
                    if stage_id_code != '0':
                        sum_cash[pds.forecast] += pds.sum_cash
        return sum_cash

    def print_quater_head(self, workbook, sheet, row, column, YEAR):
        global strYEAR
        global YEARint

        for x in self.dict_contract_pds.items():
            y = list(x[1].values())
            head_format_month = workbook.add_format({
                'border': 1,
                'text_wrap': True,
                'align': 'center',
                'valign': 'vcenter',
                "bold": True,
                "fg_color": y[1],
                "font_size": 11,
            })
            head_format_month_dark = workbook.add_format({
                'border': 1,
                'text_wrap': True,
                'align': 'center',
                'valign': 'vcenter',
                "bold": True,
                "fg_color": '#' + hex(int(y[1][1:], 16) - 0x303030)[2:],
                "font_size": 11,
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
            head_format_month_detail_next = workbook.add_format({
                'border': 1,
                'text_wrap': True,
                'align': 'center',
                'valign': 'vcenter',
                "bold": False,
                "fg_color": '#F3F8F0',
                "font_size": 9,
            })

            colbeg = column

            for elementone in self.quarter_rus_name:

                element = elementone.replace('YEAR', strYEAR)

                sheet.set_row(row + 1, 25)
                sheet.set_row(row + 2, 25)

                if 'NEXT' not in element:
                    if 'Q1' in elementone or 'Q2' in elementone :
                        sheet.set_column(column, column + 3, 13, False, {'hidden': 1, 'level': 2})
                        sheet.merge_range(row, column, row, column + 3, element, head_format_month)
                        sheet.merge_range(row + 1, column, row + 2, column, "План " + element,
                                          head_format_month_itogo)
                        column += 1
                        sheet.merge_range(row + 1, column, row + 2, column, 'Факт', head_format_month_detail_fact)
                        column += 1
                        sheet.merge_range(row + 1, column, row + 1, column + 1,
                                          'Прогноз до конца периода (на дату отчета)',
                                          head_format_month_detail)
                        sheet.write_string(row + 2, column, 'Обязательство', head_format_month_detail)
                        column += 1
                        sheet.write_string(row + 2, column, 'Резерв', head_format_month_detail)
                        column += 1
                    elif 'HY1' in elementone:
                        sheet.set_column(column, column + 4, 13, False, {'hidden': 1, 'level': 1})
                        sheet.merge_range(row, column, row, column + 4, element, head_format_month)
                        sheet.merge_range(row + 1, column, row + 2, column, "План " + element,
                                          head_format_month_itogo)
                        column += 1
                        sheet.merge_range(row + 1, column, row + 2, column, 'Факт', head_format_month_detail_fact)
                        column += 1
                        sheet.merge_range(row + 1, column, row + 2, column, "% исполнения плана " + element,
                                          head_format_month_itogo_percent)
                        column += 1
                        sheet.merge_range(row + 1, column, row + 1, column + 1,
                                          'Прогноз до конца периода (на дату отчета)',
                                          head_format_month_detail)
                        sheet.write_string(row + 2, column, 'Обязательство', head_format_month_detail)
                        column += 1
                        sheet.write_string(row + 2, column, 'Резерв', head_format_month_detail)
                        column += 1
                    elif 'Q3' in elementone or 'Q4' in elementone :
                        sheet.set_column(column, column + 4, 13, False, {'hidden': 1, 'level': 2})
                        sheet.merge_range(row, column, row, column + 4, element, head_format_month)
                        sheet.merge_range(row + 1, column, row + 2, column, "План " + element,
                                          head_format_month_itogo)
                        column += 1
                        sheet.merge_range(row + 1, column, row + 2, column, "План " + element + " 6+6",
                                          head_format_month_itogo_6_plus_6)
                        column += 1
                        sheet.merge_range(row + 1, column, row + 2, column, 'Факт', head_format_month_detail_fact)
                        column += 1
                        sheet.merge_range(row + 1, column, row + 1, column + 1,
                                          'Прогноз до конца периода (на дату отчета)',
                                          head_format_month_detail)
                        sheet.write_string(row + 2, column, 'Обязательство', head_format_month_detail)
                        column += 1
                        sheet.write_string(row + 2, column, 'Резерв', head_format_month_detail)
                        column += 1
                    elif 'HY2' in elementone:
                        sheet.set_column(column, column + 4, 13, False, {'hidden': 1, 'level': 1})
                        sheet.merge_range(row, column, row, column + 4, element, head_format_month)
                        sheet.merge_range(row + 1, column, row + 2, column, "План " + element,
                                          head_format_month_itogo)
                        column += 1
                        sheet.merge_range(row + 1, column, row + 2, column, "План " + element + " 6+6",
                                          head_format_month_itogo_6_plus_6)
                        column += 1
                        sheet.merge_range(row + 1, column, row + 2, column, 'Факт', head_format_month_detail_fact)
                        column += 1
                        sheet.merge_range(row + 1, column, row + 1, column + 1,
                                          'Прогноз до конца периода (на дату отчета)',
                                          head_format_month_detail)
                        sheet.write_string(row + 2, column, 'Обязательство', head_format_month_detail)
                        column += 1
                        sheet.write_string(row + 2, column, 'Резерв', head_format_month_detail)
                        column += 1
                    elif element == YEAR:
                        sheet.set_column(column, column + 5, 13, False)
                        sheet.merge_range(row, column, row, column + 5, element, head_format_month)
                        sheet.merge_range(row + 1, column, row + 2, column, "План " + element,
                                          head_format_month_itogo)
                        column += 1
                        sheet.merge_range(row + 1, column, row + 2, column, "План " + element + " 6+6",
                                          head_format_month_itogo_6_plus_6)
                        column += 1
                        sheet.merge_range(row + 1, column, row + 2, column, 'Факт', head_format_month_detail_fact)
                        column += 1
                        sheet.merge_range(row + 1, column, row + 2, column, "% исполнения плана 6+6 " + element,
                                          head_format_month_itogo_percent)
                        column += 1
                        sheet.merge_range(row + 1, column, row + 1, column + 1,
                                          'Прогноз до конца периода (на дату отчета)',
                                          head_format_month_detail)
                        sheet.write_string(row + 2, column, 'Обязательство', head_format_month_detail)
                        column += 1
                        sheet.write_string(row + 2, column, 'Резерв', head_format_month_detail)
                        column += 1
                elif element == 'NEXT':
                    if x[0] == 2:  # ПДС
                        sheet.merge_range(row, column, row, column + 1,str(YEARint + 1), head_format_month)
                        sheet.set_column(column, column + 2, 13, False, {'hidden': 1, 'level': 1})
                        sheet.merge_range(row + 1, column, row + 1, column + 1, 'Прогноз ' + str(YEARint + 1), head_format_month_detail_next)
                    else:
                        sheet.merge_range(row, column, row, column + 2,str(YEARint + 1), head_format_month)
                        sheet.set_column(column, column + 3, 13, False, {'hidden': 1, 'level': 1})
                        sheet.merge_range(row + 1, column, row + 1, column + 2, 'Прогноз ' + str(YEARint + 1), head_format_month_detail_next)
                    sheet.write_string(row + 2, column, 'Обязательство', head_format_month_detail_next)
                    column += 1
                    sheet.write_string(row + 2, column, 'Резерв', head_format_month_detail_next)
                    column += 1
                    if x[0] != 2:
                        sheet.write_string(row + 2, column, 'Потенциал', head_format_month_detail_next)
                        column += 1

                elif element == 'AFTER NEXT':
                    sheet.write_string(row, column, str(YEARint + 2), head_format_month)
                    sheet.set_column(column, column, 13, False, {'hidden': 1, 'level': 1})
                    sheet.merge_range(row + 1, column, row + 2, column, 'Прогноз ' + str(YEARint + 2),
                                      head_format_month_detail_next)
                    column += 1

            sheet.merge_range(row - 1, colbeg, row - 1, column - 1, y[0], head_format_month)
        return column

    def print_quarter_revenue_project(self, sheet, row, column, element, project, responsibility_center, params, row_format_number, row_format_number_color_fact):
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

        if 'Q1' in element or 'Q2' in element :

            months = self.get_months_from_quarter(element)

            if project.end_presale_project_month.month in months and YEARint == project.end_presale_project_month.year:
                if project.stage_id.code in ('100','100(done)'):
                    sheet.write_number(row, column + 1, project.amount_total_in_company_currency, row_format_number_color_fact)
                    sum100tmp += project.amount_total_in_company_currency
                if project.stage_id.code == '75':
                    sheet.write_number(row, column + 2, project.amount_total_in_company_currency, row_format_number)
                    sum75tmp += project.amount_total_in_company_currency
                if project.stage_id.code == '50':
                    sheet.write_number(row, column + 3, project.amount_total_in_company_currency, row_format_number)
                    sum50tmp += project.amount_total_in_company_currency

        elif 'Q3' in element or 'Q4' in element :

            months = self.get_months_from_quarter(element)

            if project.end_presale_project_month.month in months and YEARint == project.end_presale_project_month.year:
                if project.stage_id.code in ('100','100(done)'):
                    sheet.write_number(row, column + 2, project.amount_total_in_company_currency, row_format_number_color_fact)
                    sum100tmp += project.amount_total_in_company_currency
                if project.stage_id.code == '75':
                    sheet.write_number(row, column + 3, project.amount_total_in_company_currency, row_format_number)
                    sum75tmp += project.amount_total_in_company_currency
                if project.stage_id.code == '50':
                    sheet.write_number(row, column + 4, project.amount_total_in_company_currency, row_format_number)
                    sum50tmp += project.amount_total_in_company_currency

        elif element == 'NEXT':

            if project.end_presale_project_month.year == YEARint + 1:
                if project.stage_id.code in ('75', '100'):
                    sheet.write_number(row, column + 0,
                                       project.amount_total_in_company_currency,
                                       row_format_number)
                    sum_next_75_tmp = project.amount_total_in_company_currency
                if project.stage_id.code == '50':
                    sheet.write_number(row, column + 1,
                                       project.amount_total_in_company_currency * params['50'],
                                       row_format_number)
                    sum_next_50_tmp = project.amount_total_in_company_currency * params['50']
                if project.stage_id.code == '30':
                    sheet.write_number(row, column + 2,
                                       project.amount_total_in_company_currency * params['30'],
                                       row_format_number)
                    sum_next_30_tmp = project.amount_total_in_company_currency * params['30']
            elif project.end_presale_project_month.year == YEARint + 2:
                if project.stage_id.code in ('75', '100'):
                    sum_after_next_tmp = project.amount_total_in_company_currency
                if project.stage_id.code == '50':
                    sum_after_next_tmp = project.amount_total_in_company_currency * params[
                        '50']
                if project.stage_id.code == '30':
                    sum_after_next_tmp = project.amount_total_in_company_currency * params[
                        '30']
                sheet.write_number(row, column + 3,
                                   sum_after_next_tmp,
                                   row_format_number)

        return sum75tmpetalon, sum50tmpetalon, sum100tmp, sum75tmp, sum50tmp

    def calculate_quarter_revenue(self, element, project, responsibility_center, params):
        global strYEAR
        global YEARint

        sum75tmpetalon = 0
        sum50tmpetalon = 0
        sum100tmp = 0
        sum75tmp = 0
        sum50tmp = 0
        sum_next_75_q1_tmp = 0
        sum_next_50_q1_tmp = 0
        sum_next_30_q1_tmp = 0
        sum_next_75_tmp = 0
        sum_next_50_tmp = 0
        sum_next_30_tmp = 0
        sum_after_next_tmp = 0

        if 'Q' in element:

            months = self.get_months_from_quarter(element)

            if project.stage_id.code not in ('0', '10'):

                if project.end_presale_project_month.month in months and YEARint == project.end_presale_project_month.year:
                    if project.stage_id.code in ('100', '100(done)'):
                        sum100tmp = project.amount_total_in_company_currency
                    if project.stage_id.code == '75':
                        sum75tmp = project.amount_total_in_company_currency
                    if project.stage_id.code == '50':
                        sum50tmp = project.amount_total_in_company_currency

        elif 'NEXT' in element:
            if project.stage_id.code not in ('0', '10'):

                if project.end_presale_project_month.year == YEARint + 1 and project.end_presale_project_month.month in self.get_months_from_quarter('Q1'):
                    if project.stage_id.code in ('75', '100'):
                        sum_next_75_q1_tmp = project.amount_total_in_company_currency
                    if project.stage_id.code == '50':
                        sum_next_50_q1_tmp = project.amount_total_in_company_currency * params['50']
                    if project.stage_id.code == '30':
                        sum_next_30_q1_tmp = project.amount_total_in_company_currency * params['30']
                if project.end_presale_project_month.year == YEARint + 1:
                    if project.stage_id.code in ('75', '100'):
                        sum_next_75_tmp = project.amount_total_in_company_currency
                    if project.stage_id.code == '50':
                        sum_next_50_tmp = project.amount_total_in_company_currency * params['50']
                    if project.stage_id.code == '30':
                        sum_next_30_tmp = project.amount_total_in_company_currency * params['30']
                elif project.end_presale_project_month.year == YEARint + 2:
                    if project.stage_id.code in ('75', '100'):
                        sum_after_next_tmp = project.amount_total_in_company_currency
                    if project.stage_id.code == '50':
                        sum_after_next_tmp = project.amount_total_in_company_currency * params[
                            '50']
                    if project.stage_id.code == '30':
                        sum_after_next_tmp = project.amount_total_in_company_currency * params[
                            '30']

        return (sum75tmpetalon, sum50tmpetalon,
                sum100tmp, sum75tmp, sum50tmp,
                sum_next_75_q1_tmp, sum_next_50_q1_tmp, sum_next_30_q1_tmp,
                sum_next_75_tmp, sum_next_50_tmp, sum_next_30_tmp,
                sum_after_next_tmp)

    def get_pds_forecast_from_distributions(self, sum, project, year, months):

        sum_distribution_pds = 0
        has_distribution = False
        sum_ostatok_pds = {'commitment': 0, 'reserve': 0, 'potential': 0}

        if project.step_status == 'project':
            pds_list = project.planned_cash_flow_ids
        elif project.step_status == 'step':
            pds_list = project.planned_step_cash_flow_ids

        for planned_cash in pds_list:
            if (not months or planned_cash.date_cash.month in months) and planned_cash.date_cash.year == year:

                sum_distribution_pds += planned_cash.distribution_sum_without_vat

                stage_id_code = project.stage_id.code

                if (planned_cash.distribution_sum_with_vat_ostatok > 0 and planned_cash.sum_cash > 0
                        or planned_cash.distribution_sum_with_vat_ostatok < 0 and planned_cash.sum_cash < 0):  # учитываем отрицательный ПДС для Энсиса
                    if planned_cash.forecast == 'from_project':
                        if stage_id_code in ('75', '100', '100(done)'):
                            sum_ostatok_pds['commitment'] += planned_cash.distribution_sum_with_vat_ostatok
                        elif stage_id_code == '50':
                            sum_ostatok_pds['reserve'] += planned_cash.distribution_sum_with_vat_ostatok
                        elif stage_id_code == '30':
                            sum_ostatok_pds['potential'] += planned_cash.distribution_sum_with_vat_ostatok
                    else:
                        if stage_id_code != '0':
                            sum_ostatok_pds[planned_cash.forecast] += planned_cash.distribution_sum_with_vat_ostatok
        if sum_distribution_pds != 0:  # если есть распределение, то остаток = остатку распределения
            for key in sum:
                sum[key] = sum_ostatok_pds[key]
                # if not project.is_correction_project:
                #     sum[key] = max(sum_ostatok_pds[key], 0)
                # else:
                #     sum[key] = sum_ostatok_pds[key]
        return sum

    def print_quarter_pds_project(self, sheet, row, column, element, project, responsibility_center, params, row_format_number, row_format_number_color_fact):
        global strYEAR
        global YEARint

        sum75tmpetalon = 0
        sum50tmpetalon = 0
        sum100tmp = 0
        sum75tmp = 0
        sum50tmp = 0
        sum_next_75_q1_tmp = 0
        sum_next_50_q1_tmp = 0
        sum_next_30_q1_tmp = 0
        sum_next_75_tmp = 0
        sum_next_50_tmp = 0
        sum_next_30_tmp = 0
        sum_after_next_tmp = 0

        if 'Q1' in element or 'Q2' in element :
            months = self.get_months_from_quarter(element)

            sum100tmp = self.get_sum_fact_pds_project_year_quarter(project, YEARint, element, False)
            pds_fact_wo_distributions = self.get_sum_fact_pds_project_year_quarter(project, YEARint, element, True)
            sheet.write_number(row, column + 1, sum100tmp, row_format_number_color_fact)

            sum = self.get_sum_plan_pds_project_year_quarter(project, YEARint, element)

            if not project.is_correction_project:
                if abs(pds_fact_wo_distributions) >= abs(sum['commitment']):  # учитываем отрицательный ПДС для Энсиса
                    sum100tmp_ostatok = pds_fact_wo_distributions - sum['commitment']
                    sum['commitment'] = 0
                    sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                else:
                    sum['commitment'] = sum['commitment'] - pds_fact_wo_distributions

            # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
            sum = self.get_pds_forecast_from_distributions(sum, project, YEARint, months)

            sheet.write_number(row, column + 2, sum['commitment'], row_format_number)
            sum75tmp += sum['commitment']
            sheet.write_number(row, column + 3, sum['reserve'], row_format_number)
            sum50tmp += sum['reserve']

        if 'Q3' in element or 'Q4' in element :
            months = self.get_months_from_quarter(element)

            sum100tmp = self.get_sum_fact_pds_project_year_quarter(project, YEARint, element, False)
            pds_fact_wo_distributions = self.get_sum_fact_pds_project_year_quarter(project, YEARint, element, True)

            sheet.write_number(row, column + 2, sum100tmp, row_format_number_color_fact)

            sum = self.get_sum_plan_pds_project_year_quarter(project, YEARint, element)

            if not project.is_correction_project:
                if abs(pds_fact_wo_distributions) >= abs(sum['commitment']):
                    sum100tmp_ostatok = pds_fact_wo_distributions - sum['commitment']
                    sum['commitment'] = 0
                    sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                else:
                    sum['commitment'] = sum['commitment'] - pds_fact_wo_distributions

            # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
            sum = self.get_pds_forecast_from_distributions(sum, project, YEARint, months)

            sheet.write_number(row, column + 3, sum['commitment'], row_format_number)
            sum75tmp += sum['commitment']
            sheet.write_number(row, column + 4, sum['reserve'], row_format_number)
            sum50tmp += sum['reserve']

        elif element == 'NEXT':

            sum100tmp_q1 = self.get_sum_fact_pds_project_year_quarter(project, YEARint + 1, 'Q1', False)
            sum100tmp = self.get_sum_fact_pds_project_year_quarter(project, YEARint + 1, False, False)
            pds_fact_wo_distributions_q1 = self.get_sum_fact_pds_project_year_quarter(project, YEARint + 1, 'Q1', True)
            pds_fact_wo_distributions = self.get_sum_fact_pds_project_year_quarter(project, YEARint + 1, False, True)
            sum_q1 = self.get_sum_plan_pds_project_year_quarter(project, YEARint + 1, 'Q1')
            sum = self.get_sum_plan_pds_project_year_quarter(project, YEARint + 1, False)

            if not project.is_correction_project:
                if abs(pds_fact_wo_distributions_q1) >= abs(sum_q1['commitment']):
                    sum100tmp_q1_ostatok = pds_fact_wo_distributions_q1 - sum_q1['commitment']
                    sum_q1['commitment'] = 0
                    sum_q1['reserve'] = max(sum_q1['reserve'] - sum100tmp_q1_ostatok, 0)
                else:
                    sum_q1['commitment'] = sum_q1['commitment'] - pds_fact_wo_distributions_q1

                if abs(pds_fact_wo_distributions) >= abs(sum['commitment']):
                    sum100tmp_ostatok = pds_fact_wo_distributions - sum['commitment']
                    sum['commitment'] = 0
                    sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                else:
                    sum['commitment'] = sum['commitment'] - pds_fact_wo_distributions

            # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
            sum_q1 = self.get_pds_forecast_from_distributions(sum_q1, project, YEARint + 1, self.get_months_from_quarter('Q1'))
            sum = self.get_pds_forecast_from_distributions(sum, project, YEARint + 1, False)

            sheet.write_number(row, column + 0, sum['commitment'], row_format_number)
            sum_next_75_tmp += sum['commitment']
            sheet.write_number(row, column + 1, sum['reserve'] * params['50'], row_format_number)
            sum_next_50_tmp += sum['reserve'] * params['50']
            # sheet.write_number(row, column + 2, sum['potential'] * params['30'], row_format_number)
            # sum_next_30_tmp += sum['potential'] * params['30']

        elif element == 'AFTER NEXT':

            sum100tmp = self.get_sum_fact_pds_project_year_quarter(project, YEARint + 2, False, False)
            pds_fact_wo_distributions = self.get_sum_fact_pds_project_year_quarter(project, YEARint + 2, False, True)
            sum = self.get_sum_plan_pds_project_year_quarter(project, YEARint + 2, False)

            if not project.is_correction_project:
                if abs(pds_fact_wo_distributions) >= abs(sum['commitment']):
                    sum100tmp_ostatok = pds_fact_wo_distributions - sum['commitment']
                    sum['commitment'] = 0
                    sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                else:
                    sum['commitment'] = sum['commitment'] - pds_fact_wo_distributions

            # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
            sum = self.get_pds_forecast_from_distributions(sum , project, YEARint + 2, False)

            sum_after_next_tmp += sum['commitment']
            sum_after_next_tmp += sum['reserve'] * params['50']
            # sum_after_next_tmp += sum['potential'] * params['30']
            sheet.write_number(row, column + 0, sum_after_next_tmp, row_format_number)

        return sum75tmpetalon, sum50tmpetalon, sum100tmp, sum75tmp, sum50tmp

    def calculate_quarter_pds(self, element, project, responsibility_center, params):
        global strYEAR
        global YEARint

        sum75tmpetalon = 0
        sum50tmpetalon = 0
        sum100tmp = 0
        sum75tmp = 0
        sum50tmp = 0
        sum_next_75_q1_tmp = 0
        sum_next_50_q1_tmp = 0
        sum_next_30_q1_tmp = 0
        sum_next_75_tmp = 0
        sum_next_50_tmp = 0
        sum_next_30_tmp = 0
        sum_after_next_tmp = 0

        if 'Q' in element:

            months = self.get_months_from_quarter(element)

            if project.stage_id.code not in ('0', '10'):

                sum100tmp = self.get_sum_fact_pds_project_year_quarter(project, YEARint, element, False)
                pds_fact_wo_distributions = self.get_sum_fact_pds_project_year_quarter(project, YEARint, element, True)
                sum = self.get_sum_plan_pds_project_year_quarter(project, YEARint, element)

                if not project.is_correction_project:
                    if abs(pds_fact_wo_distributions) >= abs(sum['commitment']):
                        sum100tmp_ostatok = pds_fact_wo_distributions - sum['commitment']
                        sum['commitment'] = 0
                        sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                    else:
                        sum['commitment'] = sum['commitment'] - pds_fact_wo_distributions

                # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                sum = self.get_pds_forecast_from_distributions(sum, project, YEARint, months)

                sum75tmp += sum['commitment']
                sum50tmp += sum['reserve']

        elif element == 'NEXT':
            if project.stage_id.code not in ('0', '10'):

                sum100tmp_q1 = self.get_sum_fact_pds_project_year_quarter(project, YEARint + 1, 'Q1', False)
                sum100tmp = self.get_sum_fact_pds_project_year_quarter(project, YEARint + 1, False, False)
                pds_fact_wo_distributions_q1 = self.get_sum_fact_pds_project_year_quarter(project, YEARint + 1, 'Q1', True)
                pds_fact_wo_distributions = self.get_sum_fact_pds_project_year_quarter(project, YEARint + 1, False, True)
                sum_q1 = self.get_sum_plan_pds_project_year_quarter(project, YEARint + 1, 'Q1')
                sum = self.get_sum_plan_pds_project_year_quarter(project, YEARint + 1, False)

                if not project.is_correction_project:
                    if abs(pds_fact_wo_distributions_q1) >= abs(sum_q1['commitment']):
                        sum100tmp_q1_ostatok = pds_fact_wo_distributions_q1 - sum_q1['commitment']
                        sum_q1['commitment'] = 0
                        sum_q1['reserve'] = max(sum_q1['reserve'] - sum100tmp_q1_ostatok, 0)
                    else:
                        sum_q1['commitment'] = sum_q1['commitment'] - pds_fact_wo_distributions_q1

                    if abs(pds_fact_wo_distributions) >= abs(sum['commitment']):
                        sum100tmp_ostatok = pds_fact_wo_distributions - sum['commitment']
                        sum['commitment'] = 0
                        sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                    else:
                        sum['commitment'] = sum['commitment'] - pds_fact_wo_distributions

                # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                sum_q1 = self.get_pds_forecast_from_distributions(sum_q1, project, YEARint + 1, self.get_months_from_quarter('Q1'))
                sum = self.get_pds_forecast_from_distributions(sum, project, YEARint + 1, False)

                sum_next_75_q1_tmp += sum_q1['commitment']
                sum_next_50_q1_tmp += sum_q1['reserve'] * params['50']
                # sum_next_30_q1_tmp += sum_q1['potential'] * params['30']

                sum_next_75_tmp += sum['commitment']
                sum_next_50_tmp += sum['reserve'] * params['50']
                # sum_next_30_tmp += sum['potential'] * params['30']

        elif element == 'AFTER NEXT':

            if project.stage_id.code not in ('0', '10'):

                sum100tmp = self.get_sum_fact_pds_project_year_quarter(project, YEARint + 2, False, False)
                pds_fact_wo_distributions = self.get_sum_fact_pds_project_year_quarter(project, YEARint + 2, False, True)
                sum = self.get_sum_plan_pds_project_year_quarter(project, YEARint + 2, False)

                if not project.is_correction_project:
                    if abs(pds_fact_wo_distributions) >= abs(sum['commitment']):
                        sum100tmp_ostatok = pds_fact_wo_distributions - sum['commitment']
                        sum['commitment'] = 0
                        sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                    else:
                        sum['commitment'] = sum['commitment'] - pds_fact_wo_distributions

                # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                sum = self.get_pds_forecast_from_distributions(sum, project, YEARint + 2, False)

                sum_after_next_tmp += sum['commitment']
                sum_after_next_tmp += sum['reserve'] * params['50']
                # sum_after_next_tmp += sum['potential'] * params['30']

        return (sum75tmpetalon, sum50tmpetalon,
                sum100tmp, sum75tmp, sum50tmp,
                sum_next_75_q1_tmp, sum_next_50_q1_tmp, sum_next_30_q1_tmp,
                sum_next_75_tmp, sum_next_50_tmp, sum_next_30_tmp,
                sum_after_next_tmp)

    def get_sum_fact_acceptance_project_year_quarter(self, project, year, quarter, without_distributions):
        sum_cash = 0

        if quarter:
            months = self.get_months_from_quarter(quarter)

        if project.step_status == 'project':
            acceptance_list = project.fact_acceptance_flow_ids
        elif project.step_status == 'step':
            acceptance_list = project.fact_step_acceptance_flow_ids

        if acceptance_list:
            for acceptance in acceptance_list:
                if (not quarter or acceptance.date_cash.month in months) and acceptance.date_cash.year == year:
                    if without_distributions and acceptance.distribution_acceptance_ids:
                        continue
                    sum_cash += acceptance.sum_cash_without_vat
        return sum_cash

    def get_sum_fact_margin_project_year_quarter(self, project, year, quarter, without_distributions):
        if project.is_parent_project:
            if project.margin_from_children_to_parent:
                sum_cash, sum_cash_without_manual = self.get_margin_fact(project, year, quarter, without_distributions, 1)
                for child_project in project.child_project_ids:
                    if child_project.project_have_steps:
                        for child_step in child_project.step_project_child_ids:
                            child_sum_cash, child_sum_cash_without_manual = self.get_margin_fact(child_step, year,
                                                                                                 quarter,
                                                                                                 without_distributions,
                                                                                                 child_project.margin_rate_for_parent)
                            sum_cash += child_sum_cash
                            sum_cash_without_manual += child_sum_cash_without_manual
                    else:
                        child_sum_cash, child_sum_cash_without_manual = self.get_margin_fact(child_project, year, quarter, without_distributions, child_project.margin_rate_for_parent)
                        sum_cash += child_sum_cash
                        sum_cash_without_manual += child_sum_cash_without_manual
            else:
                total_percent = 0
                for child_project in project.child_project_ids:
                    total_percent += child_project.margin_rate_for_parent
                sum_cash, sum_cash_without_manual = self.get_margin_fact(project, year, quarter, without_distributions, (1 - total_percent))
        elif project.is_child_project:
            if project.parent_project_id.margin_from_children_to_parent:
                sum_cash, sum_cash_without_manual = self.get_margin_fact(project, year, quarter, without_distributions, (1 - project.margin_rate_for_parent))
            else:
                sum_cash, sum_cash_without_manual = self.get_margin_fact(project, year, quarter, without_distributions, 1)
                if project.parent_project_id.project_have_steps:
                    for parent_step in project.parent_project_id.step_project_child_ids:
                        parent_sum_cash, parent_sum_cash_without_manual = self.get_margin_fact(
                            parent_step, year, quarter, without_distributions, project.margin_rate_for_parent
                        )
                        sum_cash += parent_sum_cash
                        sum_cash_without_manual += parent_sum_cash_without_manual
                else:
                    parent_sum_cash, parent_sum_cash_without_manual = self.get_margin_fact(
                        project.parent_project_id, year, quarter, without_distributions, project.margin_rate_for_parent
                    )
                    sum_cash += parent_sum_cash
                    sum_cash_without_manual += parent_sum_cash_without_manual
        else:
            sum_cash, sum_cash_without_manual = self.get_margin_fact(project, year, quarter, without_distributions, 1)
        return sum_cash, sum_cash_without_manual

    def get_margin_fact(self, project, year, quarter, without_distributions, multiplier):
        sum_cash = 0
        sum_cash_without_manual = 0

        if quarter:
            months = self.get_months_from_quarter(quarter)

        if project.step_status == 'project':
            acceptance_list = project.fact_acceptance_flow_ids
        elif project.step_status == 'step':
            acceptance_list = project.fact_step_acceptance_flow_ids

        if acceptance_list:
            for acceptance in acceptance_list:
                if (not quarter or acceptance.date_cash.month in months) and acceptance.date_cash.year == year:
                    if without_distributions and acceptance.distribution_acceptance_ids:
                        continue
                    sum_cash += acceptance.margin * multiplier
                    if not any(distribution.fact_acceptance_flow_id.margin_manual_input for distribution in
                        acceptance.distribution_acceptance_ids):
                        sum_cash_without_manual += acceptance.margin * multiplier

        return sum_cash, sum_cash_without_manual

    def get_sum_planned_acceptance_project_year_quarter(self, project, year, quarter):
        sum_acceptance = {'commitment': 0, 'reserve': 0, 'potential': 0}

        if quarter:
            months = self.get_months_from_quarter(quarter)

        if project.step_status == 'project':
            acceptance_list = project.planned_acceptance_flow_ids
        elif project.step_status == 'step':
            acceptance_list = project.planned_step_acceptance_flow_ids

        if acceptance_list:
            for acceptance in acceptance_list:
                if (not quarter or acceptance.date_cash.month in months) and acceptance.date_cash.year == year:
                    stage_id_code = project.stage_id.code
                    if acceptance.forecast == 'from_project':
                        if stage_id_code in ('75', '100', '100(done)'):
                            sum_acceptance['commitment'] += acceptance.sum_cash_without_vat
                        elif stage_id_code == '50':
                            sum_acceptance['reserve'] += acceptance.sum_cash_without_vat
                        elif stage_id_code == '30':
                            sum_acceptance['potential'] += acceptance.sum_cash_without_vat
                    else:
                        if stage_id_code != '0':
                            sum_acceptance[acceptance.forecast] += acceptance.sum_cash_without_vat
        return sum_acceptance

    def get_sum_planned_margin_project_year_quarter(self, project, year, quarter):
        if project.is_parent_project:
            if project.margin_from_children_to_parent:
                sum_margin = self.get_margin_plan(project, year, quarter, 1)
                for child_project in project.child_project_ids:
                    if child_project.project_have_steps:
                        for child_step in child_project.step_project_child_ids:
                            child_sum_margin = self.get_margin_plan(child_step, year, quarter,
                                                                    child_project.margin_rate_for_parent)
                            for key in sum_margin:
                                sum_margin[key] += child_sum_margin[key]
                    else:
                        child_sum_margin = self.get_margin_plan(child_project, year, quarter, child_project.margin_rate_for_parent)
                        for key in sum_margin:
                            sum_margin[key] += child_sum_margin[key]
            else:
                total_percent = 0
                for child_project in project.child_project_ids:
                    total_percent += child_project.margin_rate_for_parent
                sum_margin = self.get_margin_plan(project, year, quarter, (1 - total_percent))
        elif project.is_child_project:
            if project.parent_project_id.margin_from_children_to_parent:
                sum_margin = self.get_margin_plan(project, year, quarter, (1 - project.margin_rate_for_parent))
            else:
                sum_margin = self.get_margin_plan(project, year, quarter, 1)
                if project.parent_project_id.project_have_steps:
                    for parent_step in project.parent_project_id.step_project_child_ids:
                        parent_sum_margin = self.get_margin_plan(
                            parent_step, year, quarter, project.margin_rate_for_parent
                        )
                        for key in sum_margin:
                            sum_margin[key] += parent_sum_margin[key]
                else:
                    parent_sum_margin = self.get_margin_plan(project.parent_project_id, year, quarter, project.margin_rate_for_parent)
                    for key in sum_margin:
                        sum_margin[key] += parent_sum_margin[key]
        else:
            sum_margin = self.get_margin_plan(project, year, quarter, 1)
        return sum_margin

    def get_margin_plan(self, project, year, quarter, multiplier):
        sum_margin = {'commitment': 0, 'reserve': 0, 'potential': 0}

        if quarter:
            months = self.get_months_from_quarter(quarter)

        profitability = project.profitability

        if project.step_status == 'project':
            acceptance_list = project.planned_acceptance_flow_ids
        elif project.step_status == 'step':
            acceptance_list = project.planned_step_acceptance_flow_ids

        if acceptance_list:
            for acceptance in acceptance_list:
                if ((not quarter or acceptance.date_cash.month in months)
                        and acceptance.date_cash.year == year
                        and not any(distribution.fact_acceptance_flow_id.margin_manual_input for distribution in acceptance.distribution_acceptance_ids)):  # если нет ручной маржи - добавляем
                    stage_id_code = project.stage_id.code
                    if acceptance.forecast == 'from_project':
                        if stage_id_code in ('75', '100', '100(done)'):
                            sum_margin['commitment'] += acceptance.sum_cash_without_vat * profitability * multiplier / 100
                        elif stage_id_code == '50':
                            sum_margin['reserve'] += acceptance.sum_cash_without_vat * profitability * multiplier / 100
                        elif stage_id_code == '30':
                            sum_margin['potential'] += acceptance.sum_cash_without_vat * profitability * multiplier / 100
                    else:
                        if stage_id_code != '0':
                            sum_margin[acceptance.forecast] += acceptance.sum_cash_without_vat * profitability * multiplier / 100
        return sum_margin

    def get_act_forecast_from_distributions(self, sum, project, year, months):

        sum_distribution_acceptance = 0
        sum_ostatok_acceptance = {'commitment': 0, 'reserve': 0, 'potential': 0}

        if project.step_status == 'project':
            acceptance_list = project.planned_acceptance_flow_ids
        elif project.step_status == 'step':
            acceptance_list = project.planned_step_acceptance_flow_ids

        for planned_acceptance in acceptance_list:
            if (not months or planned_acceptance.date_cash.month in months) and planned_acceptance.date_cash.year == year:
                sum_distribution_acceptance += planned_acceptance.distribution_sum_without_vat
                stage_id_code = project.stage_id.code

                if planned_acceptance.distribution_sum_without_vat_ostatok > 0:
                    if planned_acceptance.forecast == 'from_project':
                        if stage_id_code in ('75', '100', '100(done)'):
                            sum_ostatok_acceptance['commitment'] += planned_acceptance.distribution_sum_without_vat_ostatok
                        elif stage_id_code == '50':
                            sum_ostatok_acceptance['reserve'] += planned_acceptance.distribution_sum_without_vat_ostatok
                        elif stage_id_code == '30':
                            sum_ostatok_acceptance['potential'] += planned_acceptance.distribution_sum_without_vat_ostatok
                    else:
                        if stage_id_code != '0':
                            sum_ostatok_acceptance[
                                planned_acceptance.forecast] += planned_acceptance.distribution_sum_without_vat_ostatok

        if sum_distribution_acceptance:  # если есть распределение, то остаток = остатку распределения
            sum = sum_ostatok_acceptance
            for key in sum:
                if not project.is_correction_project:
                    sum[key] = max(sum[key], 0)
        return  sum

    def get_margin_forecast_from_distributions(self, margin_sum, plan, project, year, months, margin_rate_for_parent):
        if project.is_parent_project:
            if project.margin_from_children_to_parent:
                margin_sum = self.get_margin_forecast(margin_sum, plan, project, year, months, 1)
                for child_project in project.child_project_ids:
                    if child_project.project_have_steps:
                        for child_step in child_project.step_project_child_ids:
                            margin_sum = self.get_margin_forecast(margin_sum, plan, child_step, year, months,
                                                                  child_project.margin_rate_for_parent)
                    else:
                        margin_sum = self.get_margin_forecast(margin_sum, plan, child_project, year, months, child_project.margin_rate_for_parent)
            else:
                total_percent = 0
                for child_project in project.child_project_ids:
                    total_percent += child_project.margin_rate_for_parent
                margin_sum = self.get_margin_forecast(margin_sum, plan, project, year, months, (1 - total_percent))
        elif project.is_child_project:
            if project.parent_project_id.margin_from_children_to_parent:
                margin_sum = self.get_margin_forecast(margin_sum, plan, project, year, months, (1 - project.margin_rate_for_parent))
            else:
                margin_sum = self.get_margin_forecast(margin_sum, plan, project, year, months, 1)
                if project.parent_project_id.project_have_steps:
                    for parent_step in project.parent_project_id.step_project_child_ids:
                        margin_sum = self.get_margin_forecast(margin_sum, plan, parent_step, year, months,
                                                              project.margin_rate_for_parent)
                else:
                    margin_sum = self.get_margin_forecast(margin_sum, plan, project.parent_project_id, year, months, project.margin_rate_for_parent)
        else:
            margin_sum = self.get_margin_forecast(margin_sum, plan, project, year, months, 1)
        return margin_sum

    def get_margin_forecast(self, margin_sum, plan, project, year, months, multiplier):
        margin_plan = plan.copy()
        sum_distribution_acceptance = 0

        if project.step_status == 'project':
            acceptance_list = project.planned_acceptance_flow_ids
        elif project.step_status == 'step':
            acceptance_list = project.planned_step_acceptance_flow_ids

        for planned_acceptance in acceptance_list:
            if (not months or planned_acceptance.date_cash.month in months) and planned_acceptance.date_cash.year == year:
                sum_distribution_acceptance += planned_acceptance.distribution_sum_without_vat
                # суммируем доли маржи фактов в соотношении (сумма распределения/суммы факта)
                margin_distribution = 0
                for distribution in planned_acceptance.distribution_acceptance_ids:
                    if distribution.fact_acceptance_flow_id.margin_manual_input:  # если есть ручная маржа - пропускаем
                        continue
                    if distribution.fact_acceptance_flow_id.sum_cash_without_vat != 0:
                        margin_distribution += (distribution.fact_acceptance_flow_id.margin
                                                * distribution.sum_cash_without_vat
                                                / distribution.fact_acceptance_flow_id.sum_cash_without_vat)
                stage_id_code = project.stage_id.code

                if planned_acceptance.forecast == 'from_project':
                    if stage_id_code in ('75', '100', '100(done)'):
                        margin_plan['commitment'] -= margin_distribution * multiplier
                    elif stage_id_code == '50':
                        margin_plan['reserve'] -= margin_distribution * multiplier
                else:
                    if stage_id_code != '0':
                        margin_plan[planned_acceptance.forecast] -= margin_distribution * multiplier

        if sum_distribution_acceptance != 0:  # если есть распределение, то остаток = остатку распределения
            margin_sum = margin_plan
            for key in margin_sum:
                if not project.is_correction_project:
                    margin_sum[key] = max(margin_sum[key], 0)
        return margin_sum

    def print_quarter_planned_acceptance_project(self, sheet, row, column, element, project, responsibility_center, params, row_format_number, row_format_number_color_fact):
        global strYEAR
        global YEARint

        sum75tmpetalon = sum50tmpetalon = sum100tmp = sum100tmp_q1 = sum100tmp_wo_distributions = sum100tmp_wo_distributions_q1 = sum75tmp = sum50tmp = 0
        prof75tmpetalon = prof50tmpetalon = prof100tmp = prof100tmp_q1 = prof75tmp = prof50tmp = 0
        sum_next_75_q1_tmp = 0
        sum_next_50_q1_tmp = 0
        sum_next_30_q1_tmp = 0
        sum_next_75_tmp = 0
        sum_next_50_tmp = 0
        sum_next_30_tmp = 0
        sum_after_next_tmp = 0
        prof_next_75_q1_tmp = 0
        prof_next_50_q1_tmp = 0
        prof_next_30_q1_tmp = 0
        prof_next_75_tmp = 0
        prof_next_50_tmp = 0
        prof_next_30_tmp = 0
        prof_after_next_tmp = 0

        if element in ('Q1', 'Q2'):
            months = self.get_months_from_quarter(element)

            profitability = project.profitability

            sum100tmp_proj = self.get_sum_fact_acceptance_project_year_quarter(project, YEARint, element, False)
            acc_fact_wo_distributions = self.get_sum_fact_acceptance_project_year_quarter(project, YEARint, element, True)
            prof100tmp_proj, prof100tmp_proj_wo_manual = self.get_sum_fact_margin_project_year_quarter(project, YEARint, element, False)
            _, mrg_fact_wo_distribution = self.get_sum_fact_margin_project_year_quarter(project, YEARint, element, True)
            sheet.write_number(row, column + 1, sum100tmp_proj, row_format_number_color_fact)
            sheet.write_number(row, column + 1 + params['margin_shift'], prof100tmp_proj, row_format_number_color_fact)

            sum100tmp += sum100tmp_proj
            sum100tmp_wo_distributions += acc_fact_wo_distributions
            prof100tmp += prof100tmp_proj

            sum = self.get_sum_planned_acceptance_project_year_quarter(project, YEARint, element)
            margin_sum = self.get_sum_planned_margin_project_year_quarter(project, YEARint, element)

            margin_plan = {'commitment': 0, 'reserve': 0, 'potential': 0}

            if margin_sum:
                margin_plan = margin_sum.copy()

            if not project.is_correction_project:
                if sum100tmp_wo_distributions >= sum['commitment']:
                    sum100tmp_ostatok = sum100tmp_wo_distributions - sum['commitment']
                    sum['commitment'] = 0
                    sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                else:
                    sum['commitment'] = sum['commitment'] - sum100tmp_wo_distributions

                if mrg_fact_wo_distribution > 0:
                    if mrg_fact_wo_distribution >= margin_plan['commitment']:  # маржа если нет распределения
                        prof100tmp_ostatok = mrg_fact_wo_distribution - margin_plan['commitment']
                        margin_sum['commitment'] = 0
                        margin_sum['reserve'] = max(margin_plan['reserve'] - prof100tmp_ostatok, 0)
                    else:
                        margin_sum['commitment'] = margin_plan['commitment'] - mrg_fact_wo_distribution

            # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
            sum = self.get_act_forecast_from_distributions(sum, project, YEARint, months)
            margin_sum = self.get_margin_forecast_from_distributions(margin_sum, margin_plan, project, YEARint, months, 1)

            for key in sum:  # убираем отрицательные, если не корректировочный проект
                if not project.is_correction_project:
                    sum[key] = max(sum[key], 0)
                    margin_sum[key] = max(margin_sum[key], 0)

            sheet.write_number(row, column + 2, sum['commitment'], row_format_number)
            sheet.write_number(row, column + 2 + params['margin_shift'], margin_sum['commitment'], row_format_number)
            sum75tmp += sum['commitment']
            prof75tmp += margin_sum['commitment']
            sheet.write_number(row, column + 3, sum['reserve'], row_format_number)
            sheet.write_number(row, column + 3 + params['margin_shift'], margin_sum['reserve'], row_format_number)
            sum50tmp += sum['reserve']
            prof50tmp += margin_sum['reserve']

        if element in ('Q3', 'Q4'):
            months = self.get_months_from_quarter(element)

            profitability = project.profitability

            sum100tmp_proj = self.get_sum_fact_acceptance_project_year_quarter(project, YEARint, element, False)
            acc_fact_wo_distributions = self.get_sum_fact_acceptance_project_year_quarter(project, YEARint, element, True)
            prof100tmp_proj, prof100tmp_proj_wo_manual = self.get_sum_fact_margin_project_year_quarter(project, YEARint, element, False)
            _, mrg_fact_wo_distribution = self.get_sum_fact_margin_project_year_quarter(project, YEARint, element, True)
            sheet.write_number(row, column + 2, sum100tmp_proj, row_format_number_color_fact)
            sheet.write_number(row, column + 2 + params['margin_shift'], prof100tmp_proj, row_format_number_color_fact)

            sum100tmp += sum100tmp_proj
            sum100tmp_wo_distributions += acc_fact_wo_distributions
            prof100tmp += prof100tmp_proj

            sum = self.get_sum_planned_acceptance_project_year_quarter(project, YEARint, element)
            margin_sum = self.get_sum_planned_margin_project_year_quarter(project, YEARint, element)

            margin_plan = {'commitment': 0, 'reserve': 0, 'potential': 0}

            if margin_sum:
                margin_plan = margin_sum.copy()

            if not project.is_correction_project:
                if sum100tmp_wo_distributions >= sum['commitment']:
                    sum100tmp_ostatok = sum100tmp_wo_distributions - sum['commitment']
                    sum['commitment'] = 0
                    sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                else:
                    sum['commitment'] = sum['commitment'] - sum100tmp_wo_distributions

                if mrg_fact_wo_distribution > 0:
                    if mrg_fact_wo_distribution >= margin_plan['commitment']:  # маржа если нет распределения
                        prof100tmp_ostatok = mrg_fact_wo_distribution - margin_plan['commitment']
                        margin_sum['commitment'] = 0
                        margin_sum['reserve'] = max(margin_plan['reserve'] - prof100tmp_ostatok, 0)
                    else:
                        margin_sum['commitment'] = margin_plan['commitment'] - mrg_fact_wo_distribution

            # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
            sum = self.get_act_forecast_from_distributions(sum, project, YEARint, months)
            margin_sum = self.get_margin_forecast_from_distributions(margin_sum, margin_plan, project, YEARint, months, 1)

            for key in sum:  # убираем отрицательные, если не корректировочный проект
                if not project.is_correction_project:
                    sum[key] = max(sum[key], 0)
                    margin_sum[key] = max(margin_sum[key], 0)

            sheet.write_number(row, column + 3, sum['commitment'], row_format_number)
            sheet.write_number(row, column + 3 + params['margin_shift'], margin_sum['commitment'], row_format_number)
            sum75tmp += sum['commitment']
            prof75tmp += margin_sum['commitment']
            sheet.write_number(row, column + 4, sum['reserve'], row_format_number)
            sheet.write_number(row, column + 4 + params['margin_shift'], margin_sum['reserve'], row_format_number)
            sum50tmp += sum['reserve']
            prof50tmp += margin_sum['reserve']

        elif element == 'NEXT':
            profitability = project.profitability

            sum100tmp_q1_proj = self.get_sum_fact_acceptance_project_year_quarter(project, YEARint + 1, 'Q1', False)
            acc_fact_wo_distributions_q1 = self.get_sum_fact_acceptance_project_year_quarter(project, YEARint + 1, 'Q1', False)
            prof100tmp_q1_proj, prof100tmp_q1_proj_wo_manual = self.get_sum_fact_margin_project_year_quarter(project, YEARint + 1, 'Q1', False)
            _, mrg_fact_wo_distribution_q1 = self.get_sum_fact_margin_project_year_quarter(project, YEARint + 1, 'Q1', True)
            sum100tmp_proj = self.get_sum_fact_acceptance_project_year_quarter(project, YEARint + 1, False, False)
            acc_fact_wo_distributions = self.get_sum_fact_acceptance_project_year_quarter(project, YEARint + 1, False, True)
            prof100tmp_proj, prof100tmp_proj_wo_manual = self.get_sum_fact_margin_project_year_quarter(project, YEARint + 1, False, False)
            _, mrg_fact_wo_distribution = self.get_sum_fact_margin_project_year_quarter(project, YEARint + 1, False, True)


            sum100tmp_q1 += sum100tmp_q1_proj
            sum100tmp_wo_distributions_q1 += acc_fact_wo_distributions_q1
            prof100tmp_q1 += prof100tmp_q1_proj
            sum100tmp += sum100tmp_proj
            sum100tmp_wo_distributions += acc_fact_wo_distributions
            prof100tmp += prof100tmp_proj

            sum_q1 = self.get_sum_planned_acceptance_project_year_quarter(project, YEARint + 1, 'Q1')
            margin_sum_q1 = self.get_sum_planned_margin_project_year_quarter(project, YEARint + 1, 'Q1')
            sum = self.get_sum_planned_acceptance_project_year_quarter(project, YEARint + 1, False)
            margin_sum = self.get_sum_planned_margin_project_year_quarter(project, YEARint + 1, False)

            margin_plan_q1 = {'commitment': 0, 'reserve': 0, 'potential': 0}
            margin_plan = {'commitment': 0, 'reserve': 0, 'potential': 0}

            if margin_sum:
                margin_plan = margin_sum.copy()

            if margin_sum_q1:
                margin_plan_q1 = margin_sum_q1.copy()

            if not project.is_correction_project:
                if sum100tmp_wo_distributions_q1 >= sum_q1['commitment']:
                    sum100tmp_q1_ostatok = sum100tmp_wo_distributions_q1 - sum_q1['commitment']
                    sum_q1['commitment'] = 0
                    sum_q1['reserve'] = max(sum_q1['reserve'] - sum100tmp_q1_ostatok, 0)
                else:
                    sum_q1['commitment'] = sum_q1['commitment'] - sum100tmp_wo_distributions_q1

                if sum100tmp_wo_distributions >= sum['commitment']:
                    sum100tmp_ostatok = sum100tmp_wo_distributions - sum['commitment']
                    sum['commitment'] = 0
                    sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                else:
                    sum['commitment'] = sum['commitment'] - sum100tmp_wo_distributions

                if mrg_fact_wo_distribution_q1 > 0:
                    if mrg_fact_wo_distribution_q1 >= margin_plan_q1['commitment']:  # маржа если нет распределения
                        prof100tmp_q1_ostatok = mrg_fact_wo_distribution_q1 - margin_plan_q1['commitment']
                        margin_sum_q1['commitment'] = 0
                        margin_sum_q1['reserve'] = max(margin_plan_q1['reserve'] - prof100tmp_q1_ostatok, 0)
                    else:
                        margin_sum_q1['commitment'] = margin_plan_q1['commitment'] - mrg_fact_wo_distribution_q1

                if mrg_fact_wo_distribution > 0:
                    if mrg_fact_wo_distribution >= margin_plan['commitment']:  # маржа если нет распределения
                        prof100tmp_ostatok = mrg_fact_wo_distribution - margin_plan['commitment']
                        margin_sum['commitment'] = 0
                        margin_sum['reserve'] = max(margin_plan['reserve'] - prof100tmp_ostatok, 0)
                    else:
                        margin_sum['commitment'] = margin_plan['commitment'] - mrg_fact_wo_distribution

            if all(value == 0 for value in sum_q1.values()) and project.company_id.id != 10 and project.end_sale_project_month.year == YEARint + 1 and project.end_sale_project_month.month in self.get_months_from_quarter('Q1'):  # если актирование 0, а месяц в нужном году, берем выручку
                if project.stage_id.code == '30':
                    sum_q1['potential'] = project.amount_untaxed_in_company_currency
            #
            if all(value == 0 for value in sum.values()) and project.company_id.id != 10 and project.end_sale_project_month.year == YEARint + 1:  # если актирование 0, а месяц в нужном году, берем выручку
                if project.stage_id.code == '30':
                    sum['potential'] = project.amount_untaxed_in_company_currency

            # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
            sum_q1 = self.get_act_forecast_from_distributions(sum_q1, project, YEARint + 1,  self.get_months_from_quarter('Q1'))
            margin_sum_q1 = self.get_margin_forecast_from_distributions(margin_sum_q1, margin_plan_q1, project, YEARint + 1, self.get_months_from_quarter('Q1'), 1)

            sum = self.get_act_forecast_from_distributions(sum, project, YEARint + 1, False)
            margin_sum = self.get_margin_forecast_from_distributions(margin_sum, margin_plan, project, YEARint + 1, False, 1)

            for key in sum:  # убираем отрицательные, если не корректировочный проект
                if not project.is_correction_project:
                    sum_q1[key] = max(sum_q1[key], 0)
                    margin_sum_q1[key] = max(margin_sum_q1[key], 0)
                    sum[key] = max(sum[key], 0)
                    margin_sum[key] = max(margin_sum[key], 0)

            sheet.write_number(row, column + 0, sum['commitment'], row_format_number)
            sheet.write_number(row, column + 0 + params['margin_shift'], margin_sum['commitment'],
                               row_format_number)
            sum_next_75_tmp += sum['commitment']
            prof_next_75_tmp += margin_sum['commitment']
            sheet.write_number(row, column + 1, sum['reserve'] * params['50'], row_format_number)
            sheet.write_number(row, column + 1 + params['margin_shift'], margin_sum['reserve'] * params['50'],
                               row_format_number)
            sum_next_50_tmp += sum['reserve'] * params['50']
            prof_next_50_tmp += margin_sum['reserve'] * params['50']
            sheet.write_number(row, column + 2, sum['potential'] * params['30'], row_format_number)
            sheet.write_number(row, column + 2 + params['margin_shift'], margin_sum['potential'] * params['30'],
                               row_format_number)
            sum_next_30_tmp += sum['potential'] * params['30']
            prof_next_30_tmp += margin_sum['potential'] * params['30']

        elif element == 'AFTER NEXT':
            profitability = project.profitability

            sum100tmp_proj = self.get_sum_fact_acceptance_project_year_quarter(project, YEARint + 2, False, False)
            acc_fact_wo_distributions = self.get_sum_fact_acceptance_project_year_quarter(project, YEARint + 2, False, True)
            prof100tmp_proj, prof100tmp_proj_wo_manual = self.get_sum_fact_margin_project_year_quarter(project, YEARint + 2, False, False)
            _, mgr_fact_wo_distributions = self.get_sum_fact_margin_project_year_quarter(project, YEARint + 2, False, True)

            sum100tmp += sum100tmp_proj
            sum100tmp_wo_distributions += acc_fact_wo_distributions
            prof100tmp += prof100tmp_proj

            sum = self.get_sum_planned_acceptance_project_year_quarter(project, YEARint + 2, False)
            margin_sum = self.get_sum_planned_margin_project_year_quarter(project, YEARint + 2, False)

            margin_plan = {'commitment': 0, 'reserve': 0, 'potential': 0}

            if margin_sum:
                margin_plan = margin_sum.copy()

            if not project.is_correction_project:
                if sum100tmp_wo_distributions >= sum['commitment']:
                    sum100tmp_ostatok = sum100tmp_wo_distributions - sum['commitment']
                    sum['commitment'] = 0
                    sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                else:
                    sum['commitment'] = sum['commitment'] - sum100tmp_wo_distributions

                if mgr_fact_wo_distributions > 0:
                    if mgr_fact_wo_distributions >= margin_plan['commitment']:  # маржа если нет распределения
                        prof100tmp_ostatok = mgr_fact_wo_distributions - margin_plan['commitment']
                        margin_sum['commitment'] = 0
                        margin_sum['reserve'] = max(margin_plan['reserve'] - prof100tmp_ostatok, 0)
                    else:
                        margin_sum['commitment'] = margin_plan['commitment'] - mgr_fact_wo_distributions

            if all(value == 0 for value in sum.values()) and project.company_id.id != 10 and project.end_sale_project_month.year == YEARint + 2:  # если актирование 0, а месяц в нужном году, берем выручку
                if project.stage_id.code == '30':
                    sum['potential'] = project.amount_untaxed_in_company_currency

            # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
            sum = self.get_act_forecast_from_distributions(sum, project, YEARint + 2, False)
            margin_sum = self.get_margin_forecast_from_distributions(margin_sum, margin_plan, project, YEARint + 2, False, 1)

            for key in sum:  # убираем отрицательные, если не корректировочный проект
                if not project.is_correction_project:
                    sum[key] = max(sum[key], 0)
                    margin_sum[key] = max(margin_sum[key], 0)

            sum_after_next_tmp += sum['commitment']
            prof_after_next_tmp += margin_sum['commitment']
            sum_after_next_tmp += sum['reserve'] * params['50']
            prof_after_next_tmp += margin_sum['reserve'] * params['50']
            sum_after_next_tmp += sum['potential'] * params['30']
            prof_after_next_tmp += margin_sum['potential'] * params['30']
            sheet.write_number(row, column + 0, sum_after_next_tmp, row_format_number)
            sheet.write_number(row, column + 0 + params['margin_shift'], prof_after_next_tmp,
                               row_format_number)

        return sum75tmpetalon, sum50tmpetalon, sum100tmp, sum75tmp, sum50tmp

    def calculate_quarter_planned_acceptance(self, element, project, responsibility_center, params):
        global strYEAR
        global YEARint

        sum75tmpetalon = sum50tmpetalon = sum100tmp = sum100tmp_q1 = sum100tmp_wo_distributions = sum100tmp_wo_distributions_q1 = sum75tmp = sum50tmp = 0
        prof75tmpetalon = prof50tmpetalon = prof100tmp = prof100tmp_q1 = prof75tmp = prof50tmp = 0
        sum_next_75_q1_tmp = 0
        sum_next_50_q1_tmp = 0
        sum_next_30_q1_tmp = 0
        sum_next_75_tmp = 0
        sum_next_50_tmp = 0
        sum_next_30_tmp = 0
        sum_after_next_tmp = 0
        prof_next_75_q1_tmp = 0
        prof_next_50_q1_tmp = 0
        prof_next_30_q1_tmp = 0
        prof_next_75_tmp = 0
        prof_next_50_tmp = 0
        prof_next_30_tmp = 0
        prof_after_next_tmp = 0

        if element in ('Q1', 'Q2', 'Q3', 'Q4'):
            months = self.get_months_from_quarter(element)
            if project.stage_id.code not in ('0', '10'):

                profitability = project.profitability

                sum100tmp_proj = self.get_sum_fact_acceptance_project_year_quarter(project, YEARint, element, False)
                acc_fact_wo_distributions = self.get_sum_fact_acceptance_project_year_quarter(project, YEARint, element, True)
                prof100tmp_proj, prof100tmp_proj_wo_manual = self.get_sum_fact_margin_project_year_quarter(project, YEARint, element, False)
                _, mrg_fact_wo_distributions = self.get_sum_fact_margin_project_year_quarter(project, YEARint, element, True)

                sum100tmp += sum100tmp_proj
                sum100tmp_wo_distributions += acc_fact_wo_distributions
                prof100tmp += prof100tmp_proj

                sum = self.get_sum_planned_acceptance_project_year_quarter(project, YEARint, element)
                margin_sum = self.get_sum_planned_margin_project_year_quarter(project, YEARint, element)

                margin_plan = {'commitment': 0, 'reserve': 0, 'potential': 0}

                if margin_sum:
                    margin_plan = margin_sum.copy()

                if not project.is_correction_project:
                    if sum100tmp_wo_distributions >= sum['commitment']:
                        sum100tmp_ostatok = sum100tmp_wo_distributions - sum['commitment']
                        sum['commitment'] = 0
                        sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                    else:
                        sum['commitment'] = sum['commitment'] - sum100tmp_wo_distributions

                    if mrg_fact_wo_distributions > 0:
                        if mrg_fact_wo_distributions >= margin_plan['commitment']:  # маржа если нет распределения
                            prof100tmp_ostatok = mrg_fact_wo_distributions - margin_plan['commitment']
                            margin_sum['commitment'] = 0
                            margin_sum['reserve'] = max(margin_plan['reserve'] - prof100tmp_ostatok, 0)
                        else:
                            margin_sum['commitment'] = margin_plan['commitment'] - mrg_fact_wo_distributions

                # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                sum = self.get_act_forecast_from_distributions(sum, project, YEARint, months)
                margin_sum = self.get_margin_forecast_from_distributions(margin_sum, margin_plan, project, YEARint, months, 1)

                for key in sum: # убираем отрицательные, если не корректировочный проект
                    if not project.is_correction_project:
                        sum[key] = max(sum[key], 0)
                        margin_sum[key] = max(margin_sum[key], 0)

                sum75tmp += sum['commitment']
                prof75tmp += margin_sum['commitment']
                sum50tmp += sum['reserve']
                prof50tmp += margin_sum['reserve']

        elif element == 'NEXT':
            if project.stage_id.code not in ('0', '10'):

                profitability = project.profitability

                sum100tmp_q1_proj = self.get_sum_fact_acceptance_project_year_quarter(project, YEARint + 1, 'Q1', False)
                acc_fact_wo_distributions_q1 = self.get_sum_fact_acceptance_project_year_quarter(project, YEARint + 1, 'Q1', True)
                prof100tmp_q1_proj, prof100tmp_q1_proj_wo_manual = self.get_sum_fact_margin_project_year_quarter(project, YEARint + 1, 'Q1', False)
                _, mrg_fact_wo_distributions_q1 = self.get_sum_fact_margin_project_year_quarter(project, YEARint + 1, 'Q1', True)
                sum100tmp_proj = self.get_sum_fact_acceptance_project_year_quarter(project, YEARint + 1, False, False)
                acc_fact_wo_distributions = self.get_sum_fact_acceptance_project_year_quarter(project, YEARint + 1, False, True)
                prof100tmp_proj, prof100tmp_proj_wo_manual = self.get_sum_fact_margin_project_year_quarter(project, YEARint + 1, False, False)
                _, mrg_fact_wo_distributions = self.get_sum_fact_margin_project_year_quarter(project, YEARint + 1, False, True)


                sum100tmp_q1 += sum100tmp_q1_proj
                sum100tmp_wo_distributions_q1 += acc_fact_wo_distributions_q1

                prof100tmp_q1 += prof100tmp_q1_proj

                sum100tmp += sum100tmp_proj
                sum100tmp_wo_distributions += acc_fact_wo_distributions

                prof100tmp += prof100tmp_proj

                sum_q1 = self.get_sum_planned_acceptance_project_year_quarter(project, YEARint + 1, 'Q1')
                margin_sum_q1 = self.get_sum_planned_margin_project_year_quarter(project, YEARint + 1, 'Q1')
                sum = self.get_sum_planned_acceptance_project_year_quarter(project, YEARint + 1, False)
                margin_sum = self.get_sum_planned_margin_project_year_quarter(project, YEARint + 1, False)

                margin_plan_q1 = {'commitment': 0, 'reserve': 0, 'potential': 0}
                margin_plan = {'commitment': 0, 'reserve': 0, 'potential': 0}

                if margin_sum:
                    margin_plan = margin_sum.copy()

                if margin_sum_q1:
                    margin_plan_q1 = margin_sum_q1.copy()

                if not project.is_correction_project:
                    if sum100tmp_wo_distributions_q1 >= sum_q1['commitment']:
                        sum100tmp_q1_ostatok = sum100tmp_wo_distributions_q1 - sum_q1['commitment']
                        sum_q1['commitment'] = 0
                        sum_q1['reserve'] = max(sum_q1['reserve'] - sum100tmp_q1_ostatok, 0)
                    else:
                        sum_q1['commitment'] = sum_q1['commitment'] - sum100tmp_wo_distributions_q1

                    if sum100tmp_wo_distributions >= sum['commitment']:
                        sum100tmp_ostatok = sum100tmp_wo_distributions - sum['commitment']
                        sum['commitment'] = 0
                        sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                    else:
                        sum['commitment'] = sum['commitment'] - sum100tmp_wo_distributions

                    if mrg_fact_wo_distributions_q1 > 0:
                        if mrg_fact_wo_distributions_q1 >= margin_plan_q1['commitment']:  # маржа если нет распределения
                            prof100tmp_q1_ostatok = mrg_fact_wo_distributions_q1 - margin_plan_q1['commitment']
                            margin_sum_q1['commitment'] = 0
                            margin_sum_q1['reserve'] = max(margin_plan_q1['reserve'] - prof100tmp_q1_ostatok, 0)
                        else:
                            margin_sum_q1['commitment'] = margin_plan_q1['commitment'] - mrg_fact_wo_distributions_q1

                    if mrg_fact_wo_distributions > 0:
                        if mrg_fact_wo_distributions >= margin_plan['commitment']:  # маржа если нет распределения
                            prof100tmp_ostatok = mrg_fact_wo_distributions - margin_plan['commitment']
                            margin_sum['commitment'] = 0
                            margin_sum['reserve'] = max(margin_plan['reserve'] - prof100tmp_ostatok, 0)
                        else:
                            margin_sum['commitment'] = margin_plan['commitment'] - mrg_fact_wo_distributions

                if (all(value == 0 for value in sum_q1.values()) and project.company_id.id != 10 and project.end_sale_project_month.year == YEARint + 1
                        and project.end_sale_project_month.month in self.get_months_from_quarter('Q1')):  # если актирование 0, а месяц в нужном году, берем выручку
                    if project.stage_id.code == '30':
                        sum_q1['potential'] = project.amount_untaxed_in_company_currency
                #
                if all(value == 0 for value in sum.values()) and project.company_id.id != 10 and project.end_sale_project_month.year == YEARint + 1:  # если актирование 0, а месяц в нужном году, берем выручку
                    if project.stage_id.code == '30':
                        sum['potential'] = project.amount_untaxed_in_company_currency

                # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                sum_q1 = self.get_act_forecast_from_distributions(sum, project, YEARint + 1, self.get_months_from_quarter('Q1'))
                margin_sum_q1 = self.get_margin_forecast_from_distributions(margin_sum, margin_plan, project, YEARint + 1,
                                                                         self.get_months_from_quarter('Q1'), 1)

                sum = self.get_act_forecast_from_distributions(sum, project, YEARint + 1, False)
                margin_sum = self.get_margin_forecast_from_distributions(margin_sum, margin_plan, project, YEARint + 1,
                                                                         False, 1)

                for key in sum:  # убираем отрицательные, если не корректировочный проект
                    if not project.is_correction_project:
                        sum_q1[key] = max(sum_q1[key], 0)
                        margin_sum_q1[key] = max(margin_sum_q1[key], 0)
                        sum[key] = max(sum[key], 0)
                        margin_sum[key] = max(margin_sum[key], 0)

                sum_next_75_q1_tmp += sum_q1['commitment']
                prof_next_75_q1_tmp += margin_sum_q1['commitment']
                sum_next_50_q1_tmp += sum_q1['reserve'] * params['50']
                prof_next_50_q1_tmp += margin_sum_q1['reserve'] * params['50']
                sum_next_30_q1_tmp += sum_q1['potential'] * params['30']
                prof_next_30_q1_tmp += margin_sum_q1['potential'] * params['30']

                sum_next_75_tmp += sum['commitment']
                prof_next_75_tmp += margin_sum['commitment']
                sum_next_50_tmp += sum['reserve'] * params['50']
                prof_next_50_tmp += margin_sum['reserve'] * params['50']
                sum_next_30_tmp += sum['potential'] * params['30']
                prof_next_30_tmp += margin_sum['potential'] * params['30']

        elif element == 'AFTER NEXT':
            if project.stage_id.code not in ('0', '10'):

                profitability = project.profitability

                sum100tmp_proj = self.get_sum_fact_acceptance_project_year_quarter(project, YEARint + 2, False, False)
                acc_fact_wo_distribution = self.get_sum_fact_acceptance_project_year_quarter(project, YEARint + 2, False, True)
                prof100tmp_proj, prof100tmp_proj_wo_manual = self.get_sum_fact_margin_project_year_quarter(project, YEARint + 2, False, False)
                _, mrg_fact_wo_distributions = self.get_sum_fact_margin_project_year_quarter(project, YEARint + 2, False, True)

                sum100tmp += sum100tmp_proj
                sum100tmp_wo_distributions += acc_fact_wo_distribution
                prof100tmp += prof100tmp_proj

                sum = self.get_sum_planned_acceptance_project_year_quarter(project, YEARint + 2, False)
                margin_sum = self.get_sum_planned_margin_project_year_quarter(project, YEARint + 2, False)

                margin_plan = {'commitment': 0, 'reserve': 0, 'potential': 0}

                if margin_sum:
                    margin_plan = margin_sum.copy()

                if not project.is_correction_project:
                    if sum100tmp_wo_distributions >= sum['commitment']:
                        sum100tmp_ostatok = sum100tmp_wo_distributions - sum['commitment']
                        sum['commitment'] = 0
                        sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                    else:
                        sum['commitment'] = sum['commitment'] - sum100tmp_wo_distributions

                    if mrg_fact_wo_distributions > 0:
                        if mrg_fact_wo_distributions >= margin_plan['commitment']:  # маржа если нет распределения
                            prof100tmp_ostatok = mrg_fact_wo_distributions - margin_plan['commitment']
                            margin_sum['commitment'] = 0
                            margin_sum['reserve'] = max(margin_plan['reserve'] - prof100tmp_ostatok, 0)
                        else:
                            margin_sum['commitment'] = margin_plan['commitment'] - mrg_fact_wo_distributions

                if all(value == 0 for value in sum.values()) and project.company_id.id != 10 and project.end_sale_project_month.year == YEARint + 2:  # если актирование 0, а месяц в нужном году, берем выручку
                    if project.stage_id.code == '30':
                        sum['potential'] = project.amount_untaxed_in_company_currency

                # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                sum = self.get_act_forecast_from_distributions(sum, project, YEARint + 2, False)
                margin_sum = self.get_margin_forecast_from_distributions(margin_sum, margin_plan, project, YEARint + 2,
                                                                         False, 1)

                for key in sum:  # убираем отрицательные, если не корректировочный проект
                    if not project.is_correction_project:
                        sum[key] = max(sum[key], 0)
                        margin_sum[key] = max(margin_sum[key], 0)

                sum_after_next_tmp += sum['commitment']
                prof_after_next_tmp += margin_sum['commitment']
                sum_after_next_tmp += sum['reserve'] * params['50']
                prof_after_next_tmp += margin_sum['reserve'] * params['50']
                sum_after_next_tmp += sum['potential'] * params['30']
                prof_after_next_tmp += margin_sum['potential'] * params['30']
        return (
            sum75tmpetalon, sum50tmpetalon, sum100tmp, sum75tmp, sum50tmp,
            prof75tmpetalon, prof50tmpetalon, prof100tmp, prof75tmp, prof50tmp,
            sum_next_75_q1_tmp, sum_next_50_q1_tmp, sum_next_30_q1_tmp,
            sum_next_75_tmp, sum_next_50_tmp, sum_next_30_tmp, sum_after_next_tmp,
            prof_next_75_q1_tmp, prof_next_50_q1_tmp, prof_next_30_q1_tmp,
            prof_next_75_tmp, prof_next_50_tmp, prof_next_30_tmp, prof_after_next_tmp
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

    def center_has_plan(self, responsibility_center):
        return self.env['project_budget.budget_plan_supervisor_spec'].search([
                    ('budget_plan_supervisor_id.year', '=', YEARint),
                    ('budget_plan_supervisor_id.responsibility_center_id', '=', responsibility_center.id),
                ])

    def print_row_values(self, workbook, sheet, row, column, YEAR, project, responsibility_center, params):
        global strYEAR
        global YEARint

        row_format_number = workbook.add_format({
            'border': 1,
            'font_size': 10,
        })
        row_format_number.set_num_format('#,##0')
        row_format_number_color_fact = workbook.add_format({
            "fg_color": '#C6E0B4',
            'border': 1,
            'font_size': 10,
        })
        row_format_number_color_fact.set_num_format('#,##0')
        head_format_month_itogo = workbook.add_format({
            'border': 1,
            "fg_color": '#D9E1F2',
            'diag_type': 3
        })
        row_format_number_color_percent = workbook.add_format({
            "fg_color": '#ffff99',
            'border': 1,
            'font_size': 10,
            'num_format': '0.00%',
        })

        if project.stage_id.code == '0':
            row_format_number.set_font_color('red')
            row_format_number_color_fact.set_font_color('red')
            head_format_month_itogo.set_font_color('red')

        sumQ100etalon =0
        sumQ75etalon = 0
        sumQ50etalon = 0
        sumQ100 =0
        sumQ75 = 0
        sumQ50 = 0
        sumHY100etalon =0
        sumHY75etalon = 0
        sumHY50etalon = 0
        sumHY100 =0
        sumHY75 = 0
        sumHY50 = 0
        sumYear100etalon =0
        sumYear75etalon = 0
        sumYear50etalon = 0
        sumYear100 =0
        sumYear75 = 0
        sumYear50 = 0

        # печать Контрактование, с НДС
        for element in self.quarter_rus_name:
            column += 1
            sumQ75tmpetalon = sumQ50tmpetalon = sumQ100tmp = sumQ75tmp = sumQ50tmp = 0

            if 'Q1' in element or 'Q2' in element:
                sheet.write_number(row, column + 0, 0, row_format_number)
                sheet.write_number(row, column + 1, 0, row_format_number_color_fact)
                sheet.write_number(row, column + 2, 0, row_format_number)
                sheet.write_number(row, column + 3, 0, row_format_number)
            elif 'Q3' in element or 'Q4' in element:
                sheet.write_number(row, column + 0, 0, row_format_number)
                sheet.write_number(row, column + 1, 0, row_format_number)
                sheet.write_number(row, column + 2, 0, row_format_number_color_fact)
                sheet.write_number(row, column + 3, 0, row_format_number)
                sheet.write_number(row, column + 4, 0, row_format_number)
            elif 'HY1' in element:
                sheet.write_number(row, column + 0, 0, row_format_number)
                sheet.write_number(row, column + 1, 0, row_format_number_color_fact)
                sheet.write_number(row, column + 2, 0, row_format_number_color_percent)
                sheet.write_number(row, column + 3, 0, row_format_number)
                sheet.write_number(row, column + 4, 0, row_format_number)
            elif 'HY2' in element:
                sheet.write_number(row, column + 0, 0, row_format_number)
                sheet.write_number(row, column + 1, 0, row_format_number)
                sheet.write_number(row, column + 2, 0, row_format_number_color_fact)
                sheet.write_number(row, column + 3, 0, row_format_number)
                sheet.write_number(row, column + 4, 0, row_format_number)
            elif element == 'YEAR':
                sheet.write_number(row, column + 0, 0, row_format_number)
                sheet.write_number(row, column + 1, 0, row_format_number)
                sheet.write_number(row, column + 2, 0, row_format_number_color_fact)
                sheet.write_number(row, column + 3, 0, row_format_number_color_percent)
                sheet.write_number(row, column + 4, 0, row_format_number)
                sheet.write_number(row, column + 5, 0, row_format_number)
            elif element == 'NEXT':
                sheet.write_number(row, column + 0, 0, row_format_number)
                sheet.write_number(row, column + 1, 0, row_format_number)
                sheet.write_number(row, column + 2, 0, row_format_number)
                sheet.write_number(row, column + 3, 0, row_format_number)

            sumQ75tmpetalon, sumQ50tmpetalon, sumQ100tmp, sumQ75tmp, sumQ50tmp = self.print_quarter_revenue_project(
                sheet, row, column, element, project, responsibility_center, params,
                row_format_number, row_format_number_color_fact
            )
            sumQ75etalon += sumQ75tmpetalon
            sumQ50etalon += sumQ50tmpetalon
            sumQ100 += sumQ100tmp
            sumQ75 += sumQ75tmp
            sumQ50 += sumQ50tmp

            if 'HY1' in element:  # 'HY1/YEAR' 'HY2/YEAR'
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8),xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 0, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 7),xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 1, formula, row_format_number_color_fact)
                sheet.write_formula(
                    row,
                    column + 2,
                    f'=IFERROR({xl_col_to_name(column + 1)}{row + 1}/{xl_col_to_name(column)}{row + 1}," ")',
                    row_format_number_color_percent
                )
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 6),
                                                       xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 3, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 5),
                                                       xl_col_to_name(column - 1))
                sheet.write_formula(row, column + 4, formula, row_format_number)

            elif 'HY2' in element:  # 'HY1/YEAR' 'HY2/YEAR'
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 10),
                                                       xl_col_to_name(column - 5))
                sheet.write_formula(row, column + 0, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 9),
                                                       xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8),
                                                       xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 7),
                                                       xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 3, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 6),
                                                       xl_col_to_name(column - 1))
                sheet.write_formula(row, column + 4, formula, row_format_number)

                sumYear100etalon += sumHY100etalon
                sumYear75etalon += sumHY75etalon
                sumYear50etalon += sumHY50etalon
                sumYear100 += sumHY100
                sumYear75 += sumHY75
                sumYear50 += sumHY50
                sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0

            elif element == 'YEAR':  # 'YEAR'

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 20), xl_col_to_name(column - 5))
                sheet.write_formula(row, column + 0, formula, row_format_number)
                formula = '=sum({1}{0})'.format(row + 1, xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 19), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)
                sheet.write_formula(
                    row,
                    column + 3,
                    f'=IFERROR({xl_col_to_name(column + 2)}{row + 1}/{xl_col_to_name(column + 1)}{row + 1}," ")',
                    row_format_number_color_percent
                )
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 17), xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 4, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 16), xl_col_to_name(column - 1))
                sheet.write_formula(row, column + 5, formula, row_format_number)

            if 'Q1' in element or 'Q2' in element:
                column += 3
            elif 'Q3' in element or 'Q4' in element:
                column += 4
            elif 'HY1' in element:
                column += 4
            elif 'HY2' in element:
                column += 4
            elif element == 'YEAR':
                column += 5
            elif element == 'NEXT':
                column += 2
        #end печать Контрактование, с НДС

        # Поступление денежных средсв, с НДС
        sumYear100etalon = sumYear75etalon = sumYear50etalon = sumYear100 = sumYear75 = sumYear50 = 0
        sumQ100etalon = sumQ75etalon = sumQ50etalon = sumQ100 = sumQ75 = sumQ50 = 0
        sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0

        for element in self.quarter_rus_name:
            column += 1
            sumQ75tmpetalon = sumQ50tmpetalon = sumQ100tmp = sumQ75tmp = sumQ50tmp = 0

            if 'Q1' in element or 'Q2' in element:
                sheet.write_number(row, column + 0, 0, row_format_number)
                sheet.write_number(row, column + 1, 0, row_format_number_color_fact)
                sheet.write_number(row, column + 2, 0, row_format_number)
                sheet.write_number(row, column + 3, 0, row_format_number)
            elif 'Q3' in element or 'Q4' in element:
                sheet.write_number(row, column + 0, 0, row_format_number)
                sheet.write_number(row, column + 1, 0, row_format_number)
                sheet.write_number(row, column + 2, 0, row_format_number_color_fact)
                sheet.write_number(row, column + 3, 0, row_format_number)
                sheet.write_number(row, column + 4, 0, row_format_number)
            elif 'HY1' in element:
                sheet.write_number(row, column + 0, 0, row_format_number)
                sheet.write_number(row, column + 1, 0, row_format_number_color_fact)
                sheet.write_number(row, column + 2, 0, row_format_number_color_percent)
                sheet.write_number(row, column + 3, 0, row_format_number)
                sheet.write_number(row, column + 4, 0, row_format_number)
            elif 'HY2' in element:
                sheet.write_number(row, column + 0, 0, row_format_number)
                sheet.write_number(row, column + 1, 0, row_format_number)
                sheet.write_number(row, column + 2, 0, row_format_number_color_fact)
                sheet.write_number(row, column + 3, 0, row_format_number)
                sheet.write_number(row, column + 4, 0, row_format_number)
            elif element == 'YEAR':
                sheet.write_number(row, column + 0, 0, row_format_number)
                sheet.write_number(row, column + 1, 0, row_format_number)
                sheet.write_number(row, column + 2, 0, row_format_number_color_fact)
                sheet.write_number(row, column + 3, 0, row_format_number_color_percent)
                sheet.write_number(row, column + 4, 0, row_format_number)
                sheet.write_number(row, column + 5, 0, row_format_number)
            elif element == 'NEXT':
                sheet.write_number(row, column + 0, 0, row_format_number)
                sheet.write_number(row, column + 1, 0, row_format_number)
                sheet.write_number(row, column + 2, 0, row_format_number)

            sumQ75tmpetalon, sumQ50tmpetalon, sumQ100tmp, sumQ75tmp, sumQ50tmp = self.print_quarter_pds_project(
                sheet, row, column, element, project, responsibility_center, params,
                row_format_number, row_format_number_color_fact
            )

            sumQ75etalon += sumQ75tmpetalon
            sumQ50etalon += sumQ50tmpetalon
            sumQ100 += sumQ100tmp
            sumQ75 += sumQ75tmp
            sumQ50 += sumQ50tmp

            if 'HY1' in element:  # 'HY1/YEAR' 'HY2/YEAR'
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8), xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 0, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 7), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 1, formula, row_format_number_color_fact)
                sheet.write_formula(
                    row,
                    column + 2,
                    f'=IFERROR({xl_col_to_name(column + 1)}{row + 1}/{xl_col_to_name(column)}{row + 1}," ")',
                    row_format_number_color_percent
                )
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 6),
                                                       xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 3, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 5),
                                                       xl_col_to_name(column - 1))
                sheet.write_formula(row, column + 4, formula, row_format_number)

            elif 'HY2' in element:  # 'HY1/YEAR' 'HY2/YEAR'
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 10),
                                                       xl_col_to_name(column - 5))
                sheet.write_formula(row, column + 0, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 9),
                                                       xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8),
                                                       xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 7),
                                                       xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 3, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 6),
                                                       xl_col_to_name(column - 1))
                sheet.write_formula(row, column + 4, formula, row_format_number)

                sumYear100etalon += sumHY100etalon
                sumYear75etalon += sumHY75etalon
                sumYear50etalon += sumHY50etalon
                sumYear100 += sumHY100
                sumYear75 += sumHY75
                sumYear50 += sumHY50
                sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0

            elif element == 'YEAR':  # 'YEAR'

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 20), xl_col_to_name(column - 5))
                sheet.write_formula(row, column + 0, formula, row_format_number)
                formula = '=sum({1}{0})'.format(row + 1, xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 19), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)
                sheet.write_formula(
                    row,
                    column + 3,
                    f'=IFERROR({xl_col_to_name(column + 2)}{row + 1}/{xl_col_to_name(column + 1)}{row + 1}," ")',
                    row_format_number_color_percent
                )
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 17), xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 4, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 16), xl_col_to_name(column - 1))
                sheet.write_formula(row, column + 5, formula, row_format_number)

            if 'Q1' in element or 'Q2' in element:
                column += 3
            elif 'Q3' in element or 'Q4' in element:
                column += 4
            elif 'HY1' in element:
                column += 4
            elif 'HY2' in element:
                column += 4
            elif element == 'YEAR':
                column += 5
            elif element == 'NEXT':
                column += 1
        # end Поступление денежных средсв, с НДС

        # Валовая Выручка, без НДС
        sumYear100etalon = sumYear75etalon = sumYear50etalon = sumYear100 = sumYear75 = sumYear50 = 0
        sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0

        for element in self.quarter_rus_name:

            column += 1

            if 'Q1' in element or 'Q2' in element:
                sheet.write_number(row, column + 0, 0, row_format_number)
                sheet.write_number(row, column + 1, 0, row_format_number_color_fact)
                sheet.write_number(row, column + 2, 0, row_format_number)
                sheet.write_number(row, column + 3, 0, row_format_number)
                sheet.write_number(row, column + 0 + params['margin_shift'], 0, row_format_number)
                sheet.write_number(row, column + 1 + params['margin_shift'], 0, row_format_number_color_fact)
                sheet.write_number(row, column + 2 + params['margin_shift'], 0, row_format_number)
                sheet.write_number(row, column + 3 + params['margin_shift'], 0, row_format_number)
            elif 'Q3' in element or 'Q4' in element:
                sheet.write_number(row, column + 0, 0, row_format_number)
                sheet.write_number(row, column + 1, 0, row_format_number)
                sheet.write_number(row, column + 2, 0, row_format_number_color_fact)
                sheet.write_number(row, column + 3, 0, row_format_number)
                sheet.write_number(row, column + 4, 0, row_format_number)
                sheet.write_number(row, column + 0 + params['margin_shift'], 0, row_format_number)
                sheet.write_number(row, column + 1 + params['margin_shift'], 0, row_format_number)
                sheet.write_number(row, column + 2 + params['margin_shift'], 0, row_format_number_color_fact)
                sheet.write_number(row, column + 3 + params['margin_shift'], 0, row_format_number)
                sheet.write_number(row, column + 4 + params['margin_shift'], 0, row_format_number)
            elif 'HY1' in element:
                sheet.write_number(row, column + 0, 0, row_format_number)
                sheet.write_number(row, column + 1, 0, row_format_number_color_fact)
                sheet.write_number(row, column + 2, 0, row_format_number_color_percent)
                sheet.write_number(row, column + 3, 0, row_format_number)
                sheet.write_number(row, column + 4, 0, row_format_number)
                sheet.write_number(row, column + 0 + params['margin_shift'], 0, row_format_number)
                sheet.write_number(row, column + 1 + params['margin_shift'], 0, row_format_number_color_fact)
                sheet.write_number(row, column + 2 + params['margin_shift'], 0, row_format_number_color_percent)
                sheet.write_number(row, column + 3 + params['margin_shift'], 0, row_format_number)
                sheet.write_number(row, column + 4 + params['margin_shift'], 0, row_format_number)
            elif 'HY2' in element:
                sheet.write_number(row, column + 0, 0, row_format_number)
                sheet.write_number(row, column + 1, 0, row_format_number)
                sheet.write_number(row, column + 2, 0, row_format_number_color_fact)
                sheet.write_number(row, column + 3, 0, row_format_number)
                sheet.write_number(row, column + 4, 0, row_format_number)
                sheet.write_number(row, column + 0 + params['margin_shift'], 0, row_format_number)
                sheet.write_number(row, column + 1 + params['margin_shift'], 0, row_format_number)
                sheet.write_number(row, column + 2 + params['margin_shift'], 0, row_format_number_color_fact)
                sheet.write_number(row, column + 3 + params['margin_shift'], 0, row_format_number)
                sheet.write_number(row, column + 4 + params['margin_shift'], 0, row_format_number)
            elif element == 'YEAR':
                sheet.write_number(row, column + 0, 0, row_format_number)
                sheet.write_number(row, column + 1, 0, row_format_number)
                sheet.write_number(row, column + 2, 0, row_format_number_color_fact)
                sheet.write_number(row, column + 3, 0, row_format_number_color_percent)
                sheet.write_number(row, column + 4, 0, row_format_number)
                sheet.write_number(row, column + 5, 0, row_format_number)
                sheet.write_number(row, column + 0 + params['margin_shift'], 0, row_format_number)
                sheet.write_number(row, column + 1 + params['margin_shift'], 0, row_format_number)
                sheet.write_number(row, column + 2 + params['margin_shift'], 0, row_format_number_color_fact)
                sheet.write_number(row, column + 3 + params['margin_shift'], 0, row_format_number_color_percent)
                sheet.write_number(row, column + 4 + params['margin_shift'], 0, row_format_number)
                sheet.write_number(row, column + 5 + params['margin_shift'], 0, row_format_number)
            elif element == 'NEXT':
                sheet.write_number(row, column + 0, 0, row_format_number)
                sheet.write_number(row, column + 1, 0, row_format_number)
                sheet.write_number(row, column + 2, 0, row_format_number)
                sheet.write_number(row, column + 3, 0, row_format_number)
                sheet.write_number(row, column + 0 + params['margin_shift'], 0, row_format_number)
                sheet.write_number(row, column + 1 + params['margin_shift'], 0, row_format_number)
                sheet.write_number(row, column + 2 + params['margin_shift'], 0, row_format_number)
                sheet.write_number(row, column + 3 + params['margin_shift'], 0, row_format_number)

            (sumQ75etalon, sumQ50etalon,
             sumQ100, sumQ75, sumQ50) = self.print_quarter_planned_acceptance_project(
                sheet,
                row,
                column,
                element,
                project,
                responsibility_center,
                params,
                row_format_number,
                row_format_number_color_fact
            )

            sumHY100etalon += sumQ100etalon
            sumHY75etalon += sumQ75etalon
            sumHY50etalon += sumQ50etalon
            sumHY100 += sumQ100
            sumHY75 += sumQ75
            sumHY50 += sumQ50

            if 'HY1' in element:  # 'HY1/YEAR' 'HY2/YEAR'
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8), xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 0, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 7), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 1, formula, row_format_number_color_fact)
                sheet.write_formula(
                    row,
                    column + 2,
                    f'=IFERROR({xl_col_to_name(column + 1)}{row + 1}/{xl_col_to_name(column)}{row + 1}," ")',
                    row_format_number_color_percent
                )
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 6),
                                                       xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 3, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 5),
                                                       xl_col_to_name(column - 1))
                sheet.write_formula(row, column + 4, formula, row_format_number)


                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8 + params['margin_shift']), xl_col_to_name(column - 4 + params['margin_shift']))
                sheet.write_formula(row, column + 0 + params['margin_shift'], formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 7 + params['margin_shift']), xl_col_to_name(column - 3 + params['margin_shift']))
                sheet.write_formula(row, column + 1 + params['margin_shift'], formula, row_format_number_color_fact)
                sheet.write_formula(
                    row,
                    column + 2 + params['margin_shift'],
                    f'=IFERROR({xl_col_to_name(column + 1 + params["margin_shift"])}{row + 1}/{xl_col_to_name(column + params["margin_shift"])}{row + 1}," ")',
                    row_format_number_color_percent
                )
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 6 + params['margin_shift']),
                                                       xl_col_to_name(column - 2 + params['margin_shift']))
                sheet.write_formula(row, column + 3 + params['margin_shift'], formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 5 + params['margin_shift']),
                                                       xl_col_to_name(column - 1 + params['margin_shift']))
                sheet.write_formula(row, column + 4 + params['margin_shift'], formula, row_format_number)

                sumYear100etalon += sumHY100etalon
                sumYear75etalon += sumHY75etalon
                sumYear50etalon += sumHY50etalon
                sumYear100 += sumHY100
                sumYear75 += sumHY75
                sumYear50 += sumHY50
                sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0

            elif 'HY2' in element:  # 'HY1/YEAR' 'HY2/YEAR'
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 10),
                                                       xl_col_to_name(column - 5))
                sheet.write_formula(row, column + 0, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 9),
                                                       xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8),
                                                       xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 7),
                                                       xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 3, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 6),
                                                       xl_col_to_name(column - 1))
                sheet.write_formula(row, column + 4, formula, row_format_number)

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 10 + params['margin_shift']),
                                                       xl_col_to_name(column - 5 + params['margin_shift']))
                sheet.write_formula(row, column + 0 + params['margin_shift'], formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 9 + params['margin_shift']),
                                                       xl_col_to_name(column - 4 + params['margin_shift']))
                sheet.write_formula(row, column + 1 + params['margin_shift'], formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8 + params['margin_shift']),
                                                       xl_col_to_name(column - 3 + params['margin_shift']))
                sheet.write_formula(row, column + 2 + params['margin_shift'], formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 7 + params['margin_shift']),
                                                       xl_col_to_name(column - 2 + params['margin_shift']))
                sheet.write_formula(row, column + 3 + params['margin_shift'], formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 6 + params['margin_shift']),
                                                       xl_col_to_name(column - 1 + params['margin_shift']))
                sheet.write_formula(row, column + 4 + params['margin_shift'], formula, row_format_number)

                sumYear100etalon += sumHY100etalon
                sumYear75etalon += sumHY75etalon
                sumYear50etalon += sumHY50etalon
                sumYear100 += sumHY100
                sumYear75 += sumHY75
                sumYear50 += sumHY50
                sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0

            elif element == 'YEAR':  # 'YEAR'

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 20), xl_col_to_name(column - 5))
                sheet.write_formula(row, column + 0, formula, row_format_number)
                formula = '=sum({1}{0})'.format(row + 1, xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 19), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)
                sheet.write_formula(
                    row,
                    column + 3,
                    f'=IFERROR({xl_col_to_name(column + 2)}{row + 1}/{xl_col_to_name(column + 1)}{row + 1}," ")',
                    row_format_number_color_percent
                )
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 17), xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 4, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 16), xl_col_to_name(column - 1))
                sheet.write_formula(row, column + 5, formula, row_format_number)

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 20 + params['margin_shift']), xl_col_to_name(column - 5 + params['margin_shift']))
                sheet.write_formula(row, column + 0 + params['margin_shift'], formula, row_format_number)
                formula = '=sum({1}{0})'.format(row + 1, xl_col_to_name(column - 4 + params['margin_shift']))
                sheet.write_formula(row, column + 1 + params['margin_shift'], formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 19 + params['margin_shift']), xl_col_to_name(column - 3 + params['margin_shift']))
                sheet.write_formula(row, column + 2 + params['margin_shift'], formula, row_format_number_color_fact)
                sheet.write_formula(
                    row,
                    column + 3 + params['margin_shift'],
                    f'=IFERROR({xl_col_to_name(column + 2 + params["margin_shift"])}{row + 1}/{xl_col_to_name(column + 1 + params["margin_shift"])}{row + 1}," ")',
                    row_format_number_color_percent
                )
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 17 + params['margin_shift']), xl_col_to_name(column - 2 + params['margin_shift']))
                sheet.write_formula(row, column + 4 + params['margin_shift'], formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 16 + params['margin_shift']), xl_col_to_name(column - 1 + params['margin_shift']))
                sheet.write_formula(row, column + 5 + params['margin_shift'], formula, row_format_number)

            if 'Q1' in element or 'Q2' in element:
                column += 3
            elif 'Q3' in element or 'Q4' in element:
                column += 4
            elif 'HY1' in element:
                column += 4
            elif 'HY2' in element:
                column += 4
            elif element == 'YEAR':
                column += 5
            elif element == 'NEXT':
                column += 2
        # end Валовая Выручка, без НДС

    def print_row_values_center(self, workbook, sheet, row, column, YEAR, projects, responsibility_center, formula_centers,
                                params, formats):
        global strYEAR
        global YEARint

        # печать Контрактование, с НДС

        for element in self.quarter_rus_name:

            column += 1

            sumM75etalon = 0
            sumM50etalon = 0
            sumM100 = 0
            sumM75 = 0
            sumM50 = 0
            sum_next_75_q1 = 0
            sum_next_50_q1 = 0
            sum_next_30_q1 = 0
            sum_next_75 = 0
            sum_next_50 = 0
            sum_next_30 = 0
            sum_after_next = 0

            if 'Q1' in element or 'Q2' in element:
                sheet.write_number(row, column + 0, 0, formats['number'])
                sheet.write_number(row, column + 1, 0, formats['fact'])
                sheet.write_number(row, column + 2, 0, formats['number'])
                sheet.write_number(row, column + 3, 0, formats['number'])
            elif 'Q3' in element or 'Q4' in element:
                sheet.write_number(row, column + 0, 0, formats['number'])
                sheet.write_number(row, column + 1, 0, formats['number'])
                sheet.write_number(row, column + 2, 0, formats['fact'])
                sheet.write_number(row, column + 3, 0, formats['number'])
                sheet.write_number(row, column + 4, 0, formats['number'])
            elif 'HY1' in element:
                sheet.write_number(row, column + 0, 0, formats['number'])
                sheet.write_number(row, column + 1, 0, formats['fact'])
                sheet.write_number(row, column + 2, 0, formats['percent'])
                sheet.write_number(row, column + 3, 0, formats['number'])
                sheet.write_number(row, column + 4, 0, formats['number'])
            elif 'HY2' in element:
                sheet.write_number(row, column + 0, 0, formats['number'])
                sheet.write_number(row, column + 1, 0, formats['number'])
                sheet.write_number(row, column + 2, 0, formats['fact'])
                sheet.write_number(row, column + 3, 0, formats['number'])
                sheet.write_number(row, column + 4, 0, formats['number'])
            elif element == 'YEAR':
                sheet.write_number(row, column + 0, 0, formats['number'])
                sheet.write_number(row, column + 1, 0, formats['number'])
                sheet.write_number(row, column + 2, 0, formats['fact'])
                sheet.write_number(row, column + 3, 0, formats['percent'])
                sheet.write_number(row, column + 4, 0, formats['number'])
                sheet.write_number(row, column + 5, 0, formats['number'])
            elif element == 'NEXT':
                sheet.write_number(row, column + 0, 0, formats['number'])
                sheet.write_number(row, column + 1, 0, formats['number'])
                sheet.write_number(row, column + 2, 0, formats['number'])
                sheet.write_number(row, column + 3, 0, formats['number'])

            for project in projects:
                (sumM75tmpetalon, sumM50tmpetalon,
                 sumM100tmp, sumM75tmp, sumM50tmp,
                 sum_next_75_q1_tmp, sum_next_50_q1_tmp, sum_next_30_q1_tmp,
                 sum_next_75_tmp, sum_next_50_tmp, sum_next_30_tmp,
                 sum_after_next_tmp) = self.calculate_quarter_revenue(element, project, responsibility_center, params)

                sumM75etalon += sumM75tmpetalon
                sumM50etalon += sumM50tmpetalon
                sumM100 += sumM100tmp
                sumM75 += sumM75tmp
                sumM50 += sumM50tmp
                sum_next_75_q1 += sum_next_75_q1_tmp
                sum_next_50_q1 += sum_next_50_q1_tmp
                sum_next_30_q1 += sum_next_30_q1_tmp
                sum_next_75 += sum_next_75_tmp
                sum_next_50 += sum_next_50_tmp
                sum_next_30 += sum_next_30_tmp
                sum_after_next += sum_after_next_tmp

            child_centers_rows = formula_centers.get('responsibility_center_' + str(responsibility_center.id if responsibility_center else '')) or ''

            if 'Q' in element:
                if 'Q1' in element or 'Q2' in element:
                    f_Q100 = 'sum(' + str(sumM100) + child_centers_rows.format(xl_col_to_name(column + 1)) + ')'
                    f_Q75 = 'sum(' + str(sumM75) + child_centers_rows.format(xl_col_to_name(column + 2)) + ')'
                    f_Q50 = 'sum(' + str(sumM50) + child_centers_rows.format(xl_col_to_name(column + 3)) + ')'

                    sheet.write_formula(row, column + 1, f_Q100, formats['fact'])
                    sheet.write_formula(row, column + 2, f_Q75, formats['forecast'])
                    sheet.write_formula(row, column + 3, f_Q50, formats['forecast'])
                    column += 3

                elif 'Q3' in element or 'Q4' in element:
                    f_Q100 = 'sum(' + str(sumM100) + child_centers_rows.format(xl_col_to_name(column + 2)) + ')'
                    f_Q75 = 'sum(' + str(sumM75) + child_centers_rows.format(xl_col_to_name(column + 3)) + ')'
                    f_Q50 = 'sum(' + str(sumM50) + child_centers_rows.format(xl_col_to_name(column + 4)) + ')'

                    sheet.write_formula(row, column + 2, f_Q100, formats['fact'])
                    sheet.write_formula(row, column + 3, f_Q75, formats['forecast'])
                    sheet.write_formula(row, column + 4, f_Q50, formats['forecast'])
                    column += 4

            elif 'HY1' in element:  # 'HY1/YEAR' 'HY2/YEAR'
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 7), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 1, formula, formats['fact'])

                sheet.write_formula(
                    row,
                    column + 2,
                    f'=IFERROR({xl_col_to_name(column + 1)}{row + 1}/{xl_col_to_name(column)}{row + 1}," ")',
                    formats['percent']
                )

                formula = '=sum({1}{0},{2}{0})'.format(
                    row + 1,
                    xl_col_to_name(column - 6),
                    xl_col_to_name(column - 2)
                )
                sheet.write_formula(row, column + 3, formula, formats['forecast'])
                formula = '=sum({1}{0},{2}{0})'.format(
                    row + 1,
                    xl_col_to_name(column - 5),
                    xl_col_to_name(column - 1)
                )
                sheet.write_formula(row, column + 4, formula, formats['forecast'])
                column += 4

            elif 'HY2' in element:  # 'HY1/YEAR' 'HY2/YEAR'
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 2, formula, formats['fact'])

                formula = '=sum({1}{0},{2}{0})'.format(
                    row + 1,
                    xl_col_to_name(column - 7),
                    xl_col_to_name(column - 2)
                )
                sheet.write_formula(row, column + 3, formula, formats['forecast'])
                formula = '=sum({1}{0},{2}{0})'.format(
                    row + 1,
                    xl_col_to_name(column - 6),
                    xl_col_to_name(column - 1)
                )
                sheet.write_formula(row, column + 4, formula, formats['forecast'])
                column += 4

            elif element == 'YEAR':  # 'YEAR'
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 19), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 2, formula, formats['fact'])

                sheet.write_formula(
                    row,
                    column + 3,
                    f'=IFERROR({xl_col_to_name(column + 2)}{row + 1}/{xl_col_to_name(column + 1)}{row + 1}," ")',
                    formats['percent']
                )

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 17), xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 4, formula, formats['forecast'])
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 16), xl_col_to_name(column - 1))
                sheet.write_formula(row, column + 5, formula, formats['forecast'])
                column += 5

            elif element == 'NEXT':

                f_sum_next_75 = 'sum(' + str(sum_next_75) + child_centers_rows.format(xl_col_to_name(column)) + ')'
                f_sum_next_50 = 'sum(' + str(sum_next_50) + child_centers_rows.format(xl_col_to_name(column + 1)) + ')'
                f_sum_next_30 = 'sum(' + str(sum_next_30) + child_centers_rows.format(xl_col_to_name(column + 2)) + ')'
                sheet.write_formula(row, column, f_sum_next_75, formats['next'])
                sheet.write_formula(row, column + 1, f_sum_next_50, formats['next'])
                sheet.write_formula(row, column + 2, f_sum_next_30, formats['next'])
                column += 2

            elif element == 'AFTER NEXT':
                f_sum_after_next = 'sum(' + str(sum_after_next) + child_centers_rows.format(
                    xl_col_to_name(column)) + ')'
                sheet.write_formula(row, column, f_sum_after_next, formats['next'])
        # end печать Контрактование, с НДС

        # Поступление денежных средств, с НДС
        for element in self.quarter_rus_name:
            column += 1

            sumM75etalon = 0
            sumM50etalon = 0
            sumM100 = 0
            sumM75 = 0
            sumM50 = 0
            sum_next_75_q1 = 0
            sum_next_50_q1 = 0
            sum_next_30_q1 = 0
            sum_next_75 = 0
            sum_next_50 = 0
            sum_next_30 = 0
            sum_after_next = 0

            if 'Q1' in element or 'Q2' in element:
                sheet.write_number(row, column + 0, 0, formats['number'])
                sheet.write_number(row, column + 1, 0, formats['fact'])
                sheet.write_number(row, column + 2, 0, formats['number'])
                sheet.write_number(row, column + 3, 0, formats['number'])
            elif 'Q3' in element or 'Q4' in element:
                sheet.write_number(row, column + 0, 0, formats['number'])
                sheet.write_number(row, column + 1, 0, formats['number'])
                sheet.write_number(row, column + 2, 0, formats['fact'])
                sheet.write_number(row, column + 3, 0, formats['number'])
                sheet.write_number(row, column + 4, 0, formats['number'])
            elif 'HY1' in element:
                sheet.write_number(row, column + 0, 0, formats['number'])
                sheet.write_number(row, column + 1, 0, formats['fact'])
                sheet.write_number(row, column + 2, 0, formats['percent'])
                sheet.write_number(row, column + 3, 0, formats['number'])
                sheet.write_number(row, column + 4, 0, formats['number'])
            elif 'HY2' in element:
                sheet.write_number(row, column + 0, 0, formats['number'])
                sheet.write_number(row, column + 1, 0, formats['number'])
                sheet.write_number(row, column + 2, 0, formats['fact'])
                sheet.write_number(row, column + 3, 0, formats['number'])
                sheet.write_number(row, column + 4, 0, formats['number'])
            elif element == 'YEAR':
                sheet.write_number(row, column + 0, 0, formats['number'])
                sheet.write_number(row, column + 1, 0, formats['number'])
                sheet.write_number(row, column + 2, 0, formats['fact'])
                sheet.write_number(row, column + 3, 0, formats['percent'])
                sheet.write_number(row, column + 4, 0, formats['number'])
                sheet.write_number(row, column + 5, 0, formats['number'])
            elif element == 'NEXT':
                sheet.write_number(row, column + 0, 0, formats['number'])
                sheet.write_number(row, column + 1, 0, formats['number'])
                sheet.write_number(row, column + 2, 0, formats['number'])

            for project in projects:
                (sumM75tmpetalon, sumM50tmpetalon,
                 sumM100tmp, sumM75tmp, sumM50tmp,
                 sum_next_75_q1_tmp, sum_next_50_q1_tmp, sum_next_30_q1_tmp,
                 sum_next_75_tmp, sum_next_50_tmp, sum_next_30_tmp,
                 sum_after_next_tmp) = self.calculate_quarter_pds(element, project, responsibility_center, params)

                sumM75etalon += sumM75tmpetalon
                sumM50etalon += sumM50tmpetalon
                sumM100 += sumM100tmp
                sumM75 += sumM75tmp
                sumM50 += sumM50tmp
                sum_next_75_q1 += sum_next_75_q1_tmp
                sum_next_50_q1 += sum_next_50_q1_tmp
                sum_next_30_q1 += sum_next_30_q1_tmp
                sum_next_75 += sum_next_75_tmp
                sum_next_50 += sum_next_50_tmp
                sum_next_30 += sum_next_30_tmp
                sum_after_next += sum_after_next_tmp

            child_centers_rows = formula_centers.get('responsibility_center_' + str(responsibility_center.id if responsibility_center else '')) or ''

            if 'Q' in element:
                if 'Q1' in element or 'Q2' in element:
                    f_Q100 = 'sum(' + str(sumM100) + child_centers_rows.format(xl_col_to_name(column + 1)) + ')'
                    f_Q75 = 'sum(' + str(sumM75) + child_centers_rows.format(xl_col_to_name(column + 2)) + ')'
                    f_Q50 = 'sum(' + str(sumM50) + child_centers_rows.format(xl_col_to_name(column + 3)) + ')'

                    sheet.write_formula(row, column + 1, f_Q100, formats['fact'])
                    sheet.write_formula(row, column + 2, f_Q75, formats['forecast'])
                    sheet.write_formula(row, column + 3, f_Q50, formats['forecast'])
                    column += 3

                elif 'Q3' in element or 'Q4' in element:
                    f_Q100 = 'sum(' + str(sumM100) + child_centers_rows.format(xl_col_to_name(column + 2)) + ')'
                    f_Q75 = 'sum(' + str(sumM75) + child_centers_rows.format(xl_col_to_name(column + 3)) + ')'
                    f_Q50 = 'sum(' + str(sumM50) + child_centers_rows.format(xl_col_to_name(column + 4)) + ')'

                    sheet.write_formula(row, column + 2, f_Q100, formats['fact'])
                    sheet.write_formula(row, column + 3, f_Q75, formats['forecast'])
                    sheet.write_formula(row, column + 4, f_Q50, formats['forecast'])
                    column += 4

            elif 'HY1' in element:  # 'HY1/YEAR' 'HY2/YEAR'
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 7), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 1, formula, formats['fact'])

                sheet.write_formula(
                    row,
                    column + 2,
                    f'=IFERROR({xl_col_to_name(column + 1)}{row + 1}/{xl_col_to_name(column)}{row + 1}," ")',
                    formats['percent']
                )

                formula = '=sum({1}{0},{2}{0})'.format(
                    row + 1,
                    xl_col_to_name(column - 6),
                    xl_col_to_name(column - 2)
                )
                sheet.write_formula(row, column + 3, formula, formats['forecast'])
                formula = '=sum({1}{0},{2}{0})'.format(
                    row + 1,
                    xl_col_to_name(column - 5),
                    xl_col_to_name(column - 1)
                )
                sheet.write_formula(row, column + 4, formula, formats['forecast'])
                column += 4

            elif 'HY2' in element:  # 'HY1/YEAR' 'HY2/YEAR'
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 2, formula, formats['fact'])

                formula = '=sum({1}{0},{2}{0})'.format(
                    row + 1,
                    xl_col_to_name(column - 7),
                    xl_col_to_name(column - 2)
                )
                sheet.write_formula(row, column + 3, formula, formats['forecast'])
                formula = '=sum({1}{0},{2}{0})'.format(
                    row + 1,
                    xl_col_to_name(column - 6),
                    xl_col_to_name(column - 1)
                )
                sheet.write_formula(row, column + 4, formula, formats['forecast'])
                column += 4

            elif element == 'YEAR':  # 'YEAR'
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 19), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 2, formula, formats['fact'])

                sheet.write_formula(
                    row,
                    column + 3,
                    f'=IFERROR({xl_col_to_name(column + 2)}{row + 1}/{xl_col_to_name(column + 1)}{row + 1}," ")',
                    formats['percent']
                )

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 17), xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 4, formula, formats['forecast'])
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 16), xl_col_to_name(column - 1))
                sheet.write_formula(row, column + 5, formula, formats['forecast'])
                column += 5

            elif element == 'NEXT':
                f_sum_next_75 = 'sum(' + str(sum_next_75) + child_centers_rows.format(xl_col_to_name(column)) + ')'
                f_sum_next_50 = 'sum(' + str(sum_next_50) + child_centers_rows.format(xl_col_to_name(column + 1)) + ')'
                sheet.write_formula(row, column, f_sum_next_75, formats['next'])
                sheet.write_formula(row, column + 1, f_sum_next_50, formats['next'])
                column += 1

            elif element == 'AFTER NEXT':
                f_sum_after_next = 'sum(' + str(sum_after_next) + child_centers_rows.format(
                    xl_col_to_name(column)) + ')'
                sheet.write_formula(row, column, f_sum_after_next, formats['next'])
        # end Поступление денежных средсв, с НДС

        # Валовая Выручка, без НДС
        sumYear100etalon = sumYear75etalon = sumYear50etalon = sumYear100 = sumYear75 = sumYear50 = 0
        sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0

        for element in self.quarter_rus_name:

            column += 1

            sumQ100etalon = sumQ75etalon = sumQ50etalon = sumQ100 = sumQ75 = sumQ50 = 0
            profQ100etalon = profQ75etalon = profQ50etalon = profQ100 = profQ75 = profQ50 = 0
            sum_next_75_q1 = sum_next_50_q1 = sum_next_30_q1 = 0
            sum_next_75 = sum_next_50 = sum_next_30 = sum_after_next = 0
            prof_next_75_q1 = prof_next_50_q1 = prof_next_30_q1 = 0
            prof_next_75 = prof_next_50 = prof_next_30 = prof_after_next = 0

            if 'Q1' in element or 'Q2' in element:
                sheet.write_number(row, column + 0, 0, formats['number'])
                sheet.write_number(row, column + 1, 0, formats['fact'])
                sheet.write_number(row, column + 2, 0, formats['number'])
                sheet.write_number(row, column + 3, 0, formats['number'])
                sheet.write_number(row, column + 0 + params['margin_shift'], 0, formats['number'])
                sheet.write_number(row, column + 1 + params['margin_shift'], 0, formats['fact'])
                sheet.write_number(row, column + 2 + params['margin_shift'], 0, formats['number'])
                sheet.write_number(row, column + 3 + params['margin_shift'], 0, formats['number'])
            elif 'Q3' in element or 'Q4' in element:
                sheet.write_number(row, column + 0, 0, formats['number'])
                sheet.write_number(row, column + 1, 0, formats['number'])
                sheet.write_number(row, column + 2, 0, formats['fact'])
                sheet.write_number(row, column + 3, 0, formats['number'])
                sheet.write_number(row, column + 4, 0, formats['number'])
                sheet.write_number(row, column + 0 + params['margin_shift'], 0, formats['number'])
                sheet.write_number(row, column + 1 + params['margin_shift'], 0, formats['number'])
                sheet.write_number(row, column + 2 + params['margin_shift'], 0, formats['fact'])
                sheet.write_number(row, column + 3 + params['margin_shift'], 0, formats['number'])
                sheet.write_number(row, column + 4 + params['margin_shift'], 0, formats['number'])
            elif 'HY1' in element:
                sheet.write_number(row, column + 0, 0, formats['number'])
                sheet.write_number(row, column + 1, 0, formats['fact'])
                sheet.write_number(row, column + 2, 0, formats['percent'])
                sheet.write_number(row, column + 3, 0, formats['number'])
                sheet.write_number(row, column + 4, 0, formats['number'])
                sheet.write_number(row, column + 0 + params['margin_shift'], 0, formats['number'])
                sheet.write_number(row, column + 1 + params['margin_shift'], 0, formats['fact'])
                sheet.write_number(row, column + 2 + params['margin_shift'], 0, formats['percent'])
                sheet.write_number(row, column + 3 + params['margin_shift'], 0, formats['number'])
                sheet.write_number(row, column + 4 + params['margin_shift'], 0, formats['number'])
            elif 'HY2' in element:
                sheet.write_number(row, column + 0, 0, formats['number'])
                sheet.write_number(row, column + 1, 0, formats['number'])
                sheet.write_number(row, column + 2, 0, formats['fact'])
                sheet.write_number(row, column + 3, 0, formats['number'])
                sheet.write_number(row, column + 4, 0, formats['number'])
                sheet.write_number(row, column + 0 + params['margin_shift'], 0, formats['number'])
                sheet.write_number(row, column + 1 + params['margin_shift'], 0, formats['number'])
                sheet.write_number(row, column + 2 + params['margin_shift'], 0, formats['fact'])
                sheet.write_number(row, column + 3 + params['margin_shift'], 0, formats['number'])
                sheet.write_number(row, column + 4 + params['margin_shift'], 0, formats['number'])
            elif element == 'YEAR':
                sheet.write_number(row, column + 0, 0, formats['number'])
                sheet.write_number(row, column + 1, 0, formats['number'])
                sheet.write_number(row, column + 2, 0, formats['fact'])
                sheet.write_number(row, column + 3, 0, formats['percent'])
                sheet.write_number(row, column + 4, 0, formats['number'])
                sheet.write_number(row, column + 5, 0, formats['number'])
                sheet.write_number(row, column + 0 + params['margin_shift'], 0, formats['number'])
                sheet.write_number(row, column + 1 + params['margin_shift'], 0, formats['number'])
                sheet.write_number(row, column + 2 + params['margin_shift'], 0, formats['fact'])
                sheet.write_number(row, column + 3 + params['margin_shift'], 0, formats['percent'])
                sheet.write_number(row, column + 4 + params['margin_shift'], 0, formats['number'])
                sheet.write_number(row, column + 5 + params['margin_shift'], 0, formats['number'])
            elif element == 'NEXT':
                sheet.write_number(row, column + 0, 0, formats['number'])
                sheet.write_number(row, column + 1, 0, formats['number'])
                sheet.write_number(row, column + 2, 0, formats['number'])
                sheet.write_number(row, column + 3, 0, formats['number'])
                sheet.write_number(row, column + 0 + params['margin_shift'], 0, formats['number'])
                sheet.write_number(row, column + 1 + params['margin_shift'], 0, formats['number'])
                sheet.write_number(row, column + 2 + params['margin_shift'], 0, formats['number'])
                sheet.write_number(row, column + 3 + params['margin_shift'], 0, formats['number'])

            for project in projects:
                (sum75tmpetalon, sum50tmpetalon, sum100tmp, sum75tmp, sum50tmp,
                 prof75tmpetalon, prof50tmpetalon, prof100tmp, prof75tmp, prof50tmp,
                 sum_next_75_q1_tmp, sum_next_50_q1_tmp, sum_next_30_q1_tmp,
                 sum_next_75_tmp, sum_next_50_tmp, sum_next_30_tmp, sum_after_next_tmp,
                 prof_next_75_q1_tmp, prof_next_50_q1_tmp, prof_next_30_q1_tmp,
                 prof_next_75_tmp, prof_next_50_tmp, prof_next_30_tmp, prof_after_next_tmp
                 ) = self.calculate_quarter_planned_acceptance(element, project, responsibility_center, params)

                sumQ75etalon += sum75tmpetalon
                sumQ50etalon += sum50tmpetalon
                sumQ100 += sum100tmp
                sumQ75 += sum75tmp
                sumQ50 += sum50tmp
                sum_next_75_q1 += sum_next_75_q1_tmp
                sum_next_50_q1 += sum_next_50_q1_tmp
                sum_next_30_q1 += sum_next_30_q1_tmp
                sum_next_75 += sum_next_75_tmp
                sum_next_50 += sum_next_50_tmp
                sum_next_30 += sum_next_30_tmp
                sum_after_next += sum_after_next_tmp

                profQ75etalon += prof75tmpetalon
                profQ50etalon += prof50tmpetalon
                profQ100 += prof100tmp
                profQ75 += prof75tmp
                profQ50 += prof50tmp
                prof_next_75_q1 += prof_next_75_q1_tmp
                prof_next_50_q1 += prof_next_50_q1_tmp
                prof_next_30_q1 += prof_next_30_q1_tmp
                prof_next_75 += prof_next_75_tmp
                prof_next_50 += prof_next_50_tmp
                prof_next_30 += prof_next_30_tmp
                prof_after_next += prof_after_next_tmp

            child_centers_rows = formula_centers.get('responsibility_center_' + str(responsibility_center.id if responsibility_center else '')) or ''

            if 'Q' in element:
                if 'Q1' in element or 'Q2' in element:
                    f_sumQ100 = 'sum(' + str(sumQ100) + child_centers_rows.format(xl_col_to_name(column + 1)) + ')'
                    f_sumQ75 = 'sum(' + str(sumQ75) + child_centers_rows.format(xl_col_to_name(column + 2)) + ')'
                    f_sumQ50 = 'sum(' + str(sumQ50) + child_centers_rows.format(xl_col_to_name(column + 3)) + ')'
                    f_profQ100 = 'sum(' + str(profQ100) + child_centers_rows.format(xl_col_to_name(column + 1 + params['margin_shift'])) + ')'
                    f_profQ75 = 'sum(' + str(profQ75) + child_centers_rows.format(xl_col_to_name(column + 2 + params['margin_shift'])) + ')'
                    f_profQ50 = 'sum(' + str(profQ50) + child_centers_rows.format(xl_col_to_name(column + 3 + params['margin_shift'])) + ')'

                    sheet.write_formula(row, column + 1, f_sumQ100, formats['fact'])
                    sheet.write_formula(row, column + 1 + params['margin_shift'], f_profQ100, formats['fact'])
                    sheet.write_formula(row, column + 2, f_sumQ75, formats['forecast'])
                    sheet.write_formula(row, column + 2 + params['margin_shift'], f_profQ75, formats['forecast'])
                    sheet.write_formula(row, column + 3, f_sumQ50, formats['forecast'])
                    sheet.write_formula(row, column + 3 + params['margin_shift'], f_profQ50, formats['forecast'])
                    column += 3

                elif 'Q3' in element or 'Q4' in element:
                    f_sumQ100 = 'sum(' + str(sumQ100) + child_centers_rows.format(xl_col_to_name(column + 2)) + ')'
                    f_sumQ75 = 'sum(' + str(sumQ75) + child_centers_rows.format(xl_col_to_name(column + 3)) + ')'
                    f_sumQ50 = 'sum(' + str(sumQ50) + child_centers_rows.format(xl_col_to_name(column + 4)) + ')'
                    f_profQ100 = 'sum(' + str(profQ100) + child_centers_rows.format(
                        xl_col_to_name(column + 2 + params['margin_shift'])) + ')'
                    f_profQ75 = 'sum(' + str(profQ75) + child_centers_rows.format(
                        xl_col_to_name(column + 3 + params['margin_shift'])) + ')'
                    f_profQ50 = 'sum(' + str(profQ50) + child_centers_rows.format(
                        xl_col_to_name(column + 4 + params['margin_shift'])) + ')'

                    sheet.write_formula(row, column + 2, f_sumQ100, formats['fact'])
                    sheet.write_formula(row, column + 2 + params['margin_shift'], f_profQ100,
                                        formats['fact'])
                    sheet.write_formula(row, column + 3, f_sumQ75, formats['forecast'])
                    sheet.write_formula(row, column + 3 + params['margin_shift'], f_profQ75,
                                        formats['forecast'])
                    sheet.write_formula(row, column + 4, f_sumQ50, formats['forecast'])
                    sheet.write_formula(row, column + 4 + params['margin_shift'], f_profQ50,
                                        formats['forecast'])
                    column += 4

            elif 'HY1' in element:  # 'HY1/YEAR итого' 'HY2/YEAR итого'
                sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 7), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 1, formula, formats['fact'])
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 7 + params['margin_shift']),
                                                       xl_col_to_name(column - 3 + params['margin_shift']))
                sheet.write_formula(row, column + 1 + params['margin_shift'], formula, formats['fact'])

                sheet.write_formula(
                    row,
                    column + 2,
                    f'=IFERROR({xl_col_to_name(column + 1)}{row + 1}/{xl_col_to_name(column + 0)}{row + 1}," ")',
                    formats['percent']
                )
                sheet.write_formula(
                    row,
                    column + 2 + params['margin_shift'],
                    f'=IFERROR({xl_col_to_name(column + 1 + params["margin_shift"])}{row + 1}/{xl_col_to_name(column + 0 + params["margin_shift"])}{row + 1}," ")',
                    formats['percent']
                )

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 6),
                                                       xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 3, formula, formats['forecast'])
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 5),
                                                       xl_col_to_name(column - 1))
                sheet.write_formula(row, column + 4, formula, formats['forecast'])

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 6 + params['margin_shift']),
                                                       xl_col_to_name(column - 2 + params['margin_shift']))
                sheet.write_formula(row, column + 3 + params['margin_shift'], formula, formats['forecast'])
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 5 + params['margin_shift']),
                                                       xl_col_to_name(column - 1 + params['margin_shift']))
                sheet.write_formula(row, column + 4 + params['margin_shift'], formula, formats['forecast'])
                column += 4

            elif 'HY2' in element:  # 'HY1/YEAR итого' 'HY2/YEAR итого'
                sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 2, formula, formats['fact'])
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8 + params['margin_shift']),
                                                       xl_col_to_name(column - 3 + params['margin_shift']))
                sheet.write_formula(row, column + 2 + params['margin_shift'], formula, formats['fact'])

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 7),
                                                       xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 3, formula, formats['forecast'])
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 6),
                                                       xl_col_to_name(column - 1))
                sheet.write_formula(row, column + 4, formula, formats['forecast'])

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 7 + params['margin_shift']),
                                                       xl_col_to_name(column - 2 + params['margin_shift']))
                sheet.write_formula(row, column + 3 + params['margin_shift'], formula, formats['forecast'])
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 6 + params['margin_shift']),
                                                       xl_col_to_name(column - 1 + params['margin_shift']))
                sheet.write_formula(row, column + 4 + params['margin_shift'], formula, formats['forecast'])
                column += 4

            elif element == 'YEAR':  # 'YEAR'
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 19), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 2, formula, formats['fact'])
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 19 + params['margin_shift']),
                                                       xl_col_to_name(column - 3 + params['margin_shift']))
                sheet.write_formula(row, column + 2 + params['margin_shift'], formula, formats['fact'])

                column += 1
                sheet.write_formula(
                    row,
                    column + 2,
                    f'=IFERROR({xl_col_to_name(column + 1)}{row + 1}/{xl_col_to_name(column)}{row + 1}," ")',
                    formats['percent']
                )
                sheet.write_formula(
                    row,
                    column + 2 + params['margin_shift'],
                    f'=IFERROR({xl_col_to_name(column + 1 + params["margin_shift"])}{row + 1}/{xl_col_to_name(column + params["margin_shift"])}{row + 1}," ")',
                    formats['percent']
                )

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 18), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 3, formula, formats['forecast'])
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 17), xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 4, formula, formats['forecast'])

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 18 + params['margin_shift']),
                                                       xl_col_to_name(column - 3 + params['margin_shift']))
                sheet.write_formula(row, column + 3 + params['margin_shift'], formula, formats['forecast'])
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 17 + params['margin_shift']),
                                                       xl_col_to_name(column - 2 + params['margin_shift']))
                sheet.write_formula(row, column + 4 + params['margin_shift'], formula, formats['forecast'])
                column += 4

            elif element == 'NEXT':
                f_sum_next_75 = 'sum(' + str(sum_next_75) + child_centers_rows.format(xl_col_to_name(column)) + ')'
                f_sum_next_50 = 'sum(' + str(sum_next_50) + child_centers_rows.format(xl_col_to_name(column + 1)) + ')'
                f_sum_next_30 = 'sum(' + str(sum_next_30) + child_centers_rows.format(xl_col_to_name(column + 2)) + ')'
                sheet.write_formula(row, column, f_sum_next_75, formats['next'])
                sheet.write_formula(row, column + 1, f_sum_next_50, formats['next'])
                sheet.write_formula(row, column + 2, f_sum_next_30, formats['next'])
                f_prof_next_75 = 'sum(' + str(prof_next_75) + child_centers_rows.format(
                    xl_col_to_name(column + params['margin_shift'])) + ')'
                f_prof_next_50 = 'sum(' + str(prof_next_50) + child_centers_rows.format(
                    xl_col_to_name(column + 1 + params['margin_shift'])) + ')'
                f_prof_next_30 = 'sum(' + str(prof_next_30) + child_centers_rows.format(
                    xl_col_to_name(column + 2 + params['margin_shift'])) + ')'
                sheet.write_formula(row, column + params['margin_shift'], f_prof_next_75, formats['next'])
                sheet.write_formula(row, column + 1 + params['margin_shift'], f_prof_next_50, formats['next'])
                sheet.write_formula(row, column + 2 + params['margin_shift'], f_prof_next_30, formats['next'])
                column += 2

            elif element == 'AFTER NEXT':
                f_sum_after_next = 'sum(' + str(sum_after_next) + child_centers_rows.format(
                    xl_col_to_name(column)) + ')'
                sheet.write_formula(row, column, f_sum_after_next, formats['next'])
                f_prof_after_next = 'sum(' + str(prof_after_next) + child_centers_rows.format(
                    xl_col_to_name(column + params['margin_shift'])) + ')'
                sheet.write_formula(row, column + params['margin_shift'], f_prof_after_next, formats['next'])

        # end Валовая Выручка, без НДС

    def print_summary_row(self, sheet, summary_formula, row, col, type, formats):
        for period in ('contraction', 'cash_flow', 'gross_revenue', 'margin'):
            for colFormula in ('Q1', 'Q2', 'HY1', 'Q3', 'Q4', 'HY2', 'YEAR', 'NEXT'):
                if colFormula in ('Q1', 'Q2'):
                    if type != 'center':
                        formula = summary_formula.format(xl_col_to_name(col))
                        sheet.write_formula(row, col, formula, formats['plan'])
                    formula = summary_formula.format(xl_col_to_name(col + 1))
                    sheet.write_formula(row, col + 1, formula, formats['fact'])
                    formula = summary_formula.format(xl_col_to_name(col + 2))
                    sheet.write_formula(row, col + 2, formula, formats['forecast'])
                    formula = summary_formula.format(xl_col_to_name(col + 3))
                    sheet.write_formula(row, col + 3, formula, formats['forecast'])
                    col += 4
                elif colFormula == 'HY1':
                    if type != 'center':
                        formula = summary_formula.format(xl_col_to_name(col))
                        sheet.write_formula(row, col, formula, formats['plan'])
                    formula = summary_formula.format(xl_col_to_name(col + 1))
                    sheet.write_formula(row, col + 1, formula, formats['fact'])
                    formula = f'=IFERROR({xl_col_to_name(col + 1)}{row + 1}/{xl_col_to_name(col)}{row + 1}," ")'
                    sheet.write_formula(row, col + 2, formula, formats['percent'])
                    formula = summary_formula.format(xl_col_to_name(col + 3))
                    sheet.write_formula(row, col + 3, formula, formats['forecast'])
                    formula = summary_formula.format(xl_col_to_name(col + 4))
                    sheet.write_formula(row, col + 4, formula, formats['forecast'])
                    col += 5
                elif colFormula in ('Q3', 'Q4'):
                    if type != 'center':
                        formula = summary_formula.format(xl_col_to_name(col))
                        sheet.write_formula(row, col, formula, formats['plan'])
                        formula = summary_formula.format(xl_col_to_name(col + 1))
                        sheet.write_formula(row, col + 1, formula, formats['plan'])
                    formula = summary_formula.format(xl_col_to_name(col + 2))
                    sheet.write_formula(row, col + 2, formula, formats['fact'])
                    formula = summary_formula.format(xl_col_to_name(col + 3))
                    sheet.write_formula(row, col + 3, formula, formats['forecast'])
                    formula = summary_formula.format(xl_col_to_name(col + 4))
                    sheet.write_formula(row, col + 4, formula, formats['forecast'])
                    col += 5
                elif colFormula == 'HY2':
                    if type != 'center':
                        formula = summary_formula.format(xl_col_to_name(col))
                        sheet.write_formula(row, col, formula, formats['plan'])
                        formula = summary_formula.format(xl_col_to_name(col + 1))
                        sheet.write_formula(row, col + 1, formula, formats['plan'])
                    formula = summary_formula.format(xl_col_to_name(col + 2))
                    sheet.write_formula(row, col + 2, formula, formats['fact'])
                    formula = summary_formula.format(xl_col_to_name(col + 3))
                    sheet.write_formula(row, col + 3, formula, formats['forecast'])
                    formula = summary_formula.format(xl_col_to_name(col + 4))
                    sheet.write_formula(row, col + 4, formula, formats['forecast'])
                    col += 5
                elif colFormula == 'YEAR':
                    if type != 'center':
                        formula = summary_formula.format(xl_col_to_name(col))
                        sheet.write_formula(row, col, formula, formats['plan'])
                        formula = summary_formula.format(xl_col_to_name(col + 1))
                        sheet.write_formula(row, col + 1, formula, formats['plan'])
                    formula = summary_formula.format(xl_col_to_name(col + 2))
                    sheet.write_formula(row, col + 2, formula, formats['fact'])
                    formula = f'=IFERROR({xl_col_to_name(col + 2)}{row + 1}/{xl_col_to_name(col + 1)}{row + 1}," ")'
                    sheet.write_formula(row, col + 3, formula, formats['percent'])
                    formula = summary_formula.format(xl_col_to_name(col + 4))
                    sheet.write_formula(row, col + 4, formula, formats['forecast'])
                    formula = summary_formula.format(xl_col_to_name(col + 5))
                    sheet.write_formula(row, col + 5, formula, formats['forecast'])
                    col += 6
                elif colFormula == 'NEXT':
                    formula = summary_formula.format(xl_col_to_name(col))
                    sheet.write_formula(row, col, formula, formats['next'])
                    formula = summary_formula.format(xl_col_to_name(col + 1))
                    sheet.write_formula(row, col + 1, formula, formats['next'])
                    formula = summary_formula.format(xl_col_to_name(col + 2))
                    sheet.write_formula(row, col + 2, formula, formats['next'])
                    col += 3
                    if period != 'cash_flow':  # нет потенциала в следующем году в ПДС
                        formula = summary_formula.format(xl_col_to_name(col))
                        sheet.write_formula(row, col, formula, formats['next'])
                        col += 1

    def print_center_plan_row(self, sheet, row, responsibility_center, formula_centers, row_format_plan):
        plan_contracting = self.env['project_budget.budget_plan_supervisor_spec'].search([
            ('budget_plan_supervisor_id.year', '=', YEARint),
            ('budget_plan_supervisor_id.responsibility_center_id', '=', responsibility_center.id),
            ('type_row', '=', 'contracting'),
        ])

        plan_cash = self.env['project_budget.budget_plan_supervisor_spec'].search([
            ('budget_plan_supervisor_id.year', '=', YEARint),
            ('budget_plan_supervisor_id.responsibility_center_id', '=', responsibility_center.id),
            ('type_row', '=', 'cash'),
        ])

        plan_acceptance = self.env['project_budget.budget_plan_supervisor_spec'].search([
            ('budget_plan_supervisor_id.year', '=', YEARint),
            ('budget_plan_supervisor_id.responsibility_center_id', '=', responsibility_center.id),
            ('type_row', '=', 'acceptance'),
        ])

        plan_margin_income = self.env['project_budget.budget_plan_supervisor_spec'].search([
            ('budget_plan_supervisor_id.year', '=', YEARint),
            ('budget_plan_supervisor_id.responsibility_center_id', '=', responsibility_center.id),
            ('type_row', '=', 'margin_income'),
        ])

        child_centers_rows = formula_centers.get('responsibility_center_' + str(responsibility_center.id)) or ''

        if child_centers_rows:
            plan_dict = {
                'contracting': {
                    'Q1': 'sum(' + str(plan_contracting.q1_plan) + child_centers_rows.format(xl_col_to_name(plan_shift['contracting']['Q1'])) + ')',
                    'Q2': 'sum(' + str(plan_contracting.q2_plan) + child_centers_rows.format(xl_col_to_name(plan_shift['contracting']['Q2'])) + ')',
                    'Q3': 'sum(' + str(plan_contracting.q3_plan) + child_centers_rows.format(xl_col_to_name(plan_shift['contracting']['Q3'])) + ')',
                    'Q4': 'sum(' + str(plan_contracting.q4_plan) + child_centers_rows.format(xl_col_to_name(plan_shift['contracting']['Q4'])) + ')',
                    'Q3_66': 'sum(' + str(plan_contracting.q3_plan_6_6) + child_centers_rows.format(xl_col_to_name(plan_shift['contracting']['Q3_66'])) + ')',
                    'Q4_66': 'sum(' + str(plan_contracting.q4_plan_6_6) + child_centers_rows.format(xl_col_to_name(plan_shift['contracting']['Q4_66'])) + ')',
                    'HY1': 'sum(' + str(plan_contracting.q1_plan) + ',' + str(plan_contracting.q2_plan) + child_centers_rows.format(xl_col_to_name(plan_shift['contracting']['HY1'])) + ')',
                    'HY2': 'sum(' + str(plan_contracting.q3_plan) + ',' + str(plan_contracting.q4_plan) + child_centers_rows.format(xl_col_to_name(plan_shift['contracting']['HY2'])) + ')',
                    'HY2_66': 'sum(' + str(plan_contracting.q3_plan_6_6) + ',' + str(plan_contracting.q4_plan_6_6) + child_centers_rows.format(xl_col_to_name(plan_shift['contracting']['HY2_66'])) + ')',
                    'Y': 'sum(' + str(plan_contracting.q1_plan) + ',' + str(plan_contracting.q2_plan) + ',' + str(plan_contracting.q3_plan) + ',' + str(plan_contracting.q4_plan) + child_centers_rows.format(xl_col_to_name(plan_shift['contracting']['Y'])) + ')',
                    'Y_66': 'sum(' + str(plan_contracting.q1_fact) + ',' + str(plan_contracting.q2_fact) + ',' + str(plan_contracting.q3_plan_6_6) + ',' + str(plan_contracting.q4_plan_6_6) + child_centers_rows.format(xl_col_to_name(plan_shift['contracting']['Y_66'])) + ')',
                },
                'cash': {
                    'Q1': 'sum(' + str(plan_cash.q1_plan) + child_centers_rows.format(xl_col_to_name(plan_shift['cash']['Q1'])) + ')',
                    'Q2': 'sum(' + str(plan_cash.q2_plan) + child_centers_rows.format(xl_col_to_name(plan_shift['cash']['Q2'])) + ')',
                    'Q3': 'sum(' + str(plan_cash.q3_plan) + child_centers_rows.format(xl_col_to_name(plan_shift['cash']['Q3'])) + ')',
                    'Q4': 'sum(' + str(plan_cash.q4_plan) + child_centers_rows.format(xl_col_to_name(plan_shift['cash']['Q4'])) + ')',
                    'Q3_66': 'sum(' + str(plan_cash.q3_plan_6_6) + child_centers_rows.format(xl_col_to_name(plan_shift['cash']['Q3_66'])) + ')',
                    'Q4_66': 'sum(' + str(plan_cash.q4_plan_6_6) + child_centers_rows.format(xl_col_to_name(plan_shift['cash']['Q4_66'])) + ')',
                    'HY1': 'sum(' + str(plan_cash.q1_plan) + ',' + str(
                        plan_cash.q2_plan) + child_centers_rows.format(
                        xl_col_to_name(plan_shift['cash']['HY1'])) + ')',
                    'HY2': 'sum(' + str(plan_cash.q3_plan) + ',' + str(
                        plan_cash.q4_plan) + child_centers_rows.format(
                        xl_col_to_name(plan_shift['cash']['HY2'])) + ')',
                    'HY2_66': 'sum(' + str(plan_cash.q3_plan_6_6) + ',' + str(
                        plan_cash.q4_plan_6_6) + child_centers_rows.format(
                        xl_col_to_name(plan_shift['cash']['HY2_66'])) + ')',
                    'Y': 'sum(' + str(plan_cash.q1_plan) + ',' + str(plan_cash.q2_plan) + ',' + str(
                        plan_cash.q3_plan) + ',' + str(plan_cash.q4_plan) + child_centers_rows.format(
                        xl_col_to_name(plan_shift['cash']['Y'])) + ')',
                    'Y_66': 'sum(' + str(plan_cash.q1_fact) + ',' + str(plan_cash.q2_fact) + ',' + str(
                        plan_cash.q3_plan_6_6) + ',' + str(
                        plan_cash.q4_plan_6_6) + child_centers_rows.format(
                        xl_col_to_name(plan_shift['cash']['Y_66'])) + ')',
                },
                'acceptance': {
                    'Q1': 'sum(' + str(plan_acceptance.q1_plan) + child_centers_rows.format(xl_col_to_name(plan_shift['acceptance']['Q1'])) + ')',
                    'Q2': 'sum(' + str(plan_acceptance.q2_plan) + child_centers_rows.format(xl_col_to_name(plan_shift['acceptance']['Q2'])) + ')',
                    'Q3': 'sum(' + str(plan_acceptance.q3_plan) + child_centers_rows.format(xl_col_to_name(plan_shift['acceptance']['Q3'])) + ')',
                    'Q4': 'sum(' + str(plan_acceptance.q4_plan) + child_centers_rows.format(xl_col_to_name(plan_shift['acceptance']['Q4'])) + ')',
                    'Q3_66': 'sum(' + str(plan_acceptance.q3_plan_6_6) + child_centers_rows.format(xl_col_to_name(plan_shift['acceptance']['Q3_66'])) + ')',
                    'Q4_66': 'sum(' + str(plan_acceptance.q4_plan_6_6) + child_centers_rows.format(xl_col_to_name(plan_shift['acceptance']['Q4_66'])) + ')',
                    'HY1': 'sum(' + str(plan_acceptance.q1_plan) + ',' + str(
                        plan_acceptance.q2_plan) + child_centers_rows.format(
                        xl_col_to_name(plan_shift['acceptance']['HY1'])) + ')',
                    'HY2': 'sum(' + str(plan_acceptance.q3_plan) + ',' + str(
                        plan_acceptance.q4_plan) + child_centers_rows.format(
                        xl_col_to_name(plan_shift['acceptance']['HY2'])) + ')',
                    'HY2_66': 'sum(' + str(plan_acceptance.q3_plan_6_6) + ',' + str(
                        plan_acceptance.q4_plan_6_6) + child_centers_rows.format(
                        xl_col_to_name(plan_shift['acceptance']['HY2_66'])) + ')',
                    'Y': 'sum(' + str(plan_acceptance.q1_plan) + ',' + str(plan_acceptance.q2_plan) + ',' + str(
                        plan_acceptance.q3_plan) + ',' + str(plan_acceptance.q4_plan) + child_centers_rows.format(
                        xl_col_to_name(plan_shift['acceptance']['Y'])) + ')',
                    'Y_66': 'sum(' + str(plan_acceptance.q1_fact) + ',' + str(plan_acceptance.q2_fact) + ',' + str(
                        plan_acceptance.q3_plan_6_6) + ',' + str(
                        plan_acceptance.q4_plan_6_6) + child_centers_rows.format(
                        xl_col_to_name(plan_shift['acceptance']['Y_66'])) + ')',
                },
                'margin_income': {
                    'Q1': 'sum(' + str(plan_margin_income.q1_plan) + child_centers_rows.format(xl_col_to_name(plan_shift['margin_income']['Q1'])) + ')',
                    'Q2': 'sum(' + str(plan_margin_income.q2_plan) + child_centers_rows.format(xl_col_to_name(plan_shift['margin_income']['Q2'])) + ')',
                    'Q3': 'sum(' + str(plan_margin_income.q3_plan) + child_centers_rows.format(xl_col_to_name(plan_shift['margin_income']['Q3'])) + ')',
                    'Q4': 'sum(' + str(plan_margin_income.q4_plan) + child_centers_rows.format(xl_col_to_name(plan_shift['margin_income']['Q4'])) + ')',
                    'Q3_66': 'sum(' + str(plan_margin_income.q3_plan_6_6) + child_centers_rows.format(xl_col_to_name(plan_shift['margin_income']['Q3_66'])) + ')',
                    'Q4_66': 'sum(' + str(plan_margin_income.q4_plan_6_6) + child_centers_rows.format(xl_col_to_name(plan_shift['margin_income']['Q4_66'])) + ')',
                    'HY1': 'sum(' + str(plan_margin_income.q1_plan) + ',' + str(
                        plan_margin_income.q2_plan) + child_centers_rows.format(
                        xl_col_to_name(plan_shift['margin_income']['HY1'])) + ')',
                    'HY2': 'sum(' + str(plan_margin_income.q3_plan) + ',' + str(
                        plan_margin_income.q4_plan) + child_centers_rows.format(
                        xl_col_to_name(plan_shift['margin_income']['HY2'])) + ')',
                    'HY2_66': 'sum(' + str(plan_margin_income.q3_plan_6_6) + ',' + str(
                        plan_margin_income.q4_plan_6_6) + child_centers_rows.format(
                        xl_col_to_name(plan_shift['margin_income']['HY2_66'])) + ')',
                    'Y': 'sum(' + str(plan_margin_income.q1_plan) + ',' + str(plan_margin_income.q2_plan) + ',' + str(
                        plan_margin_income.q3_plan) + ',' + str(plan_margin_income.q4_plan) + child_centers_rows.format(
                        xl_col_to_name(plan_shift['margin_income']['Y'])) + ')',
                    'Y_66': 'sum(' + str(plan_margin_income.q1_fact) + ',' + str(plan_margin_income.q2_fact) + ',' + str(
                        plan_margin_income.q3_plan_6_6) + ',' + str(
                        plan_margin_income.q4_plan_6_6) + child_centers_rows.format(
                        xl_col_to_name(plan_shift['margin_income']['Y_66'])) + ')',
                },
            }
        else:
            plan_dict = {
                'contracting': {
                    'Q1': str(plan_contracting.q1_plan),
                    'Q2': str(plan_contracting.q2_plan),
                    'Q3': str(plan_contracting.q3_plan),
                    'Q4': str(plan_contracting.q4_plan),
                    'Q3_66': str(plan_contracting.q3_plan_6_6),
                    'Q4_66': str(plan_contracting.q4_plan_6_6),
                    'HY1': '=SUM(' + xl_col_to_name(plan_shift['contracting']['Q1']) + '{0} + ' + xl_col_to_name(
                        plan_shift['contracting']['Q2']) + '{0})',
                    'HY2': '=SUM(' + xl_col_to_name(plan_shift['contracting']['Q3']) + '{0} + ' + xl_col_to_name(
                        plan_shift['contracting']['Q4']) + '{0})',
                    'HY2_66': '=SUM(' + xl_col_to_name(plan_shift['contracting']['Q3_66']) + '{0} + ' + xl_col_to_name(
                        plan_shift['contracting']['Q4_66']) + '{0})',
                    'Y': '=SUM(' + xl_col_to_name(plan_shift['contracting']['HY1']) + '{0} + ' + xl_col_to_name(
                        plan_shift['contracting']['HY2']) + '{0})',
                    'Y_66': '=SUM(' + xl_col_to_name(plan_shift['contracting']['HY2_66']) + '{0} + '
                            + str(plan_contracting.q1_fact) + ' + '
                            + str(plan_contracting.q2_fact) + ')',
                },
                'cash': {
                    'Q1': str(plan_cash.q1_plan),
                    'Q2': str(plan_cash.q2_plan),
                    'Q3': str(plan_cash.q3_plan),
                    'Q4': str(plan_cash.q4_plan),
                    'Q3_66': str(plan_cash.q3_plan_6_6),
                    'Q4_66': str(plan_cash.q4_plan_6_6),
                    'HY1': '=SUM(' + xl_col_to_name(plan_shift['cash']['Q1']) + '{0} + ' + xl_col_to_name(
                        plan_shift['cash']['Q2']) + '{0})',
                    'HY2': '=SUM(' + xl_col_to_name(plan_shift['cash']['Q3']) + '{0} + ' + xl_col_to_name(
                        plan_shift['cash']['Q4']) + '{0})',
                    'HY2_66': '=SUM(' + xl_col_to_name(
                        plan_shift['cash']['Q3_66']) + '{0} + ' + xl_col_to_name(
                        plan_shift['cash']['Q4_66']) + '{0})',
                    'Y': '=SUM(' + xl_col_to_name(plan_shift['cash']['HY1']) + '{0} + ' + xl_col_to_name(
                        plan_shift['cash']['HY2']) + '{0})',
                    'Y_66': '=SUM(' + xl_col_to_name(plan_shift['cash']['HY2_66']) + '{0} + '
                            + str(plan_cash.q1_fact) + ' + '
                            + str(plan_cash.q2_fact) + ')',
                },
                'acceptance': {
                    'Q1': str(plan_acceptance.q1_plan),
                    'Q2': str(plan_acceptance.q2_plan),
                    'Q3': str(plan_acceptance.q3_plan),
                    'Q4': str(plan_acceptance.q4_plan),
                    'Q3_66': str(plan_acceptance.q3_plan_6_6),
                    'Q4_66': str(plan_acceptance.q4_plan_6_6),
                    'HY1': '=SUM(' + xl_col_to_name(plan_shift['acceptance']['Q1']) + '{0} + ' + xl_col_to_name(
                        plan_shift['acceptance']['Q2']) + '{0})',
                    'HY2': '=SUM(' + xl_col_to_name(plan_shift['acceptance']['Q3']) + '{0} + ' + xl_col_to_name(
                        plan_shift['acceptance']['Q4']) + '{0})',
                    'HY2_66': '=SUM(' + xl_col_to_name(
                        plan_shift['acceptance']['Q3_66']) + '{0} + ' + xl_col_to_name(
                        plan_shift['acceptance']['Q4_66']) + '{0})',
                    'Y': '=SUM(' + xl_col_to_name(plan_shift['acceptance']['HY1']) + '{0} + ' + xl_col_to_name(
                        plan_shift['acceptance']['HY2']) + '{0})',
                    'Y_66': '=SUM(' + xl_col_to_name(plan_shift['acceptance']['HY2_66']) + '{0} + '
                            + str(plan_acceptance.q1_fact) + ' + '
                            + str(plan_acceptance.q2_fact) + ')',
                },
                'margin_income': {
                    'Q1': str(plan_margin_income.q1_plan),
                    'Q2': str(plan_margin_income.q2_plan),
                    'Q3': str(plan_margin_income.q3_plan),
                    'Q4': str(plan_margin_income.q4_plan),
                    'Q3_66': str(plan_margin_income.q3_plan_6_6),
                    'Q4_66': str(plan_margin_income.q4_plan_6_6),
                    'HY1': '=SUM(' + xl_col_to_name(plan_shift['margin_income']['Q1']) + '{0} + ' + xl_col_to_name(
                        plan_shift['margin_income']['Q2']) + '{0})',
                    'HY2': '=SUM(' + xl_col_to_name(plan_shift['margin_income']['Q3']) + '{0} + ' + xl_col_to_name(
                        plan_shift['margin_income']['Q4']) + '{0})',
                    'HY2_66': '=SUM(' + xl_col_to_name(
                        plan_shift['margin_income']['Q3_66']) + '{0} + ' + xl_col_to_name(
                        plan_shift['margin_income']['Q4_66']) + '{0})',
                    'Y': '=SUM(' + xl_col_to_name(plan_shift['margin_income']['HY1']) + '{0} + ' + xl_col_to_name(
                        plan_shift['margin_income']['HY2']) + '{0})',
                    'Y_66': '=SUM(' + xl_col_to_name(plan_shift['margin_income']['HY2_66']) + '{0} + '
                            + str(plan_margin_income.q1_fact) + ' + '
                            + str(plan_margin_income.q2_fact) + ')',
                },
            }
        for plan_type in plan_dict.keys():
            for plan_period in plan_dict[plan_type].keys():
                sheet.write_formula(row, plan_shift[plan_type][plan_period],
                                    plan_dict[plan_type][plan_period].format(row + 1),
                                    row_format_plan)

    def printrow(self, sheet, workbook, companies, responsibility_centers, budget, row, formulaItogo, level, params, virtual_company):
        global strYEAR
        global YEARint
        global dict_formula
        global max_level

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

        row_format_center = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": False,
            "num_format": '#,##0',
        })
        row_format_center_plan = workbook.add_format({
            "fg_color": '#D9E1F2',
            'border': 1,
            'font_size': 10,
            'num_format': '#,##0',
        })
        row_format_center_fact = workbook.add_format({
            "fg_color": '#C6E0B4',
            'border': 1,
            'font_size': 10,
            'num_format': '#,##0',
        })
        row_format_center_percent = workbook.add_format({
            "fg_color": '#ffff99',
            'border': 1,
            'font_size': 10,
            'num_format': '0.00%',
        })
        row_format_center_forecast = workbook.add_format({
            "fg_color": '#E2EFDA',
            'border': 1,
            'font_size': 10,
            'num_format': '#,##0',
        })
        row_format_center_next = workbook.add_format({
            "fg_color": '#F3F8F0',
            'border': 1,
            'font_size': 10,
            'num_format': '#,##0',
        })
        row_format_company = workbook.add_format({
            'border': 1,
            'font_size': 12,
            "bold": True,
            "num_format": '#,##0',
            "top": 2,
        })
        row_format_company_small = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "num_format": '#,##0',
        })
        row_format_company_plan = workbook.add_format({
            'border': 1,
            'font_size': 12,
            "bold": True,
            "num_format": '#,##0',
            "top": 2,
            'fg_color': '#D9E1F2',
        })
        row_format_company_plan_small = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "num_format": '#,##0',
            'fg_color': '#D9E1F2',
        })
        row_format_company_fact = workbook.add_format({
            'border': 1,
            'font_size': 12,
            "bold": True,
            "num_format": '#,##0',
            "top": 2,
            "fg_color": '#C6E0B4',
        })
        row_format_company_fact_small = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "num_format": '#,##0',
            "fg_color": '#C6E0B4',
        })
        row_format_company_percent = workbook.add_format({
            'border': 1,
            'font_size': 12,
            "bold": True,
            'num_format': '0.00%',
            "top": 2,
            "fg_color": '#ffff99',
        })
        row_format_company_percent_small = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            'num_format': '0.00%',
            "fg_color": '#ffff99',
        })
        row_format_company_forecast = workbook.add_format({
            'border': 1,
            'font_size': 12,
            "bold": True,
            "num_format": '#,##0',
            "top": 2,
            "fg_color": '#E2EFDA',
        })
        row_format_company_forecast_small = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "num_format": '#,##0',
            "fg_color": '#E2EFDA',
        })
        row_format_company_next = workbook.add_format({
            'border': 1,
            'font_size': 12,
            "bold": True,
            "num_format": '#,##0',
            "top": 2,
            "fg_color": '#F3F8F0',
        })
        row_format_company_next_small = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "num_format": '#,##0',
            "fg_color": '#F3F8F0',
        })
        row_format_company_empty = workbook.add_format({
            "fg_color": '#F2F2F2',
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
        center_format_number = workbook.add_format({
            'border': 1,
            'font_size': 10,
            'num_format': '#,##0',
        })
        center_format_plan = workbook.add_format({
            "fg_color": '#D9E1F2',
            'border': 1,
            'font_size': 10,
            'num_format': '#,##0',
        })
        center_format_fact = workbook.add_format({
            "fg_color": '#C6E0B4',
            'border': 1,
            'font_size': 10,
            'num_format': '#,##0',
        })
        center_format_percent = workbook.add_format({
            "fg_color": '#ffff99',
            'border': 1,
            'font_size': 10,
            'num_format': '0.00%',
        })
        center_format_forecast = workbook.add_format({
            "fg_color": '#E2EFDA',
            'border': 1,
            'font_size': 10,
            'num_format': '#,##0',
        })
        center_format_next = workbook.add_format({
            "fg_color": '#F3F8F0',
            'border': 1,
            'font_size': 10,
            'num_format': '#,##0',
        })

        formats_center = {
            'number': center_format_number,
            'plan': center_format_plan,
            'fact': center_format_fact,
            'percent': center_format_percent,
            'forecast': center_format_forecast,
            'next': center_format_next,
        }
        formats_company = {
            'number': row_format_company,
            'plan': row_format_company_plan,
            'fact': row_format_company_fact,
            'percent': row_format_company_percent,
            'forecast': row_format_company_forecast,
            'next': row_format_company_next,
        }
        formats_company_small = {
            'number': row_format_company_small,
            'plan': row_format_company_plan_small,
            'fact': row_format_company_fact_small,
            'percent': row_format_company_percent_small,
            'forecast': row_format_company_forecast_small,
            'next': row_format_company_next_small,
        }

        isFoundProjectsByCenter = False
        isFoundProjectsByManager = False
        begRowProjectsByCenter = 0

        cur_budget_projects = self.env['project_budget.projects'].search([
            ('commercial_budget_id', '=', budget.id),
            ('stage_id.code', '!=', '0'),
            ('is_not_for_mc_report', '=', False),
            '|', '&', ('step_status', '=', 'step'),
            ('step_project_parent_id.project_have_steps', '=', True),
            '&', ('step_status', '=', 'project'),
            ('project_have_steps', '=', False),
        ]).sorted(key=lambda
            r: (r.key_account_manager_id.name, r.stage_id.code, r.project_id) if r.step_status == 'project' else (r.key_account_manager_id.name, r.stage_id.code, r.step_project_parent_id.project_id + r.project_id))

        # cur_responsibility_centers = responsibility_centers.filtered(lambda r: r in cur_budget_projects.responsibility_center_id or r in {center.parent_id for center in cur_budget_projects.responsibility_center_id if center.parent_id in responsibility_centers})
        cur_responsibility_centers = responsibility_centers
        # cur_project_managers = project_managers.filtered(lambda r: r in cur_budget_projects.project_manager_id)

        if virtual_company:
            cur_companies = companies
        else:
            cur_companies = companies.filtered(lambda r: r in cur_responsibility_centers.company_id)

        for company in cur_companies:
            print('company = ', company.name)
            isFoundProjectsByCompany = False
            formulaProjectCompany = '=sum(0'

            dict_formula['center_ids_not_empty'] = {}

            if company.id not in dict_formula['company_ids']:  # встречаем компанию первый раз

                params['vgo_row'] = 0
                params['ole_row'] = 0
                params['vgo_lines'] = []
                params['ole_lines'] = []
                params['vgo_is_present'] = []
                params['ole_is_present'] = []
                if not virtual_company:
                    params['vgo_is_present'] = cur_budget_projects.filtered(
                        lambda p: company.partner_id.id == p.signer_id.id
                        and p.company_partner_id
                        and company.partner_id.id != p.company_partner_id.partner_id.id
                        and not p.is_parent_project
                        and p.company_partner_id.partner_id.id in group_companies
                        and p.company_id.id == company.id
                    ).ids

                if company.name == params['systematica_name']:
                    params['ole_is_present'] = cur_budget_projects.filtered(
                        lambda p: p.company_partner_id.partner_id.id == p.signer_id.id
                                  and company.partner_id.id != p.signer_id.id
                                  and not p.is_parent_project
                                  and p.company_partner_id.partner_id.id in group_companies
                                  and p.company_id.id == company.id
                    ).ids

                if company.name == params['systematica_name']:
                    row += 1
                row += 1
                dict_formula['company_ids'][company.id] = row
                if params['vgo_is_present'] and params['ole_is_present']:
                    row += 3
                    params['vgo_row'] = row - 1
                    params['ole_row'] = row
                elif params['vgo_is_present'] or params['ole_is_present']:
                    row += 2
                    if params['vgo_is_present']:
                        params['vgo_row'] = row
                    elif params['ole_is_present']:
                        params['ole_row'] = row

            if virtual_company:
                filtered_centers = cur_responsibility_centers
            else:
                filtered_centers = cur_responsibility_centers.filtered(lambda r: r in (center for center in self.env[
                    'account.analytic.account'].search([
                    ('plan_id', '=', self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
                    ('company_id', '=', company.id),
            ])))

            for responsibility_center in filtered_centers:

                print('responsibility_center.name = ', responsibility_center.name)

                begRowProjectsByCenter = 0
                projects_start_row = 0

                row0 = row

                child_responsibility_centers = self.env['account.analytic.account'].search([
                    ('parent_id', '=', responsibility_center.id),
                    ('plan_id', '=', self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
                ], order='name')

                if responsibility_center.child_ids:
                    row += 1
                    dict_formula['center_ids'][responsibility_center.id] = row
                    row0, formulaItogo = self.printrow(
                        sheet, workbook, companies, child_responsibility_centers, budget, row, formulaItogo, level + 1,
                        params, virtual_company
                    )

                isFoundProjectsByCenter = False
                if row0 != row:
                    isFoundProjectsByCenter = True

                row = row0

                formulaProjectCenter = '=sum(0'

                for spec in cur_budget_projects:
                    if spec.vgo == '-':

                        if begRowProjectsByCenter == 0:
                            begRowProjectsByCenter = row

                        if spec.responsibility_center_id == responsibility_center:
                            if self.isProjectinYear(spec) is False or spec.stage_id.code in ('0', '10'):
                                continue

                            isFoundProjectsByCenter = True
                            isFoundProjectsByCompany = True

                if self.center_has_plan(responsibility_center):
                    isFoundProjectsByCenter = True
                    isFoundProjectsByCompany = True

                if level > 1:
                    isFoundProjectsByCompany = False

                if isFoundProjectsByCenter:

                    dict_formula['center_ids_not_empty'][responsibility_center.id] = row

                    column = 0

                    if child_responsibility_centers:
                        center_row = dict_formula['center_ids'].get(responsibility_center.id)
                    else:
                        row += 1
                        center_row = row

                    center_name = responsibility_center.print_name_mc or responsibility_center.name

                    sheet.write_string(center_row, column, '       ' * level + center_name, row_format_center)
                    if params['report_with_projects']:
                        sheet.merge_range(center_row, column + 1, center_row, column + params["shift"] , '', row_format_center)
                    sheet.set_row(center_row, False, False, {'hidden': 1, 'level': level})

                    str_responsibility_center_id = 'responsibility_center_' + str(int(responsibility_center.parent_id))
                    if str_responsibility_center_id in dict_formula:
                        dict_formula[str_responsibility_center_id] = dict_formula[str_responsibility_center_id] + ',{0}' + str(
                            center_row + 1)
                    else:
                        dict_formula[str_responsibility_center_id] = ',{0}' + str(center_row + 1)

                    formulaProjectCenter += ',{0}' + f'{begRowProjectsByCenter + 2}' + ':{0}' + f'{center_row}'

                    str_responsibility_center_id = 'responsibility_center_' + str(int(responsibility_center.id))
                    if str_responsibility_center_id in dict_formula:
                        formulaProjectCenter = formulaProjectCenter + dict_formula[str_responsibility_center_id] + ')'
                    else:
                        formulaProjectCenter = formulaProjectCenter + ')'

                    projects = self.env['project_budget.projects'].search([
                        ('stage_id.code', '!=', '0'),
                        ('commercial_budget_id', '=', budget.id),
                        ('is_not_for_mc_report', '=', False),
                        ('responsibility_center_id', '=', responsibility_center.id),
                        '|', '&', ('step_status', '=', 'step'),
                        ('step_project_parent_id.project_have_steps', '=', True),
                        '&', ('step_status', '=', 'project'),
                        ('project_have_steps', '=', False),
                        ])

                    if params['report_with_projects']:
                        for spec in cur_budget_projects:
                            if spec.vgo == '-':
                                if spec.responsibility_center_id == responsibility_center:
                                    if self.isProjectinYear(spec) is False or spec.stage_id.code in ('0', '10'):
                                        continue

                                    # печатаем строки проектов
                                    row += 1
                                    sheet.set_row(row, False, False, {'hidden': 1, 'level': max_level})
                                    cur_row_format = row_format
                                    cur_row_format_number = row_format_number
                                    if spec.stage_id.code == '0':
                                        cur_row_format = row_format_canceled_project
                                        cur_row_format_number = row_format_number_canceled_project
                                    column = 0
                                    sheet.write_string(row, column, '       ' * max_level + spec.key_account_manager_id.name, cur_row_format)
                                    column += 1
                                    sheet.write_string(row, column, spec.partner_id.name, cur_row_format)
                                    column += 1
                                    sheet.write_string(row, column, spec.essence_project, cur_row_format)
                                    column += 1
                                    if spec.step_status == 'project':
                                        sheet.write_string(row, column, (spec.step_project_number or '') + ' | ' + (
                                                    spec.project_id or ''), cur_row_format)
                                    elif spec.step_status == 'step':
                                        sheet.write_string(row, column, (
                                                spec.step_project_number or '') + ' | ' + spec.step_project_parent_id.project_id + " | " + spec.project_id,
                                                           cur_row_format)
                                    column += 1
                                    sheet.write_string(row, column, self.get_estimated_probability_name_forecast(
                                        spec.stage_id.code), cur_row_format)
                                    column += 1
                                    sheet.write_number(row, column,
                                                       spec.amount_total_in_company_currency,
                                                       cur_row_format_number)
                                    column += 1
                                    sheet.write_number(row, column,
                                                       spec.margin_in_company_currency,
                                                       cur_row_format_number)
                                    column += 1
                                    sheet.write_string(row, column, f'{spec.profitability:.2f}' + '%', cur_row_format)
                                    column += 1
                                    sheet.write_string(row, column, spec.dogovor_number or '', cur_row_format)
                                    column += 1
                                    sheet.write_string(row, column, spec.tax_id.name or '', cur_row_format)
                                    column += 1
                                    sheet.write_string(row, column, '', cur_row_format)
                                    self.print_row_values(workbook, sheet, row, column, strYEAR, spec, responsibility_center, params)
                                    if projects_start_row == 0:
                                        projects_start_row = row
                                    if spec.id in params['vgo_is_present']:
                                        params['vgo_lines'].append(row + 1)
                                    elif spec.id in params['ole_is_present']:
                                        params['ole_lines'].append(row + 1)
                    else:
                        self.print_row_values_center(
                            workbook,
                            sheet,
                            center_row,
                            column + params["shift"] ,
                            strYEAR,
                            projects,
                            responsibility_center,
                            dict_formula,
                            params,
                            formats_center
                        )
                        self.print_center_plan_row(sheet, center_row, responsibility_center, dict_formula,
                                                   row_format_center_plan)

                    if level == 1:
                        formulaProjectCompany += ',{0}' + f'{center_row + 1}'
                    if params['report_with_projects']:
                        row += 1
                        sheet.write_string(row, column, '', row_format_company_empty)
                        sheet.set_row(row, 14, row_format_company_empty, {'hidden': 1, 'level': level})
                else:
                    if responsibility_center.child_ids:
                        if all(child.id not in dict_formula['center_ids_not_empty'] for child in
                               responsibility_center.child_ids):
                            row -= 1
                if isFoundProjectsByCenter and params['report_with_projects']:
                    child_centers_rows = dict_formula.get('responsibility_center_' + str(responsibility_center.id)) or ''
                    if projects_start_row:
                        formula = '=sum({0}' + str(projects_start_row + 1) + ':{0}' + str(row) + child_centers_rows + ')'
                    elif child_centers_rows:
                        formula = '=sum(' + child_centers_rows + ')'
                    else:
                        formula = False
                    if formula:
                        self.print_summary_row(sheet, formula, center_row, params["shift"] + 1, 'center', formats_center)
                    self.print_center_plan_row(sheet, center_row, responsibility_center, dict_formula, row_format_center_plan)

            if isFoundProjectsByCompany:
                column = 0

                company_row = dict_formula['company_ids'][company.id]

                if params['vgo_is_present'] or params['ole_is_present'] and not virtual_company:
                    sheet.write_string(company_row, column, company.name + ' (c учетом ВГО и проектов др. ЮЛ Холдинга)', row_format_company)
                    sheet.set_row(company_row + 1, False, False, {'hidden': 1, 'level': level})
                    sheet.write_string(company_row + 1, column, company.name + ' (коммерческие)', row_format_company_small)
                    vgo_company_row = company_row
                else:
                    sheet.write_string(company_row, column, company.name, row_format_company)

                if params['vgo_is_present'] and not virtual_company:
                    sheet.set_row(vgo_company_row + 2, False, False, {'hidden': 1, 'level': level})
                    sheet.write_string(vgo_company_row + 2, column, company.name + ' (ВГО)', row_format_company_small)
                    vgo_company_row += 1
                if params['ole_is_present'] and not virtual_company:
                    sheet.set_row(vgo_company_row + 2, False, False, {'hidden': 1, 'level': level})
                    sheet.write_string(vgo_company_row + 2, column, company.name + ' (проекты др. ЮЛ Холдинга)', row_format_company_small)

                if params['report_with_projects']:
                    sheet.merge_range(company_row, column + 1, company_row, column + params["shift"] , '', row_format_company)
                    if params['vgo_is_present'] or params['ole_is_present'] and not virtual_company:
                        sheet.merge_range(company_row + 1, column + 1, company_row + 1, column + params["shift"], '',
                                          row_format_company_small)
                        sheet.merge_range(company_row + 2, column + 1, company_row + 2, column + params["shift"], '',
                                          row_format_company_small)
                    if params['vgo_is_present'] and params['ole_is_present'] and not virtual_company:
                        sheet.merge_range(company_row + 3, column + 1, company_row + 3, column + params["shift"], '',
                                          row_format_company_small)

                formulaProjectCompany += ')'
                # print('formulaProjectCompany',formulaProjectCompany)
                # оформление строки Компания
                col = params["shift"] + 1
                self.print_summary_row(sheet, formulaProjectCompany, company_row, col, 'company', formats_company)

                if params['vgo_is_present'] or params['ole_is_present'] and not virtual_company:
                    if params['vgo_is_present'] and params['ole_is_present']:
                        formula = '=' + '-'.join('{0}' + str(r) for r in (company_row + 1, company_row + 3, company_row + 4))
                    else:
                        formula = '=' + '-'.join('{0}' + str(r) for r in (company_row + 1, company_row + 3))
                    self.print_summary_row(sheet, formula, company_row + 1, col, 'company', formats_company)
                vgo_company_row = company_row
                if params['report_with_projects']:
                    if params['vgo_is_present'] and not virtual_company:
                        formula = '=' + '+'.join('{0}' + str(r) for r in params['vgo_lines'])
                        self.print_summary_row(sheet, formula, company_row + 2, col, 'company', formats_company)

                        vgo_company_row += 1
                    if params['ole_is_present'] and not virtual_company:
                        formula = '=' + '+'.join('{0}' + str(r) for r in params['ole_lines'])
                        self.print_summary_row(sheet, formula, vgo_company_row + 2, col, 'company', formats_company)
                else:
                    if params['vgo_is_present'] and not virtual_company:
                        projects = self.env['project_budget.projects'].search([
                            ('id', 'in', params['vgo_is_present']),
                            ('company_id', '=', company.id),
                        ])
                        self.print_row_values_center(
                            workbook,
                            sheet,
                            params['vgo_row'],
                            column + params["shift"] ,
                            strYEAR,
                            projects,
                            False,
                            dict_formula,
                            params,
                            formats_company_small,
                        )
                        for type in plan_shift:  # нули в планах ВГО
                            for c in plan_shift[type].values():
                                sheet.write(params['vgo_row'], c, 0, row_format_center_plan)

                    if params['ole_is_present'] and not virtual_company:
                        projects = self.env['project_budget.projects'].search([
                            ('id', 'in', params['ole_is_present']),
                            ('company_id', '=', company.id),
                        ])
                        self.print_row_values_center(
                            workbook,
                            sheet,
                            params['ole_row'],
                            column + params["shift"] ,
                            strYEAR,
                            projects,
                            False,
                            dict_formula,
                            params,
                            formats_company_small,
                        )
                        for type in plan_shift:  # нули в планах ЮЛ
                            for c in plan_shift[type].values():
                                sheet.write(params['ole_row'], c, 0, row_format_center_plan)

                if virtual_company:  # строка суммирования Систематики и Облака
                    systematica = self.env['res.company'].search([('name', '=', params['systematica_name'])])
                    sum_row = dict_formula['company_ids'][systematica.id] - 1
                    virtual_row = dict_formula['company_ids'][params['virtual_company_id']]
                    formula = '=sum({0}' + f'{sum_row + 2}' + ',{0}' + f'{virtual_row + 1})'

                    sheet.write_string(
                        sum_row, column,
                        params['systematica_name'] + ' + ' + params['virtual_company_name'] + ' (c учетом ВГО и проектов др. ЮЛ Холдинга)',
                        row_format_company
                    )
                    if params['report_with_projects']:
                        sheet.merge_range(
                            sum_row, column + 1, sum_row, column + params["shift"], '',
                            row_format_company
                        )

                    self.print_summary_row(sheet, formula, sum_row, col, 'company', formats_company)

                # план виртуальной компаний
                if virtual_company:
                    responsibility_center_id = self.env['account.analytic.account'].search([
                        ('code', '=', params['company_separate_center_code']),
                        ('plan_id', '=', self.env.ref(
                            'analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
                    ]).id

                    company_plan_contracting = self.env['project_budget.budget_plan_supervisor_spec'].search([
                        ('budget_plan_supervisor_id.year', '=', YEARint),
                        ('budget_plan_supervisor_id.responsibility_center_id', '=', responsibility_center_id),
                        ('type_row', '=', 'contracting'),
                    ])

                    company_plan_cash = self.env['project_budget.budget_plan_supervisor_spec'].search([
                        ('budget_plan_supervisor_id.year', '=', YEARint),
                        ('budget_plan_supervisor_id.responsibility_center_id', '=', responsibility_center_id),
                        ('type_row', '=', 'cash'),
                    ])

                    company_plan_acceptance = self.env['project_budget.budget_plan_supervisor_spec'].search([
                        ('budget_plan_supervisor_id.year', '=', YEARint),
                        ('budget_plan_supervisor_id.responsibility_center_id', '=', responsibility_center_id),
                        ('type_row', '=', 'acceptance'),
                    ])

                    company_plan_margin_income = self.env['project_budget.budget_plan_supervisor_spec'].search([
                        ('budget_plan_supervisor_id.year', '=', YEARint),
                        ('budget_plan_supervisor_id.responsibility_center_id', '=', responsibility_center_id),
                        ('type_row', '=', 'margin_income'),
                    ])

                    company_plan = {
                        'contracting': {
                            'Q1': str(company_plan_contracting.q1_plan),
                            'Q2': str(company_plan_contracting.q2_plan),
                            'Q3': str(company_plan_contracting.q3_plan),
                            'Q4': str(company_plan_contracting.q4_plan),
                            'Q3_66': str(company_plan_contracting.q3_plan_6_6),
                            'Q4_66': str(company_plan_contracting.q4_plan_6_6),
                            'HY1': '=SUM(' + xl_col_to_name(plan_shift['contracting']['Q1']) + '{0} + ' + xl_col_to_name(
                                plan_shift['contracting']['Q2']) + '{0})',
                            'HY2': '=SUM(' + xl_col_to_name(plan_shift['contracting']['Q3']) + '{0} + ' + xl_col_to_name(
                                plan_shift['contracting']['Q4']) + '{0})',
                            'HY2_66': '=SUM(' + xl_col_to_name(plan_shift['contracting']['Q3_66']) + '{0} + ' + xl_col_to_name(
                                plan_shift['contracting']['Q4_66']) + '{0})',
                            'Y': '=SUM(' + xl_col_to_name(plan_shift['contracting']['HY1']) + '{0} + ' + xl_col_to_name(
                                plan_shift['contracting']['HY2']) + '{0})',
                            'Y_66': '=SUM(' + xl_col_to_name(plan_shift['contracting']['HY2_66']) + '{0} + '
                                    + str(company_plan_contracting.q1_fact) + ' + '
                                    + str(company_plan_contracting.q2_fact) + ')',
                        },
                        'cash': {
                            'Q1': str(company_plan_cash.q1_plan),
                            'Q2': str(company_plan_cash.q2_plan),
                            'Q3': str(company_plan_cash.q3_plan),
                            'Q4': str(company_plan_cash.q4_plan),
                            'Q3_66': str(company_plan_cash.q3_plan_6_6),
                            'Q4_66': str(company_plan_cash.q4_plan_6_6),
                            'HY1': '=SUM(' + xl_col_to_name(plan_shift['cash']['Q1']) + '{0} + ' + xl_col_to_name(
                                plan_shift['cash']['Q2']) + '{0})',
                            'HY2': '=SUM(' + xl_col_to_name(plan_shift['cash']['Q3']) + '{0} + ' + xl_col_to_name(
                                plan_shift['cash']['Q4']) + '{0})',
                            'HY2_66': '=SUM(' + xl_col_to_name(
                                plan_shift['cash']['Q3_66']) + '{0} + ' + xl_col_to_name(
                                plan_shift['cash']['Q4_66']) + '{0})',
                            'Y': '=SUM(' + xl_col_to_name(plan_shift['cash']['HY1']) + '{0} + ' + xl_col_to_name(
                                plan_shift['cash']['HY2']) + '{0})',
                            'Y_66': '=SUM(' + xl_col_to_name(plan_shift['cash']['HY2_66']) + '{0} + '
                                    + str(company_plan_cash.q1_fact) + ' + '
                                    + str(company_plan_cash.q2_fact) + ')',
                        },
                        'acceptance': {
                            'Q1': str(company_plan_acceptance.q1_plan),
                            'Q2': str(company_plan_acceptance.q2_plan),
                            'Q3': str(company_plan_acceptance.q3_plan),
                            'Q4': str(company_plan_acceptance.q4_plan),
                            'Q3_66': str(company_plan_acceptance.q3_plan_6_6),
                            'Q4_66': str(company_plan_acceptance.q4_plan_6_6),
                            'HY1': '=SUM(' + xl_col_to_name(plan_shift['acceptance']['Q1']) + '{0} + ' + xl_col_to_name(
                                plan_shift['acceptance']['Q2']) + '{0})',
                            'HY2': '=SUM(' + xl_col_to_name(plan_shift['acceptance']['Q3']) + '{0} + ' + xl_col_to_name(
                                plan_shift['acceptance']['Q4']) + '{0})',
                            'HY2_66': '=SUM(' + xl_col_to_name(
                                plan_shift['acceptance']['Q3_66']) + '{0} + ' + xl_col_to_name(
                                plan_shift['acceptance']['Q4_66']) + '{0})',
                            'Y': '=SUM(' + xl_col_to_name(plan_shift['acceptance']['HY1']) + '{0} + ' + xl_col_to_name(
                                plan_shift['acceptance']['HY2']) + '{0})',
                            'Y_66': '=SUM(' + xl_col_to_name(plan_shift['acceptance']['HY2_66']) + '{0} + '
                                    + str(company_plan_acceptance.q1_fact) + ' + '
                                    + str(company_plan_acceptance.q2_fact) + ')',
                        },
                        'margin_income': {
                            'Q1': str(company_plan_margin_income.q1_plan),
                            'Q2': str(company_plan_margin_income.q2_plan),
                            'Q3': str(company_plan_margin_income.q3_plan),
                            'Q4': str(company_plan_margin_income.q4_plan),
                            'Q3_66': str(company_plan_margin_income.q3_plan_6_6),
                            'Q4_66': str(company_plan_margin_income.q4_plan_6_6),
                            'HY1': '=SUM(' + xl_col_to_name(plan_shift['margin_income']['Q1']) + '{0} + ' + xl_col_to_name(
                                plan_shift['margin_income']['Q2']) + '{0})',
                            'HY2': '=SUM(' + xl_col_to_name(plan_shift['margin_income']['Q3']) + '{0} + ' + xl_col_to_name(
                                plan_shift['margin_income']['Q4']) + '{0})',
                            'HY2_66': '=SUM(' + xl_col_to_name(
                                plan_shift['margin_income']['Q3_66']) + '{0} + ' + xl_col_to_name(
                                plan_shift['margin_income']['Q4_66']) + '{0})',
                            'Y': '=SUM(' + xl_col_to_name(plan_shift['margin_income']['HY1']) + '{0} + ' + xl_col_to_name(
                                plan_shift['margin_income']['HY2']) + '{0})',
                            'Y_66': '=SUM(' + xl_col_to_name(plan_shift['margin_income']['HY2_66']) + '{0} + '
                                    + str(company_plan_margin_income.q1_fact) + ' + '
                                    + str(company_plan_margin_income.q2_fact) + ')',
                        },
                    }

                    for plan_type in company_plan.keys():
                        for plan_period in company_plan[plan_type].keys():
                            sheet.write_formula(company_row, plan_shift[plan_type][plan_period],
                                                company_plan[plan_type][plan_period].format(company_row + 1),
                                                row_format_company_plan)

        return row, formulaItogo

    def print_external_data(self, workbook, sheet, row, external_data, params):
        global dict_formula

        row_format_company = workbook.add_format({
            'border': 1,
            'font_size': 12,
            "bold": True,
            "num_format": '#,##0',
            "top": 2,
        })
        row_format_company_plan = workbook.add_format({
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
            "fg_color": '#C6E0B4',
        })
        row_format_company_percent = workbook.add_format({
            'border': 1,
            'font_size': 12,
            "bold": True,
            'num_format': '0.00%',
            "top": 2,
            "fg_color": '#ffff99',
        })
        row_format_company_forecast = workbook.add_format({
            'border': 1,
            'font_size': 12,
            "bold": True,
            "num_format": '#,##0',
            "top": 2,
            "fg_color": '#E2EFDA',
        })
        row_format_company_next = workbook.add_format({
            'border': 1,
            'font_size': 12,
            "bold": True,
            "num_format": '#,##0',
            "top": 2,
            "fg_color": '#F3F8F0',
        })
        row_format_company_empty = workbook.add_format({
            "fg_color": '#F2F2F2',
        })

        company = external_data.company_id
        row += 1
        dict_formula['company_ids'][company.id] = row

        data_list = external_data.data.split(',')

        data_list.pop(80)  # удаляем Потенциал ПДС следующего года

        column = 0

        sheet.write_string(row, column, company.name, row_format_company)
        if params['report_with_projects']:
            sheet.merge_range(row, column + 1, row, column + params["shift"], '', row_format_company)

        table_shift = -1
        shift = params["shift"]
        m_shift = params["margin_shift"]
        for i in range(0, 4):  # оформление строки Компания
            for colFormula in range(0, 7):
                col = i * (m_shift - 6) + colFormula * 5 + 1
                sheet.write_number(row, col + shift, float(data_list[col + table_shift]), row_format_company_plan)
                col = i * (m_shift - 6) + colFormula * 5 + 2
                sheet.write_number(row, col + shift, float(data_list[col + table_shift]), row_format_company_plan)
                col = i * (m_shift - 6) + colFormula * 5 + 3
                sheet.write_number(row, col + shift, float(data_list[col + table_shift]), row_format_company_fact)
                if colFormula in (2, 6):
                    col = i * (m_shift - 6) + colFormula * 5 + 4
                    formula = f'=IFERROR({xl_col_to_name(col + shift - 1)}{row + 1}/{xl_col_to_name(col + shift - 2)}{row + 1}," ")'
                    sheet.write_formula(row, col + shift, formula, row_format_company_percent)
                    shift += 1
                    table_shift += 1
                col = i * (m_shift - 6) + colFormula * 5 + 4
                sheet.write_number(row, col + shift, float(data_list[col + table_shift]), row_format_company_forecast)
                col = i * (m_shift - 6) + colFormula * 5 + 5
                sheet.write_number(row, col + shift, float(data_list[col + table_shift]), row_format_company_forecast)
            if i == 1:  # ПДС
                for x in range(3):
                    col = (i + 1) * (m_shift - 6) + x + 1
                    sheet.write_number(row, col + shift, float(data_list[col + table_shift]), row_format_company_next)
                shift += 3
                table_shift += 3
            else:
                for x in range(4):
                    col = (i + 1) * (m_shift - 6) + x + 1
                    sheet.write_number(row, col + shift, float(data_list[col + table_shift]), row_format_company_next)
                shift += 4
                table_shift += 4

        if params['report_with_projects']:
            row += 1
            sheet.set_row(row, 14, row_format_company_empty, {'hidden': 1, 'level': 1})
        return row


    def calculate_max_level(self, start_parent_centers, budget_projects):  # считаем max_level
        depth_dict = {}
        max_depth = 1
        parents = [False,]
        new_parents = []
        parent_centers = start_parent_centers
        while parent_centers:
            for center in parent_centers:
                depth_dict[center] = max_depth
                new_parents.append(center.id)
            max_depth += 1
            parents = new_parents
            new_parents = []
            parent_centers = self.env['account.analytic.account'].search([
                ('parent_id', 'in', parents),
                ('plan_id', '=', self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
            ])
        depth = 1
        for project in budget_projects:
            depth = max(depth, depth_dict.get(project.responsibility_center_id, 0))
            if depth == max_depth:
                break
        return depth + 1

    def printworksheet(self, workbook, budget, namesheet, params):
        global strYEAR
        global YEARint
        global max_level

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
            "fg_color": '#BFBFBF',
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

        formats_itogo = {
            'number': row_format_number_itogo,
            'plan': row_format_number_itogo,
            'fact': row_format_number_itogo,
            'percent': row_format_number_itogo_percent,
            'forecast': row_format_number_itogo,
            'next': row_format_number_itogo,
        }

        date_format = workbook.add_format({'num_format': 'd mmmm yyyy'})
        row = 0
        sheet.write_string(row, 0, budget.name, bold)
        row = 2
        column = 0
        sheet.merge_range(row - 1, 0, row, 0, "Прогноз", head_format)
        if params['report_with_projects']:
            sheet.merge_range(row + 1, 0, row + 2, 0, "БЮ/Проектный офис/КАМ", head_format_1)
        else:
            sheet.merge_range(row + 1, 0, row + 2, 0, "БЮ/Проектный офис", head_format_1)
        sheet.set_column(column, column, 40)
        if params['report_with_projects']:
            sheet.merge_range(row - 1, 1, row, 10, "", head_format)
            column += 1
            sheet.merge_range(row + 1, column, row + 2, column, "Заказчик", head_format_1)
            # sheet.set_column(column, column, 25)
            column += 1
            sheet.merge_range(row + 1, column, row + 2, column, "Наименование Проекта", head_format_1)
            # sheet.set_column(column, column, 12.25)
            column += 1
            sheet.merge_range(row + 1, column, row + 2, column, "Номер этапа проекта", head_format_1)
            # sheet.set_column(column, column, 15)
            column += 1
            sheet.merge_range(row + 1, column, row + 2, column, "Стадия продажи", head_format_1)
            # sheet.set_column(column, column, 16.88)
            column += 1
            sheet.merge_range(row + 1, column, row + 2, column, "Сумма проекта, руб.", head_format_1)
            # sheet.set_column(column, column, 14)
            column += 1
            sheet.merge_range(row + 1, column, row + 2, column, "Валовая прибыль экспертно, руб.", head_format_1)
            # sheet.set_column(column, column, 14)
            column += 1
            sheet.merge_range(row + 1, column, row + 2, column, "Прибыльность, экспертно, %", head_format_1)
            # sheet.set_column(column, column, 9)
            column += 1
            sheet.merge_range(row + 1, column, row + 2, column, "Номер договора", head_format_1)
            # sheet.set_column(column, column, 11.88)
            column += 1
            sheet.merge_range(row + 1, column, row + 2, column, "НДС", head_format_1)
            # sheet.set_column(column, column, 7)
            sheet.set_column(1, 9, False, False, {'hidden': 1, 'level': 3})
            column += 1
            sheet.merge_range(row + 1, column, row + 2, column, "", head_format_1)
            sheet.set_column(column, column, 2)

        if params['report_with_projects']:
            sheet.freeze_panes(5, 3)
        else:
            sheet.freeze_panes(5, 1)

        column += 1
        column = self.print_quater_head(workbook, sheet, row, column, strYEAR)

        sheet.autofilter(4, 0, 4, column - 1)

        row += 2

        cur_budget_projects = self.env['project_budget.projects'].search([
            ('responsibility_center_id.code', 'not in', params['all_separate_centers_codes']),
            ('commercial_budget_id', '=', budget.id),
            ('stage_id.code', '!=', '0'),
            ('is_not_for_mc_report', '=', False),
            '|', '&', ('step_status', '=', 'step'),
            ('step_project_parent_id.project_have_steps', '=', True),
            '&', ('step_status', '=', 'project'),
            ('project_have_steps', '=', False),
        ])
        parent_centers = self.env['account.analytic.account'].search([
            ('code', 'not in', params['all_separate_centers_codes']),
            ('parent_id', 'in', [False,]),
            ('plan_id', '=',
             self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
        ])
        max_level = self.calculate_max_level(parent_centers, cur_budget_projects)

        separate_budget_projects = self.env['project_budget.projects'].search([
            ('responsibility_center_id.code', 'in', params['all_separate_centers_codes']),
            ('commercial_budget_id', '=', budget.id),
            ('stage_id.code', '!=', '0'),
            ('is_not_for_mc_report', '=', False),
            '|', '&', ('step_status', '=', 'step'),
            ('step_project_parent_id.project_have_steps', '=', True),
            '&', ('step_status', '=', 'project'),
            ('project_have_steps', '=', False),
        ])
        separate_parent_centers = self.env['account.analytic.account'].search([
            ('code', 'in', params['all_separate_centers_codes']),
            ('plan_id', '=', self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
        ])
        separate_level = self.calculate_max_level(separate_parent_centers, separate_budget_projects) - 1
        max_level = max(max_level, separate_level)

        companies_sort = {
            7: 1,  # Систематика
            8: 2,  # Систематика Консалтинг
            3: 3,  # Ландата
            4: 4,  # Энсис Технологии
            5: 5,  # Топс Бизнес Интегратор
            2: 6,  # Доверенная среда
            14: 7,  # Триафлай
            6: 8,  # Хэд Пойнт
            9: 9,  # Облако.ру
        }

        systematica_companies = self.env['res.company'].search([('name', '=', params['systematica_name'])])
        not_systematica_companies = self.env['res.company'].search([('name', '!=', params['systematica_name'])]).sorted(
                key=lambda r: companies_sort.get(r.id, 99))

        oblako_company = VirtualCompany(params['virtual_company_id'], params['virtual_company_name'])

        responsibility_centers = self.env['account.analytic.account'].search([
            ('code', 'not in', params['all_separate_centers_codes']),
            ('parent_id', '=', False),
            ('plan_id', '=', self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
        ], order='sequence')  # для сортировки так делаем + берем сначала только верхние элементы

        separate_responsibility_centers = self.env['account.analytic.account'].search([
            ('code', 'in', params['parent_separate_centers_codes']),
            ('plan_id', '=',
             self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
        ], order='sequence')  # для сортировки так делаем + берем сначала только верхние элементы

        formulaItogo = '=sum(0'

        if systematica_companies:
            row, formulaItogo = self.printrow(
                sheet, workbook, systematica_companies, responsibility_centers, budget, row, formulaItogo,
                1, params,False
            )

            row, formulaItogo = self.printrow(
                sheet, workbook, (oblako_company,), separate_responsibility_centers, budget, row, formulaItogo,
                1, params, True
            )
        if not_systematica_companies:
            row, formulaItogo = self.printrow(
                sheet, workbook, not_systematica_companies, responsibility_centers, budget, row, formulaItogo,
                1, params,False
            )

        # печатаем данные из внешних источников
        # if budget.date_actual:
        #     current_date = budget.date_actual.date()
        # else:
        #     current_date = date.today()
        #
        # current_week_start = current_date - timedelta(days=current_date.isocalendar()[2] - 1)
        # current_week_end = current_date + timedelta(days=(7 - current_date.isocalendar()[2]))
        # previous_week_start = current_date - timedelta(days=current_date.isocalendar()[2] + 6)
        #
        # print('current_date', current_date, current_week_start, current_week_end)
        #
        # for company in systematica_companies + not_systematica_companies:
        #     external_data = self.env['project_budget.report_external_data'].search([
        #         ('report_date', '<=', current_week_end),
        #         ('company_id', '=', company.id),
        #     ], order='report_date desc', limit=1)
        #     if external_data:
        #         row = self.print_external_data(workbook, sheet, row, external_data, params)
        # end печатаем данные из внешних источников

        row += 1
        column = 0
        sheet.write_string(row, column, 'ИТОГО по отчету', row_format_number_itogo)
        if params['report_with_projects']:
            sheet.merge_range(row, column + 1, row, column + params["shift"] , '', row_format_number_itogo)
        for company_row in dict_formula['company_ids'].values():
            formulaItogo += ',{0}' + str(company_row + 1)
        formulaItogo = formulaItogo + ')'
        col = params["shift"] + 1
        self.print_summary_row(sheet, formulaItogo, row, col, 'total', formats_itogo)
    def generate_xlsx_report(self, workbook, data, budgets):
        global plan_shift
        global strYEAR
        strYEAR = str(data['year'])
        global YEARint
        YEARint = int(strYEAR)
        global dict_formula
        dict_formula = {'company_ids': {}, 'center_ids': {}, 'center_ids_not_empty': {}}
        global max_level
        global group_companies

        group_companies = self.env['res.company'].sudo().search([]).partner_id.ids

        params = {
            '50': data['koeff_reserve'],
            '30': data['koeff_potential'],
            'report_with_projects': data['report_with_projects'],
            'shift': 0,
            'margin_shift': 38,
            'all_separate_centers_codes': [
                '05', 'ПО_Облако.ру (интеграторский сервис)', 'ПО_Облако.ру (облачный сервис)',
                'ПО_Облако.ру (облачный сервис новые)', 'ПО_Облако.ру (облачный сервис база)',
            ],
            'parent_separate_centers_codes': ['05',],
            'company_separate_center_code': '05',
            'systematica_name': 'НКК',
            'virtual_company_id': 9999,
            'vgo_is_present': [],
            'ole_is_present': [],
            'vgo_row': 0,
            'ole_row': 0,
            'vgo_lines': [],
            'ole_lines': [],
        }

        # START Отладочные данные
        # params = {
        #     '50': data['koeff_reserve'],
        #     '30': data['koeff_potential'],
        #     'report_with_projects': data['report_with_projects'],
        #     'shift': 0,
        #     'margin_shift': 38,
        #     'all_separate_centers_codes': ['05', '12', '13', '14', '16', '17', '18', '19'],
        #     'parent_separate_centers_codes': ['05',],
        #     'company_separate_center_code': '05',
        #     'systematica_name': 'НКК',
        #     'virtual_company_id': 9999,
        # }
        # END Отладочные данные

        params['virtual_company_name'] = self.env['account.analytic.account'].search([
            ('plan_id', '=', self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
            ('code', '=', params['company_separate_center_code']),
        ]).name

        if data['report_with_projects']:
            params['shift'] = 10

        cash_shift = 38
        acceptance_shift = 75
        margin_income_shift = acceptance_shift + params['margin_shift']

        plan_shift = {
            'contracting': {
                'Q1': params['shift'] + 1,
                'Q2': params['shift'] + 5,
                'HY1': params['shift'] + 9,
                'Q3': params['shift'] + 14,
                'Q3_66': params['shift'] + 15,
                'Q4': params['shift'] + 19,
                'Q4_66': params['shift'] + 20,
                'HY2': params['shift'] + 24,
                'HY2_66': params['shift'] + 25,
                'Y': params['shift'] + 29,
                'Y_66': params['shift'] + 30,
            },
            'cash': {
                'Q1': params['shift'] + 1 + cash_shift,
                'Q2': params['shift'] + 5 + cash_shift,
                'HY1': params['shift'] + 9 + cash_shift,
                'Q3': params['shift'] + 14 + cash_shift,
                'Q3_66': params['shift'] + 15 + cash_shift,
                'Q4': params['shift'] + 19 + cash_shift,
                'Q4_66': params['shift'] + 20 + cash_shift,
                'HY2': params['shift'] + 24 + cash_shift,
                'HY2_66': params['shift'] + 25 + cash_shift,
                'Y': params['shift'] + 29 + cash_shift,
                'Y_66': params['shift'] + 30 + cash_shift,
            },
            'acceptance': {
                'Q1': params['shift'] + 1 + acceptance_shift,
                'Q2': params['shift'] + 5 + acceptance_shift,
                'HY1': params['shift'] + 9 + acceptance_shift,
                'Q3': params['shift'] + 14 + acceptance_shift,
                'Q3_66': params['shift'] + 15 + acceptance_shift,
                'Q4': params['shift'] + 19 + acceptance_shift,
                'Q4_66': params['shift'] + 20 + acceptance_shift,
                'HY2': params['shift'] + 24 + acceptance_shift,
                'HY2_66': params['shift'] + 25 + acceptance_shift,
                'Y': params['shift'] + 29 + acceptance_shift,
                'Y_66': params['shift'] + 30 + acceptance_shift,
            },
            'margin_income': {
                'Q1': params['shift'] + 1 + margin_income_shift,
                'Q2': params['shift'] + 5 + margin_income_shift,
                'HY1': params['shift'] + 9 + margin_income_shift,
                'Q3': params['shift'] + 14 + margin_income_shift,
                'Q3_66': params['shift'] + 15 + margin_income_shift,
                'Q4': params['shift'] + 19 + margin_income_shift,
                'Q4_66': params['shift'] + 20 + margin_income_shift,
                'HY2': params['shift'] + 24 + margin_income_shift,
                'HY2_66': params['shift'] + 25 + margin_income_shift,
                'Y': params['shift'] + 29 + margin_income_shift,
                'Y_66': params['shift'] + 30 + margin_income_shift,
            },
        }

        commercial_budget_id = data['commercial_budget_id']
        budget = self.env['project_budget.commercial_budget'].search([('id', '=', commercial_budget_id)])
        self.printworksheet(workbook, budget, 'Прогноз', params)
