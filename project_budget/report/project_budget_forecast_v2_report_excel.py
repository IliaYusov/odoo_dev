from odoo import models
import datetime
import xlsxwriter
from xlsxwriter.utility import xl_col_to_name
import logging

isdebug = False
logger = logging.getLogger("*___forecast_report___*")

class report_budget_forecast_excel(models.AbstractModel):
    _name = 'report.project_budget.report_budget_forecast_v2_excel'
    _description = 'project_budget.report_budget_forecast_v2_excel'
    _inherit = 'report.report_xlsx.abstract'


    YEARint = 2023
    koeff_reserve = float(1)
    year_end = 2023

    def isProjectinYear(self, project):
        global YEARint

        if project:
            if project.stage_id.code == '0':  # проверяем последний зафиксированный бюджет в предыдущих годах
                last_fixed_project = self.env['project_budget.projects'].sudo().search(
                    [('date_actual', '<', datetime.date(YEARint,1,1)),
                     ('budget_state', '=', 'fixed'),
                     ('project_id', '=', project.project_id),
                     ], limit=1, order='date_actual desc')
                if last_fixed_project and last_fixed_project.stage_id.code == '0':
                    return False

            if (project.end_presale_project_month.year >= YEARint and project.end_presale_project_month.year <= YEARint + 2)\
                    or (project.end_sale_project_month.year >= YEARint and project.end_sale_project_month.year <= YEARint + 2)\
                    or (project.end_presale_project_month.year <= YEARint and project.end_sale_project_month.year >= YEARint + 2):
                return True
            for pds in project.planned_cash_flow_ids:
                if pds.date_cash.year >= YEARint and pds.date_cash.year <= YEARint + 2:
                    return True
            for pds in project.fact_cash_flow_ids:
                if pds.date_cash.year >= YEARint and pds.date_cash.year <= YEARint + 2:
                    return True
            for act in project.planned_acceptance_flow_ids:
                if act.date_cash.year >= YEARint and act.date_cash.year <= YEARint + 2:
                    return True
            for act in project.fact_acceptance_flow_ids:
                if act.date_cash.year >= YEARint and act.date_cash.year <= YEARint + 2:
                    return True
            for pds in project.planned_step_cash_flow_ids:
                if pds.date_cash.year >= YEARint and pds.date_cash.year <= YEARint + 2:
                    return True
            for pds in project.fact_step_cash_flow_ids:
                if pds.date_cash.year >= YEARint and pds.date_cash.year <= YEARint + 2:
                    return True
            for act in project.planned_step_acceptance_flow_ids:
                if act.date_cash.year >= YEARint and act.date_cash.year <= YEARint + 2:
                    return True
            for act in project.fact_step_acceptance_flow_ids:
                if act.date_cash.year >= YEARint and act.date_cash.year <= YEARint + 2:
                    return True
        return False

    month_rus_name_contract_pds = ['Январь','Февраль','Март','Q1 итого','Апрель','Май','Июнь','Q2 итого','HY1 YEAR итого',
                                    'Июль','Август','Сентябрь','Q3 итого','Октябрь','Ноябрь','Декабрь','Q4 итого',
                                   'HY2 YEAR итого','YEAR итого']
    month_rus_name_revenue_margin = ['Q1','Q2','HY1 YEAR','Q3','Q4','HY2 YEAR','YEAR итого']

    # array_col_itogi = [28, 49, 55, 76, 97, 103, 109, 130, 151, 157, 178, 199, 205, 211, 217, 223, 229, 235, 241, 254, 260, 266, 272, 278, 284, 297,]
    #
    # array_col_itogi75 = [247, 291,]
    #
    # array_col_itogi75NoFormula = [248, 292,]

    dict_formula = {}
    # dict_contract_pds = {
    #     1: {'name': 'Контрактование, с НДС', 'color': '#FFD966'},
    #     2: {'name': 'Поступление денежных средств, с НДС', 'color': '#D096BF'}
    # }

    dict_revenue_margin= {
        1: {'name': 'Валовая Выручка, без НДС', 'color': '#B4C6E7'},
        2: {'name': 'Валовая прибыль (Маржа 1), без НДС', 'color': '#F4FD9F'}
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

    def get_quater_from_month(self,month):
        if month in (1,2,3):
            return 'Q1'
        if month in (4,5,6):
            return 'Q2'
        if month in (7,8,9):
            return 'Q3'
        if month in (10,11,12):
            return 'Q4'
        return False


    def get_months_from_quater(self,quater_name):
        months = False;
        if quater_name == 'Q1':
            months=(1,2,3)
        if quater_name == 'Q2':
            months=(4,5,6)
        if quater_name == 'Q3':
            months=(7,8,9)
        if quater_name == 'Q4':
            months=(10,11,12)
        return months

    def get_sum_fact_pds_project_month(self, project, year, month):
        sum_cash = 0

        if project.step_status == 'project':
            pds_list = project.fact_cash_flow_ids
        elif project.step_status == 'step':
            pds_list = project.fact_step_cash_flow_ids

        for pds in pds_list:

            if (pds.date_cash.month == month or not month) and pds.date_cash.year == year:
                sum_cash += pds.sum_cash

        return sum_cash

    def get_sum_plan_pds_project_month(self, project, year, month):
        sum_cash = {'commitment': 0, 'reserve':0}

        if project.step_status == 'project':
            pds_list = project.planned_cash_flow_ids
        elif project.step_status == 'step':
            pds_list = project.planned_step_cash_flow_ids

        stage_id_code = project.stage_id.code

        for pds in pds_list:

            if (pds.date_cash.month == month or not month) and pds.date_cash.year == year:

                if pds.forecast == 'from_project':
                    if stage_id_code in ('75', '100', '100(done)'):
                        sum_cash['commitment'] = sum_cash.get('commitment', 0) + pds.sum_cash
                    elif stage_id_code == '50':
                        sum_cash['reserve'] = sum_cash.get('reserve', 0) + pds.sum_cash
                else:
                    if stage_id_code != '0':
                        sum_cash[pds.forecast] = sum_cash.get(pds.forecast, 0) + pds.sum_cash

        return sum_cash

    def print_month_head_contract(self, workbook, sheet, row, column, year, elements, next):

        x = {'name': 'Контрактование, с НДС', 'color': '#FFD966'}

        y = list(x.values())
        head_format_month = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "bold" : True,
            "fg_color" : y[1],
            "font_size" : 12,
        })
        head_format_month_itogo = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "bold": True,
            "fg_color": '#DCE6F1',
            "font_size": 12,
        })
        head_format_month_detail = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "bold": False,
            "fg_color": '#E2EFDA',
            "font_size": 8,
        })
        head_format_month_detail_fact = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "bold": True,
            "fg_color": '#C6E0B4',
            "font_size": 8,
        })

        colbeg = column
        colbegQ= column
        colbegH= column
        colbegY= column

        for elementone in elements:
            strYEARprint = str(year)

            element = elementone.replace('YEAR',strYEARprint)
            if 'итого' in element:
                if next:
                    sheet.merge_range(row, column, row, column + 3, element, head_format_month)
                else:
                    if 'Q1' in elementone or 'Q2' in elementone:
                        sheet.set_column(column, column + 4, False, False, {'hidden': 1, 'level': 2})
                        sheet.merge_range(row, column, row, column + 4, element, head_format_month)
                    elif 'Q3' in elementone or 'Q4' in elementone:
                        sheet.set_column(column, column + 5, False, False, {'hidden': 1, 'level': 2})
                        sheet.merge_range(row, column, row, column + 5, element, head_format_month)
                    elif 'HY1' in elementone:
                        sheet.set_column(column, column + 4, False, False, {'hidden': 1, 'level': 1})
                        sheet.merge_range(row, column, row, column + 4, element, head_format_month)
                    elif 'HY2' in elementone:
                        sheet.set_column(column, column + 5, False, False, {'hidden': 1, 'level': 1})
                        sheet.merge_range(row, column, row, column + 5, element, head_format_month)
                    elif elementone == 'YEAR итого':
                        sheet.merge_range(row, column, row, column + 5, element, head_format_month)

                sheet.merge_range(row + 1, column, row + 2, column, "План " + element.replace(' итого',''), head_format_month_itogo)
                column += 1

                if not ('Q1' in element or 'Q2' in element or 'HY1' in element) and not next:
                    sheet.merge_range(row + 1, column, row + 2, column, "План " + element.replace(' итого','') + " 6+6"
                                      , head_format_month_itogo)
                    column += 1

            else:
                sheet.merge_range(row, column, row, column + 3, element, head_format_month)
                sheet.set_column(column, column+4, False, False, {'hidden': 1, 'level': 3})
            if not next:
                sheet.merge_range(row+1, column, row+2, column, 'Факт', head_format_month_detail_fact)
                column += 1
            sheet.merge_range(row + 1, column, row + 1, column + 2, 'Прогноз до конца периода (на дату отчета)',head_format_month_detail)
            sheet.write_string(row + 2, column, 'Обязательство', head_format_month_detail)
            column += 1
            sheet.write_string(row + 2, column, 'Резерв', head_format_month_detail)
            column += 1
            sheet.write_string(row + 2, column, 'Потенциал', head_format_month_detail)
            column += 1

            if 'Q' in elementone or 'НY' in elementone or 'YEAR' in elementone:
                colbegQ = column

            if 'НY' in elementone or 'YEAR' in elementone:
                colbegH = column

        sheet.merge_range(row-1, colbeg, row-1, column - 1, y[0], head_format_month)

        return column

    def print_month_head_pds(self, workbook, sheet, row, column, year, elements, next):

        x = {'name': 'Поступление денежных средств, с НДС', 'color': '#D096BF'}

        y = list(x.values())
        head_format_month = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "bold" : True,
            "fg_color" : y[1],
            "font_size" : 12,
        })
        head_format_month_itogo = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "bold": True,
            "fg_color": '#DCE6F1',
            "font_size": 12,
        })
        head_format_month_detail = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "bold": False,
            "fg_color": '#E2EFDA',
            "font_size": 8,
        })
        head_format_month_detail_fact = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "bold": True,
            "fg_color": '#C6E0B4',
            "font_size": 8,
        })

        colbeg = column
        colbegQ= column
        colbegH= column
        colbegY= column

        for elementone in elements:
            strYEARprint = str(year)

            element = elementone.replace('YEAR',strYEARprint)
            if 'итого' in element:
                if next:
                    sheet.merge_range(row, column, row, column + 2, element, head_format_month)
                else:
                    if 'Q1' in elementone or 'Q2' in elementone:
                        sheet.set_column(column, column + 3, False, False, {'hidden': 1, 'level': 2})
                        sheet.merge_range(row, column, row, column + 3, element, head_format_month)
                    elif 'Q3' in elementone or 'Q4' in elementone:
                        sheet.set_column(column, column + 4, False, False, {'hidden': 1, 'level': 2})
                        sheet.merge_range(row, column, row, column + 4, element, head_format_month)
                    elif 'HY1' in elementone:
                        sheet.set_column(column, column + 3, False, False, {'hidden': 1, 'level': 1})
                        sheet.merge_range(row, column, row, column + 3, element, head_format_month)
                    elif 'HY2' in elementone:
                        sheet.set_column(column, column + 4, False, False, {'hidden': 1, 'level': 1})
                        sheet.merge_range(row, column, row, column + 4, element, head_format_month)
                    elif elementone == 'YEAR итого':
                        sheet.merge_range(row, column, row, column + 4, element, head_format_month)

                sheet.merge_range(row + 1, column, row + 2, column, "План "+element.replace(' итого',''), head_format_month_itogo)
                column += 1

                if not ('Q1' in element or 'Q2' in element or 'HY1' in element) and not next:
                    sheet.merge_range(row + 1, column, row + 2, column, "План " + element.replace(' итого','') + " 6+6"
                                      , head_format_month_itogo)
                    column += 1

            else:
                sheet.merge_range(row, column, row, column + 2, element, head_format_month)
                sheet.set_column(column, column+4, False, False, {'hidden': 1, 'level': 3})
            if not next:
                sheet.merge_range(row+1, column, row+2, column, 'Факт', head_format_month_detail_fact)
                column += 1
            sheet.merge_range(row + 1, column, row + 1, column + 1, 'Прогноз до конца периода (на дату отчета)',head_format_month_detail)
            sheet.write_string(row + 2, column, 'Обязательство', head_format_month_detail)
            column += 1
            sheet.write_string(row + 2, column, 'Резерв', head_format_month_detail)
            column += 1
            if elementone.find('Q') != -1 or elementone.find('НY') != -1 or elementone.find('YEAR') != -1:
                colbegQ = column

            if elementone.find('НY') != -1 or elementone.find('YEAR') != -1:
                colbegH = column
        sheet.merge_range(row-1, colbeg, row-1, column - 1, y[0], head_format_month)

        return column

    def print_month_head_revenue_margin(self, workbook, sheet, row, column, year, elements, next):

        for x in self.dict_revenue_margin.items():
            y = list(x[1].values())
            head_format_month = workbook.add_format({
                'border': 1,
                'text_wrap': True,
                'align': 'center',
                'valign': 'vcenter',
                "bold" : True,
                "fg_color" : y[1],
                "font_size" : 12,
            })
            head_format_month_itogo = workbook.add_format({
                'border': 1,
                'text_wrap': True,
                'align': 'center',
                'valign': 'vcenter',
                "bold": True,
                "fg_color": '#DCE6F1',
                "font_size": 12,
            })
            head_format_month_detail = workbook.add_format({
                'border': 1,
                'text_wrap': True,
                'align': 'center',
                'valign': 'vcenter',
                "bold": False,
                "fg_color": '#E2EFDA',
                "font_size": 8,
            })
            head_format_month_detail_fact = workbook.add_format({
                'border': 1,
                'text_wrap': True,
                'align': 'center',
                'valign': 'vcenter',
                "bold": True,
                "fg_color": '#C6E0B4',
                "font_size": 8,
            })

            strYEARprint = str(year)

            colbeg = column

            for elementone in elements:
                element = elementone.replace('YEAR', strYEARprint)
                potential_column = 0

                if 'итого' in element and x[0] == 1:
                    potential_column = 1

                if next:
                    sheet.merge_range(row, column, row, column + 2 + potential_column, element, head_format_month)
                else:
                    if 'Q1' in elementone or 'Q2' in elementone:
                        sheet.set_column(column, column + 3, False, False, {'hidden': 1, 'level': 2})
                        sheet.merge_range(row, column, row, column + 3, element, head_format_month)
                    elif 'Q3' in elementone or 'Q4' in elementone:
                        sheet.set_column(column, column + 4, False, False, {'hidden': 1, 'level': 2})
                        sheet.merge_range(row, column, row, column + 4, element, head_format_month)
                    elif 'HY1' in elementone:
                        sheet.set_column(column, column + 3, False, False, {'hidden': 1, 'level': 1})
                        sheet.merge_range(row, column, row, column + 3, element, head_format_month)
                    elif 'HY2' in elementone:
                        sheet.set_column(column, column + 4, False, False, {'hidden': 1, 'level': 1})
                        sheet.merge_range(row, column, row, column + 4, element, head_format_month)
                    elif elementone == 'YEAR итого':
                        sheet.merge_range(row, column, row, column + 4 + potential_column, element, head_format_month)

                sheet.merge_range(row + 1, column, row + 2, column, "План " + element.replace(' итого', ''),
                                  head_format_month_itogo)
                column += 1

                if not ('Q1' in element or 'Q2' in element or 'HY1' in element) and not next:
                    sheet.merge_range(row + 1, column, row + 2, column, "План " + element.replace(' итого','') + " 6+6"
                                      , head_format_month_itogo)
                    column += 1

                if not next:
                    sheet.merge_range(row + 1, column , row + 2, column , 'Факт', head_format_month_detail_fact)
                    column += 1

                if 'итого' in element and x[0] == 1:
                    sheet.merge_range(row + 1, column, row + 1, column + 2,
                                      'Прогноз до конца периода (на дату отчета)',
                                      head_format_month_detail)
                    sheet.write_string(row + 2, column, 'Обязательство', head_format_month_detail)
                    column += 1
                    sheet.write_string(row + 2, column, 'Резерв', head_format_month_detail)
                    column += 1
                    sheet.write_string(row + 2, column, 'Потенциал', head_format_month_detail)
                    column += 1
                else:
                    sheet.merge_range(row + 1, column, row + 1, column + 1,
                                      'Прогноз до конца периода (на дату отчета)',
                                      head_format_month_detail)
                    sheet.write_string(row + 2, column, 'Обязательство', head_format_month_detail)
                    column += 1
                    sheet.write_string(row + 2, column, 'Резерв', head_format_month_detail)
                    column += 1

            sheet.merge_range(row-1, colbeg, row-1, column - 1, y[0], head_format_month)
        return column

    def get_currency_rate_by_project(self,project):
        project_currency_rates = self.env['project_budget.project_currency_rates']
        return project_currency_rates._get_currency_rate_for_project_in_company_currency(project)

    def print_month_revenue_project(self, sheet, row, column, month, project, year, row_format_number,row_format_number_color_fact, next):
        global koeff_reserve
        global koeff_potential

        sum75tmpetalon = 0
        sum50tmpetalon = 0
        sum100tmp = 0
        sum75tmp = 0
        sum50tmp = 0
        sum30tmp = 0

        if month:
            if month == project.end_presale_project_month.month and project.end_presale_project_month.year == year:
                currency_rate = self.get_currency_rate_by_project(project)
                if not next:
                    if project.stage_id.code in ('100','100(done)'):
                        sheet.write_number(row, column + 0, project.total_amount_of_revenue_with_vat * currency_rate, row_format_number_color_fact)
                        sum100tmp += project.total_amount_of_revenue_with_vat * currency_rate
                    if project.stage_id.code == '75':
                        sheet.write_number(row, column + 1, project.total_amount_of_revenue_with_vat * currency_rate, row_format_number)
                        sum75tmp += project.total_amount_of_revenue_with_vat * currency_rate
                    if project.stage_id.code == '50':
                        sheet.write_number(row, column + 2, project.total_amount_of_revenue_with_vat * koeff_reserve * currency_rate, row_format_number)
                        sum50tmp += project.total_amount_of_revenue_with_vat * koeff_reserve*currency_rate
                    if project.stage_id.code == '30':
                        sheet.write_number(row, column + 3, project.total_amount_of_revenue_with_vat * koeff_potential * currency_rate, row_format_number)
                        sum30tmp += project.total_amount_of_revenue_with_vat * koeff_potential * currency_rate
                else:
                    if project.stage_id.code == '75':
                        sheet.write_number(row, column + 0, project.total_amount_of_revenue_with_vat * currency_rate, row_format_number)
                    if project.stage_id.code == '50':
                        sheet.write_number(row, column + 1, project.total_amount_of_revenue_with_vat * koeff_reserve * currency_rate, row_format_number)
                    if project.stage_id.code == '30':
                        sheet.write_number(row, column + 2, project.total_amount_of_revenue_with_vat * koeff_potential * currency_rate, row_format_number)
        return sum75tmpetalon, sum50tmpetalon, sum100tmp, sum75tmp, sum50tmp, sum30tmp

    def print_year_pds_project(self, sheet, row, column, project, year, row_format_number, row_format_number_color_fact, next):
        global koeff_reserve

        sum75tmpetalon = sum50tmpetalon = sum100tmp = sum75tmp = sum50tmp = 0
        if year:
            sum = {'commitment': 0, 'reserve': 0, 'potential': 0}

            sum100tmp = self.get_sum_fact_pds_project_month(project, year, False)

            if sum100tmp:
                if not next:
                    sheet.write_number(row, column + 0, sum100tmp, row_format_number_color_fact)

            sum = self.get_sum_plan_pds_project_month(project, year, False)

            if not project.is_correction_project:
                if sum100tmp >= sum.get('commitment', 0):
                    sum100tmp_ostatok = sum100tmp - sum['commitment']
                    sum['commitment'] = 0
                    sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                else:
                    sum['commitment'] = sum['commitment'] - sum100tmp

            # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
            sum_ostatok_pds = {'commitment': 0, 'reserve':0, 'potential': 0}
            sum_distribution_pds = 0

            if project.step_status == 'project':
                planned_cash_flows = project.planned_cash_flow_ids
            elif project.step_status == 'step':
                planned_cash_flows = project.planned_step_cash_flow_ids

            for planned_cash_flow in planned_cash_flows:
                if planned_cash_flow.date_cash.year == year:
                    sum_distribution_pds += planned_cash_flow.distribution_sum_without_vat
                    stage_id_code = project.stage_id.code

                    if planned_cash_flow.forecast == 'from_project':
                        if stage_id_code in ('75', '100', '100(done)'):
                            sum_ostatok_pds['commitment'] = sum_ostatok_pds.get('commitment', 0) + planned_cash_flow.distribution_sum_with_vat_ostatok
                        elif stage_id_code == '50':
                            sum_ostatok_pds['reserve'] = sum_ostatok_pds.get('reserve', 0) + planned_cash_flow.distribution_sum_with_vat_ostatok
                    else:
                        if stage_id_code != '0':
                            sum_ostatok_pds[planned_cash_flow.forecast] = sum_ostatok_pds.get(planned_cash_flow.forecast, 0) + planned_cash_flow.distribution_sum_with_vat_ostatok

            if sum_distribution_pds != 0 : # если есть распределение, то остаток = остатку распределения
                sum = sum_ostatok_pds
                for key in sum:
                    if sum[key] < 0 and not project.is_correction_project:
                        sum[key] = 0

            if sum:
                sheet.write_number(row, column + 0, sum.get('commitment', 0), row_format_number)
                sum75tmp += sum.get('commitment', 0)
                sheet.write_number(row, column + 1, sum.get('reserve', 0) * koeff_reserve, row_format_number)
                sum50tmp += sum.get('reserve', 0) * koeff_reserve

        return sum75tmpetalon, sum50tmpetalon, sum100tmp, sum75tmp, sum50tmp

    def print_month_pds_project(self, sheet, row, column, month, project, year, row_format_number, row_format_number_color_fact, next):
        global koeff_reserve

        sum75tmpetalon = sum50tmpetalon = sum100tmp = sum75tmp = sum50tmp = 0
        if month:
            sum = {'commitment': 0, 'reserve': 0, 'potential': 0}

            sum100tmp = self.get_sum_fact_pds_project_month(project, year, month)

            if sum100tmp:
                if not next:
                    sheet.write_number(row, column + 0, sum100tmp, row_format_number_color_fact)

            sum = self.get_sum_plan_pds_project_month(project, year, month)

            if not project.is_correction_project:
                if sum100tmp >= sum.get('commitment', 0):
                    sum100tmp_ostatok = sum100tmp - sum['commitment']
                    sum['commitment'] = 0
                    sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                else:
                    sum['commitment'] = sum['commitment'] - sum100tmp

            # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
            sum_ostatok_pds = {'commitment': 0, 'reserve':0, 'potential': 0}
            sum_distribution_pds = 0

            if project.step_status == 'project':
                planned_cash_flows = project.planned_cash_flow_ids
            elif project.step_status == 'step':
                planned_cash_flows = project.planned_step_cash_flow_ids

            for planned_cash_flow in planned_cash_flows:
                if planned_cash_flow.date_cash.month == month and planned_cash_flow.date_cash.year == year:
                    sum_distribution_pds += planned_cash_flow.distribution_sum_without_vat
                    stage_id_code = project.stage_id.code

                    if planned_cash_flow.forecast == 'from_project':
                        if stage_id_code in ('75', '100', '100(done)'):
                            sum_ostatok_pds['commitment'] = sum_ostatok_pds.get('commitment', 0) + planned_cash_flow.distribution_sum_with_vat_ostatok
                        elif stage_id_code == '50':
                            sum_ostatok_pds['reserve'] = sum_ostatok_pds.get('reserve', 0) + planned_cash_flow.distribution_sum_with_vat_ostatok
                    else:
                        if stage_id_code != '0':
                            sum_ostatok_pds[planned_cash_flow.forecast] = sum_ostatok_pds.get(planned_cash_flow.forecast, 0) + planned_cash_flow.distribution_sum_with_vat_ostatok

            if sum_distribution_pds != 0 : # если есть распределение, то остаток = остатку распределения
                sum = sum_ostatok_pds
                for key in sum:
                    if sum[key] < 0 and not project.is_correction_project:
                        sum[key] = 0

            if sum:
                if not next:
                    sheet.write_number(row, column + 1, sum.get('commitment', 0), row_format_number)
                    sum75tmp += sum.get('commitment', 0)
                    sheet.write_number(row, column + 2, sum.get('reserve', 0) * koeff_reserve, row_format_number)
                    sum50tmp += sum.get('reserve', 0) * koeff_reserve
                else:
                    sheet.write_number(row, column + 0, sum.get('commitment', 0), row_format_number)
                    sum75tmp += sum.get('commitment', 0)
                    sheet.write_number(row, column + 1, sum.get('reserve', 0) * koeff_reserve, row_format_number)
                    sum50tmp += sum.get('reserve', 0) * koeff_reserve

        return sum75tmpetalon, sum50tmpetalon, sum100tmp, sum75tmp, sum50tmp

    def get_sum_fact_acceptance_project_quater(self, project, year, element_name):
        sum_cash = 0

        months = self.get_months_from_quater(element_name)

        if project.step_status == 'project':
            acceptance_list = project.fact_acceptance_flow_ids
        elif project.step_status == 'step':
            acceptance_list = project.fact_step_acceptance_flow_ids

        if acceptance_list:
            for acceptance in acceptance_list:
                if (not months or acceptance.date_cash.month in months) and acceptance.date_cash.year == year:
                    sum_cash += acceptance.sum_cash_without_vat
        return sum_cash

    def get_sum_fact_margin_project_quarter(self, project, year, element_name):
        sum_cash = 0

        months = self.get_months_from_quater(element_name)

        if project.is_child_project:
            child_rate = (1 / (1 - project.margin_rate_for_parent))
        else:
            child_rate = 1

        if project.is_parent_project:
            for child_project in project.child_project_ids:
                if child_project.project_have_steps:
                    for child_step in child_project.step_project_child_ids:
                        sum_cash += self.get_sum_fact_margin_project_quarter(child_step, year, element_name) * child_project.margin_rate_for_parent
                else:
                    sum_cash += self.get_sum_fact_margin_project_quarter(child_project, year, element_name) * child_project.margin_rate_for_parent
            return sum_cash

        if project.step_status == 'project':
            acceptance_list = project.fact_acceptance_flow_ids
        elif project.step_status == 'step':
            acceptance_list = project.fact_step_acceptance_flow_ids

        if acceptance_list:
            for acceptance in acceptance_list:
                if (not months or acceptance.date_cash.month in months) and acceptance.date_cash.year == year:
                    if project.is_child_project:
                        sum_cash += acceptance.margin * child_rate
                    else:
                        sum_cash += acceptance.margin
        return sum_cash

    def get_sum_planned_acceptance_project_quater(self, project, year, element_name):

        sum_acceptance = {'commitment': 0, 'reserve':0, 'potential': 0}

        months = self.get_months_from_quater(element_name)

        if project.step_status == 'project':
            acceptance_list = project.planned_acceptance_flow_ids
        elif project.step_status == 'step':
            acceptance_list = project.planned_step_acceptance_flow_ids

        stage_id_code = project.stage_id.code

        if acceptance_list:
            for acceptance in acceptance_list:
                if (not months or acceptance.date_cash.month in months) and acceptance.date_cash.year == year:
                    if acceptance.forecast == 'from_project':
                        if stage_id_code in ('75', '100', '100(done)'):
                            sum_acceptance['commitment'] = sum_acceptance.get('commitment', 0) + acceptance.sum_cash_without_vat
                        elif stage_id_code == '50':
                            sum_acceptance['reserve'] = sum_acceptance.get('reserve', 0) + acceptance.sum_cash_without_vat
                    else:
                        if stage_id_code != '0':
                            sum_acceptance[acceptance.forecast] = sum_acceptance.get(acceptance.forecast, 0) + acceptance.sum_cash_without_vat
        return sum_acceptance

    def get_sum_planned_margin_project_quater(self, project, year, element_name):

        sum_margin = {'commitment': 0, 'reserve': 0, 'potential': 0}

        if project.is_child_project:
            child_rate = (1 / (1 - project.margin_rate_for_parent))
        else:
            child_rate = 1

        months = self.get_months_from_quater(element_name)
        if project.is_parent_project:
            for child_project in project.child_project_ids:
                if child_project.project_have_steps:
                    for child_step in child_project.step_project_child_ids:
                        for key in sum_margin:
                            sum_margin[key] += self.get_sum_planned_margin_project_quater(child_step, year, element_name)[key] * child_project.margin_rate_for_parent
                else:
                    for key in sum_margin:
                        sum_margin[key] += self.get_sum_planned_margin_project_quater(child_project, year, element_name)[key] * child_project.margin_rate_for_parent
            return sum_margin

        if project.step_status == 'project':
            acceptance_list = project.planned_acceptance_flow_ids
        elif project.step_status == 'step':
            acceptance_list = project.planned_step_acceptance_flow_ids

        stage_id_code = project.stage_id.code
        profitability = project.profitability

        if acceptance_list:
            for acceptance in acceptance_list:
                if any(distribution.fact_acceptance_flow_id.margin_manual_input for distribution in
                       acceptance.distribution_acceptance_ids):  # если есть ручная маржа - пропускаем
                    continue
                if (not months or acceptance.date_cash.month in months) and acceptance.date_cash.year == year:
                    if acceptance.forecast == 'from_project':
                        if stage_id_code in ('75', '100', '100(done)'):
                            sum_margin['commitment'] += acceptance.sum_cash_without_vat * profitability * child_rate / 100
                        elif stage_id_code == '50':
                            sum_margin['reserve'] += acceptance.sum_cash_without_vat * profitability * child_rate / 100
                    else:
                        if stage_id_code != '0':
                            sum_margin[acceptance.forecast] += acceptance.sum_cash_without_vat * profitability * child_rate / 100
        return sum_margin

    def get_margin_forecast_from_distributions(self, planned_acceptance, margin_plan, project, margin_rate_for_parent):
        # суммируем доли маржи фактов в соотношении (сумма распределения/суммы факта)
        margin_distribution = 0

        if project.is_child_project:
            child_rate = (1 / (1 - project.margin_rate_for_parent))
        else:
            child_rate = 1

        for distribution in planned_acceptance.distribution_acceptance_ids:
            if distribution.fact_acceptance_flow_id.sum_cash_without_vat != 0:
                margin_distribution += distribution.fact_acceptance_flow_id.margin * distribution.sum_cash_without_vat / distribution.fact_acceptance_flow_id.sum_cash_without_vat

        stage_id_code = project.stage_id.code

        if planned_acceptance.forecast == 'from_project':
            if stage_id_code in ('75', '100', '100(done)'):
                margin_plan['commitment'] -= margin_distribution * margin_rate_for_parent * child_rate
            elif stage_id_code == '50':
                margin_plan['reserve'] -= margin_distribution * margin_rate_for_parent * child_rate
        else:
            if stage_id_code != '0':
                margin_plan[planned_acceptance.forecast] -= margin_distribution * margin_rate_for_parent * child_rate
        return  margin_plan

    def get_sum_planned_acceptance_project_from_distribution(self, project, year, element_name):
        # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
        sum_ostatok_acceptance = {'commitment': 0, 'reserve': 0, 'potential': 0}
        sum_distribution_acceptance = 0

        months = self.get_months_from_quater(element_name)

        if project.step_status == 'project':
            acceptance_list = project.planned_acceptance_flow_ids
        elif project.step_status == 'step':
            acceptance_list = project.planned_step_acceptance_flow_ids

        stage_id_code = project.stage_id.code

        for planned_acceptance_flow in acceptance_list:

            if (not months or planned_acceptance_flow.date_cash.month in months) and planned_acceptance_flow.date_cash.year == year:

                sum_distribution_acceptance += planned_acceptance_flow.distribution_sum_without_vat

                if planned_acceptance_flow.forecast == 'from_project':
                    if stage_id_code in ('75', '100', '100(done)'):
                        sum_ostatok_acceptance['commitment'] = sum_ostatok_acceptance.get('commitment',
                                                                                          0) + planned_acceptance_flow.distribution_sum_without_vat_ostatok
                    elif stage_id_code == '50':
                        sum_ostatok_acceptance['reserve'] = sum_ostatok_acceptance.get('reserve',
                                                                                       0) + planned_acceptance_flow.distribution_sum_without_vat_ostatok
                else:
                    if stage_id_code != '0':
                        sum_ostatok_acceptance[planned_acceptance_flow.forecast] = sum_ostatok_acceptance.get(
                            planned_acceptance_flow.forecast,
                            0) + planned_acceptance_flow.distribution_sum_without_vat_ostatok

        if sum_distribution_acceptance:  # если есть распределение, то остаток = остатку распределения
            return sum_ostatok_acceptance
        else:
            return False

    def get_sum_planned_margin_project_from_distribution(self, project, year, element_name, margin_plan, margin_rate_for_parent):
        # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
        sum_distribution_acceptance = 0
        new_margin_plan = margin_plan.copy()
        months = self.get_months_from_quater(element_name)

        if project.is_parent_project:
            for child_project in project.child_project_ids:
                if child_project.project_have_steps:
                    for child_step in child_project.step_project_child_ids:
                        new_margin_plan = self.get_sum_planned_margin_project_from_distribution(
                            child_step, year, element_name, margin_plan, child_project.margin_rate_for_parent
                        )
                        if new_margin_plan:
                            margin_plan = new_margin_plan
                else:
                    new_margin_plan = self.get_sum_planned_margin_project_from_distribution(
                        child_project, year, element_name, margin_plan, child_project.margin_rate_for_parent
                    )
                    if new_margin_plan:
                        margin_plan = new_margin_plan
            return margin_plan

        if project.step_status == 'project':
            acceptance_list = project.planned_acceptance_flow_ids
        elif project.step_status == 'step':
            acceptance_list = project.planned_step_acceptance_flow_ids

        for planned_acceptance_flow in acceptance_list:
            if any(distribution.fact_acceptance_flow_id.margin_manual_input for distribution in
                   planned_acceptance_flow.distribution_acceptance_ids):  # если есть ручная маржа - отдаем нулевой прогноз
                sum_distribution_acceptance += 1
                continue

            if (not months or planned_acceptance_flow.date_cash.month in months) and planned_acceptance_flow.date_cash.year == year:

                sum_distribution_acceptance += planned_acceptance_flow.distribution_sum_without_vat

                new_margin_plan = self.get_margin_forecast_from_distributions(planned_acceptance_flow, new_margin_plan,
                                                                              project, margin_rate_for_parent)

        if sum_distribution_acceptance:  # если есть распределение, то остаток = остатку распределения
            return new_margin_plan
        else:
            return False

    def print_year_planned_acceptance_project(self, sheet, row, column, project, year, row_format_number, row_format_number_color_fact,margin_shift,next):

        sum75tmpetalon = sum50tmpetalon = sum100tmp = sum75tmp = sum50tmp = 0

        if year:

            profitability = project.profitability

            margin_rate_for_child = 1
            if project.parent_project_id:
                margin_rate_for_child = (1 - project.margin_rate_for_parent)
            elif project.step_project_parent_id.parent_project_id:
                margin_rate_for_child = (1 - project.step_project_parent_id.margin_rate_for_parent)

            sum100tmp = self.get_sum_fact_acceptance_project_quater(project, year, False)
            margin100tmp = self.get_sum_fact_margin_project_quarter(project, year, False)

            if not next:
                if sum100tmp:
                    sheet.write_number(row, column + 0, sum100tmp, row_format_number_color_fact)
                if margin100tmp:
                    sheet.write_number(row, column + 0 + margin_shift, margin100tmp * margin_rate_for_child, row_format_number_color_fact)

            sum = self.get_sum_planned_acceptance_project_quater(project, year, False)
            margin_sum = self.get_sum_planned_margin_project_quater(project, year, False)

            margin_plan = {'commitment': 0, 'reserve': 0, 'potential': 0}

            if margin_sum:
                margin_plan = margin_sum.copy()

            if not project.is_correction_project and not project.is_parent_project:

                if sum100tmp >= sum.get('commitment', 0):
                    sum100tmp_ostatok = sum100tmp - sum['commitment']
                    sum['commitment'] = 0
                    sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                else:
                    sum['commitment'] = sum['commitment'] - sum100tmp

                if margin100tmp >= margin_plan['commitment']:  # маржа если нет распределения
                    margin100tmp_ostatok = margin100tmp - margin_plan['commitment']
                    margin_sum['commitment'] = 0
                    margin_sum['reserve'] = max(margin_plan['reserve'] - margin100tmp_ostatok, 0)
                else:
                    margin_sum['commitment'] = margin_plan['commitment'] - margin100tmp

            sum_ostatok_acceptance = self.get_sum_planned_acceptance_project_from_distribution(project, year, False)
            new_margin_plan = self.get_sum_planned_margin_project_from_distribution(project, year, False, margin_plan, 1)

            if sum_ostatok_acceptance:
                sum = sum_ostatok_acceptance
            if new_margin_plan:
                margin_sum = new_margin_plan

            for key in sum:
                if not project.is_correction_project:
                    sum[key] = max(sum[key], 0)
                    margin_sum[key] = max(margin_sum[key], 0)

            if sum:
                sheet.write_number(row, column + 0, sum.get('commitment', 0), row_format_number)
                sheet.write_number(row, column + 0 + margin_shift, margin_sum.get('commitment', 0) * margin_rate_for_child, row_format_number)
                sum75tmp += sum.get('commitment', 0)
                sheet.write_number(row, column + 1, sum.get('reserve', 0) * koeff_reserve, row_format_number)
                sheet.write_number(row, column + 1 + margin_shift, margin_sum.get('reserve', 0) * koeff_reserve * margin_rate_for_child, row_format_number)
                sum50tmp += sum.get('reserve', 0) * koeff_reserve

        return sum75tmpetalon, sum50tmpetalon, sum100tmp, sum75tmp, sum50tmp

    def print_quater_planned_acceptance_project(self, sheet, row, column, element_name, project, year, row_format_number, row_format_number_color_fact,margin_shift,next):

        sum75tmpetalon = sum50tmpetalon = sum100tmp = sum75tmp = sum50tmp = 0

        if element_name in ('Q1','Q2','Q3','Q4'):

            profitability = project.profitability

            margin_rate_for_child = 1
            if project.parent_project_id:
                margin_rate_for_child = (1 - project.margin_rate_for_parent)
            elif project.step_project_parent_id.parent_project_id:
                margin_rate_for_child = (1 - project.step_project_parent_id.margin_rate_for_parent)

            sum100tmp = self.get_sum_fact_acceptance_project_quater(project, year, element_name)
            margin100tmp = self.get_sum_fact_margin_project_quarter(project, year, element_name)

            if not next:
                if sum100tmp:
                    sheet.write_number(row, column + 0, sum100tmp, row_format_number_color_fact)
                if margin100tmp:
                    sheet.write_number(row, column + 0 + margin_shift, margin100tmp * margin_rate_for_child, row_format_number_color_fact)

            sum = self.get_sum_planned_acceptance_project_quater(project, year, element_name)
            margin_sum = self.get_sum_planned_margin_project_quater(project, year, element_name)

            margin_plan = {'commitment': 0, 'reserve': 0, 'potential': 0}

            if margin_sum:
                margin_plan = margin_sum.copy()

            if not project.is_correction_project and not project.is_parent_project:

                if sum100tmp >= sum.get('commitment', 0):
                    sum100tmp_ostatok = sum100tmp - sum['commitment']
                    sum['commitment'] = 0
                    sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                else:
                    sum['commitment'] = sum['commitment'] - sum100tmp

                if margin100tmp >= margin_plan['commitment']:  # маржа если нет распределения
                    margin100tmp_ostatok = margin100tmp - margin_plan['commitment']
                    margin_sum['commitment'] = 0
                    margin_sum['reserve'] = max(margin_plan['reserve'] - margin100tmp_ostatok, 0)
                else:
                    margin_sum['commitment'] = margin_plan['commitment'] - margin100tmp

            sum_ostatok_acceptance = self.get_sum_planned_acceptance_project_from_distribution(project, year, element_name)
            new_margin_plan = self.get_sum_planned_margin_project_from_distribution(project, year, element_name, margin_plan, 1)

            if sum_ostatok_acceptance:
                sum = sum_ostatok_acceptance
            if new_margin_plan:
                margin_sum = new_margin_plan

            for key in sum:
                if not project.is_correction_project:
                    sum[key] = max(sum[key], 0)
                    margin_sum[key] = max(margin_sum[key], 0)

            if sum:
                if not next:
                    sheet.write_number(row, column + 1, sum.get('commitment', 0), row_format_number)
                    sheet.write_number(row, column + 1 + margin_shift, margin_sum.get('commitment', 0) * margin_rate_for_child, row_format_number)
                    sum75tmp += sum.get('commitment', 0)
                    sheet.write_number(row, column + 2, sum.get('reserve', 0) * koeff_reserve, row_format_number)
                    sheet.write_number(row, column + 2 + margin_shift, margin_sum.get('reserve', 0) * koeff_reserve * margin_rate_for_child, row_format_number)
                    sum50tmp += sum.get('reserve', 0) * koeff_reserve
                else:
                    sheet.write_number(row, column + 0, sum.get('commitment', 0), row_format_number)
                    sheet.write_number(row, column + 0 + margin_shift, margin_sum.get('commitment', 0) * margin_rate_for_child, row_format_number)
                    sum75tmp += sum.get('commitment', 0)
                    sheet.write_number(row, column + 1, sum.get('reserve', 0) * koeff_reserve, row_format_number)
                    sheet.write_number(row, column + 1 + margin_shift, margin_sum.get('reserve', 0) * koeff_reserve * margin_rate_for_child, row_format_number)
                    sum50tmp += sum.get('reserve', 0) * koeff_reserve

        return sum75tmpetalon, sum50tmpetalon, sum100tmp, sum75tmp, sum50tmp

    def get_month_number_rus(self, monthNameRus):
        if monthNameRus == 'Январь': return 1
        if monthNameRus == 'Февраль': return 2
        if monthNameRus == 'Март' : return 3
        if monthNameRus == 'Апрель' : return 4
        if monthNameRus == 'Май' : return 5
        if monthNameRus == 'Июнь' : return 6
        if monthNameRus == 'Июль' : return 7
        if monthNameRus == 'Август' : return 8
        if monthNameRus == 'Сентябрь' : return 9
        if monthNameRus == 'Октябрь' : return 10
        if monthNameRus == 'Ноябрь' : return 11
        if monthNameRus == 'Декабрь' : return 12
        return False

    def office_has_plan(self, project_office):
        return self.env['project_budget.budget_plan_supervisor_spec'].search([
                    ('budget_plan_supervisor_id.year', '=', YEARint),
                    ('budget_plan_supervisor_id.project_office_id', '=', project_office.id),
                ])

    def print_row_values(self, workbook, sheet, row, column,  project, margin_shift, next_margin_shift):
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
        row_format_fact_cross = workbook.add_format({
            "fg_color": '#C6E0B4',
            'border': 1,
            'diag_type': 3,
        })
        head_format_month_itogo = workbook.add_format({
            'border': 1,
            "fg_color": '#DCE6F1',
            'diag_type': 3,
        })

        if project.stage_id.code == '0':
            row_format_number.set_font_color('red')
            row_format_number_color_fact.set_font_color('red')
            head_format_month_itogo.set_font_color('red')

        if project.stage_id.code not in ('100', '100(done)'):
            row_format_number_color_fact.set_diag_type(3)

        sumQ100etalon = 0
        sumQ75etalon = 0
        sumQ50etalon = 0
        sumQ100 =0
        sumQ75 = 0
        sumQ50 = 0
        sumQ30 = 0
        sumHY100etalon =0
        sumHY75etalon = 0
        sumHY50etalon = 0
        sumHY100 = 0
        sumHY75 = 0
        sumHY50 = 0
        sumHY30 = 0
        sumYear100etalon = 0
        sumYear75etalon = 0
        sumYear50etalon = 0
        sumYear100 = 0
        sumYear75 = 0
        sumYear50 = 0
        sumYear30 = 0

        for name, shifts in plan_shift.items():  # формат ячеек в следующих годах
            sheet.write_string(row, shifts['NEXT'], "", head_format_month_itogo)
            sheet.write_string(row, shifts['NEXT'] + 1, "", row_format_number)
            sheet.write_string(row, shifts['NEXT'] + 2, "", row_format_number)
            sheet.write_string(row, shifts['AFTER_NEXT'], "", head_format_month_itogo)
            sheet.write_string(row, shifts['AFTER_NEXT'] + 1, "", row_format_number)
            sheet.write_string(row, shifts['AFTER_NEXT'] + 2, "", row_format_number)
            if name in ('revenue', 'acceptance'):
                sheet.write_string(row, shifts['AFTER_NEXT'] + 3, "", row_format_number)
                sheet.write_string(row, shifts['NEXT'] + 3, "", row_format_number)

        # печать Контрактование, с НДС
        for element in self.month_rus_name_contract_pds:
            column += 1
            sumQ75tmpetalon = sumQ50tmpetalon = sumQ100tmp = sumQ75tmp = sumQ50tmp = sumQ30tmp = 0
            shift = 0

            if 'итого' in element:
                sheet.write_string(row, column, "", head_format_month_itogo)
                column += 1
            if 'Q3' in element or 'Q4' in element or 'HY2' in element or element == 'YEAR итого':
                sheet.write_string(row, column, "", head_format_month_itogo)
                column += 1
                shift = 1

            sheet.write_string(row, column + 0, "", row_format_number_color_fact)
            sheet.write_string(row, column + 1, "", row_format_number)
            sheet.write_string(row, column + 2, "", row_format_number)
            sheet.write_string(row, column + 3, "", row_format_number)
            fact_columns.add(column)

            sumQ75tmpetalon, sumQ50tmpetalon, sumQ100tmp, sumQ75tmp, sumQ50tmp, sumQ30tmp= self.print_month_revenue_project(sheet, row, column, self.get_month_number_rus(element),
                                                                                    project, YEARint, row_format_number, row_format_number_color_fact, False)
            _, _, _, _, _, _= self.print_month_revenue_project(sheet, row, plan_shift['revenue']['NEXT'] + 1, self.get_month_number_rus(element),
                                                                                    project, YEARint + 1, row_format_number, row_format_number_color_fact, True)
            _, _, _, _, _, _= self.print_month_revenue_project(sheet, row, plan_shift['revenue']['AFTER_NEXT'] + 1, self.get_month_number_rus(element),
                                                                                    project, YEARint + 2, row_format_number, row_format_number_color_fact, True)
            sumQ75etalon += sumQ75tmpetalon
            sumQ50etalon += sumQ50tmpetalon
            sumQ100 += sumQ100tmp
            sumQ75 += sumQ75tmp
            sumQ50 += sumQ50tmp
            sumQ30 += sumQ30tmp

            if 'Q' in element: #'Q1 итого' 'Q2 итого' 'Q3 итого' 'Q4 итого'

                formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1,xl_col_to_name(column - 13 - shift),xl_col_to_name(column - 9 - shift),xl_col_to_name(column - 5 - shift))
                sheet.write_formula(row, column + 0,formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1,xl_col_to_name(column - 12 - shift),xl_col_to_name(column - 8 - shift),xl_col_to_name(column - 4 - shift))
                sheet.write_formula(row, column + 1,formula, row_format_number)
                formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1,xl_col_to_name(column - 11 - shift),xl_col_to_name(column - 7 - shift),xl_col_to_name(column - 3 - shift))
                sheet.write_formula(row, column + 2,formula, row_format_number)
                formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1,xl_col_to_name(column - 10 - shift),xl_col_to_name(column - 6 - shift),xl_col_to_name(column - 2 - shift))
                sheet.write_formula(row, column + 3,formula, row_format_number)

                sumHY100etalon += sumQ100etalon
                sumHY75etalon += sumQ75etalon
                sumHY50etalon += sumQ50etalon
                sumHY100 += sumQ100
                sumHY75 += sumQ75
                sumHY50 += sumQ50
                sumHY30 += sumQ30
                sumQ100etalon = sumQ75etalon = sumQ50etalon = sumQ100 = sumQ75  = sumQ50  = sumQ50 = 0

            if 'HY' in element:  # 'HY1/YEAR итого' 'HY2/YEAR итого'

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 22 - shift - shift),xl_col_to_name(column - 5 - shift))
                sheet.write_formula(row, column + 0, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 21 - shift - shift),xl_col_to_name(column - 4 - shift))
                sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 20 - shift - shift),xl_col_to_name(column - 3 - shift))
                sheet.write_formula(row, column + 2, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 19 - shift - shift),xl_col_to_name(column - 2 - shift))
                sheet.write_formula(row, column + 3, formula, row_format_number)


                sumYear100etalon += sumHY100etalon
                sumYear75etalon += sumHY75etalon
                sumYear50etalon += sumHY50etalon
                sumYear100 += sumHY100
                sumYear75 += sumHY75
                sumYear50 += sumHY50
                sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0

            if element == 'YEAR итого':  # 'YEAR итого'

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 48), xl_col_to_name(column - 6))
                sheet.write_formula(row, column + 0, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 47), xl_col_to_name(column - 5))
                sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 46), xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 2, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 45), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 3, formula, row_format_number)
            column += 3
        #end печать Контрактование, с НДС

        # Поступление денежных средств, с НДС
        sumYear100etalon = sumYear75etalon = sumYear50etalon = sumYear100 = sumYear75 = sumYear50 = 0
        sumQ100etalon = sumQ75etalon = sumQ50etalon = sumQ100 = sumQ75 = sumQ50 = 0
        sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0

        for element in self.month_rus_name_contract_pds:
            column += 1
            sumQ75tmpetalon = sumQ50tmpetalon = sumQ100tmp = sumQ75tmp = sumQ50tmp = 0

            shift = 0

            if 'итого' in element:
                sheet.write_string(row, column, "", head_format_month_itogo)
                column += 1
            if 'Q3' in element or 'Q4' in element or 'HY2' in element or element == 'YEAR итого':
                sheet.write_string(row, column, "", head_format_month_itogo)
                column += 1
                shift = 1

            sheet.write_string(row, column + 0, "", row_format_number_color_fact)
            sheet.write_string(row, column + 1, "", row_format_number)
            sheet.write_string(row, column + 2, "", row_format_number)
            fact_columns.add(column)


            sumQ75tmpetalon, sumQ50tmpetalon, sumQ100tmp, sumQ75tmp, sumQ50tmp = self.print_month_pds_project(sheet, row, column, self.get_month_number_rus(element)
                                                                                        ,project, YEARint, row_format_number, row_format_number_color_fact, False)

            sumQ75etalon += sumQ75tmpetalon
            sumQ50etalon += sumQ50tmpetalon
            sumQ100 += sumQ100tmp
            sumQ75 += sumQ75tmp
            sumQ50 += sumQ50tmp

            if element.find('Q') != -1:  # 'Q1 итого' 'Q2 итого' 'Q3 итого' 'Q4 итого'
                if sumQ100 != 0:      sheet.write_number(row, column + 0, sumQ100, row_format_number_color_fact)
                if sumQ75 != 0:       sheet.write_number(row, column + 1, sumQ75, row_format_number)
                if sumQ50 != 0:       sheet.write_number(row, column + 2, sumQ50, row_format_number)
                sumHY100etalon += sumQ100etalon
                sumHY75etalon += sumQ75etalon
                sumHY50etalon += sumQ50etalon
                sumHY100 += sumQ100
                sumHY75 += sumQ75
                sumHY50 += sumQ50
                sumQ100etalon = sumQ75etalon = sumQ50etalon = sumQ100 = sumQ75 = sumQ50 = 0
                formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1, xl_col_to_name(column - 10 - shift),xl_col_to_name(column - 7 - shift), xl_col_to_name(column - 4 - shift))
                sheet.write_formula(row, column + 0, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1, xl_col_to_name(column - 9 - shift),xl_col_to_name(column - 6 - shift), xl_col_to_name(column - 3 - shift))
                sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1, xl_col_to_name(column - 8 - shift),xl_col_to_name(column - 5 - shift), xl_col_to_name(column - 2 - shift))
                sheet.write_formula(row, column + 2, formula, row_format_number)

            if element.find('HY') != -1:  # 'HY1/YEAR итого' 'HY2/YEAR итого'
                sumYear100etalon += sumHY100etalon
                sumYear75etalon += sumHY75etalon
                sumYear50etalon += sumHY50etalon
                sumYear100 += sumHY100
                sumYear75 += sumHY75
                sumYear50 += sumHY50
                sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 17 - shift - shift), xl_col_to_name(column - 4 - shift))
                sheet.write_formula(row, column + 0, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 16 - shift - shift), xl_col_to_name(column - 3 - shift))
                sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 15 - shift - shift), xl_col_to_name(column - 2 - shift))
                sheet.write_formula(row, column + 2, formula, row_format_number)

            if element == 'YEAR итого':  # 'YEAR итого'
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 38), xl_col_to_name(column - 5))
                sheet.write_formula(row, column + 0, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 37), xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 36), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 2, formula, row_format_number)
            column += 2
        _, _, _, _, _ = self.print_year_pds_project(sheet, row, plan_shift['pds']['NEXT'] + 1, project, YEARint + 1, row_format_number,
                                                    row_format_number_color_fact, True)
        _, _, _, _, _ = self.print_year_pds_project(sheet, row, plan_shift['pds']['AFTER_NEXT'] + 1, project, YEARint + 2, row_format_number,
                                                    row_format_number_color_fact, True)
        # end Поступление денежных средств, с НДС

        # Валовая Выручка, без НДС
        sumYear100etalon = sumYear75etalon = sumYear50etalon = sumYear100 = sumYear75 = sumYear50 = 0
        sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0

        profitability = project.profitability

        for element in self.month_rus_name_revenue_margin:
            column += 1
            sheet.write_string(row, column, "", head_format_month_itogo)
            sheet.write_string(row, column + margin_shift, "", head_format_month_itogo)
            if 'Q3' in element or 'Q4' in element or 'HY2' in element or element == 'YEAR итого':
                addcolumn = 1
                column += 1
                sheet.write_string(row, column, "", head_format_month_itogo)
                sheet.write_string(row, column + margin_shift, "", head_format_month_itogo)
            column += 1
            sheet.write_string(row, column + 0, "", row_format_number_color_fact)
            sheet.write_string(row, column + 1, "", row_format_number)
            sheet.write_string(row, column + 2, "", row_format_number)
            sheet.write_string(row, column + 0 + margin_shift, "", row_format_number_color_fact)
            sheet.write_string(row, column + 1 + margin_shift, "", row_format_number)
            sheet.write_string(row, column + 2 + margin_shift, "", row_format_number)
            fact_columns.add(column)
            fact_columns.add(column + margin_shift)

            sumQ75etalon, sumQ50etalon, sumQ100, sumQ75, sumQ50 = self.print_quater_planned_acceptance_project(
                sheet,row,column,element,project,YEARint,row_format_number,row_format_number_color_fact,margin_shift, False
            )

            sumHY100etalon += sumQ100etalon
            sumHY75etalon += sumQ75etalon
            sumHY50etalon += sumQ50etalon
            sumHY100 += sumQ100
            sumHY75 += sumQ75
            sumHY50 += sumQ50

            if element.find('HY') != -1:  # 'HY1/YEAR итого' 'HY2/YEAR итого'
                addcolumn = 0
                if 'Q3' in element or 'Q4' in element or 'HY2' in element or element == 'YEAR итого':
                    addcolumn = 1

                sumYear100etalon += sumHY100etalon
                sumYear75etalon += sumHY75etalon
                sumYear50etalon += sumHY50etalon
                sumYear100 += sumHY100
                sumYear75 += sumHY75
                sumYear50 += sumHY50
                sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8 - addcolumn - addcolumn), xl_col_to_name(column - 4 - addcolumn))
                sheet.write_formula(row, column + 0, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 7 - addcolumn - addcolumn),  xl_col_to_name(column - 3 - addcolumn))
                sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 6 - addcolumn - addcolumn),  xl_col_to_name(column - 2 - addcolumn))
                sheet.write_formula(row, column + 2, formula, row_format_number)

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8 + margin_shift - addcolumn - addcolumn), xl_col_to_name(column - 4 + margin_shift - addcolumn))
                sheet.write_formula(row, column + 0 + margin_shift, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 7 + margin_shift - addcolumn - addcolumn),  xl_col_to_name(column - 3 + margin_shift - addcolumn))
                sheet.write_formula(row, column + 1 + margin_shift, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 6 + margin_shift - addcolumn - addcolumn),  xl_col_to_name(column - 2 + margin_shift - addcolumn))
                sheet.write_formula(row, column + 2 + margin_shift, formula, row_format_number)

            if element == 'YEAR итого':  # 'YEAR итого'
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 20), xl_col_to_name(column - 5))
                sheet.write_formula(row, column + 0, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 19), xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 18), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 2, formula, row_format_number)

                self.print_acceptance_potential(sheet, row, column, project, YEARint, row_format_number)
                self.print_acceptance_potential(sheet, row, plan_shift['acceptance']['NEXT'], project, YEARint + 1, row_format_number)
                self.print_acceptance_potential(sheet, row, plan_shift['acceptance']['AFTER_NEXT'], project, YEARint + 2, row_format_number)

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 20 + margin_shift), xl_col_to_name(column - 5 + margin_shift))
                sheet.write_formula(row, column + 0 + margin_shift, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 19 + margin_shift), xl_col_to_name(column - 4 + margin_shift))
                sheet.write_formula(row, column + 1 + margin_shift, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 18 + margin_shift), xl_col_to_name(column - 3 + margin_shift))
                sheet.write_formula(row, column + 2 + margin_shift, formula, row_format_number)

            column += 2
        _, _, _, _, _ = self.print_year_planned_acceptance_project(sheet,row,plan_shift['acceptance']['NEXT'] + 1,project,YEARint + 1,row_format_number,row_format_number_color_fact,next_margin_shift, True)
        _, _, _, _, _ = self.print_year_planned_acceptance_project(sheet,row,plan_shift['acceptance']['AFTER_NEXT'] + 1,project,YEARint + 2,row_format_number,row_format_number_color_fact,next_margin_shift, True)

        # end Валовая Выручка, без НДС

    def print_acceptance_potential(self, sheet, row, column, project, year, format):

        year_acceptance_30 = 0

        if project.step_status == 'project':
            project_id = 'projects_id'
        elif project.step_status == 'step':
            project_id = 'step_project_child_id'

        potential_acceptances = (self.env['project_budget.planned_acceptance_flow'].
                                 search(['&', '&', '&',
                                         (f'{project_id}', '=', project.id),
                                         ('date_cash', '>=', datetime.date(year, 1, 1)),
                                         ('date_cash', '<=', datetime.date(year, 12, 31)),
                                         '|', '&', ('forecast', '=', 'potential'),
                                         (f'{project_id}.stage_id.code', '!=', '0'),
                                         '&', ('forecast', '=', 'from_project'),
                                         (f'{project_id}.stage_id.code', '=', '30'),
                                         ]))
        if potential_acceptances:
            for acceptance in potential_acceptances:
                year_acceptance_30 += acceptance.distribution_sum_without_vat_ostatok
        elif project.stage_id.code == '30' and project.end_sale_project_month.year == year:
            year_acceptance_30 = project.total_amount_of_revenue

        sheet.write_number(row, column + 3, year_acceptance_30, format)

    def print_estimated_rows(self, sheet, row, format, format_cross):

        for colFormula in range(2, start_column):
            sheet.write_string(row, colFormula, '', format)

        for colFormula in list(range(start_column, 220 + start_column)) + list(range(221 + start_column, 235 + start_column)) + list(range(236 + start_column, 250 + start_column)):
            sheet.write_string(row, colFormula, '', format)

        for type in plan_shift:  # формулы расчетных планов
            column = start_column
            if type in ('revenue', 'pds'):
                shift = 0
                if type == 'revenue':
                    width = 4
                elif type == 'pds':
                    column += 87
                    width = 3
                for element in range(len(self.month_rus_name_contract_pds)):
                    if element in [3, 7, 8]:  # учитываем колонки планов
                        shift += 1
                    elif element in [12, 16, 17, 18]:  # учитываем колонки планов 6+6
                        shift += 2
                    formula_fact = '={1}{0}'.format(
                        row,
                        xl_col_to_name(column + shift + element * width),
                    )
                    formula_forecast = '={1}{0}*$D$1+{2}{0}*$D$2'.format(
                        row,
                        xl_col_to_name(column + shift + element * width + 1),
                        xl_col_to_name(column + shift + element * width + 2),
                    )
                    sheet.write_formula(
                        row,
                        column + shift + element * width,
                        formula_fact,
                        format
                    )
                    sheet.merge_range(
                        row,
                        column + shift + element * width + 1,
                        row,
                        column + shift + element * width + 2,
                        formula_forecast,
                        format
                    )
                    if type == 'revenue':
                        sheet.write_string(row, column + shift + element * width + 3, '',
                                           format_cross)
            else:
                shift = 0
                if type == 'acceptance':
                    column += 156
                    width = 4
                elif type == 'margin':
                    column += 189
                    width = 4
                for element in range(len(self.month_rus_name_revenue_margin)):
                    if element in [3, 4, 5, 6]:  # учитываем колонки планов
                        shift += 1
                    formula_fact = '={1}{0}'.format(
                        row,
                        xl_col_to_name(column + shift + element * width),
                    )
                    formula_forecast = '={1}{0}*$D$1+{2}{0}*$D$2'.format(
                        row,
                        xl_col_to_name(column + shift + element * width + 1),
                        xl_col_to_name(column + shift + element * width + 2),
                    )
                    sheet.write_formula(
                        row,
                        column + shift + element * width,
                        formula_fact,
                        format
                    )
                    sheet.merge_range(
                        row,
                        column + shift + element * width + 1,
                        row,
                        column + shift + element * width + 2,
                        formula_forecast,
                        format
                    )
                if type == 'acceptance':
                    sheet.write_string(row, column + shift + element * width + 3, '',
                                       format_cross)
        for type,shifts in plan_shift.items():
            formula = '={1}{0}*$D$1+{2}{0}*$D$2'.format(
                row,
                xl_col_to_name(shifts['NEXT'] + 1),
                xl_col_to_name(shifts['NEXT'] + 2),
            )
            sheet.merge_range(row, shifts['NEXT'] + 1, row, shifts['NEXT'] + 2, formula, format)
            formula = '={1}{0}*$D$1+{2}{0}*$D$2'.format(
                row,
                xl_col_to_name(shifts['AFTER_NEXT'] + 1),
                xl_col_to_name(shifts['AFTER_NEXT'] + 2),
            )
            sheet.merge_range(row, shifts['AFTER_NEXT'] + 1, row, shifts['AFTER_NEXT'] + 2, formula, format)
            if type in ('revenue', 'acceptance'):
                sheet.write_string(row, shifts['NEXT'] + 3, '', format_cross)
                sheet.write_string(row, shifts['AFTER_NEXT'] + 3, '', format_cross)

    def print_row(self, sheet, workbook, companies, project_offices, key_account_managers, stages, budget, row, level, project_office_ids):
        global YEARint
        global dict_formula
        global use_6_6
        head_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_size': 10,
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
            "font_size": 8,
        })
        row_format_date_month = workbook.add_format({
            'border': 1,
            'font_size': 10,
        })

        row_format_manager = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#D9D9D9',
        })
        row_format_manager.set_num_format('#,##0')

        row_format_manager_estimated_plan = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#FDE9D9',
            "num_format": '#,##0',
            'align': 'center',
        })

        row_format_manager_estimated_plan_left = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#FDE9D9',
            "num_format": '#,##0',
        })

        row_format_manager_estimated_plan_cross = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#FDE9D9',
            "num_format": '#,##0',
            'align': 'center',
            'diag_type': 3,

        })

        row_format_office = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#8DB4E2',
        })
        row_format_office.set_num_format('#,##0')

        row_format_office_estimated_plan = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#CCC0DA',
            "num_format": '#,##0',
            'align': 'center',
        })

        row_format_office_estimated_plan_left = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#CCC0DA',
            "num_format": '#,##0',
        })

        row_format_office_estimated_plan_cross = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#CCC0DA',
            "num_format": '#,##0',
            'align': 'center',
            'diag_type': 3,
        })

        row_format_plan = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#DCE6F1',
            "num_format": '#,##0',
        })

        row_format_probability = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#F2DCDB',
            "num_format": '#,##0',
        })

        row_format_date_month.set_num_format('mmm yyyy')

        row_format = workbook.add_format({
            'border': 1,
            'font_size': 10
        })

        row_format_canceled_project = workbook.add_format({
            'border': 1,
            'font_size': 10
        })
        row_format_canceled_project.set_font_color('red')

        row_format_number = workbook.add_format({
            'border': 1,
            'font_size': 10,
        })
        row_format_number.set_num_format('#,##0')

        row_format_date = workbook.add_format({
            'border': 1,
            'font_size': 10,
        })
        row_format_date.set_num_format('dd.mm.yyyy')

        row_format_number_canceled_project = workbook.add_format({
            'border': 1,
            'font_size': 10,
        })
        row_format_number_canceled_project.set_num_format('#,##0')
        row_format_number_canceled_project.set_font_color('red')

        row_format_date_canceled_project = workbook.add_format({
            'border': 1,
            'font_size': 10,
        })
        row_format_date_canceled_project.set_num_format('dd.mm.yyyy')
        row_format_date_canceled_project.set_font_color('red')


        row_format_number_itogo = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#A9D08E',

        })
        row_format_number_itogo.set_num_format('#,##0')

        head_format_month_itogo = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "bold": True,
            "fg_color": '#DCE6F1',
            "font_size": 10,
        })
        head_format_month_itogo.set_num_format('#,##0')

        row_format_plan_cross = workbook.add_format({
            'border': 1,
            "fg_color": '#DCE6F1',
            'diag_type': 3
        })

        row_format_fact_cross = workbook.add_format({
            "fg_color": '#C6E0B4',
            'border': 1,
            'diag_type': 3,
        })

        row_format_company_estimated_plan = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#FFFF00',
            "num_format": '#,##0',
            'align': 'center',
        })

        row_format_company_estimated_plan_left = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#FFFF00',
            "num_format": '#,##0',
        })

        row_format_company_estimated_plan_cross = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#FFFF00',
            "num_format": '#,##0',
            'align': 'center',
            'diag_type': 3,
        })

        # if isdebug:
        #     logger.info(f' def print_row | office_parent_id = { office_parent_id }')

        #project_offices = self.env['project_budget.project_office'].search([],order='name')  # для сортировки так делаем + берем сначала только верхние элементы

        isFoundProjectsByCompany = False
        isFoundProjectsByOffice = False
        isFoundProjectsByManager = False
        begRowProjectsByManager = 0

        cur_budget_projects = self.env['project_budget.projects'].search([
            '&',
            ('commercial_budget_id', '=', budget.id),
            '|', '&', ('step_status', '=', 'step'),
            ('step_project_parent_id.project_have_steps', '=', True),
            '&', ('step_status', '=', 'project'),
            ('project_have_steps', '=', False),
        ], order='project_id asc')

        # cur_project_offices = project_offices.filtered(lambda r: r in cur_budget_projects.project_office_id or r in {office.parent_id for office in cur_budget_projects.project_office_id if office.parent_id in project_offices})
        cur_project_offices = project_offices
        cur_project_managers = key_account_managers.filtered(lambda r: r in cur_budget_projects.key_account_manager_id)
        cur_estimated_probabilities = stages.filtered(lambda r: r in cur_budget_projects.stage_id)
        cur_companies = companies.filtered(lambda r: r in cur_project_offices.company_id)
        # print('cur_budget_projects=',cur_budget_projects)
        # print('****')
        # print('project_offices=',project_offices)
        # print('project_managers=',project_managers)
        # print('cur_project_offices=',cur_project_offices)
        # print('cur_project_managers=', cur_project_managers)
        # print('cur_estimated_probabilities=', cur_estimated_probabilities)

        for company in cur_companies:
            print('company =', company.name)
            isFoundProjectsByCompany = False
            formulaCompany = '=sum(0'

            row0 = row

            for project_office in cur_project_offices.filtered(lambda r: r in (office for office in self.env[
                'project_budget.project_office'].search([('company_id', '=', company.id), ]))):
                print('project_office =', project_office.name)

                child_project_offices = self.env['project_budget.project_office'].search(
                    [('parent_id', '=', project_office.id)], order='name')

                row0 = self.print_row(sheet, workbook, companies, child_project_offices, key_account_managers, stages, budget, row, level, project_office_ids)

                isFoundProjectsByOffice = False
                if row0 != row:
                    isFoundProjectsByOffice = True

                row = row0

                formulaProjectOffice = '=sum(0'

                for project_manager in cur_project_managers.filtered(lambda emp: emp.company_id == company):

                    print('project_manager =', project_manager.name)
                    isFoundProjectsByManager = False
                    begRowProjectsByManager = 0
                    formulaProjectManager = '=sum(0'
                    column = -1

                    for stage in cur_estimated_probabilities:
                        isFoundProjectsByProbability = False
                        begRowProjectsByProbability = 0

                        for spec in cur_budget_projects:
                            if (spec.id not in dict_formula['printed_projects']
                                and spec.project_office_id == project_office
                                and spec.key_account_manager_id == project_manager
                                and spec.stage_id == stage
                                and self.isProjectinYear(spec) == True
                                and spec.vgo == '-'
                            ):
                                cur_project_rate = self.get_currency_rate_by_project(spec)

                                if begRowProjectsByManager == 0:
                                    begRowProjectsByManager = row

                                if begRowProjectsByProbability == 0:
                                    begRowProjectsByProbability = row

                                isFoundProjectsByCompany = True
                                isFoundProjectsByOffice = True
                                isFoundProjectsByManager = True
                                isFoundProjectsByProbability = True

                                row += 1
                                sheet.set_row(row, False, False, {'hidden': 1, 'level': level + 2})
                                cur_row_format = row_format
                                cur_row_format_number = row_format_number
                                cur_row_format_date = row_format_date
                                if spec.stage_id.code == '0':
                                    cur_row_format = row_format_canceled_project
                                    cur_row_format_number = row_format_number_canceled_project
                                    cur_row_format_date = row_format_date_canceled_project
                                column = 0
                                sheet.write_string(row, column, spec.project_office_id.name, cur_row_format)
                                column += 1
                                sheet.write_string(row, column, spec.key_account_manager_id.name, cur_row_format)
                                column += 1
                                sheet.write_string(row, column, spec.partner_id.name, cur_row_format)
                                column += 1
                                sheet.write_string(row, column, (spec.essence_project or ''), cur_row_format)
                                column += 1
                                if spec.step_status == 'step':
                                    sheet.write_string(row, column, (spec.step_project_parent_id.project_id or '') + ' | ' + spec.project_id, cur_row_format)
                                else:
                                    sheet.write_string(row, column, spec.project_id, cur_row_format)
                                column += 1
                                sheet.write_string(row, column, (spec.step_project_number or ''), cur_row_format)
                                column += 1
                                sheet.write_number(row, column, spec.total_amount_of_revenue_with_vat*cur_project_rate, cur_row_format_number)
                                column += 1
                                if spec.stage_id.code == '100':
                                    sheet.write_datetime(row, column, spec.end_presale_project_month, cur_row_format_date)
                                else:
                                    sheet.write(row, column, None, cur_row_format)
                                column += 1
                                sheet.write_number(row, column, spec.profitability, cur_row_format_number)
                                column += 1
                                sheet.write_string(row, column, '', head_format_1)
                                self.print_row_values(workbook, sheet, row, column, spec, 33, 4)
                                dict_formula['printed_projects'].add(spec.id)

                        if isFoundProjectsByProbability:
                            row += 1
                            column = 0
                            sheet.merge_range(row, column, row, column + 3, project_manager.name + ' ' + stage.code
                                               + ' %', row_format_probability)
                            sheet.set_row(row, False, False, {'hidden': 1, 'level': level + 2})

                            formulaProjectManager = formulaProjectManager + ',{0}' + str(row + 1)
                            for colFormula in range(2, start_column):
                                sheet.write_string(row, colFormula, '', row_format_probability)
                            for colFormula in list(range(start_column, 220 + start_column)) + list(range(221 + start_column, 235 + start_column)) + list(range(236 + start_column, 250 + start_column)):
                                formula = '=sum({2}{0}:{2}{1})'.format(begRowProjectsByProbability + 2, row,
                                                                       xl_col_to_name(colFormula))
                                if colFormula in fact_columns and stage.code not in ('100', '100(done)'):
                                    sheet.write_formula(row, colFormula, formula, row_format_fact_cross)  # кресты в фактах где вероятности < 100
                                else:
                                    sheet.write_formula(row, colFormula, formula, row_format_probability)

                            for type in plan_shift: # кресты в планах
                                for c in plan_shift[type].values():
                                    sheet.write_string(row, c, '', row_format_plan_cross)

                    if isFoundProjectsByManager:
                        row += 1
                        column = 0
                        sheet.merge_range(row, column, row, column + 3, 'ИТОГО: ' + project_manager.name, row_format_manager)
                        sheet.set_row(row, False, False, {'hidden': 1, 'level': level + 1})
                        # print('setrow manager  row = ', row)
                        # print('setrow manager level = ', level)

                        formulaProjectOffice = formulaProjectOffice + ',{0}'+str(row + 1)

                        for colFormula in range(2, start_column):
                            sheet.write_string(row, colFormula, '', row_format_manager)

                        for colFormula in list(range(start_column, 220 + start_column)) + list(range(221 + start_column, 235 + start_column)) + list(range(236 + start_column, 250 + start_column)):
                            formula = formulaProjectManager.format(xl_col_to_name(colFormula)) + ')'
                            sheet.write_formula(row, colFormula, formula, row_format_manager)

                        # расчетный план КАМа
                        row += 1
                        column = 0
                        sheet.merge_range(row, column, row, column + 3, 'ИТОГО: Расчетный План по ' + project_manager.name, row_format_manager_estimated_plan_left)
                        sheet.set_row(row, False, False, {'hidden': 1, 'level': level})

                        self.print_estimated_rows(sheet, row, row_format_manager_estimated_plan, row_format_manager_estimated_plan_cross)

                        for type in plan_shift: # кресты в планах
                            for c in plan_shift[type].values():
                                sheet.write_string(row - 1, c, '', row_format_plan_cross)
                                sheet.write_string(row, c, '', row_format_plan_cross)

                        # планы КАМов
                        plan_revenue = self.env['project_budget.budget_plan_kam_spec'].search([
                            ('budget_plan_kam_id.year', '=', YEARint),
                            ('budget_plan_kam_id.key_account_manager_id', '=', project_manager.id),
                            ('type_row', '=', 'contracting'),
                        ])
                        plan_pds = self.env['project_budget.budget_plan_kam_spec'].search([
                            ('budget_plan_kam_id.year', '=', YEARint),
                            ('budget_plan_kam_id.key_account_manager_id', '=', project_manager.id),
                            ('type_row', '=', 'cash'),
                        ])
                        plan_acceptance = self.env['project_budget.budget_plan_kam_spec'].search([
                            ('budget_plan_kam_id.year', '=', YEARint),
                            ('budget_plan_kam_id.key_account_manager_id', '=', project_manager.id),
                            ('type_row', '=', 'acceptance'),
                        ])
                        plan_margin = self.env['project_budget.budget_plan_kam_spec'].search([
                            ('budget_plan_kam_id.year', '=', YEARint),
                            ('budget_plan_kam_id.key_account_manager_id', '=', project_manager.id),
                            ('type_row', '=', 'margin_income'),
                        ])

                        plan_revenue_next = self.env['project_budget.budget_plan_kam_spec'].search([
                            ('budget_plan_kam_id.year', '=', YEARint + 1),
                            ('budget_plan_kam_id.key_account_manager_id', '=', project_manager.id),
                            ('type_row', '=', 'contracting'),
                        ])
                        plan_pds_next = self.env['project_budget.budget_plan_kam_spec'].search([
                            ('budget_plan_kam_id.year', '=', YEARint + 1),
                            ('budget_plan_kam_id.key_account_manager_id', '=', project_manager.id),
                            ('type_row', '=', 'cash'),
                        ])
                        plan_acceptance_next = self.env['project_budget.budget_plan_kam_spec'].search([
                            ('budget_plan_kam_id.year', '=', YEARint + 1),
                            ('budget_plan_kam_id.key_account_manager_id', '=', project_manager.id),
                            ('type_row', '=', 'acceptance'),
                        ])
                        plan_margin_next = self.env['project_budget.budget_plan_kam_spec'].search([
                            ('budget_plan_kam_id.year', '=', YEARint + 1),
                            ('budget_plan_kam_id.key_account_manager_id', '=', project_manager.id),
                            ('type_row', '=', 'margin_income'),
                        ])
                        plan_revenue_after_next = self.env['project_budget.budget_plan_kam_spec'].search([
                            ('budget_plan_kam_id.year', '=', YEARint + 2),
                            ('budget_plan_kam_id.key_account_manager_id', '=', project_manager.id),
                            ('type_row', '=', 'contracting'),
                        ])
                        plan_pds_after_next = self.env['project_budget.budget_plan_kam_spec'].search([
                            ('budget_plan_kam_id.year', '=', YEARint + 2),
                            ('budget_plan_kam_id.key_account_manager_id', '=', project_manager.id),
                            ('type_row', '=', 'cash'),
                        ])
                        plan_acceptance_after_next = self.env['project_budget.budget_plan_kam_spec'].search([
                            ('budget_plan_kam_id.year', '=', YEARint + 2),
                            ('budget_plan_kam_id.key_account_manager_id', '=', project_manager.id),
                            ('type_row', '=', 'acceptance'),
                        ])
                        plan_margin_after_next = self.env['project_budget.budget_plan_kam_spec'].search([
                            ('budget_plan_kam_id.year', '=', YEARint + 2),
                            ('budget_plan_kam_id.key_account_manager_id', '=', project_manager.id),
                            ('type_row', '=', 'margin_income'),
                        ])

                        for plan in (plan_revenue, plan_pds, plan_acceptance, plan_margin):
                            if plan.q3_plan_6_6 != 0 or plan.q4_plan_6_6 != 0:
                                use_6_6 = True

                        for plan in (
                            {'column': plan_shift['revenue']['Q1'], 'formula': f'{plan_revenue.q1_plan}'},
                            {'column': plan_shift['revenue']['Q2'], 'formula': f'{plan_revenue.q2_plan}'},
                            {'column': plan_shift['revenue']['HY1'], 'formula': f'{plan_revenue.q1_plan} + {plan_revenue.q2_plan}'},
                            {'column': plan_shift['revenue']['Q3'], 'formula': f'{plan_revenue.q3_plan}'},
                            {'column': plan_shift['revenue']['Q3 6+6'], 'formula': f'{plan_revenue.q3_plan_6_6}'},
                            {'column': plan_shift['revenue']['Q4'], 'formula': f'{plan_revenue.q4_plan}'},
                            {'column': plan_shift['revenue']['Q4 6+6'], 'formula': f'{plan_revenue.q4_plan_6_6}'},
                            {'column': plan_shift['revenue']['HY2'],
                             'formula': f'{plan_revenue.q3_plan} + {plan_revenue.q4_plan}'},
                            {'column': plan_shift['revenue']['HY2 6+6'], 'formula': f'{plan_revenue.q3_plan_6_6} + {plan_revenue.q4_plan_6_6}'},
                            {'column': plan_shift['revenue']['Y'], 'formula': f'{plan_revenue.q1_plan} + {plan_revenue.q2_plan} + {plan_revenue.q3_plan} + {plan_revenue.q4_plan}'},
                            {'column': plan_shift['revenue']['Y 6+6'], 'formula': f'{plan_revenue.q3_plan_6_6} + {plan_revenue.q4_plan_6_6} + {plan_revenue.q1_fact} + {plan_revenue.q2_fact}'},
                            {'column': plan_shift['pds']['Q1'], 'formula': f'{plan_pds.q1_plan}'},
                            {'column': plan_shift['pds']['Q2'], 'formula': f'{plan_pds.q2_plan}'},
                            {'column': plan_shift['pds']['HY1'], 'formula': f'{plan_pds.q1_plan} + {plan_pds.q2_plan}'},
                            {'column': plan_shift['pds']['Q3'], 'formula': f'{plan_pds.q3_plan}'},
                            {'column': plan_shift['pds']['Q3 6+6'], 'formula': f'{plan_pds.q3_plan_6_6}'},
                            {'column': plan_shift['pds']['Q4'], 'formula': f'{plan_pds.q4_plan}'},
                            {'column': plan_shift['pds']['Q4 6+6'], 'formula': f'{plan_pds.q4_plan_6_6}'},
                            {'column': plan_shift['pds']['HY2'],
                             'formula': f'{plan_pds.q3_plan} + {plan_pds.q4_plan}'},
                            {'column': plan_shift['pds']['HY2 6+6'], 'formula': f'{plan_pds.q3_plan_6_6} + {plan_pds.q4_plan_6_6}'},
                            {'column': plan_shift['pds']['Y'], 'formula': f'{plan_pds.q1_plan} + {plan_pds.q2_plan} + {plan_pds.q3_plan} + {plan_pds.q4_plan}'},
                            {'column': plan_shift['pds']['Y 6+6'], 'formula': f'{plan_pds.q3_plan_6_6} + {plan_pds.q4_plan_6_6} + {plan_pds.q1_fact} + {plan_pds.q2_fact}'},
                            {'column': plan_shift['acceptance']['Q1'], 'formula': f'{plan_acceptance.q1_plan}'},
                            {'column': plan_shift['acceptance']['Q2'], 'formula': f'{plan_acceptance.q2_plan}'},
                            {'column': plan_shift['acceptance']['HY1'],
                             'formula': f'{plan_acceptance.q1_plan} + {plan_acceptance.q2_plan}'},
                            {'column': plan_shift['acceptance']['Q3'], 'formula': f'{plan_acceptance.q3_plan}'},
                            {'column': plan_shift['acceptance']['Q3 6+6'], 'formula': f'{plan_acceptance.q3_plan_6_6}'},
                            {'column': plan_shift['acceptance']['Q4'], 'formula': f'{plan_acceptance.q4_plan}'},
                            {'column': plan_shift['acceptance']['Q4 6+6'], 'formula': f'{plan_acceptance.q4_plan_6_6}'},
                            {'column': plan_shift['acceptance']['HY2'],
                             'formula': f'{plan_acceptance.q3_plan} + {plan_acceptance.q4_plan}'},
                            {'column': plan_shift['acceptance']['HY2 6+6'], 'formula': f'{plan_acceptance.q3_plan_6_6} + {plan_acceptance.q4_plan_6_6}'},
                            {'column': plan_shift['acceptance']['Y'],
                             'formula': f'{plan_acceptance.q1_plan} + {plan_acceptance.q2_plan} + {plan_acceptance.q3_plan} + {plan_acceptance.q4_plan}'},
                            {'column': plan_shift['acceptance']['Y 6+6'], 'formula': f'{plan_acceptance.q3_plan_6_6} + {plan_acceptance.q4_plan_6_6} + {plan_acceptance.q1_fact} + {plan_acceptance.q2_fact}'},
                            {'column': plan_shift['margin']['Q1'], 'formula': f'{plan_margin.q1_plan}'},
                            {'column': plan_shift['margin']['Q2'], 'formula': f'{plan_margin.q2_plan}'},
                            {'column': plan_shift['margin']['HY1'],
                             'formula': f'{plan_margin.q1_plan} + {plan_margin.q2_plan}'},
                            {'column': plan_shift['margin']['Q3'], 'formula': f'{plan_margin.q3_plan}'},
                            {'column': plan_shift['margin']['Q3 6+6'], 'formula': f'{plan_margin.q3_plan_6_6}'},
                            {'column': plan_shift['margin']['Q4'], 'formula': f'{plan_margin.q4_plan}'},
                            {'column': plan_shift['margin']['Q4 6+6'], 'formula': f'{plan_margin.q4_plan_6_6}'},
                            {'column': plan_shift['margin']['HY2'],
                             'formula': f'{plan_margin.q3_plan} + {plan_margin.q4_plan}'},
                            {'column': plan_shift['margin']['HY2 6+6'], 'formula': f'{plan_margin.q3_plan_6_6} + {plan_margin.q4_plan_6_6}'},
                            {'column': plan_shift['margin']['Y'],
                             'formula': f'{plan_margin.q1_plan} + {plan_margin.q2_plan} + {plan_margin.q3_plan} + {plan_margin.q4_plan}'},
                            {'column': plan_shift['margin']['Y 6+6'], 'formula': f'{plan_margin.q3_plan_6_6} + {plan_margin.q4_plan_6_6} + {plan_margin.q1_fact} + {plan_margin.q2_fact}'},
                            {'column': plan_shift['revenue']['NEXT'],
                             'formula': f'{plan_revenue_next.q1_plan + plan_revenue_next.q2_plan + plan_revenue_next.q3_plan + plan_revenue_next.q4_plan}'},
                            {'column': plan_shift['pds']['NEXT'],
                             'formula': f'{plan_pds_next.q1_plan + plan_pds_next.q2_plan + plan_pds_next.q3_plan + plan_pds_next.q4_plan}'},
                            {'column': plan_shift['acceptance']['NEXT'],
                             'formula': f'{plan_acceptance_next.q1_plan + plan_acceptance_next.q2_plan + plan_acceptance_next.q3_plan + plan_acceptance_next.q4_plan}'},
                            {'column': plan_shift['margin']['NEXT'],
                             'formula': f'{plan_margin_next.q1_plan + plan_margin_next.q2_plan + plan_margin_next.q3_plan + plan_margin_next.q4_plan}'},
                            {'column': plan_shift['revenue']['AFTER_NEXT'],
                             'formula': f'{plan_revenue_after_next.q1_plan + plan_revenue_after_next.q2_plan + plan_revenue_after_next.q3_plan + plan_revenue_after_next.q4_plan}'},
                            {'column': plan_shift['pds']['AFTER_NEXT'],
                             'formula': f'{plan_pds_after_next.q1_plan + plan_pds_after_next.q2_plan + plan_pds_after_next.q3_plan + plan_pds_after_next.q4_plan}'},
                            {'column': plan_shift['acceptance']['AFTER_NEXT'],
                             'formula': f'{plan_acceptance_after_next.q1_plan + plan_acceptance_after_next.q2_plan + plan_acceptance_after_next.q3_plan + plan_acceptance_after_next.q4_plan}'},
                            {'column': plan_shift['margin']['AFTER_NEXT'],
                             'formula': f'{plan_margin_after_next.q1_plan + plan_margin_after_next.q2_plan + plan_margin_after_next.q3_plan + plan_margin_after_next.q4_plan}'},
                        ):

                            kam_formula = '(' + plan['formula'] + ')'

                            sheet.write_formula(row, plan['column'], kam_formula, row_format_plan)
                            sheet.set_row(row, False, False, {'hidden': 1, 'level': level + 1})

                        # for plan in (
                        #         {'column': plan_shift['revenue']['HY1'],
                        #          'formula': f"={xl_col_to_name(plan_shift['revenue']['Q1'])}{row + 1} + {xl_col_to_name(plan_shift['revenue']['Q2'])}{row + 1}"},
                        #         {'column': plan_shift['revenue']['HY2'],
                        #          'formula': f"={xl_col_to_name(plan_shift['revenue']['Q3'])}{row + 1} + {xl_col_to_name(plan_shift['revenue']['Q4'])}{row + 1}"},
                        #         {'column': plan_shift['revenue']['Y'],
                        #          'formula': f"={xl_col_to_name(plan_shift['revenue']['HY1'])}{row + 1} + {xl_col_to_name(plan_shift['revenue']['HY2'])}{row + 1}"},
                        #         {'column': plan_shift['pds']['HY1'],
                        #          'formula': f"={xl_col_to_name(plan_shift['pds']['Q1'])}{row + 1} + {xl_col_to_name(plan_shift['pds']['Q2'])}{row + 1}"},
                        #         {'column': plan_shift['pds']['HY2'],
                        #          'formula': f"={xl_col_to_name(plan_shift['pds']['Q3'])}{row + 1} + {xl_col_to_name(plan_shift['pds']['Q4'])}{row + 1}"},
                        #         {'column': plan_shift['pds']['Y'],
                        #          'formula': f"={xl_col_to_name(plan_shift['pds']['HY1'])}{row + 1} + {xl_col_to_name(plan_shift['pds']['HY2'])}{row + 1}"},
                        #         {'column': plan_shift['acceptance']['HY1'],
                        #          'formula': f"={xl_col_to_name(plan_shift['acceptance']['Q1'])}{row + 1} + {xl_col_to_name(plan_shift['acceptance']['Q2'])}{row + 1}"},
                        #         {'column': plan_shift['acceptance']['HY2'],
                        #          'formula': f"={xl_col_to_name(plan_shift['acceptance']['Q3'])}{row + 1} + {xl_col_to_name(plan_shift['acceptance']['Q4'])}{row + 1}"},
                        #         {'column': plan_shift['acceptance']['Y'],
                        #          'formula': f"={xl_col_to_name(plan_shift['acceptance']['HY1'])}{row + 1} + {xl_col_to_name(plan_shift['acceptance']['HY2'])}{row + 1}"},
                        #         {'column': plan_shift['margin']['HY1'],
                        #          'formula': f"={xl_col_to_name(plan_shift['margin']['Q1'])}{row + 1} + {xl_col_to_name(plan_shift['margin']['Q2'])}{row + 1}"},
                        #         {'column': plan_shift['margin']['HY2'],
                        #          'formula': f"={xl_col_to_name(plan_shift['margin']['Q3'])}{row + 1} + {xl_col_to_name(plan_shift['margin']['Q4'])}{row + 1}"},
                        #         {'column': plan_shift['margin']['Y'],
                        #          'formula': f"={xl_col_to_name(plan_shift['margin']['HY1'])}{row + 1} + {xl_col_to_name(plan_shift['margin']['HY2'])}{row + 1}"},
                        # ):
                        #     sheet.write_formula(row, plan['column'], plan['formula'], row_format_plan)

                if self.office_has_plan(project_office):
                    isFoundProjectsByOffice = True
                    isFoundProjectsByCompany = True

                if isFoundProjectsByOffice:
                    row += 1
                    column = 0
                    sheet.merge_range(row, column, row, column + 3, 'ИТОГО ' + project_office.name, row_format_office)
                    sheet.set_row(row, False, False, {'hidden': 1, 'level': level})

                    if not project_office.parent_id:
                        formulaCompany += ',{0}' + f'{row + 1}'

                    str_project_office_id = 'project_office_' + str(int(project_office.parent_id))
                    if str_project_office_id in dict_formula:
                        dict_formula[str_project_office_id] = dict_formula[str_project_office_id] + ',{0}' + str(row+1)
                    else:
                        dict_formula[str_project_office_id] = ',{0}'+str(row+1)

                    if not project_office.parent_id:  # корневой офис добавляем сразу
                        dict_formula['offices_lines'].add(row+1)
                    else:  # ищем всех родителей и проверяем есть ли они в выбранных офисах, если нет, добавляем
                        parent = project_office.parent_id
                        while parent:
                            if parent.id in project_office_ids:
                                break
                            else:
                                parent = parent.parent_id
                        else:
                            dict_formula['offices_lines'].add(row + 1)

                    str_project_office_id = 'project_office_' + str(int(project_office.id))

                    if str_project_office_id in dict_formula:
                        formulaProjectOffice = formulaProjectOffice + dict_formula[str_project_office_id]+')'
                    else:
                        formulaProjectOffice = formulaProjectOffice + ')'

                    for colFormula in range(2, start_column):
                        sheet.write_string(row, colFormula, '', row_format_office)

                    for colFormula in list(range(start_column, 220 + start_column)) + list(range(221 + start_column, 235 + start_column)) + list(range(236 + start_column, 250 + start_column)):
                        formula = formulaProjectOffice.format(xl_col_to_name(colFormula))
                        # print('formula = ', formula)
                        sheet.write_formula(row, colFormula, formula, row_format_office)

                    for type in plan_shift:  # кресты в планах
                        for c in plan_shift[type].values():
                            sheet.write_string(row, c, '', row_format_plan_cross)

                    # расчетный план офиса
                    row += 1
                    column = 0
                    # sheet.set_row(row, False, False, {'hidden': 1, 'level': 1})
                    # print('setrow level1 row = ', row)
                    sheet.merge_range(row, column, row, column + 3, 'ИТОГО ' + project_office.name  + ' Расчетный План:', row_format_office_estimated_plan_left)
                    self.print_estimated_rows(sheet, row, row_format_office_estimated_plan,
                                              row_format_office_estimated_plan_cross)

                    # планы офисов
                    plan_revenue = self.env['project_budget.budget_plan_supervisor_spec'].search([
                        ('budget_plan_supervisor_id.year', '=', YEARint),
                        ('budget_plan_supervisor_id.project_office_id', '=', project_office.id),
                        ('type_row', '=', 'contracting'),
                    ])
                    plan_pds = self.env['project_budget.budget_plan_supervisor_spec'].search([
                        ('budget_plan_supervisor_id.year', '=', YEARint),
                        ('budget_plan_supervisor_id.project_office_id', '=', project_office.id),
                        ('type_row', '=', 'cash'),
                    ])
                    plan_acceptance = self.env['project_budget.budget_plan_supervisor_spec'].search([
                        ('budget_plan_supervisor_id.year', '=', YEARint),
                        ('budget_plan_supervisor_id.project_office_id', '=', project_office.id),
                        ('type_row', '=', 'acceptance'),
                    ])
                    plan_margin = self.env['project_budget.budget_plan_supervisor_spec'].search([
                        ('budget_plan_supervisor_id.year', '=', YEARint),
                        ('budget_plan_supervisor_id.project_office_id', '=', project_office.id),
                        ('type_row', '=', 'margin_income'),
                    ])
                    plan_revenue_next = self.env['project_budget.budget_plan_supervisor_spec'].search([
                        ('budget_plan_supervisor_id.year', '=', YEARint + 1),
                        ('budget_plan_supervisor_id.project_office_id', '=', project_office.id),
                        ('type_row', '=', 'contracting'),
                    ])
                    plan_pds_next = self.env['project_budget.budget_plan_supervisor_spec'].search([
                        ('budget_plan_supervisor_id.year', '=', YEARint + 1),
                        ('budget_plan_supervisor_id.project_office_id', '=', project_office.id),
                        ('type_row', '=', 'cash'),
                    ])
                    plan_acceptance_next = self.env['project_budget.budget_plan_supervisor_spec'].search([
                        ('budget_plan_supervisor_id.year', '=', YEARint + 1),
                        ('budget_plan_supervisor_id.project_office_id', '=', project_office.id),
                        ('type_row', '=', 'acceptance'),
                    ])
                    plan_margin_next = self.env['project_budget.budget_plan_supervisor_spec'].search([
                        ('budget_plan_supervisor_id.year', '=', YEARint + 1),
                        ('budget_plan_supervisor_id.project_office_id', '=', project_office.id),
                        ('type_row', '=', 'margin_income'),
                    ])
                    plan_revenue_after_next = self.env['project_budget.budget_plan_supervisor_spec'].search([
                        ('budget_plan_supervisor_id.year', '=', YEARint + 2),
                        ('budget_plan_supervisor_id.project_office_id', '=', project_office.id),
                        ('type_row', '=', 'contracting'),
                    ])
                    plan_pds_after_next = self.env['project_budget.budget_plan_supervisor_spec'].search([
                        ('budget_plan_supervisor_id.year', '=', YEARint + 2),
                        ('budget_plan_supervisor_id.project_office_id', '=', project_office.id),
                        ('type_row', '=', 'cash'),
                    ])
                    plan_acceptance_after_next = self.env['project_budget.budget_plan_supervisor_spec'].search([
                        ('budget_plan_supervisor_id.year', '=', YEARint + 2),
                        ('budget_plan_supervisor_id.project_office_id', '=', project_office.id),
                        ('type_row', '=', 'acceptance'),
                    ])
                    plan_margin_after_next = self.env['project_budget.budget_plan_supervisor_spec'].search([
                        ('budget_plan_supervisor_id.year', '=', YEARint + 2),
                        ('budget_plan_supervisor_id.project_office_id', '=', project_office.id),
                        ('type_row', '=', 'margin_income'),
                    ])

                    for plan in (plan_revenue, plan_pds, plan_acceptance, plan_margin):
                        if plan.q3_plan_6_6 != 0 or plan.q4_plan_6_6 != 0:
                            use_6_6 = True

                    for plan in (
                        {'column': plan_shift['revenue']['Q1'], 'formula': f'{plan_revenue.q1_plan}'},
                        {'column': plan_shift['revenue']['Q2'], 'formula': f'{plan_revenue.q2_plan}'},
                        {'column': plan_shift['revenue']['HY1'],
                         'formula': f'{plan_revenue.q1_plan} + {plan_revenue.q2_plan}'},
                        {'column': plan_shift['revenue']['Q3'], 'formula': f'{plan_revenue.q3_plan}'},
                        {'column': plan_shift['revenue']['Q3 6+6'], 'formula': f'{plan_revenue.q3_plan_6_6}'},
                        {'column': plan_shift['revenue']['Q4'], 'formula': f'{plan_revenue.q4_plan}'},
                        {'column': plan_shift['revenue']['Q4 6+6'], 'formula': f'{plan_revenue.q4_plan_6_6}'},
                        {'column': plan_shift['revenue']['HY2'],
                         'formula': f'{plan_revenue.q3_plan} + {plan_revenue.q4_plan}'},
                        {'column': plan_shift['revenue']['HY2 6+6'],
                         'formula': f'{plan_revenue.q3_plan_6_6} + {plan_revenue.q4_plan_6_6}'},
                        {'column': plan_shift['revenue']['Y'],
                         'formula': f'{plan_revenue.q1_plan} + {plan_revenue.q2_plan} + {plan_revenue.q3_plan} + {plan_revenue.q4_plan}'},
                        {'column': plan_shift['revenue']['Y 6+6'],
                         'formula': f'{plan_revenue.q3_plan_6_6} + {plan_revenue.q4_plan_6_6} + {plan_revenue.q1_fact} + {plan_revenue.q2_fact}'},
                        {'column': plan_shift['pds']['Q1'], 'formula': f'{plan_pds.q1_plan}'},
                        {'column': plan_shift['pds']['Q2'], 'formula': f'{plan_pds.q2_plan}'},
                        {'column': plan_shift['pds']['HY1'], 'formula': f'{plan_pds.q1_plan} + {plan_pds.q2_plan}'},
                        {'column': plan_shift['pds']['Q3'], 'formula': f'{plan_pds.q3_plan}'},
                        {'column': plan_shift['pds']['Q3 6+6'], 'formula': f'{plan_pds.q3_plan_6_6}'},
                        {'column': plan_shift['pds']['Q4'], 'formula': f'{plan_pds.q4_plan}'},
                        {'column': plan_shift['pds']['Q4 6+6'], 'formula': f'{plan_pds.q4_plan_6_6}'},
                        {'column': plan_shift['pds']['HY2'],
                         'formula': f'{plan_pds.q3_plan} + {plan_pds.q4_plan}'},
                        {'column': plan_shift['pds']['HY2 6+6'],
                         'formula': f'{plan_pds.q3_plan_6_6} + {plan_pds.q4_plan_6_6}'},
                        {'column': plan_shift['pds']['Y'],
                         'formula': f'{plan_pds.q1_plan} + {plan_pds.q2_plan} + {plan_pds.q3_plan} + {plan_pds.q4_plan}'},
                        {'column': plan_shift['pds']['Y 6+6'],
                         'formula': f'{plan_pds.q3_plan_6_6} + {plan_pds.q4_plan_6_6} + {plan_pds.q1_fact} + {plan_pds.q2_fact}'},
                        {'column': plan_shift['acceptance']['Q1'], 'formula': f'{plan_acceptance.q1_plan}'},
                        {'column': plan_shift['acceptance']['Q2'], 'formula': f'{plan_acceptance.q2_plan}'},
                        {'column': plan_shift['acceptance']['HY1'],
                         'formula': f'{plan_acceptance.q1_plan} + {plan_acceptance.q2_plan}'},
                        {'column': plan_shift['acceptance']['Q3'], 'formula': f'{plan_acceptance.q3_plan}'},
                        {'column': plan_shift['acceptance']['Q3 6+6'], 'formula': f'{plan_acceptance.q3_plan_6_6}'},
                        {'column': plan_shift['acceptance']['Q4'], 'formula': f'{plan_acceptance.q4_plan}'},
                        {'column': plan_shift['acceptance']['Q4 6+6'], 'formula': f'{plan_acceptance.q4_plan_6_6}'},
                        {'column': plan_shift['acceptance']['HY2'],
                         'formula': f'{plan_acceptance.q3_plan} + {plan_acceptance.q4_plan}'},
                        {'column': plan_shift['acceptance']['HY2 6+6'],
                         'formula': f'{plan_acceptance.q3_plan_6_6} + {plan_acceptance.q4_plan_6_6}'},
                        {'column': plan_shift['acceptance']['Y'],
                         'formula': f'{plan_acceptance.q1_plan} + {plan_acceptance.q2_plan} + {plan_acceptance.q3_plan} + {plan_acceptance.q4_plan}'},
                        {'column': plan_shift['acceptance']['Y 6+6'],
                         'formula': f'{plan_acceptance.q3_plan_6_6} + {plan_acceptance.q4_plan_6_6} + {plan_acceptance.q1_fact} + {plan_acceptance.q2_fact}'},
                        {'column': plan_shift['margin']['Q1'], 'formula': f'{plan_margin.q1_plan}'},
                        {'column': plan_shift['margin']['Q2'], 'formula': f'{plan_margin.q2_plan}'},
                        {'column': plan_shift['margin']['HY1'],
                         'formula': f'{plan_margin.q1_plan} + {plan_margin.q2_plan}'},
                        {'column': plan_shift['margin']['Q3'], 'formula': f'{plan_margin.q3_plan}'},
                        {'column': plan_shift['margin']['Q3 6+6'], 'formula': f'{plan_margin.q3_plan_6_6}'},
                        {'column': plan_shift['margin']['Q4'], 'formula': f'{plan_margin.q4_plan}'},
                        {'column': plan_shift['margin']['Q4 6+6'], 'formula': f'{plan_margin.q4_plan_6_6}'},
                        {'column': plan_shift['margin']['HY2'],
                         'formula': f'{plan_margin.q3_plan} + {plan_margin.q4_plan}'},
                        {'column': plan_shift['margin']['HY2 6+6'],
                         'formula': f'{plan_margin.q3_plan_6_6} + {plan_margin.q4_plan_6_6}'},
                        {'column': plan_shift['margin']['Y'],
                         'formula': f'{plan_margin.q1_plan} + {plan_margin.q2_plan} + {plan_margin.q3_plan} + {plan_margin.q4_plan}'},
                        {'column': plan_shift['margin']['Y 6+6'],
                         'formula': f'{plan_margin.q3_plan_6_6} + {plan_margin.q4_plan_6_6} + {plan_margin.q1_fact} + {plan_margin.q2_fact}'},
                        {'column': plan_shift['revenue']['NEXT'],
                         'formula': f'{plan_revenue_next.q1_plan + plan_revenue_next.q2_plan + plan_revenue_next.q3_plan + plan_revenue_next.q4_plan}'},
                        {'column': plan_shift['pds']['NEXT'],
                         'formula': f'{plan_pds_next.q1_plan + plan_pds_next.q2_plan + plan_pds_next.q3_plan + plan_pds_next.q4_plan}'},
                        {'column': plan_shift['acceptance']['NEXT'],
                         'formula': f'{plan_acceptance_next.q1_plan + plan_acceptance_next.q2_plan + plan_acceptance_next.q3_plan + plan_acceptance_next.q4_plan}'},
                        {'column': plan_shift['margin']['NEXT'],
                         'formula': f'{plan_margin_next.q1_plan + plan_margin_next.q2_plan + plan_margin_next.q3_plan + plan_margin_next.q4_plan}'},
                        {'column': plan_shift['revenue']['AFTER_NEXT'],
                         'formula': f'{plan_revenue_after_next.q1_plan + plan_revenue_after_next.q2_plan + plan_revenue_after_next.q3_plan + plan_revenue_after_next.q4_plan}'},
                        {'column': plan_shift['pds']['AFTER_NEXT'],
                         'formula': f'{plan_pds_after_next.q1_plan + plan_pds_after_next.q2_plan + plan_pds_after_next.q3_plan + plan_pds_after_next.q4_plan}'},
                        {'column': plan_shift['acceptance']['AFTER_NEXT'],
                         'formula': f'{plan_acceptance_after_next.q1_plan + plan_acceptance_after_next.q2_plan + plan_acceptance_after_next.q3_plan + plan_acceptance_after_next.q4_plan}'},
                        {'column': plan_shift['margin']['AFTER_NEXT'],
                         'formula': f'{plan_margin_after_next.q1_plan + plan_margin_after_next.q2_plan + plan_margin_after_next.q3_plan + plan_margin_after_next.q4_plan}'},
                    ):

                        child_office_formula = dict_formula.get(str_project_office_id, '')
                        if child_office_formula:  # увеличиваем все номера строк на 1
                            child_office_formula = ',' + ','.join(('{0}' + str(int(c[3:]) + 1)) for c in child_office_formula.strip(',').split(','))
                            office_formula = '(' + plan['formula'] + child_office_formula.format(xl_col_to_name(plan['column'])).replace(',', ' + ') + ')'
                        else:
                            office_formula = '(' + plan['formula'] + ')'

                        # if child_office_formula:  # увеличиваем все номера строк на 1
                        #     child_office_formula = ','.join(('{0}' + str(int(c[3:]) + 1)) for c in child_office_formula.strip(',').split(','))
                        #     office_formula = '=sum(' + child_office_formula.format(xl_col_to_name(plan['column'])) + ')'
                        # else:
                        #     office_formula = '(' + plan['formula'] + ')'


                        sheet.write_formula(row, plan['column'], office_formula, row_format_plan)

                    # for plan in (
                    #         {'column': plan_shift['revenue']['HY1'],
                    #          'formula': f"={xl_col_to_name(plan_shift['revenue']['Q1'])}{row + 1} + {xl_col_to_name(plan_shift['revenue']['Q2'])}{row + 1}"},
                    #         {'column': plan_shift['revenue']['HY2'],
                    #          'formula': f"={xl_col_to_name(plan_shift['revenue']['Q3'])}{row + 1} + {xl_col_to_name(plan_shift['revenue']['Q4'])}{row + 1}"},
                    #         {'column': plan_shift['revenue']['Y'],
                    #          'formula': f"={xl_col_to_name(plan_shift['revenue']['HY1'])}{row + 1} + {xl_col_to_name(plan_shift['revenue']['HY2'])}{row + 1}"},
                    #         {'column': plan_shift['pds']['HY1'],
                    #          'formula': f"={xl_col_to_name(plan_shift['pds']['Q1'])}{row + 1} + {xl_col_to_name(plan_shift['pds']['Q2'])}{row + 1}"},
                    #         {'column': plan_shift['pds']['HY2'],
                    #          'formula': f"={xl_col_to_name(plan_shift['pds']['Q3'])}{row + 1} + {xl_col_to_name(plan_shift['pds']['Q4'])}{row + 1}"},
                    #         {'column': plan_shift['pds']['Y'],
                    #          'formula': f"={xl_col_to_name(plan_shift['pds']['HY1'])}{row + 1} + {xl_col_to_name(plan_shift['pds']['HY2'])}{row + 1}"},
                    #         {'column': plan_shift['acceptance']['HY1'],
                    #          'formula': f"={xl_col_to_name(plan_shift['acceptance']['Q1'])}{row + 1} + {xl_col_to_name(plan_shift['acceptance']['Q2'])}{row + 1}"},
                    #         {'column': plan_shift['acceptance']['HY2'],
                    #          'formula': f"={xl_col_to_name(plan_shift['acceptance']['Q3'])}{row + 1} + {xl_col_to_name(plan_shift['acceptance']['Q4'])}{row + 1}"},
                    #         {'column': plan_shift['acceptance']['Y'],
                    #          'formula': f"={xl_col_to_name(plan_shift['acceptance']['HY1'])}{row + 1} + {xl_col_to_name(plan_shift['acceptance']['HY2'])}{row + 1}"},
                    #         {'column': plan_shift['margin']['HY1'],
                    #          'formula': f"={xl_col_to_name(plan_shift['margin']['Q1'])}{row + 1} + {xl_col_to_name(plan_shift['margin']['Q2'])}{row + 1}"},
                    #         {'column': plan_shift['margin']['HY2'],
                    #          'formula': f"={xl_col_to_name(plan_shift['margin']['Q3'])}{row + 1} + {xl_col_to_name(plan_shift['margin']['Q4'])}{row + 1}"},
                    #         {'column': plan_shift['margin']['Y'],
                    #          'formula': f"={xl_col_to_name(plan_shift['margin']['HY1'])}{row + 1} + {xl_col_to_name(plan_shift['margin']['HY2'])}{row + 1}"},
                    # ):
                    #     sheet.write_formula(row, plan['column'], plan['formula'], row_format_plan)

            if isFoundProjectsByCompany:
                if project_office.parent_id or set(self.env['project_budget.project_office'].search([]).ids) != set(project_office_ids): # печатаем компанию только по корневым офисам и если выбраны все оффисы
                    continue
                row += 1
                column = 0
                sheet.merge_range(row, column, row, column + 3, 'ИТОГО ' + company.name, row_format_number_itogo)
                sheet.set_row(row, False, False, {'hidden': 1, 'level': level})

                str_company_id = 'company_' + str(int(company.id))

                dict_formula['companies_lines'].add(row + 1)

                formulaCompany = formulaCompany + ')'

                for colFormula in range(2, start_column):
                    sheet.write_string(row, colFormula, '', row_format_number_itogo)

                for colFormula in list(range(start_column, 220 + start_column)) + list(range(221 + start_column, 235 + start_column)) + list(range(236 + start_column, 250 + start_column)):
                    formula = formulaCompany.format(xl_col_to_name(colFormula))
                    sheet.write_formula(row, colFormula, formula, row_format_number_itogo)

                for type in plan_shift:  # кресты в планах
                    for c in plan_shift[type].values():
                        sheet.write_string(row, c, '', row_format_plan_cross)

                # расчетный план компании
                row += 1
                column = 0

                sheet.merge_range(row, column, row, column + 3, 'ИТОГО ' + company.name + ' Расчетный План:',
                                   row_format_company_estimated_plan_left)
                self.print_estimated_rows(sheet, row, row_format_company_estimated_plan,
                                          row_format_company_estimated_plan_cross)

                # планы компаний
                plan_revenue = self.env['project_budget.budget_plan_supervisor_spec'].search([
                    ('budget_plan_supervisor_id.year', '=', YEARint),
                    ('budget_plan_supervisor_id.company_id', '=', company.id),
                    ('budget_plan_supervisor_id.is_company_plan', '=', True),
                    ('type_row', '=', 'contracting'),
                ])
                plan_pds = self.env['project_budget.budget_plan_supervisor_spec'].search([
                    ('budget_plan_supervisor_id.year', '=', YEARint),
                    ('budget_plan_supervisor_id.company_id', '=', company.id),
                    ('budget_plan_supervisor_id.is_company_plan', '=', True),
                    ('type_row', '=', 'cash'),
                ])
                plan_acceptance = self.env['project_budget.budget_plan_supervisor_spec'].search([
                    ('budget_plan_supervisor_id.year', '=', YEARint),
                    ('budget_plan_supervisor_id.company_id', '=', company.id),
                    ('budget_plan_supervisor_id.is_company_plan', '=', True),
                    ('type_row', '=', 'acceptance'),
                ])
                plan_margin = self.env['project_budget.budget_plan_supervisor_spec'].search([
                    ('budget_plan_supervisor_id.year', '=', YEARint),
                    ('budget_plan_supervisor_id.company_id', '=', company.id),
                    ('budget_plan_supervisor_id.is_company_plan', '=', True),
                    ('type_row', '=', 'margin_income'),
                ])
                plan_revenue_next = self.env['project_budget.budget_plan_supervisor_spec'].search([
                    ('budget_plan_supervisor_id.year', '=', YEARint + 1),
                    ('budget_plan_supervisor_id.company_id', '=', company.id),
                    ('budget_plan_supervisor_id.is_company_plan', '=', True),
                    ('type_row', '=', 'contracting'),
                ])
                plan_pds_next = self.env['project_budget.budget_plan_supervisor_spec'].search([
                    ('budget_plan_supervisor_id.year', '=', YEARint + 1),
                    ('budget_plan_supervisor_id.company_id', '=', company.id),
                    ('budget_plan_supervisor_id.is_company_plan', '=', True),
                    ('type_row', '=', 'cash'),
                ])
                plan_acceptance_next = self.env['project_budget.budget_plan_supervisor_spec'].search([
                    ('budget_plan_supervisor_id.year', '=', YEARint + 1),
                    ('budget_plan_supervisor_id.company_id', '=', company.id),
                    ('budget_plan_supervisor_id.is_company_plan', '=', True),
                    ('type_row', '=', 'acceptance'),
                ])
                plan_margin_next = self.env['project_budget.budget_plan_supervisor_spec'].search([
                    ('budget_plan_supervisor_id.year', '=', YEARint + 1),
                    ('budget_plan_supervisor_id.company_id', '=', company.id),
                    ('budget_plan_supervisor_id.is_company_plan', '=', True),
                    ('type_row', '=', 'margin_income'),
                ])
                plan_revenue_after_next = self.env['project_budget.budget_plan_supervisor_spec'].search([
                    ('budget_plan_supervisor_id.year', '=', YEARint + 2),
                    ('budget_plan_supervisor_id.company_id', '=', company.id),
                    ('budget_plan_supervisor_id.is_company_plan', '=', True),
                    ('type_row', '=', 'contracting'),
                ])
                plan_pds_after_next = self.env['project_budget.budget_plan_supervisor_spec'].search([
                    ('budget_plan_supervisor_id.year', '=', YEARint + 2),
                    ('budget_plan_supervisor_id.company_id', '=', company.id),
                    ('budget_plan_supervisor_id.is_company_plan', '=', True),
                    ('type_row', '=', 'cash'),
                ])
                plan_acceptance_after_next = self.env['project_budget.budget_plan_supervisor_spec'].search([
                    ('budget_plan_supervisor_id.year', '=', YEARint + 2),
                    ('budget_plan_supervisor_id.company_id', '=', company.id),
                    ('budget_plan_supervisor_id.is_company_plan', '=', True),
                    ('type_row', '=', 'acceptance'),
                ])
                plan_margin_after_next = self.env['project_budget.budget_plan_supervisor_spec'].search([
                    ('budget_plan_supervisor_id.year', '=', YEARint + 2),
                    ('budget_plan_supervisor_id.company_id', '=', company.id),
                    ('budget_plan_supervisor_id.is_company_plan', '=', True),
                    ('type_row', '=', 'margin_income'),
                ])

                for plan in (plan_revenue, plan_pds, plan_acceptance, plan_margin):
                    if plan.q3_plan_6_6 != 0 or plan.q4_plan_6_6 != 0:
                        use_6_6 = True

                for plan in (
                    {'column': plan_shift['revenue']['Q1'], 'formula': f'{plan_revenue.q1_plan}'},
                    {'column': plan_shift['revenue']['Q2'], 'formula': f'{plan_revenue.q2_plan}'},
                    {'column': plan_shift['revenue']['HY1'],
                     'formula': f'{plan_revenue.q1_plan} + {plan_revenue.q2_plan}'},
                    {'column': plan_shift['revenue']['Q3'], 'formula': f'{plan_revenue.q3_plan}'},
                    {'column': plan_shift['revenue']['Q3 6+6'], 'formula': f'{plan_revenue.q3_plan_6_6}'},
                    {'column': plan_shift['revenue']['Q4'], 'formula': f'{plan_revenue.q4_plan}'},
                    {'column': plan_shift['revenue']['Q4 6+6'], 'formula': f'{plan_revenue.q4_plan_6_6}'},
                    {'column': plan_shift['revenue']['HY2'],
                     'formula': f'{plan_revenue.q3_plan} + {plan_revenue.q4_plan}'},
                    {'column': plan_shift['revenue']['HY2 6+6'],
                     'formula': f'{plan_revenue.q3_plan_6_6} + {plan_revenue.q4_plan_6_6}'},
                    {'column': plan_shift['revenue']['Y'],
                     'formula': f'{plan_revenue.q1_plan} + {plan_revenue.q2_plan} + {plan_revenue.q3_plan} + {plan_revenue.q4_plan}'},
                    {'column': plan_shift['revenue']['Y 6+6'],
                     'formula': f'{plan_revenue.q3_plan_6_6} + {plan_revenue.q4_plan_6_6} + {plan_revenue.q1_fact} + {plan_revenue.q2_fact}'},
                    {'column': plan_shift['pds']['Q1'], 'formula': f'{plan_pds.q1_plan}'},
                    {'column': plan_shift['pds']['Q2'], 'formula': f'{plan_pds.q2_plan}'},
                    {'column': plan_shift['pds']['HY1'], 'formula': f'{plan_pds.q1_plan} + {plan_pds.q2_plan}'},
                    {'column': plan_shift['pds']['Q3'], 'formula': f'{plan_pds.q3_plan}'},
                    {'column': plan_shift['pds']['Q3 6+6'], 'formula': f'{plan_pds.q3_plan_6_6}'},
                    {'column': plan_shift['pds']['Q4'], 'formula': f'{plan_pds.q4_plan}'},
                    {'column': plan_shift['pds']['Q4 6+6'], 'formula': f'{plan_pds.q4_plan_6_6}'},
                    {'column': plan_shift['pds']['HY2'],
                     'formula': f'{plan_pds.q3_plan} + {plan_pds.q4_plan}'},
                    {'column': plan_shift['pds']['HY2 6+6'],
                     'formula': f'{plan_pds.q3_plan_6_6} + {plan_pds.q4_plan_6_6}'},
                    {'column': plan_shift['pds']['Y'],
                     'formula': f'{plan_pds.q1_plan} + {plan_pds.q2_plan} + {plan_pds.q3_plan} + {plan_pds.q4_plan}'},
                    {'column': plan_shift['pds']['Y 6+6'],
                     'formula': f'{plan_pds.q3_plan_6_6} + {plan_pds.q4_plan_6_6} + {plan_pds.q1_fact} + {plan_pds.q2_fact}'},
                    {'column': plan_shift['acceptance']['Q1'], 'formula': f'{plan_acceptance.q1_plan}'},
                    {'column': plan_shift['acceptance']['Q2'], 'formula': f'{plan_acceptance.q2_plan}'},
                    {'column': plan_shift['acceptance']['HY1'],
                     'formula': f'{plan_acceptance.q1_plan} + {plan_acceptance.q2_plan}'},
                    {'column': plan_shift['acceptance']['Q3'], 'formula': f'{plan_acceptance.q3_plan}'},
                    {'column': plan_shift['acceptance']['Q3 6+6'], 'formula': f'{plan_acceptance.q3_plan_6_6}'},
                    {'column': plan_shift['acceptance']['Q4'], 'formula': f'{plan_acceptance.q4_plan}'},
                    {'column': plan_shift['acceptance']['Q4 6+6'], 'formula': f'{plan_acceptance.q4_plan_6_6}'},
                    {'column': plan_shift['acceptance']['HY2'],
                     'formula': f'{plan_acceptance.q3_plan} + {plan_acceptance.q4_plan}'},
                    {'column': plan_shift['acceptance']['HY2 6+6'],
                     'formula': f'{plan_acceptance.q3_plan_6_6} + {plan_acceptance.q4_plan_6_6}'},
                    {'column': plan_shift['acceptance']['Y'],
                     'formula': f'{plan_acceptance.q1_plan} + {plan_acceptance.q2_plan} + {plan_acceptance.q3_plan} + {plan_acceptance.q4_plan}'},
                    {'column': plan_shift['acceptance']['Y 6+6'],
                     'formula': f'{plan_acceptance.q3_plan_6_6} + {plan_acceptance.q4_plan_6_6} + {plan_acceptance.q1_fact} + {plan_acceptance.q2_fact}'},
                    {'column': plan_shift['margin']['Q1'], 'formula': f'{plan_margin.q1_plan}'},
                    {'column': plan_shift['margin']['Q2'], 'formula': f'{plan_margin.q2_plan}'},
                    {'column': plan_shift['margin']['HY1'],
                     'formula': f'{plan_margin.q1_plan} + {plan_margin.q2_plan}'},
                    {'column': plan_shift['margin']['Q3'], 'formula': f'{plan_margin.q3_plan}'},
                    {'column': plan_shift['margin']['Q3 6+6'], 'formula': f'{plan_margin.q3_plan_6_6}'},
                    {'column': plan_shift['margin']['Q4'], 'formula': f'{plan_margin.q4_plan}'},
                    {'column': plan_shift['margin']['Q4 6+6'], 'formula': f'{plan_margin.q4_plan_6_6}'},
                    {'column': plan_shift['margin']['HY2'],
                     'formula': f'{plan_margin.q3_plan} + {plan_margin.q4_plan}'},
                    {'column': plan_shift['margin']['HY2 6+6'],
                     'formula': f'{plan_margin.q3_plan_6_6} + {plan_margin.q4_plan_6_6}'},
                    {'column': plan_shift['margin']['Y'],
                     'formula': f'{plan_margin.q1_plan} + {plan_margin.q2_plan} + {plan_margin.q3_plan} + {plan_margin.q4_plan}'},
                    {'column': plan_shift['margin']['Y 6+6'],
                     'formula': f'{plan_margin.q3_plan_6_6} + {plan_margin.q4_plan_6_6} + {plan_margin.q1_fact} + {plan_margin.q2_fact}'},
                    {'column': plan_shift['revenue']['NEXT'],
                     'formula': f'{plan_revenue_next.q1_plan + plan_revenue_next.q2_plan + plan_revenue_next.q3_plan + plan_revenue_next.q4_plan}'},
                    {'column': plan_shift['pds']['NEXT'],
                     'formula': f'{plan_pds_next.q1_plan + plan_pds_next.q2_plan + plan_pds_next.q3_plan + plan_pds_next.q4_plan}'},
                    {'column': plan_shift['acceptance']['NEXT'],
                     'formula': f'{plan_acceptance_next.q1_plan + plan_acceptance_next.q2_plan + plan_acceptance_next.q3_plan + plan_acceptance_next.q4_plan}'},
                    {'column': plan_shift['margin']['NEXT'],
                     'formula': f'{plan_margin_next.q1_plan + plan_margin_next.q2_plan + plan_margin_next.q3_plan + plan_margin_next.q4_plan}'},
                    {'column': plan_shift['revenue']['AFTER_NEXT'],
                     'formula': f'{plan_revenue_after_next.q1_plan + plan_revenue_after_next.q2_plan + plan_revenue_after_next.q3_plan + plan_revenue_after_next.q4_plan}'},
                    {'column': plan_shift['pds']['AFTER_NEXT'],
                     'formula': f'{plan_pds_after_next.q1_plan + plan_pds_after_next.q2_plan + plan_pds_after_next.q3_plan + plan_pds_after_next.q4_plan}'},
                    {'column': plan_shift['acceptance']['AFTER_NEXT'],
                     'formula': f'{plan_acceptance_after_next.q1_plan + plan_acceptance_after_next.q2_plan + plan_acceptance_after_next.q3_plan + plan_acceptance_after_next.q4_plan}'},
                    {'column': plan_shift['margin']['AFTER_NEXT'],
                     'formula': f'{plan_margin_after_next.q1_plan + plan_margin_after_next.q2_plan + plan_margin_after_next.q3_plan + plan_margin_after_next.q4_plan}'},
                ):
                    formula = '=sum(' + ','.join(('{0}' + str(int(c.strip(')')) + 1)) for c in formulaCompany.split(',{0}')[1:]) + ')'  # увеличиваем все номера строк на 1
                    formula = formula.format(xl_col_to_name(plan['column']))
                    sheet.write_formula(row, plan['column'], formula, row_format_plan)
                    # company_formula = '(' + plan['formula'] + ')'
                    # sheet.write_formula(row, plan['column'], company_formula, row_format_plan)
                    # sheet.set_row(row, False, False, {'hidden': 1, 'level': level + 1})

                # for plan in (
                #         {'column': plan_shift['revenue']['HY1'],
                #          'formula': f"={xl_col_to_name(plan_shift['revenue']['Q1'])}{row + 1} + {xl_col_to_name(plan_shift['revenue']['Q2'])}{row + 1}"},
                #         {'column': plan_shift['revenue']['HY2'],
                #          'formula': f"={xl_col_to_name(plan_shift['revenue']['Q3'])}{row + 1} + {xl_col_to_name(plan_shift['revenue']['Q4'])}{row + 1}"},
                #         {'column': plan_shift['revenue']['Y'],
                #          'formula': f"={xl_col_to_name(plan_shift['revenue']['HY1'])}{row + 1} + {xl_col_to_name(plan_shift['revenue']['HY2'])}{row + 1}"},
                #         {'column': plan_shift['pds']['HY1'],
                #          'formula': f"={xl_col_to_name(plan_shift['pds']['Q1'])}{row + 1} + {xl_col_to_name(plan_shift['pds']['Q2'])}{row + 1}"},
                #         {'column': plan_shift['pds']['HY2'],
                #          'formula': f"={xl_col_to_name(plan_shift['pds']['Q3'])}{row + 1} + {xl_col_to_name(plan_shift['pds']['Q4'])}{row + 1}"},
                #         {'column': plan_shift['pds']['Y'],
                #          'formula': f"={xl_col_to_name(plan_shift['pds']['HY1'])}{row + 1} + {xl_col_to_name(plan_shift['pds']['HY2'])}{row + 1}"},
                #         {'column': plan_shift['acceptance']['HY1'],
                #          'formula': f"={xl_col_to_name(plan_shift['acceptance']['Q1'])}{row + 1} + {xl_col_to_name(plan_shift['acceptance']['Q2'])}{row + 1}"},
                #         {'column': plan_shift['acceptance']['HY2'],
                #          'formula': f"={xl_col_to_name(plan_shift['acceptance']['Q3'])}{row + 1} + {xl_col_to_name(plan_shift['acceptance']['Q4'])}{row + 1}"},
                #         {'column': plan_shift['acceptance']['Y'],
                #          'formula': f"={xl_col_to_name(plan_shift['acceptance']['HY1'])}{row + 1} + {xl_col_to_name(plan_shift['acceptance']['HY2'])}{row + 1}"},
                #         {'column': plan_shift['margin']['HY1'],
                #          'formula': f"={xl_col_to_name(plan_shift['margin']['Q1'])}{row + 1} + {xl_col_to_name(plan_shift['margin']['Q2'])}{row + 1}"},
                #         {'column': plan_shift['margin']['HY2'],
                #          'formula': f"={xl_col_to_name(plan_shift['margin']['Q3'])}{row + 1} + {xl_col_to_name(plan_shift['margin']['Q4'])}{row + 1}"},
                #         {'column': plan_shift['margin']['Y'],
                #          'formula': f"={xl_col_to_name(plan_shift['margin']['HY1'])}{row + 1} + {xl_col_to_name(plan_shift['margin']['HY2'])}{row + 1}"},
                # ):
                #     sheet.write_formula(row, plan['column'], plan['formula'], row_format_plan)

        return row

    def get_child_offices_ids(self, office_ids, res: list):
        if office_ids:
            res.extend(office_ids)
            child_offices_ids = self.env['project_budget.project_office'].search([('parent_id', 'in', office_ids)]).ids
            if child_offices_ids:
                res = self.get_child_offices_ids(child_offices_ids, res)
            return res
        else:
            return []

    def printworksheet(self,workbook,budget,namesheet, estimated_probabilities, project_office_ids, systematica_forecast, oblako_row, diff_name):
        global YEARint
        print('YEARint=',YEARint)

        report_name = budget.name
        sheet = workbook.add_worksheet(namesheet)
        sheet.set_zoom(85)
        sheet.hide_zero()
        bold = workbook.add_format({'bold': True})
        money_format = workbook.add_format({'num_format': '#,##0'})
        head_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_size': 10,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#FFFF00'
        })
        summary_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_size': 12,
            'text_wrap': True,
            'valign': 'vcenter',
            "num_format": '#,##0',
        })
        summary_format_border_top = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'text_wrap': True,
            'valign': 'vcenter',
            "num_format": '#,##0',
            'top': 2,
            'left': 2,
            'right': 2,
        })
        summary_format_border_top_center = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'text_wrap': True,
            'valign': 'vcenter',
            'align': 'center',
            "num_format": '#,##0',
            'top': 2,
            'left': 2,
            'right': 2,
        })
        summary_format_border_bottom = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'text_wrap': True,
            'valign': 'vjustify',
            'text_wrap': True,
            "num_format": '#,##0',
            'top': 1,
            'bottom': 2,
            'left': 2,
            'right': 2,
        })
        summary_format_percent = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_size': 12,
            'text_wrap': True,
            'valign': 'vcenter',
            "num_format": '0%',
        })
        head_format_1 = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "bold": False,
            "fg_color": '#C6E0B4',
            "font_size": 8,
        })
        row_format_date_month = workbook.add_format({
            'border': 1,
            'font_size': 10,
        })

        row_format_manager = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#D9D9D9',
        })
        row_format_manager.set_num_format('#,##0')

        row_format_office = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#8497B0',
        })
        row_format_office.set_num_format('#,##0')

        row_format_date_month.set_num_format('mmm yyyy')

        row_format = workbook.add_format({
            'border': 1,
            'font_size': 10
        })

        row_format_canceled_project = workbook.add_format({
            'border': 1,
            'font_size': 10
        })
        row_format_canceled_project.set_font_color('red')

        row_format_number = workbook.add_format({
            'border': 1,
            'font_size': 10,
        })
        row_format_number.set_num_format('#,##0')

        row_format_number_canceled_project = workbook.add_format({
            'border': 1,
            'font_size': 10,
        })
        row_format_number_canceled_project.set_num_format('#,##0')
        row_format_number_canceled_project.set_font_color('red')

        row_format_number_itogo = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#A9D08E',

        })
        row_format_number_itogo.set_num_format('#,##0')

        head_format_month_itogo = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "bold": True,
            "fg_color": '#DCE6F1',
            "font_size": 10,
        })
        head_format_month_itogo.set_num_format('#,##0')

        row_format_plan = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#DCE6F1',
            "num_format": '#,##0',
        })

        row_format_diff = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "bold": True,
            "fg_color": '#DDD9C4',
            "num_format": '#,##0;[red]-#,##0',
        })

        row_format_itogo_estimated_plan = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#FFFF00',
            "num_format": '#,##0',
            'align': 'center',
        })

        row_format_itogo_estimated_plan_left = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#FFFF00',
            "num_format": '#,##0',
        })

        row_format_itogo_estimated_plan_cross = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#FFFF00',
            "num_format": '#,##0',
            'align': 'center',
            'diag_type': 3,
        })

        row_format_plan_cross = workbook.add_format({
            'border': 1,
            "fg_color": '#DCE6F1',
            'diag_type': 3,
        })

        date_format = workbook.add_format({'num_format': 'd mmmm yyyy'})
        row = 0
        sheet.merge_range(row,0,row,0, budget.name, bold)
        row = 2
        column = 0
        # sheet.write_string(row, column, "Прогноз",head_format)
        sheet.write_string(row + 1, column, "Проектный офис", head_format_1)
        sheet.write_string(row + 2, column, "", head_format_1)
        sheet.set_column(column, column, 21.5)
        column += 1
        sheet.merge_range(row - 2, column, row - 1, column, "Расчетный План:", summary_format)
        sheet.write_string(row + 1, column, "КАМ", head_format_1)
        sheet.write_string(row + 2, column, "", head_format_1)
        sheet.set_column(column, column, 19.75)
        column += 1
        sheet.write_string(row - 2, column, "Обязательство", summary_format)
        sheet.write_string(row - 1, column, "Резерв", summary_format)
        sheet.write_string(row + 1, column, "Заказчик", head_format_1)
        sheet.write_string(row + 2, column, "", head_format_1)
        sheet.set_column(column, column, 25)
        column += 1
        sheet.write_number(row - 2, column, 1, summary_format_percent)
        sheet.write_number(row - 1, column, 0.6, summary_format_percent)
        sheet.write_string(row + 1, column, "Наименование Проекта", head_format_1)
        sheet.write_string(row + 2, column, "", head_format_1)
        sheet.set_column(column, column, 12.25)
        column += 1
        # sheet.write_string(row, column, "", head_format)
        sheet.write_string(row + 1, column, "Номер этапа проекта CRM", head_format_1)
        sheet.write_string(row + 2, column, "", head_format_1)
        # sheet.set_column(column, column, 15)
        column += 1
        sheet.write_string(row + 1, column, "Номер этапа проекта AX", head_format_1)
        sheet.write_string(row + 2, column, "", head_format_1)
        # sheet.set_column(column, column, 15)
        column += 1
        # sheet.write_string(row, column, "", head_format)
        sheet.write_string(row + 1, column, "Сумма проекта/этапа, руб.", head_format_1)
        sheet.write_string(row + 2, column, "", head_format_1)
        # sheet.set_column(column, column, 14)
        column += 1
        # sheet.write_string(row, column, "", head_format)
        sheet.write_string(row + 1, column, "Дата контрактования", head_format_1)
        sheet.write_string(row + 2, column, "", head_format_1)
        # sheet.set_column(column, column, 16.88)
        column += 1
        # sheet.write_string(row, column, "", head_format)
        sheet.write_string(row + 1, column, "Прибыльность, экспертно, %", head_format_1)
        sheet.write_string(row + 2, column, "", head_format_1)
        # sheet.set_column(column, column, 9)
        sheet.set_column(4, 11, False, False, {'hidden': 1, 'level': 1})
        column += 1
        # sheet.write_string(row, column, "", head_format)
        sheet.write_string(row + 1, column, "", head_format_1)
        sheet.write_string(row + 2, column, "", head_format_1)
        sheet.set_column(column, column, 2)

        sheet.freeze_panes(5, start_column)
        column += 1
        column = self.print_month_head_contract(workbook, sheet, row, column, YEARint, self.month_rus_name_contract_pds, False)
        column = self.print_month_head_pds(workbook, sheet, row, column, YEARint, self.month_rus_name_contract_pds, False)
        column = self.print_month_head_revenue_margin(workbook, sheet, row, column, YEARint, self.month_rus_name_revenue_margin, False)
        column = self.print_month_head_contract(workbook, sheet, row, column + 1, YEARint + 1, ['YEAR итого',], True)
        column = self.print_month_head_pds(workbook, sheet, row, column, YEARint + 1, ['YEAR итого',], True)
        column = self.print_month_head_revenue_margin(workbook, sheet, row, column, YEARint + 1, ['YEAR итого',], True)
        column = self.print_month_head_contract(workbook, sheet, row, column + 1, YEARint + 2, ['YEAR итого',], True)
        column = self.print_month_head_pds(workbook, sheet, row, column, YEARint + 2, ['YEAR итого',], True)
        column = self.print_month_head_revenue_margin(workbook, sheet, row, column, YEARint + 2, ['YEAR итого',], True)
        row += 2

        companies = self.env['res.company'].search([], order='name')

        project_offices = self.env['project_budget.project_office'].search([
            ('id','in',project_office_ids), ('parent_id', 'not in', project_office_ids)], order='name')  # для сортировки так делаем + не берем дочерние оффисы, если выбраны их материнские

        key_account_managers = self.env['project_budget.projects'].search([]).key_account_manager_id.sorted('name')
        # key_account_managers = self.env.ref('project_budget.group_project_budget_key_account_manager').users
        # project_managers = self.env['project_budget.project_manager'].search([], order='name')  # для сортировки так делаем

        row = self.print_row(sheet, workbook, companies, project_offices, key_account_managers, estimated_probabilities, budget, row, 1, project_office_ids)

        # ИТОГО
        row += 1
        column = 0
        sheet.merge_range(row, column, row, column + 3, 'ИТОГО по отчету', row_format_number_itogo)
        formula_itogo = False
        formula_plan = False
        if dict_formula['companies_lines']:
            formula_itogo = '=sum(' + ','.join(('{0}' + str(c)) for c in dict_formula['companies_lines']) + ')'
            formula_plan = '=sum(,' + ','.join(('{0}' + str(c + 1)) for c in dict_formula['companies_lines']) + ')'  # увеличиваем все номера строк на 1
            sheet.set_row(row, False, False, {'hidden': 1, 'level': 1})
        elif dict_formula['offices_lines']:
            formula_itogo = '=sum(' + ','.join(('{0}' + str(c)) for c in dict_formula['offices_lines']) + ')'
            formula_plan = '=sum(' + ','.join(('{0}' + str(c + 1)) for c in dict_formula['offices_lines']) + ')'  # увеличиваем все номера строк на 1
            sheet.set_row(row, False, False, {'hidden': 1, 'level': 1})

        if formula_itogo:
            for colFormula in range(2, start_column):
                sheet.write_string(row, colFormula, '', row_format_number_itogo)
            for colFormula in list(range(start_column, 220 + start_column)) + list(range(221 + start_column, 235 + start_column)) + list(range(236 + start_column, 250 + start_column)):
                formula = formula_itogo.format(xl_col_to_name(colFormula))
                sheet.write_formula(row, colFormula, formula, row_format_number_itogo)

        # расчетный план по отчету
        row += 1
        column = 0
        sheet.merge_range(row, column, row, column + 3, 'ИТОГО: Расчетный План по отчету', row_format_itogo_estimated_plan_left)
        self.print_estimated_rows(sheet, row, row_format_itogo_estimated_plan,
                                  row_format_itogo_estimated_plan_cross)

        for type in plan_shift:  # кресты в планах
            for c in plan_shift[type].values():
                if formula_plan:
                    formula = formula_plan.format(xl_col_to_name(c))
                    sheet.write_string(row - 1, c, '', row_format_plan_cross)
                    sheet.write_formula(row, c, formula, row_format_plan)

        total_row = row

        if systematica_forecast: #  Суммируем Систематику и Облако
            # ИТОГО
            column = 0
            sheet.merge_range(row + 1, column, row + 1, column + 3, 'ИТОГО: СА+Облако.ру по отчету', row_format_number_itogo)
            sheet.set_row(row + 1, False, False, {'hidden': 1, 'level': 1})
            for colFormula in range(2, start_column):
                sheet.write_string(row + 1, colFormula, '', row_format_number_itogo)
            for colFormula in list(range(start_column, 220 + start_column)) + list(range(221 + start_column, 235 + start_column)) + list(range(236 + start_column, 250 + start_column)):
                formula = '=sum({2}{0},{3}{2}{1})'.format(row, oblako_row, xl_col_to_name(colFormula), "'Прогноз (Облако.ру)'!")
                sheet.write_formula(row + 1, colFormula, formula, row_format_number_itogo)
            # расчетный план по отчету
            sheet.merge_range(row + 2, column, row + 2, column + 3, 'ИТОГО: СА+Облако.ру Расчетный План по отчету',
                              row_format_itogo_estimated_plan_left)
            self.print_estimated_rows(sheet, row + 2, row_format_itogo_estimated_plan,
                                      row_format_itogo_estimated_plan_cross)

            for type in plan_shift:  # кресты в планах
                for period, shift in plan_shift[type].items():
                    formula = '=sum({2}{0},{3}{2}{1})'.format(row + 1, oblako_row + 1, xl_col_to_name(shift),"'Прогноз (Облако.ру)'!")
                    sheet.write_string(row + 1, shift, '', row_format_plan_cross)
                    sheet.write_formula(row + 2, shift, formula, row_format_plan)
            row += 2
            sheet.activate()
            total_row += 2

        if diff_name:  # разница
            sheet.merge_range(
                row + 1, 1, row + 1, 3,
                f'Разница Итого; План ' + ('6+6' if use_6_6 else f'{YEARint}') + f' ({diff_name})/ Расчетный план до конца периода (на дату отчета)',
                row_format_diff
            )
            for type in plan_shift:
                for period, shift in plan_shift[type].items():
                    if 'NEXT' not in period and '6+6' not in period:
                        if period in ('HY2', 'Q3', 'Q4', 'Y'):
                            if use_6_6:
                                formula_diff = '=({1}{0}+{2}{0})-{3}{0}'.format(
                                    row + 1,
                                    xl_col_to_name(shift + 2),
                                    xl_col_to_name(shift + 3),
                                    xl_col_to_name(shift + 1),
                                )
                            else:
                                formula_diff = '=({1}{0}+{2}{0})-{3}{0}'.format(
                                    row + 1,
                                    xl_col_to_name(shift + 2),
                                    xl_col_to_name(shift + 3),
                                    xl_col_to_name(shift),
                                )
                            sheet.merge_range(row + 1, shift + 2, row + 1, shift + 4, formula_diff, row_format_diff)
                        else:
                            formula_diff = '=({1}{0}+{2}{0})-{3}{0}'.format(
                                row + 1,
                                xl_col_to_name(shift + 1),
                                xl_col_to_name(shift + 2),
                                xl_col_to_name(shift),
                            )
                            sheet.merge_range(row + 1, shift + 1, row + 1, shift + 3, formula_diff, row_format_diff)
            sheet.set_row(row + 1, 32)
            row += 1

        row += 2
        sheet.merge_range(row, 1, row, 2, 'Контрактование, с НДС', summary_format_border_top_center)
        sheet.write_string(row, 3, '', summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(YEARint)}:', summary_format_border_top)
        formula = '={1}{0}+{2}{0}+{3}{0}'.format(
            total_row,
            xl_col_to_name(83 + start_column),
            xl_col_to_name(84 + start_column),
            xl_col_to_name(85 + start_column),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(YEARint)}:', summary_format_border_bottom)
        formula = '={1}{0}+{2}{0}'.format(
            total_row + 1,
            xl_col_to_name(83 + start_column),
            xl_col_to_name(84 + start_column),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(YEARint + 1)}:', summary_format_border_top)
        formula = '={1}{0}+{2}{0}'.format(
            total_row,
            xl_col_to_name(222 + start_column),
            xl_col_to_name(223 + start_column),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(YEARint + 1)}:', summary_format_border_bottom)
        formula = '={1}{0}'.format(
            total_row + 1,
            xl_col_to_name(222 + start_column),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(YEARint + 2)}:', summary_format_border_top)
        formula = '={1}{0}+{2}{0}'.format(
            total_row,
            xl_col_to_name(237 + start_column),
            xl_col_to_name(238 + start_column),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(YEARint + 2)}:', summary_format_border_bottom)
        formula = '={1}{0}'.format(
            total_row + 1,
            xl_col_to_name(237 + start_column),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Итого по Компании {str(YEARint)}-{str(YEARint + 2)}:', summary_format_border_top)
        formula = '={3}{0}+{3}{1}+{3}{2}'.format(row - 1, row - 3, row - 5, xl_col_to_name(3))
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Итого Расчетный План по Компании {str(YEARint)}-{str(YEARint + 2)}:', summary_format_border_bottom)
        formula = '={3}{0}+{3}{1}+{3}{2}'.format(row - 1, row - 3, row - 5, xl_col_to_name(3))
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)

        row += 2
        sheet.merge_range(row, 1, row, 2, 'Валовая выручка, без НДС', summary_format_border_top_center)
        sheet.write_string(row, 3, '', summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(YEARint)}:', summary_format_border_top)
        formula = '={1}{0}+{2}{0}+{3}{0}'.format(
            total_row,
            xl_col_to_name(184 + start_column),
            xl_col_to_name(185 + start_column),
            xl_col_to_name(186 + start_column),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(YEARint)}:', summary_format_border_bottom)
        formula = '={1}{0}+{2}{0}'.format(
            total_row + 1,
            xl_col_to_name(184 + start_column),
            xl_col_to_name(185 + start_column),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(YEARint + 1)}:', summary_format_border_top)
        formula = '={1}{0}+{2}{0}'.format(
            total_row,
            xl_col_to_name(229 + start_column),
            xl_col_to_name(230 + start_column),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(YEARint + 1)}:', summary_format_border_bottom)
        formula = '={1}{0}'.format(
            total_row + 1,
            xl_col_to_name(229 + start_column),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(YEARint + 2)}:', summary_format_border_top)
        formula = '={1}{0}+{2}{0}'.format(
            total_row,
            xl_col_to_name(244 + start_column),
            xl_col_to_name(245 + start_column),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(YEARint + 2)}:', summary_format_border_bottom)
        formula = '={1}{0}'.format(
            total_row + 1,
            xl_col_to_name(244 + start_column),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Итого по Компании {str(YEARint)}-{str(YEARint + 2)}:', summary_format_border_top)
        formula = '={3}{0}+{3}{1}+{3}{2}'.format(row - 1, row - 3, row - 5, xl_col_to_name(3))
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Итого Расчетный План по Компании {str(YEARint)}-{str(YEARint + 2)}:', summary_format_border_bottom)
        formula = '={3}{0}+{3}{1}+{3}{2}'.format(row - 1, row - 3, row - 5, xl_col_to_name(3))
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)

        row += 2
        sheet.merge_range(row, 1, row, 2, 'ПДС, с НДС', summary_format_border_top_center)
        sheet.write_string(row, 3, '', summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(YEARint)}:', summary_format_border_top)
        formula = '={1}{0}+{2}{0}+{3}{0}'.format(
            total_row,
            xl_col_to_name(152 + start_column),
            xl_col_to_name(153 + start_column),
            xl_col_to_name(154 + start_column),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(YEARint)}:', summary_format_border_bottom)
        formula = '={1}{0}+{2}{0}'.format(
            total_row + 1,
            xl_col_to_name(152 + start_column),
            xl_col_to_name(153 + start_column),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(YEARint + 1)}:', summary_format_border_top)
        formula = '={1}{0}+{2}{0}'.format(
            total_row,
            xl_col_to_name(226 + start_column),
            xl_col_to_name(227 + start_column),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(YEARint + 1)}:', summary_format_border_bottom)
        formula = '={1}{0}'.format(
            total_row + 1,
            xl_col_to_name(226 + start_column),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(YEARint + 2)}:', summary_format_border_top)
        formula = '={1}{0}+{2}{0}'.format(
            total_row,
            xl_col_to_name(241 + start_column),
            xl_col_to_name(242 + start_column),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(YEARint + 2)}:', summary_format_border_bottom)
        formula = '={1}{0}'.format(
            total_row + 1,
            xl_col_to_name(241 + start_column),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Итого по Компании {str(YEARint)}-{str(YEARint + 2)}:', summary_format_border_top)
        formula = '={3}{0}+{3}{1}+{3}{2}'.format(row - 1, row - 3, row - 5, xl_col_to_name(3))
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Итого Расчетный План по Компании {str(YEARint)}-{str(YEARint + 2)}:', summary_format_border_bottom)
        formula = '={3}{0}+{3}{1}+{3}{2}'.format(row - 1, row - 3, row - 5, xl_col_to_name(3))
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)

        row += 2
        sheet.merge_range(row, 1, row, 2, 'Валовая прибыль (М1), без НДС', summary_format_border_top_center)
        sheet.write_string(row, 3, '', summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(YEARint)}:', summary_format_border_top)
        formula = '={1}{0}+{2}{0}+{3}{0}'.format(
            total_row,
            xl_col_to_name(217 + start_column),
            xl_col_to_name(218 + start_column),
            xl_col_to_name(219 + start_column),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(YEARint)}:', summary_format_border_bottom)
        formula = '={1}{0}+{2}{0}'.format(
            total_row + 1,
            xl_col_to_name(217 + start_column),
            xl_col_to_name(218 + start_column),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(YEARint + 1)}:', summary_format_border_top)
        formula = '={1}{0}+{2}{0}'.format(
            total_row,
            xl_col_to_name(233 + start_column),
            xl_col_to_name(234 + start_column),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(YEARint + 1)}:', summary_format_border_bottom)
        formula = '={1}{0}'.format(
            total_row + 1,
            xl_col_to_name(233 + start_column),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(YEARint + 2)}:', summary_format_border_top)
        formula = '={1}{0}+{2}{0}'.format(
            total_row,
            xl_col_to_name(248 + start_column),
            xl_col_to_name(249 + start_column),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(YEARint + 2)}:', summary_format_border_bottom)
        formula = '={1}{0}'.format(
            total_row + 1,
            xl_col_to_name(248 + start_column),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Итого по Компании {str(YEARint)}-{str(YEARint + 2)}:', summary_format_border_top)
        formula = '={3}{0}+{3}{1}+{3}{2}'.format(row - 1, row - 3, row - 5, xl_col_to_name(3))
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Итого Расчетный План по Компании {str(YEARint)}-{str(YEARint + 2)}:', summary_format_border_bottom)
        formula = '={3}{0}+{3}{1}+{3}{2}'.format(row - 1, row - 3, row - 5, xl_col_to_name(3))
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)

        print('dict_formula = ', dict_formula)
        return total_row

    def generate_xlsx_report(self, workbook, data, budgets):

        global YEARint
        YEARint = data['year']
        global year_end
        year_end = data['year_end']

        global dict_formula
        global koeff_reserve
        global koeff_potential
        global margin_shift
        global plan_shift
        global fact_columns
        global use_6_6
        global start_column
        use_6_6 = False
        koeff_reserve = data['koeff_reserve']
        koeff_potential = data['koeff_potential']
        fact_columns = set()
        project_office_ids=data['project_office_ids']

        systematica_forecast = data['systematica_forecast']

        start_column = 10

        plan_shift = {
            'revenue': {
                'Q1': start_column + 12,
                'Q2': start_column + 12 + 17,
                'HY1': start_column + 12 + 22,
                'Q3': start_column + 12 + 39,
                'Q3 6+6': start_column + 12 + 40,
                'Q4': start_column + 12 + 57,
                'Q4 6+6': start_column + 12 + 58,
                'HY2': start_column + 12 + 63,
                'HY2 6+6': start_column + 12 + 64,
                'Y': start_column + 12 + 69,
                'Y 6+6': start_column + 12 + 70,
                'NEXT': start_column + 221,
                'AFTER_NEXT': start_column + 236,
            },
            'pds': {
                'Q1': start_column + 96,
                'Q2': start_column + 96 + 13,
                'HY1': start_column + 96 + 17,
                'Q3': start_column + 96 + 30,
                'Q3 6+6': start_column + 96 + 31,
                'Q4': start_column + 96 + 44,
                'Q4 6+6': start_column + 96 + 45,
                'HY2': start_column + 96 + 49,
                'HY2 6+6': start_column + 96 + 50,
                'Y': start_column + 96 + 54,
                'Y 6+6': start_column + 96 + 55,
                'NEXT': start_column + 225,
                'AFTER_NEXT': start_column + 240,
            },
            'acceptance': {
                'Q1': start_column + 155,
                'Q2': start_column + 155 + 4,
                'HY1': start_column + 155 + 8,
                'Q3': start_column + 155 + 12,
                'Q3 6+6': start_column + 155 + 13,
                'Q4': start_column + 155 + 17,
                'Q4 6+6': start_column + 155 + 18,
                'HY2': start_column + 155 + 22,
                'HY2 6+6': start_column + 155 + 23,
                'Y': start_column + 155 + 27,
                'Y 6+6': start_column + 155 + 28,
                'NEXT': start_column + 228,
                'AFTER_NEXT': start_column + 243,
            },
            'margin': {
                'Q1': start_column + 188,
                'Q2': start_column + 188 + 4,
                'HY1': start_column + 188 + 8,
                'Q3': start_column + 188 + 12,
                'Q3 6+6': start_column + 188 + 13,
                'Q4': start_column + 188 + 17,
                'Q4 6+6': start_column + 188 + 18,
                'HY2': start_column + 188 + 22,
                'HY2 6+6': start_column + 188 + 23,
                'Y': start_column + 188 + 27,
                'Y 6+6': start_column + 188 + 28,
                'NEXT': start_column + 232,
                'AFTER_NEXT': start_column + 247,
            },
        }

        print('YEARint=',YEARint)

        commercial_budget_id = data['commercial_budget_id']
        budget = self.env['project_budget.commercial_budget'].search([('id', '=', commercial_budget_id)])
        dict_formula = {'printed_projects': set(), 'companies_lines': set(), 'offices_lines': set()}

        if systematica_forecast:

            litr_codes = ('ПО_ЛИТР',)

            oblako_codes = ('05', 'ПО_Облако.ру (облачный сервис)', 'ПО_Облако.ру (облачный сервис новые)', 'ПО_Облако.ру (облачный сервис база)', 'ПО_Облако.ру (интеграторский сервис)')

            oblako_ids = self.get_child_offices_ids(self.env['project_budget.project_office'].search([('code', 'in', oblako_codes)]).ids, [])
            litr_ids = self.get_child_offices_ids(self.env['project_budget.project_office'].search([('code', 'in', litr_codes)]).ids, [])
            systmatica_ids = self.env['project_budget.project_office'].search([
                ('id', 'in', project_office_ids),
                ('id', 'not in', oblako_ids),
                ('id', 'not in', litr_ids),
            ]).ids  # систематика без литр и облака

            dict_formula = {'printed_projects': set(), 'companies_lines': set(), 'offices_lines': set()}
            stages = self.env['project_budget.project.stage'].search([('code', '!=', '10')], order='sequence desc')
            self.printworksheet(workbook, budget, 'Прогноз (ЛИТР)', stages, litr_ids, False, 0, 'ЛИТР')

            dict_formula = {'printed_projects': set(), 'companies_lines': set(), 'offices_lines': set()}
            stages = self.env['project_budget.project.stage'].search([('code', '!=', '10')], order='sequence desc')
            oblako_row = self.printworksheet(workbook, budget, 'Прогноз (Облако.ру)', stages, oblako_ids, False, 0, False)

            dict_formula = {'printed_projects': set(), 'companies_lines': set(), 'offices_lines': set()}
            stages = self.env['project_budget.project.stage'].search([('code', '!=', '10')], order='sequence desc')
            self.printworksheet(workbook, budget, 'Прогноз', stages, systmatica_ids, True, oblako_row, 'СА+Облако.ру')

            dict_formula = {'printed_projects': set(), 'companies_lines': set(), 'offices_lines': set()}
            stages = self.env['project_budget.project.stage'].search([('code', '=', '10')], order='sequence desc')
            self.printworksheet(workbook, budget, '10%', stages, project_office_ids, False, 0, False)
        else:
            dict_formula = {'printed_projects': set(), 'companies_lines': set(), 'offices_lines': set()}
            stages = self.env['project_budget.project.stage'].search([('code', '!=', '10')], order='sequence desc')  # для сортировки так делаем
            self.printworksheet(workbook, budget, 'Прогноз', stages, project_office_ids, systematica_forecast, 0, False)

            dict_formula = {'printed_projects': set(), 'companies_lines': set(), 'offices_lines': set()}
            stages = self.env['project_budget.project.stage'].search([('code', '=', '10')], order='sequence desc')
            self.printworksheet(workbook, budget, '10%', stages, project_office_ids, systematica_forecast, 0, False)
