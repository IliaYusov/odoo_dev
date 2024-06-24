from odoo import models

import datetime
import xlsxwriter
from xlsxwriter.utility import xl_col_to_name


class report_svod_excel(models.AbstractModel):
    _name = 'report.project_budget.report_svod_excel'
    _description = 'project_budget.report_svod_excel'
    _inherit = 'report.report_xlsx.abstract'

    elements_list_head = ['FY YEAR', 'Q1 План', 'Январь(ВВ)', 'Q1(янв)', 'Февраль(ВВ)', 'Q1(фев)', 'Март(ВВ)',
                          'Q1(мар)',
                          'Q2 План', 'Апрель(ВВ)', 'Q2(апр)', 'Май(ВВ)', 'Q2(май)', 'Июнь(ВВ)', 'Q2(июнь)',
                          'Q3 План', 'Июль(ВВ)', 'Q3(июль)', 'Август(ВВ)', 'Q3(авг)', 'Сентябрь(ВВ)', 'Q3(сент)',
                          'Q4 План', 'Октябрь(ВВ)', 'Q4(окт)', 'Ноябрь(ВВ)', 'Q4(ноя)', 'Декабрь(ВВ)', 'Q4(дек)',
                          ]

    elements_list_year_Q = ['Контр-ие эталон (с НДС)', 'Контр-ие перенос (с НДС)', 'Контр-ие новые (с НДС)',
                            'Контр-ие факт (с НДС)'
        , 'Контр-ие остаток (с НДС)', 'ПДС эталон(с НДС)', 'ПДС перенос (с НДС)', 'ПДС новые (с НДС)',
                            'ПДС факт (с НДС)'
        , 'ПДС План остаток (с НДС)', 'ВВ эталон (без НДС)', 'ВВ перенос (без НДС)', 'ВВ новые (без НДС)',
                            'ВВ факт (без НДС)'
        , 'ВВ План остаток (без НДС)']
    YEARint = 2023
    year_end = 2023

    array_itogi_merge_office = [6, 7, 8, 9, 11, 12, 13, 14, 16, 17, 18, 19, 23, 24, 25, 26, 28, 29, 30, 31, 33, 34, 35, 36, 60, 61, 62, 63,
                   65, 66, 67, 68, 70, 71, 72, 73, 97, 98, 99, 100, 102, 103, 104, 105, 107, 108, 109, 110, 134, 135,
                   136, 137, 139, 140, 141, 142, 144, 145, 146, 147] # колонки где надо объединять и формулы итоговые по офису

    array_itogi_last_plan_office = [5, 10, 15, 22, 27, 32, 59,64,69,96,101,106,133,138,143] # колонки где надо  формулы итоговые по офису - послледний эталонный план

    def get_currency_rate_by_project(self,project):
        project_currency_rates = self.env['project_budget.project_currency_rates']
        return project_currency_rates._get_currency_rate_for_project_in_company_currency(project)

    def isProjectinYear(self, project):
        global YEARint

        if project:
            if project.stage_id.code == '0':  # проверяем последний зафиксированный бюджет в предыдущих годах
                last_fixed_project = self.env['project_budget.projects'].search(
                    [('date_actual', '<', datetime.date(YEARint,1,1)),
                     ('budget_state', '=', 'fixed'),
                     ('project_id', '=', project.project_id),
                     ], limit=1, order='date_actual desc')
                if last_fixed_project and last_fixed_project.stage_id.code == '0':
                    return False

            if (project.end_presale_project_month.year >= YEARint and project.end_presale_project_month.year <= year_end ) \
                    or (project.end_sale_project_month.year >= YEARint and project.end_sale_project_month.year <= year_end):
                return True
            for pds in project.planned_cash_flow_ids:
                if pds.date_cash.year >= YEARint and pds.date_cash.year <= year_end:
                    return True
            for pds in project.fact_cash_flow_ids:
                if pds.date_cash.year >= YEARint and pds.date_cash.year <= year_end:
                    return True
            for act in project.planned_acceptance_flow_ids:
                if act.date_cash.year >= YEARint and act.date_cash.year <= year_end:
                    return True
            for act in project.fact_acceptance_flow_ids:
                if act.date_cash.year >= YEARint and act.date_cash.year <= year_end:
                    return True
            for pds in project.planned_step_cash_flow_ids:
                if pds.date_cash.year >= YEARint and pds.date_cash.year <= year_end:
                    return True
            for pds in project.fact_step_cash_flow_ids:
                if pds.date_cash.year >= YEARint and pds.date_cash.year <= year_end:
                    return True
            for act in project.planned_step_acceptance_flow_ids:
                if act.date_cash.year >= YEARint and act.date_cash.year <= year_end:
                    return True
            for act in project.fact_step_acceptance_flow_ids:
                if act.date_cash.year >= YEARint and act.date_cash.year <= year_end:
                    return True

            etalon_project = self.get_etalon_project_first(project) # поищем первый эталон в году и если контрактование или последняя отгрузка были в году, то надо проект в отчете показывать
            if etalon_project:
                if (etalon_project.end_presale_project_month.year >= YEARint and  etalon_project.end_presale_project_month.year <= year_end)\
                        or (project.end_sale_project_month.year >= YEARint and project.end_sale_project_month.year <= year_end):
                    return True

        return False

    def getintestimated_probability(self, stage_id_code):
        if stage_id_code == '0' :
            return 0
        if stage_id_code == '30':
            return 30
        if stage_id_code == '50':
            return 50
        if stage_id_code == '75':
            return 75
        if stage_id_code == '100':
            return 100
        if stage_id_code == '100(done)':
            return 100
        return 0

    def get_etalon_budget(self):
        etalon_budget = self.env['project_budget.commercial_budget'].search(
            [('etalon_budget', '=', True), ('budget_state', '=', 'fixed'),('name','!=','ФИНАНСЫ эталон Q2')], limit=1,
            order='date_actual desc')
        return etalon_budget

    def get_etalon_project(self, spec):
        etalon_project = self.env['project_budget.projects'].search(
            [('etalon_budget', '=', True), ('budget_state', '=', 'fixed'), ('project_id', '=', spec.project_id)],
            limit=1, order='date_actual desc')
        # print('etalon_project.project_id = ',etalon_project.project_id)
        # print('etalon_project.date_actual = ',etalon_project.date_actual)
        return etalon_project

    def get_etalon_project_first(self,spec):
        global YEARint

        datesearch = datetime.date(YEARint, 1, 1)  # будем искать первый утвержденный в году
        etalon_project = self.env['project_budget.projects'].search([('etalon_budget', '=', True),
                                                                     ('budget_state', '=', 'fixed'),
                                                                     ('project_id', '=', spec.project_id),
                                                                     ('date_actual', '>=', datesearch)
                                                                     ], limit=1, order='date_actual')
        return etalon_project

    def print_head_elements_list_year_Q(self, workbook, sheet, row, column, head_format):
        for element in self.elements_list_year_Q:
            sheet.write_string(row, column, element, head_format)
            # if element in ('Контр-ие эталон (с НДС)','ПДС эталон(с НДС)', 'ВВ эталон (без НДС)',):
            # sheet.set_column(column, column, None, None, {'hidden': 1, 'level': 1})
            if element in ('Контр-ие перенос (с НДС)', 'Контр-ие новые (с НДС)', 'Контр-ие факт (с НДС)'
                           , 'Контр-ие остаток (с НДС)', 'ПДС перенос (с НДС)', 'ПДС новые (с НДС)', 'ПДС факт (с НДС)'
                           , 'ПДС План остаток (с НДС)', 'ВВ перенос (без НДС)', 'ВВ новые (без НДС)',
                           'ВВ факт (без НДС)'
                           , 'ВВ План остаток (без НДС)'):
                sheet.set_column(column, column, None, None, {'hidden': 1, 'level': 1})
            column += 1
        return column

    def print_week_sequence(self, sheet, row, column, cur_format, cur_range_array):
        # print('cur_range = ', cur_range_array)
        for mon in cur_range_array:
            # print('mon = ', mon)
            sheet.write_string(row, column, str(mon), cur_format)
            sheet.set_column(column, column, None, None, {'hidden': 1, 'level': 2})
            column += 1
        return column

    def print_head(self, workbook, sheet, row, column, YEAR, head_format_1, head_format_2, head_format_3):
        global YEARint
        global year_end
        for elementone in self.elements_list_head:
            element = elementone.replace('YEAR', YEAR)
            # print('element = ', element)
            column_beg = column
            if (element.find('FY ') != -1) or (element in ('Q1 План', 'Q2 План', 'Q3 План', 'Q4 План')):
                cur_format = head_format_1
                if (element.find('FY ') != -1) or (element in ('Q2 План', 'Q4 План')):
                    cur_format = head_format_1
                else:
                    if (element in ('Q1 План', 'Q3 План')):
                        cur_format = head_format_2
                column = self.print_head_elements_list_year_Q(workbook, sheet, row + 1, column, cur_format)
            else:
                cur_format = head_format_3
                if element == 'Январь(ВВ)':
                    cur_range_array = [1, 2, 3, 4]
                    column = self.print_week_sequence(sheet, row + 1, column, cur_format, cur_range_array)
                if element == 'Февраль(ВВ)':
                    cur_range_array = [5, 6, 7, 8]
                    column = self.print_week_sequence(sheet, row + 1, column, cur_format, cur_range_array)
                if element == 'Март(ВВ)':
                    cur_range_array = [9, 10, 11, 12]
                    column = self.print_week_sequence(sheet, row + 1, column, cur_format, cur_range_array)
                if element == 'Апрель(ВВ)':
                    cur_range_array = [13, 14, 15, 16]
                    column = self.print_week_sequence(sheet, row + 1, column, cur_format, cur_range_array)
                if element == 'Май(ВВ)':
                    cur_range_array = [17, 18, 19, 20]
                    column = self.print_week_sequence(sheet, row + 1, column, cur_format, cur_range_array)
                if element == 'Июнь(ВВ)':
                    cur_range_array = [21, 22, 23, 24]
                    column = self.print_week_sequence(sheet, row + 1, column, cur_format, cur_range_array)
                if element == 'Июль(ВВ)':
                    cur_range_array = [25, 26, 27, 28]
                    column = self.print_week_sequence(sheet, row + 1, column, cur_format, cur_range_array)
                if element == 'Август(ВВ)':
                    cur_range_array = [29, 30, 31, 32]
                    column = self.print_week_sequence(sheet, row + 1, column, cur_format, cur_range_array)
                if element == 'Сентябрь(ВВ)':
                    cur_range_array = [33, 34, 35, 36]
                    column = self.print_week_sequence(sheet, row + 1, column, cur_format, cur_range_array)
                if element == 'Октябрь(ВВ)':
                    cur_range_array = [37, 38, 39, 40]
                    column = self.print_week_sequence(sheet, row + 1, column, cur_format, cur_range_array)
                if element == 'Ноябрь(ВВ)':
                    cur_range_array = [41, 42, 43, 44]
                    column = self.print_week_sequence(sheet, row + 1, column, cur_format, cur_range_array)
                if element == 'Декабрь(ВВ)':
                    cur_range_array = [45, 46, 47, 48]
                    column = self.print_week_sequence(sheet, row + 1, column, cur_format, cur_range_array)

                if element in ('Q1(янв)', 'Q1(фев)', 'Q1(мар)',
                               'Q2 План', 'Q2(апр)', 'Q2(май)', 'Q2(июнь)',
                               'Q3 План', 'Q3(июль)', 'Q3(авг)', 'Q3(сент)',
                               'Q4 План', 'Q4(окт)', 'Q4(ноя)', 'Q4(дек)',
                               ):
                    sheet.write_string(row + 1, column, 'ПДС Факт (без НДС)', cur_format)
                    sheet.set_column(column, column, None, None, {'hidden': 1, 'level': 1})
                    column += 1
                    sheet.write_string(row + 1, column, 'ВВ Факт (без НДС)', cur_format)
                    sheet.set_column(column, column, None, None, {'hidden': 1, 'level': 1})
                    column += 1
            sheet.merge_range(row, column_beg, row, column - 1, element, cur_format)
            if (element.find('FY ') != -1) or (element in ('Q1 План', 'Q2 План', 'Q1(мар)', 'Q2(июнь)',
                                                           'Q3 План', 'Q3(сент)', 'Q4 План', 'Q4(дек)')):
                sheet.set_column(column, column, 2)
                column += 1
                sheet.set_column(column, column, 1)
                column += 1

    def get_sum_contract(self, project):
        global YEARint
        global year_end
        sum_year = 0
        sum_q1 = 0
        sum_q2 = 0
        sum_q3 = 0
        sum_q4 = 0
        if project:
            try:
                project_obj = project.projects_id
            except:
                project_obj = project
            currency_rate = self.get_currency_rate_by_project(project_obj)

            if project.stage_id.code in ('50', '75','100','100(done)'): # смотрим сумму контрактования в эталоне и с учетом 100
                if project.end_presale_project_month.year >= YEARint and project.end_presale_project_month.year <= year_end:
                    sum_year = project.total_amount_of_revenue_with_vat*currency_rate
                    if project.end_presale_project_month.month in (1, 2, 3):
                        sum_q1 += project.total_amount_of_revenue_with_vat*currency_rate
                    if project.end_presale_project_month.month in (4, 5, 6):
                        sum_q2 += project.total_amount_of_revenue_with_vat*currency_rate
                    if project.end_presale_project_month.month in (7, 8, 9):
                        sum_q3 += project.total_amount_of_revenue_with_vat*currency_rate
                    if project.end_presale_project_month.month in (10, 11, 12):
                        sum_q4 += project.total_amount_of_revenue_with_vat*currency_rate
        return sum_year, sum_q1, sum_q2, sum_q3, sum_q4

    def get_sum_contract_move(self, project, project_etalon):
        global YEARint
        global year_end
        sum_year = 0
        sum_q1 = 0
        sum_q2 = 0
        sum_q3 = 0
        sum_q4 = 0
        if project_etalon:  # если эталона нет, то считаем, что и переноса нет - все в новое пойдет
            if (project_etalon.stage_id.code in ('50', '75', '100','100(done)')) and (
                    project.stage_id.code in ('50', '75', '100','100(done)')):  # только 50 и 75  смотрим
                if project_etalon.end_presale_project_month.year >= YEARint \
                        and project_etalon.end_presale_project_month.year <= year_end :

                        #вот тут какая то муть была....
                        # and project.total_amount_of_revenue_with_vat == 0 \
                        # and project_etalon.total_amount_of_revenue_with_vat != 0:  # если эталон в этом году, то начинаем работать, далее только если 0 стало, а в эталоне не 0 считаем переносом
                        #

                    try:
                        project_obj = project_etalon.projects_id
                    except:
                        project_obj = project_etalon
                    currency_rate = self.get_currency_rate_by_project(project_obj)

                    if project_etalon.end_presale_project_month.year != project.end_presale_project_month.year:  # если поменялся год, то это перенос года
                        sum_year = project_etalon.total_amount_of_revenue_with_vat*currency_rate

                    if project_etalon.end_presale_project_month.year == project.end_presale_project_month.year and \
                       project_etalon.end_presale_project_quarter != project.end_presale_project_quarter:  # перенесли квартал не важно куда
                        if project_etalon.end_presale_project_month.month in (
                        1, 2, 3):  # а вот смотрим месяц попадания по эталонному бюджету
                            sum_q1 += project_etalon.total_amount_of_revenue_with_vat*currency_rate
                        if project_etalon.end_presale_project_month.month in (
                        4, 5, 6):  # а вот смотрим месяц попадания по эталонному бюджету
                            sum_q2 += project_etalon.total_amount_of_revenue_with_vat*currency_rate
                        if project_etalon.end_presale_project_month.month in (
                        7, 8, 9):  # а вот смотрим месяц попадания по эталонному бюджету
                            sum_q3 += project_etalon.total_amount_of_revenue_with_vat*currency_rate
                        if project_etalon.end_presale_project_month.month in (
                        10, 11, 12):  # а вот смотрим месяц попадания по эталонному бюджету
                            sum_q4 += project_etalon.total_amount_of_revenue_with_vat*currency_rate
        return sum_year, sum_q1, sum_q2, sum_q3, sum_q4

    def get_sum_contract_new(self, project, project_etalon):
        global YEARint
        global year_end

        sum_year = 0
        sum_q1 = 0
        sum_q2 = 0
        sum_q3 = 0
        sum_q4 = 0
        sum_contract_etalon_year = 0
        sum_contract_etalon_q1 = 0
        sum_contract_etalon_q2 = 0
        sum_contract_etalon_q3 = 0
        sum_contract_etalon_q4 = 0
        if project_etalon:
            if project_etalon.stage_id.code in (
            '50', '75', '100','100(done)'):  # если 30 или 0 то как будто нет ничего
                try:
                    project_obj = project_etalon.projects_id
                except:
                    project_obj = project_etalon
                currency_rate = self.get_currency_rate_by_project(project_obj)
                if project_etalon.end_presale_project_month.year >= YEARint \
                    and project_etalon.end_presale_project_month.year <= year_end:  # а если текущий год уже вперери.. то и показывать в отчете нечего
                    sum_contract_etalon_year = project_etalon.total_amount_of_revenue_with_vat*currency_rate
                    if project_etalon.end_presale_project_month.month in (
                    1, 2, 3):  # сумма контракта эталона в квартал
                        sum_contract_etalon_q1 = project_etalon.total_amount_of_revenue_with_vat*currency_rate
                    if project_etalon.end_presale_project_month.month in (
                    4, 5, 6):  # сумма контракта эталона в квартал
                        sum_contract_etalon_q2 = project_etalon.total_amount_of_revenue_with_vat*currency_rate
                    if project_etalon.end_presale_project_month.month in (
                    7, 8, 9):  # сумма контракта эталона в квартал
                        sum_contract_etalon_q3 = project_etalon.total_amount_of_revenue_with_vat*currency_rate
                    if project_etalon.end_presale_project_month.month in (
                    10, 11, 12):  # сумма контракта эталона в квартал
                        sum_contract_etalon_q4 = project_etalon.total_amount_of_revenue_with_vat*currency_rate

        if (project.stage_id.code in ('50', '75', '100','100(done)')):  # только 50 и 75 и 100 смотрим
            if project.end_presale_project_month.year >= YEARint\
                    and project.end_presale_project_month.year <= year_end :  # а если текущий год уже вперери.. то и показывать в отчете нечего
                try:
                    project_obj = project.projects_id
                except:
                    project_obj = project
                currency_rate = self.get_currency_rate_by_project(project_obj)
                if sum_contract_etalon_year == 0:  # сумма эталога в году 0
                    sum_year = project.total_amount_of_revenue_with_vat*currency_rate
                if project.end_presale_project_month.month in (
                1, 2, 3) and sum_contract_etalon_q1 == 0:  # в эталоне в кваратале было 0
                    sum_q1 += project.total_amount_of_revenue_with_vat*currency_rate
                if project.end_presale_project_month.month in (
                4, 5, 6) and sum_contract_etalon_q2 == 0:  # в эталоне в кваратале было 0
                    sum_q2 += project.total_amount_of_revenue_with_vat*currency_rate
                if project.end_presale_project_month.month in (
                7, 8, 9) and sum_contract_etalon_q3 == 0:  # в эталоне в кваратале было 0
                    sum_q3 += project.total_amount_of_revenue_with_vat*currency_rate
                if project.end_presale_project_month.month in (
                10, 11, 12) and sum_contract_etalon_q4 == 0:  # в эталоне в кваратале было 0
                    sum_q4 += project.total_amount_of_revenue_with_vat*currency_rate

        sum_year_fact, sum_q1_fact, sum_q2_fact, sum_q3_fact, sum_q4_fact = self.get_sum_contract_fact(project)
        # 20230530 Алина Козленко сказала, что если эталон 0, а факт есть, то новое = факт и это на все действует
        if sum_contract_etalon_year == 0 and sum_year_fact != 0 : sum_year = sum_year_fact
        if sum_contract_etalon_q1 == 0 and sum_q1_fact != 0 : sum_q1 = sum_q1_fact
        if sum_contract_etalon_q2 == 0 and sum_q2_fact != 0 : sum_q2 = sum_q2_fact
        if sum_contract_etalon_q3 == 0 and sum_q3_fact != 0 : sum_q3 = sum_q3_fact
        if sum_contract_etalon_q4 == 0 and sum_q4_fact != 0 : sum_q4 = sum_q4_fact

        return sum_year, sum_q1, sum_q2, sum_q3, sum_q4

    def get_sum_contract_fact(self, project):
        global YEARint
        global year_end

        sum_year = 0
        sum_q1 = 0
        sum_q2 = 0
        sum_q3 = 0
        sum_q4 = 0
        if not project:  # если нет объекта то все в 0
            return sum_year, sum_q1, sum_q2, sum_q3, sum_q4
        print('project.stage_id.code = ',project.stage_id.code)
        if project.stage_id.code in ('100','100(done)'):  # только 50 и 75  смотрим
            if project.end_presale_project_month.year >= YEARint\
                    and project.end_presale_project_month.year <= year_end:  # а если текущий год уже вперери.. то и показывать в отчете нечего
                try:
                    project_obj = project.projects_id
                except:
                    project_obj = project
                currency_rate = self.get_currency_rate_by_project(project_obj)
                sum_year = project.total_amount_of_revenue_with_vat
                if project.end_presale_project_month.month in (
                1, 2, 3):  # а вот смотрим месяц попадания по текущему бюджету
                    sum_q1 += project.total_amount_of_revenue_with_vat*currency_rate
                if project.end_presale_project_month.month in (
                4, 5, 6):  # а вот смотрим месяц попадания по текущему бюджету
                    sum_q2 += project.total_amount_of_revenue_with_vat*currency_rate
                if project.end_presale_project_month.month in (
                7, 8, 9):  # а вот смотрим месяц попадания по текущему бюджету
                    sum_q3 += project.total_amount_of_revenue_with_vat*currency_rate
                if project.end_presale_project_month.month in (
                10, 11, 12):  # а вот смотрим месяц попадания по текущему бюджету
                    sum_q4 += project.total_amount_of_revenue_with_vat*currency_rate

        return sum_year, sum_q1, sum_q2, sum_q3, sum_q4

    def get_sum_pds(self, project_cur, project):
        global YEARint
        global year_end

        sum_year = 0
        sum_q1 = 0
        sum_q2 = 0
        sum_q3 = 0
        sum_q4 = 0

        if project:
            if project_cur.stage_id.code in ('50', '75', '100','100(done)'): # вероятность по текущему проекту смотрим

                if project.step_status == 'project':
                    pds_list = project.planned_cash_flow_ids
                elif project.step_status == 'step':
                    pds_list = project.planned_step_cash_flow_ids

                for pds in pds_list:
                    if pds.date_cash.year >= YEARint and pds.date_cash.year <= year_end and pds.forecast in ('commitment', 'reserve', 'from_project'):
                        sum_year += pds.sum_cash
                        if pds.date_cash.month in (1, 2, 3):
                            sum_q1 += pds.sum_cash
                        if pds.date_cash.month in (4, 5, 6):
                            sum_q2 += pds.sum_cash
                        if pds.date_cash.month in (7, 8, 9):
                            sum_q3 += pds.sum_cash
                        if pds.date_cash.month in (10, 11, 12):
                            sum_q4 += pds.sum_cash
        return sum_year, sum_q1, sum_q2, sum_q3, sum_q4

    def get_sum_pds_move(self, project, project_etalon):
        global YEARint
        global year_end

        sum_etalon_year =  sum_etalon_q1 =  sum_etalon_q2 =  sum_etalon_q3 =  sum_etalon_q4 = 0
        calcsum = False

        if project.stage_id.code in ('50', '75', '100','100(done)'):

            sum_etalon_year, sum_etalon_q1, sum_etalon_q2, sum_etalon_q3, sum_etalon_q4 = self.get_sum_pds(project, project_etalon) # перенос сразу равен эталону
            sum_year, sum_q1, sum_q2, sum_q3, sum_q4 = self.get_sum_pds(project, project)
            # а если сейчас не 0, то перенос = 0
            if sum_year != 0: sum_etalon_year = 0
            if sum_q1 != 0: sum_etalon_q1 = 0
            if sum_q2 != 0: sum_etalon_q2 = 0
            if sum_q3 != 0: sum_etalon_q3 = 0
            if sum_q4 != 0: sum_etalon_q4 = 0

        return sum_etalon_year, sum_etalon_q1, sum_etalon_q2, sum_etalon_q3, sum_etalon_q4

    def get_sum_pds_new(self, project, project_etalon):
        global YEARint
        global year_end

        sum_etalon_year, sum_etalon_q1, sum_etalon_q2, sum_etalon_q3, sum_etalon_q4 = self.get_sum_pds(project, project_etalon)
        sum_year, sum_q1, sum_q2, sum_q3, sum_q4 = self.get_sum_pds(project, project) # сумму нового сразу присваиваем текущему
        # а если в эталоне не 0 , то новый = 0
        if sum_etalon_year != 0 : sum_year = 0
        if sum_etalon_q1 != 0 : sum_q1 = 0
        if sum_etalon_q2 != 0 : sum_q2 = 0
        if sum_etalon_q3 != 0 : sum_q3 = 0
        if sum_etalon_q4 != 0 : sum_q4 = 0

        sum_year_fact, sum_q1_fact, sum_q2_fact, sum_q3_fact, sum_q4_fact = self.get_sum_pds_fact(project)
        # 20230530 Алина Козленко сказала, что если в эталоне 0, а факт есть, то новое = факт и это на все действует
        if sum_etalon_year == 0 and sum_year_fact != 0: sum_year = sum_year_fact
        if sum_etalon_q1 == 0 and sum_q1_fact != 0 : sum_q1 = sum_q1_fact
        if sum_etalon_q2 == 0 and sum_q2_fact != 0 : sum_q2 = sum_q2_fact
        if sum_etalon_q3 == 0 and sum_q3_fact != 0 : sum_q3 = sum_q3_fact
        if sum_etalon_q4 == 0 and sum_q4_fact != 0: sum_q4 = sum_q4_fact
        return sum_year, sum_q1, sum_q2, sum_q3, sum_q4

    def get_sum_pds_fact(self, project):
        global YEARint
        global year_end

        sum_year = 0
        sum_q1 = 0
        sum_q2 = 0
        sum_q3 = 0
        sum_q4 = 0
        if project:

            if project.step_status == 'project':
                pds_list = project.fact_cash_flow_ids
            elif project.step_status == 'step':
                pds_list = project.fact_step_cash_flow_ids

            for pds in pds_list:
                if pds.date_cash.year >= YEARint and pds.date_cash.year <= year_end:
                    sum_year += pds.sum_cash
                    if pds.date_cash.month in (1, 2, 3):
                        sum_q1 += pds.sum_cash
                    if pds.date_cash.month in (4, 5, 6):
                        sum_q2 += pds.sum_cash
                    if pds.date_cash.month in (7, 8, 9):
                        sum_q3 += pds.sum_cash
                    if pds.date_cash.month in (10, 11, 12):
                        sum_q4 += pds.sum_cash
        return sum_year, sum_q1, sum_q2, sum_q3, sum_q4


    def get_sum_acceptance(self, project_cur, project):
        global YEARint
        global year_end
        sum_year = 0
        sum_q1 = 0
        sum_q2 = 0
        sum_q3 = 0
        sum_q4 = 0
        if project:

            if project_cur.stage_id.code in ('50', '75', '100','100(done)'): # вероятность по текущему проекту смотрим

                if project.step_status == 'project':
                    act_list = project.planned_acceptance_flow_ids
                elif project.step_status == 'step':
                    act_list = project.planned_step_acceptance_flow_ids

                for act in act_list:
                    if act.date_cash.year >= YEARint and act.date_cash.year <= year_end and act.forecast in ('commitment', 'reserve', 'from_project'):
                        sum_year += act.sum_cash_without_vat
                        if act.date_cash.month in (1, 2, 3):
                            sum_q1 += act.sum_cash_without_vat
                        if act.date_cash.month in (4, 5, 6):
                            sum_q2 += act.sum_cash_without_vat
                        if act.date_cash.month in (7, 8, 9):
                            sum_q3 += act.sum_cash_without_vat
                        if act.date_cash.month in (10, 11, 12):
                            sum_q4 += act.sum_cash_without_vat

        return sum_year, sum_q1, sum_q2, sum_q3, sum_q4

    def get_sum_acceptance_move(self, project, project_etalon):
        global YEARint
        global year_end

        sum_etalon_year =  sum_etalon_q1 =  sum_etalon_q2 =  sum_etalon_q3 =  sum_etalon_q4 = 0

        if project.stage_id.code in ('50', '75', '100','100(done)'):
            sum_etalon_year, sum_etalon_q1, sum_etalon_q2, sum_etalon_q3, sum_etalon_q4 = self.get_sum_acceptance(project, project_etalon) # перенос сразу равен эталону
            sum_year, sum_q1, sum_q2, sum_q3, sum_q4 = self.get_sum_acceptance(project, project)
            # а если сейчас не 0, то перенос = 0
            if sum_year != 0: sum_etalon_year = 0
            if sum_q1 != 0: sum_etalon_q1 = 0
            if sum_q2 != 0: sum_etalon_q2 = 0
            if sum_q3 != 0: sum_etalon_q3 = 0
            if sum_q4 != 0: sum_etalon_q4 = 0
        return sum_etalon_year, sum_etalon_q1, sum_etalon_q2, sum_etalon_q3, sum_etalon_q4

    def get_sum_acceptance_new(self, project, project_etalon):
        global YEARint
        global year_end

        sum_etalon_year, sum_etalon_q1, sum_etalon_q2, sum_etalon_q3, sum_etalon_q4 = self.get_sum_acceptance(project, project_etalon)
        sum_year, sum_q1, sum_q2, sum_q3, sum_q4 = self.get_sum_acceptance(project, project) # новый сразу = текущему
        # а если в эталоне не 0 но новый сразу в 0
        if sum_etalon_year != 0: sum_year = 0
        if sum_etalon_q1 != 0 : sum_q1 = 0
        if sum_etalon_q2 != 0 : sum_q2 = 0
        if sum_etalon_q3 != 0 : sum_q3 = 0
        if sum_etalon_q4 != 0 : sum_q4 = 0

        sum_year_fact, sum_q1_fact, sum_q2_fact, sum_q3_fact, sum_q4_fact = self.get_sum_acceptance_fact(project)
        # 20230530 Алина Козленко сказала, что если в эталоне 0, а факт есть, то новое = факт и это на все действует
        if sum_etalon_year == 0 and sum_year_fact != 0 : sum_year = sum_year_fact
        if sum_etalon_q1 == 0 and sum_q1_fact != 0 : sum_q1 = sum_q1_fact
        if sum_etalon_q2 == 0 and sum_q2_fact != 0 : sum_q2 = sum_q2_fact
        if sum_etalon_q3 == 0 and sum_q3_fact != 0 : sum_q3 = sum_q3_fact
        if sum_etalon_q4 == 0 and sum_q4_fact != 0 : sum_q4 = sum_q4_fact
        return sum_year, sum_q1, sum_q2, sum_q3, sum_q4

    def get_sum_acceptance_fact(self, project):
        global YEARint
        global year_end

        sum_year = 0
        sum_q1 = 0
        sum_q2 = 0
        sum_q3 = 0
        sum_q4 = 0
        if project:

            if project.step_status == 'project':
                act_list = project.fact_acceptance_flow_ids
            elif project.step_status == 'step':
                act_list = project.fact_step_acceptance_flow_ids

            for act in act_list:
                if act.date_cash.year >= YEARint and act.date_cash.year <= year_end:
                    sum_year += act.sum_cash_without_vat
                    if act.date_cash.month in (1, 2, 3):
                        sum_q1 += act.sum_cash_without_vat
                    if act.date_cash.month in (4, 5, 6):
                        sum_q2 += act.sum_cash_without_vat
                    if act.date_cash.month in (7, 8, 9):
                        sum_q3 += act.sum_cash_without_vat
                    if act.date_cash.month in (10, 11, 12):
                        sum_q4 += act.sum_cash_without_vat

        return sum_year, sum_q1, sum_q2, sum_q3, sum_q4

    def print_row_Values(self, workbook, sheet, row, column, project, row_format_number):
        global YEARint
        global year_end

        # row_format_number = workbook.add_format({
        #     'border': 1,
        #     'font_size': 9,
        # })
        # row_format_number.set_num_format('#,##0')

        etalon_project = self.get_etalon_project(project)

        sum_year = 0
        sum_q1 = 0
        sum_q2 = 0
        sum_q3 = 0
        sum_q4 = 0
        stage_id_code = ''

        # контрактование эталон
        stage_id_code = project.stage_id.code
        if etalon_project:
            sum_year, sum_q1, sum_q2, sum_q3, sum_q4 = self.get_sum_contract(etalon_project)
        sheet.write_number(row, column + 0, sum_year, row_format_number)
        sheet.write_number(row, column + 17, sum_q1, row_format_number)
        sheet.write_number(row, column + 54, sum_q2, row_format_number)
        sheet.write_number(row, column + 91, sum_q3, row_format_number)
        sheet.write_number(row, column + 128, sum_q4, row_format_number)
        # end контрактование эталон

        # контрактование перенос
        sum_year = 0
        sum_q1 = 0
        sum_q2 = 0
        sum_q3 = 0
        sum_q4 = 0

        if etalon_project:
            sum_year, sum_q1, sum_q2, sum_q3, sum_q4 = self.get_sum_contract_move(project, etalon_project)

        sheet.write_number(row, column + 1, sum_year, row_format_number)
        sheet.write_number(row, column + 18, sum_q1, row_format_number)
        sheet.write_number(row, column + 55, sum_q2, row_format_number)
        sheet.write_number(row, column + 92, sum_q3, row_format_number)
        sheet.write_number(row, column + 129, sum_q4, row_format_number)
        # end контрактование перенос

        # контрактование новые
        sum_year = 0
        sum_q1 = 0
        sum_q2 = 0
        sum_q3 = 0
        sum_q4 = 0

        sum_year, sum_q1, sum_q2, sum_q3, sum_q4 = self.get_sum_contract_new(project, etalon_project)

        sheet.write_number(row, column + 2, sum_year, row_format_number)
        sheet.write_number(row, column + 19, sum_q1, row_format_number)
        sheet.write_number(row, column + 56, sum_q2, row_format_number)
        sheet.write_number(row, column + 93, sum_q3, row_format_number)
        sheet.write_number(row, column + 130, sum_q4, row_format_number)
        # end контрактование новые

        # контрактование факт
        print('project_id = ', project.project_id)
        sum_year, sum_q1, sum_q2, sum_q3, sum_q4 = self.get_sum_contract_fact(project)

        sheet.write_number(row, column + 3, sum_year, row_format_number)
        sheet.write_number(row, column + 20, sum_q1, row_format_number)
        sheet.write_number(row, column + 57, sum_q2, row_format_number)
        sheet.write_number(row, column + 94, sum_q3, row_format_number)
        sheet.write_number(row, column + 131, sum_q4, row_format_number)
        # end контрактование факт

        # контрактование остаток
        sum_year_curr = sum_q1_curr = sum_q2_curr = sum_q3_curr = sum_q4_curr = 0

        sum_year_curr, sum_q1_curr, sum_q2_curr, sum_q3_curr, sum_q4_curr = self.get_sum_contract(project)


        colFormula = column + 4
        if stage_id_code in ('0','30'):
            formula = '=0'
        else:
            formula = '=-1*if({1} = 0, 0,{1}-{2}{0})'.format(row + 1,
                                                             sum_year_curr,#xl_col_to_name(colFormula - 4),
                                                          #   xl_col_to_name(colFormula - 2),
                                                          #   xl_col_to_name(colFormula - 3),
                                                             xl_col_to_name(colFormula - 1))
        sheet.write_formula(row, colFormula, formula, row_format_number)
        colFormula = column + 21
        if stage_id_code in ('0', '30'):
            formula = '=0'
        else:
            formula = '=-1*if({1} = 0, 0,{1}-{2}{0})'.format(row + 1,
                                                             sum_q1_curr   ,#xl_col_to_name(colFormula - 4), Алина сказала, что считаем только от текущего состояния, на эталон срать
                                                          #   xl_col_to_name(colFormula - 2),
                                                          #   xl_col_to_name(colFormula - 3),
                                                             xl_col_to_name(colFormula - 1))
        sheet.write_formula(row, colFormula, formula, row_format_number)
        colFormula = column + 58
        if stage_id_code in ('0', '30'):
            formula = '=0'
        else:
            formula = '=-1*if({1} = 0, 0,{1}-{2}{0})'.format(row + 1,
                                                             sum_q2_curr, #xl_col_to_name(colFormula - 4),
                                                          #   xl_col_to_name(colFormula - 2),
                                                          #   xl_col_to_name(colFormula - 3),
                                                             xl_col_to_name(colFormula - 1))
        sheet.write_formula(row, colFormula, formula, row_format_number)
        colFormula = column + 95
        if stage_id_code in ('0', '30'):
            formula = '=0'
        else:
            formula = '=-1*if({1} = 0, 0,{1}-{2}{0})'.format(row + 1,
                                                            sum_q3_curr, #xl_col_to_name(colFormula - 4),
                                                          #   xl_col_to_name(colFormula - 2),
                                                          #   xl_col_to_name(colFormula - 3),
                                                             xl_col_to_name(colFormula - 1))
        sheet.write_formula(row, colFormula, formula, row_format_number)
        colFormula = column + 132
        if stage_id_code in ('0', '30'):
            formula = '=0'
        else:
            formula = '=-1*if({1} = 0, 0,{1}-{2}{0})'.format(row + 1,
                                                            sum_q4_curr, #xl_col_to_name(colFormula - 4),
                                                          #   xl_col_to_name(colFormula - 2),
                                                          #   xl_col_to_name(colFormula - 3),
                                                             xl_col_to_name(colFormula - 1))
        sheet.write_formula(row, colFormula, formula, row_format_number)
        # end контрактование остаток

        # ПДС эталон
        sum_year,sum_q1, sum_q2, sum_q3, sum_q4 = self.get_sum_pds(project, etalon_project)
        sheet.write_number(row, column + 5, sum_year, row_format_number)
        sheet.write_number(row, column + 22, sum_q1, row_format_number)
        sheet.write_number(row, column + 59, sum_q2, row_format_number)
        sheet.write_number(row, column + 96, sum_q3, row_format_number)
        sheet.write_number(row, column + 133, sum_q4, row_format_number)
        # end ПДС эталон

        #  ПДС перенос
        sum_year,sum_q1, sum_q2, sum_q3, sum_q4 = self.get_sum_pds_move(project, etalon_project)
        sheet.write_number(row, column + 6, sum_year, row_format_number)
        sheet.write_number(row, column + 23, sum_q1, row_format_number)
        sheet.write_number(row, column + 60, sum_q2, row_format_number)
        sheet.write_number(row, column + 97, sum_q3, row_format_number)
        sheet.write_number(row, column + 134, sum_q4, row_format_number)
        #  end ПДС перенос

        #  ПДС новые
        sum_year,sum_q1, sum_q2, sum_q3, sum_q4 = self.get_sum_pds_new(project, etalon_project)
        sheet.write_number(row, column + 7, sum_year, row_format_number)
        sheet.write_number(row, column + 24, sum_q1, row_format_number)
        sheet.write_number(row, column + 61, sum_q2, row_format_number)
        sheet.write_number(row, column + 98, sum_q3, row_format_number)
        sheet.write_number(row, column + 135, sum_q4, row_format_number)
        #  end ПДС новые

        #  ПДС факт
        sum_year,sum_q1, sum_q2, sum_q3, sum_q4 = self.get_sum_pds_fact(project)
        sheet.write_number(row, column + 8, sum_year, row_format_number)
        sheet.write_number(row, column + 25, sum_q1, row_format_number)
        sheet.write_number(row, column + 62, sum_q2, row_format_number)
        sheet.write_number(row, column + 99, sum_q3, row_format_number)
        sheet.write_number(row, column + 136, sum_q4, row_format_number)
        #  end ПДС факт

        # ПДС остаток
        sum_year_curr = sum_q1_curr = sum_q2_curr = sum_q3_curr = sum_q4_curr = 0
        sum_year_curr, sum_q1_curr, sum_q2_curr, sum_q3_curr, sum_q4_curr = self.get_sum_pds(project, project)  # сумму нового сразу присваиваем текущему
        colFormula = column + 9
        if stage_id_code in ('0', '30'):
            formula = '=0'
        else:
            formula = '=-1*if({1} = 0, 0,{1}-{2}{0})'.format(row + 1,
                                                            sum_year_curr, #xl_col_to_name(colFormula - 4),Алина сказал, что смотри только на текущее состояние, на эталон срать
                                                          #   xl_col_to_name(colFormula - 2),
                                                          #   xl_col_to_name(colFormula - 3),
                                                             xl_col_to_name(colFormula - 1))
        sheet.write_formula(row, colFormula, formula, row_format_number)
        colFormula = column + 26
        if stage_id_code in ('0', '30'):
            formula = '=0'
        else:
            formula = '=-1*if({1} = 0, 0,{1}-{2}{0})'.format(row + 1,
                                                            sum_q1_curr,  #xl_col_to_name(colFormula - 4),
                                                          #   xl_col_to_name(colFormula - 2),
                                                          #   xl_col_to_name(colFormula - 3),
                                                             xl_col_to_name(colFormula - 1))
        sheet.write_formula(row, colFormula, formula, row_format_number)
        colFormula = column + 63
        if stage_id_code in ('0', '30'):
            formula = '=0'
        else:
            formula = '=-1*if({1} = 0, 0,{1}-{2}{0})'.format(row + 1,
                                                            sum_q2_curr ,#xl_col_to_name(colFormula - 4),
                                                          #   xl_col_to_name(colFormula - 2),
                                                          #   xl_col_to_name(colFormula - 3),
                                                             xl_col_to_name(colFormula - 1))
        sheet.write_formula(row, colFormula, formula, row_format_number)
        colFormula = column + 100
        if stage_id_code in ('0', '30'):
            formula = '=0'
        else:
            formula = '=-1*if({1} = 0, 0,{1}-{2}{0})'.format(row + 1,
                                                            sum_q3_curr, #xl_col_to_name(colFormula - 4),
                                                          #   xl_col_to_name(colFormula - 2),
                                                          #   xl_col_to_name(colFormula - 3),
                                                             xl_col_to_name(colFormula - 1))
        sheet.write_formula(row, colFormula, formula, row_format_number)
        colFormula = column + 137
        if stage_id_code in ('0', '30'):
            formula = '=0'
        else:
            formula = '=-1*if({1} = 0, 0,{1}-{2}{0})'.format(row + 1,
                                                            sum_q4_curr, #xl_col_to_name(colFormula - 4),
                                                          #   xl_col_to_name(colFormula - 2),
                                                          #   xl_col_to_name(colFormula - 3),
                                                             xl_col_to_name(colFormula - 1))
        sheet.write_formula(row, colFormula, formula, row_format_number)
        # end ПДС остаток

        # валовая выручка эталон
        sum_year,sum_q1, sum_q2, sum_q3, sum_q4 = self.get_sum_acceptance(project, etalon_project)
        sheet.write_number(row, column + 10, sum_year, row_format_number)
        sheet.write_number(row, column + 27, sum_q1, row_format_number)
        sheet.write_number(row, column + 64, sum_q2, row_format_number)
        sheet.write_number(row, column + 101, sum_q3, row_format_number)
        sheet.write_number(row, column + 138, sum_q4, row_format_number)
        # end валовая выручка эталон

        # валовая выручка перенос
        sum_year,sum_q1, sum_q2, sum_q3, sum_q4 = self.get_sum_acceptance_move(project, etalon_project)
        sheet.write_number(row, column + 11, sum_year, row_format_number)
        sheet.write_number(row, column + 28, sum_q1, row_format_number)
        sheet.write_number(row, column + 65, sum_q2, row_format_number)
        sheet.write_number(row, column + 102, sum_q3, row_format_number)
        sheet.write_number(row, column + 139, sum_q4, row_format_number)
        # end валовая выручка перенос

        # валовая выручка новые
        sum_year,sum_q1, sum_q2, sum_q3, sum_q4 = self.get_sum_acceptance_new(project, etalon_project)
        sheet.write_number(row, column + 12, sum_year, row_format_number)
        sheet.write_number(row, column + 29, sum_q1, row_format_number)
        sheet.write_number(row, column + 66, sum_q2, row_format_number)
        sheet.write_number(row, column + 103, sum_q3, row_format_number)
        sheet.write_number(row, column + 140, sum_q4, row_format_number)
        # end валовая выручка новые

        #  валовая выручка факт
        sum_year, sum_q1, sum_q2, sum_q3, sum_q4 = self.get_sum_acceptance_fact(project)
        sheet.write_number(row, column + 13, sum_year, row_format_number)
        sheet.write_number(row, column + 30, sum_q1, row_format_number)
        sheet.write_number(row, column + 67, sum_q2, row_format_number)
        sheet.write_number(row, column + 104, sum_q3, row_format_number)
        sheet.write_number(row, column + 141, sum_q4, row_format_number)
        #  end валовая выручка факт

        # валовая выручка остаток
        colFormula = column + 14
        sum_year_curr = sum_q1_curr = sum_q2_curr = sum_q3_curr = sum_q4_curr = 0
        sum_year_curr, sum_q1_curr, sum_q2_curr, sum_q3_curr, sum_q4_curr = self.get_sum_acceptance(project, project)
        formula = '=-1*if({1} = 0, 0, {1}-{2}{0})'.format(row + 1,
                                                             sum_year_curr,   #xl_col_to_name(colFormula - 4), аЛИНА СКАЗАЛА, ЧТО СМОТРИМ ТОЛЬКО НА ТЕКУЩЕЕ СОСТОЯНИЕ, НА ЭТАЛОН СРАТЬ
                                                       #      xl_col_to_name(colFormula - 2),
                                                       #      xl_col_to_name(colFormula - 3),
                                                             xl_col_to_name(colFormula - 1))
        sheet.write_formula(row, colFormula, formula, row_format_number)
        colFormula = column + 31
        if stage_id_code in ('0', '30'):
            formula = '=0'
        else:
            formula = '=-1*if({1} = 0, 0,{1}-{2}{0})'.format(row + 1,
                                                            sum_q1_curr, #xl_col_to_name(colFormula - 4),
                                                          #   xl_col_to_name(colFormula - 2),
                                                          #   xl_col_to_name(colFormula - 3),
                                                             xl_col_to_name(colFormula - 1))
        sheet.write_formula(row, colFormula, formula, row_format_number)
        colFormula = column + 68
        if stage_id_code in ('0', '30'):
            formula = '=0'
        else:
            formula = '=-1*if({1} = 0, 0,{1}-{2}{0})'.format(row + 1,
                                                            sum_q2_curr, #xl_col_to_name(colFormula - 4),
                                                          #   xl_col_to_name(colFormula - 2),
                                                          #   xl_col_to_name(colFormula - 3),
                                                             xl_col_to_name(colFormula - 1))
        sheet.write_formula(row, colFormula, formula, row_format_number)
        colFormula = column + 105
        if stage_id_code in ('0', '30'):
            formula = '=0'
        else:
            formula = '=-1*if({1} = 0, 0,{1}-{2}{0})'.format(row + 1,
                                                            sum_q3_curr,# xl_col_to_name(colFormula - 4),
                                                          #   xl_col_to_name(colFormula - 2),
                                                          #   xl_col_to_name(colFormula - 3),
                                                             xl_col_to_name(colFormula - 1))
        sheet.write_formula(row, colFormula, formula, row_format_number)
        colFormula = column + 142
        if stage_id_code in ('0', '30'):
            formula = '=0'
        else:
            formula = '=-1*if({1} = 0, 0,{1}-{2}{0})'.format(row + 1,
                                                            sum_q4_curr,# xl_col_to_name(colFormula - 4),
                                                            #№ xl_col_to_name(colFormula - 2),
                                                            # xl_col_to_name(colFormula - 3),
                                                             xl_col_to_name(colFormula - 1))
        sheet.write_formula(row, colFormula, formula, row_format_number)
        # end валовая выручка остаток

    def get_sum_contract_pds_act_budget(self, budget, project_office):
        global YEARint
        global year_end

        if project_office:
            projects = self.env['project_budget.projects'].search([
                ('project_office_id', '=', project_office.id),
                ('commercial_budget_id', '=', budget.id),
            ])
        else:
            projects = self.env['project_budget.projects'].search([('commercial_budget_id', '=', budget.id)])
        sum_contract_year = 0
        sum_pds_year = 0
        sum_act_year = 0
        sum_contract_q1 = 0
        sum_pds_q1 = 0
        sum_act_q1 = 0
        sum_contract_q2 = 0
        sum_pds_q2 = 0
        sum_act_q2 = 0
        sum_contract_q3 = 0
        sum_pds_q3 = 0
        sum_act_q3 = 0
        sum_contract_q4 = 0
        sum_pds_q4 = 0
        sum_act_q4 = 0
        for project in projects:
            currency_rate = self.get_currency_rate_by_project(project)

            if project.project_office_id == project_office and project.stage_id.code in ('75', '50','100','100(done)'):
                if project.end_presale_project_month.year >= YEARint and project.end_presale_project_month.year <= year_end:
                    sum_contract_year += project.total_amount_of_revenue_with_vat*currency_rate
                    if project.end_presale_project_month.month in (1, 2, 3):
                        sum_contract_q1 += project.total_amount_of_revenue_with_vat*currency_rate
                    if project.end_presale_project_month.month in (4, 5, 6):
                        sum_contract_q2 += project.total_amount_of_revenue_with_vat*currency_rate
                    if project.end_presale_project_month.month in (7, 8, 9):
                        sum_contract_q3 += project.total_amount_of_revenue_with_vat*currency_rate
                    if project.end_presale_project_month.month in (10, 11, 12):
                        sum_contract_q4 += project.total_amount_of_revenue_with_vat*currency_rate
                    if project.stage_id.code in ('100','100(done)', '75', '50'):
                        for pds in project.planned_cash_flow_ids:
                            if pds.date_cash.year >= YEARint and pds.date_cash.year <= year_end and pds.forecast in ('commitment', 'reserve', 'from_project'):
                                sum_pds_year += pds.sum_cash
                                if pds.date_cash.month in (1, 2, 3):
                                    sum_pds_q1 += project.total_amount_of_revenue_with_vat
                                if pds.date_cash.month in (4, 5, 6):
                                    sum_pds_q2 += project.total_amount_of_revenue_with_vat
                                if pds.date_cash.month in (7, 8, 9):
                                    sum_pds_q3 += project.total_amount_of_revenue_with_vat
                                if pds.date_cash.month in (10, 11, 12):
                                    sum_pds_q4 += project.total_amount_of_revenue_with_vat
                        for act in project.planned_acceptance_flow_ids:
                            if act.date_cash.year >= YEARint and act.date_cash.year <= year_end and act.forecast in ('commitment', 'reserve', 'from_project'):
                                sum_act_year += act.sum_cash_without_vat
                                if act.date_cash.month in (1, 2, 3):
                                    sum_act_q1 += act.sum_cash_without_vat
                                if act.date_cash.month in (4, 5, 6):
                                    sum_act_q2 += act.sum_cash_without_vat
                                if act.date_cash.month in (7, 8, 9):
                                    sum_act_q3 += act.sum_cash_without_vat
                                if act.date_cash.month in (10, 11, 12):
                                    sum_act_q4 += act.sum_cash_without_vat

        return sum_contract_year, sum_pds_year, sum_act_year, sum_contract_q1, sum_pds_q1, sum_act_q1, sum_contract_q2, \
            sum_pds_q2, sum_act_q2, sum_contract_q3, sum_pds_q3, sum_act_q3, sum_contract_q4, sum_pds_q4, sum_act_q4

    def print_etalon_budgets_name(self, budget, project_office, sheet, row, cur_format):
        global YEARint
        global year_end

        last_etalon_budget = self.get_etalon_budget()
        # print('last_etalon_budget = ', last_etalon_budget)
        commercial_budgets = self.env['project_budget.commercial_budget'].search(
            [('etalon_budget', '=', True), ('budget_state', '=', 'fixed'),('name','!=','ФИНАНСЫ эталон Q2')],
            order='date_actual')  # для сортировки так делаем

        isFirstIteration = True
        rowBeg = row
        for commercial_budget in commercial_budgets:
            if (project_office) and (isFirstIteration):
                isFirstIteration = False
                sheet.merge_range(row, 0, row, 4,
                                  project_office.name + '| План от ' + commercial_budget.date_actual.strftime(
                                      '%Y-%m-%d'), cur_format)
            else:
                sheet.merge_range(row, 0, row, 4, 'План от ' + commercial_budget.date_actual.strftime('%Y-%m-%d'),
                                  cur_format)
            if commercial_budget.id != last_etalon_budget.id:  # по последнему эталону надо формулами считать
                column = 5
                sum_contract_year, sum_pds_year, sum_act_year, sum_contract_q1, sum_pds_q1, sum_act_q1, sum_contract_q2, \
                    sum_pds_q2, sum_act_q2, sum_contract_q3, sum_pds_q3, sum_act_q3, sum_contract_q4, sum_pds_q4, sum_act_q4 \
                    = self.get_sum_contract_pds_act_budget(commercial_budget, project_office)
                sheet.write_number(row, column + 0, sum_contract_year, cur_format)
                sheet.write_number(row, column + 5, sum_pds_year, cur_format)
                sheet.write_number(row, column + 10, sum_act_year, cur_format)
                sheet.write_number(row, column + 17, sum_contract_q1, cur_format)
                sheet.write_number(row, column + 22, sum_pds_q1, cur_format)
                sheet.write_number(row, column + 27, sum_act_q1, cur_format)

                sheet.write_number(row, column + 54, sum_contract_q2, cur_format)
                sheet.write_number(row, column + 59, sum_pds_q2, cur_format)
                sheet.write_number(row, column + 64, sum_act_q2, cur_format)

                sheet.write_number(row, column + 91, sum_contract_q3, cur_format)
                sheet.write_number(row, column + 96, sum_pds_q3, cur_format)
                sheet.write_number(row, column + 101, sum_act_q3, cur_format)

                sheet.write_number(row, column + 128, sum_contract_q4, cur_format)
                sheet.write_number(row, column + 133, sum_pds_q4, cur_format)
                sheet.write_number(row, column + 138, sum_act_q4, cur_format)

            row += 1
        if project_office:
            sheet.merge_range(row, 0, row, 4,
                              'Прогноз c учетом отмен и переносов на ' + datetime.datetime.now().strftime('%Y-%m-%d'),
                              cur_format)
        else:
            sheet.merge_range(row, 0, row, 4, 'Прогноз на  ' + datetime.datetime.now().strftime('%Y-%m-%d'), cur_format)

        row += 1
        return row

    def printworksheet(self, workbook, budget, namesheet):
        global YEARint
        global year_end

        report_name = budget.name
        sheet = workbook.add_worksheet(namesheet)
        sheet.set_zoom(85)
        bold = workbook.add_format({'bold': True})
        money_format = workbook.add_format({'num_format': '#,##0'})
        head_format_1 = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_size': 10,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#D6DCE4'
        })
        head_format_2 = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_size': 10,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#D0CECE'
        })
        head_format_3 = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_size': 10,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#CCECFF'
        })
        row_format = workbook.add_format({
            'border': 1,
            'font_size': 9,
        })

        row_format_number = workbook.add_format({
            'border': 1,
            'font_size': 9,
        })
        row_format_number.set_num_format('#,##0;[red]-#,##0')

        row_format_canceled_project = workbook.add_format({
            'border': 1,
            'font_size': 9
        })
        row_format_canceled_project.set_font_color('red')

        row_format_number_canceled_project = workbook.add_format({
            'border': 1,
            'font_size': 9,
        })
        row_format_number_canceled_project.set_num_format('#,##0')
        row_format_number_canceled_project.set_font_color('red')

        row_format_number_probability_up = workbook.add_format({
            'border': 1,
            'font_size': 9,
        })
        row_format_number_probability_up.set_num_format('#,##0')
        row_format_number_probability_up.set_bg_color('#92D050')

        row_format_number_probability_down = workbook.add_format({
            'border': 1,
            'font_size': 9,
        })
        row_format_number_probability_down.set_num_format('#,##0')
        row_format_number_probability_down.set_bg_color('#FF0000')



        row_format_manager = workbook.add_format({
            'border': 1,
            'font_size': 9,
            "bold": True,
            'align': 'center',
            'valign': 'vcenter',
            "fg_color": '#FFD966',
        })
        row_format_manager.set_num_format('#,##0;[red]-#,##0')

        row_format_office = workbook.add_format({
            'border': 1,
            'font_size': 9,
            "bold": True,
            "fg_color": '#C7A6E8',
            'align': 'center',
            'valign': 'vcenter'
        })
        row_format_office.set_num_format('#,##0;[red]-#,##0')

        row_format_number_itogo = workbook.add_format({
            'border': 1,
            'font_size': 9,
            "bold": True,
            "fg_color": '#A9D08E',

        })
        row_format_number_itogo.set_num_format('#,##0;[red]-#,##0')

        row = 0
        column = 0
        sheet.merge_range(row, column, row + 1, column, "Проектныйофис", head_format_1)
        column += 1
        sheet.merge_range(row, column, row + 1, column, "Заказчик / Организация", head_format_1)
        column += 1
        sheet.merge_range(row, column, row + 1, column, "Суть проекта", head_format_1)
        column += 1
        sheet.merge_range(row, column, row + 1, column, "Менеджер по продажам", head_format_1)
        column += 1
        sheet.merge_range(row, column, row + 1, column, "Вероятность реализации проекта, %", head_format_1)
        column += 1
        strYEARprint = str(YEARint)
        if year_end != YEARint:
            strYEARprint = strYEARprint + " - " + str(year_end)

        column = self.print_head(workbook, sheet, row, column, strYEARprint, head_format_1, head_format_2,
                                 head_format_3)
        sheet.set_row(row, 50, None, None)
        row += 2
        row = self.print_etalon_budgets_name(budget, False, sheet, row, row_format_manager)
        for i in self.array_itogi_merge_office:
            sheet.merge_range(2, i, row - 1, i, '', row_format_manager)

        project_offices = self.env['project_budget.project_office'].search([],
                                                                           order='name')  # для сортировки так делаем
        key_account_managers = self.env.ref(
            'project_budget.group_project_budget_key_account_manager').users.employee_ids.sorted('name')
        # project_managers = self.env['project_budget.project_manager'].search([], order='name')  # для сортировки так делаем
        stages = self.env['project_budget.project.stage'].search([('name', '!=', '10')], order='sequence desc')  # для сортировки так делаем

        isFoundProjects = False
        begRowProjectsByManager = 0
        formulaItogo = '=sum(0'
        formula_itogo_last_plan = '=sum(0'
        formula_itogo_last_plan_Row_end = row-1
        isFoundProjectsByOffice = False
        formulaProjectOfficeRow = 0

        for project_office in project_offices:
            isFoundProjectsByOffice = False
            formulaProjectOffice = '=sum(0,'
            formulaProjectOffice_plan = ""
            for key_account_manager in key_account_managers:
                begRowProjectsByManager = 0
                column = -1
                isFoundProjects = False

                for stage in stages:
                    cur_budget_projects = self.env['project_budget.projects'].search([
                        ('project_office_id', '=', project_office.id),
                        ('commercial_budget_id', '=', budget.id),
                        ('key_account_manager_id', '=', key_account_manager.id),
                        # ('project_manager_id', '=', project_manager.id),
                        ('stage_id', '=', stage.id),
                        '|', '&', ('step_status', '=', 'step'),
                        ('step_project_parent_id.project_have_steps', '=', True),
                        ('project_have_steps', '=', False),
                    ], order='project_id')
                    for spec in cur_budget_projects:
                        if spec.project_office_id == project_office:
                            if self.isProjectinYear(spec) == False : continue
                            if (spec.vgo == '-'):
                                if isFoundProjectsByOffice == False:  # первый вход
                                    row += 1
                                    formulaProjectOfficeRow = row
                                    row = self.print_etalon_budgets_name(budget, project_office, sheet, row, row_format_office)
                                    row = row - 1
                                    formulaProjectOfficeRow_end = row
                                    formulaProjectOffice_plan = "= {0}" + str(row) + " - {1}"+str(formulaProjectOfficeRow + 1)+" + {2}"+str(formulaProjectOfficeRow + 1)
                                    for i in self.array_itogi_merge_office:
                                        sheet.merge_range(formulaProjectOfficeRow, i, row, i , '', row_format_office)

                                isFoundProjects = True
                                isFoundProjectsByOffice = True
                                row += 1
                                if begRowProjectsByManager == 0:
                                    begRowProjectsByManager = row

                            if spec.project_office_id == project_office:
                                sheet.set_row(row, None, None, {'hidden': 1, 'level': 2})
                                # print('setrow level2 row = ', row)
                                cur_row_format = row_format
                                cur_row_format_number = row_format_number
                                # print('spec.estimated_probability_id.name = ' + spec.estimated_probability_id.name)
                                etalon_spec = self.get_etalon_project(spec)
                                etalon_probability_int = 0
                                if etalon_spec:
                                    etalon_probability_int = self.getintestimated_probability(etalon_spec.stage_id.code)
                                current_probability_int = 0
                                if spec:
                                    current_probability_int = self.getintestimated_probability(spec.stage_id.code)
                                Probability_format = cur_row_format
                                if current_probability_int > etalon_probability_int:
                                    Probability_format = row_format_number_probability_up
                                if current_probability_int < etalon_probability_int:
                                    Probability_format = row_format_number_probability_down
                                if spec.stage_id.code == '0':
                                    # print('row_format_canceled_project')
                                    cur_row_format = row_format_canceled_project
                                    cur_row_format_number = row_format_number_canceled_project

                                column = 0
                                sheet.write_string(row, column, spec.project_office_id.name, cur_row_format)
                                column += 1
                                sheet.write_string(row, column, spec.partner_id.name, cur_row_format)
                                column += 1
                                if spec.step_status == 'step':
                                    sheet.write_string(row, column, spec.step_project_parent_id.project_id + ' | ' + spec.project_id + ' ' + spec.essence_project,
                                                       cur_row_format)
                                else:
                                    sheet.write_string(row, column, spec.project_id + ' ' + spec.essence_project, cur_row_format)
                                column += 1
                                sheet.write_string(row, column, spec.key_account_manager_id.name, cur_row_format)
                                column += 1
                                sheet.write_string(row, column, spec.stage_id.code, Probability_format)
                                column += 1
                                self.print_row_Values(workbook, sheet, row, column, spec, cur_row_format_number)
                # print('isFoundProjects = ' ,isFoundProjects)
                if isFoundProjects:
                    row += 1
                    column = 1
                    sheet.write_string(row, column, 'ИТОГО ' + key_account_manager.name, row_format_manager)
                    sheet.set_row(row, None, None, {'hidden': 1, 'level': 1})
                    formulaProjectOffice = formulaProjectOffice + ',{0}' + str(row + 1)
                    for colFormula in range(2, 5):
                        sheet.write_string(row, colFormula, '', row_format_manager)
                    for colFormula in range(5, 168):
                        formula = '=sum({2}{0}:{2}{1})'.format(begRowProjectsByManager + 1, row,
                                                               xl_col_to_name(colFormula))
                        sheet.write_formula(row, colFormula, formula, row_format_manager)

            if isFoundProjectsByOffice:
                sheet.set_row(row, None, None, {'hidden': 1, 'level': 1})
                column = 0
                # sheet.set_row(row, None, None, {'hidden': 1, 'level': 1})
                # print('setrow level1 row = ', row)
                formulaProjectOffice = formulaProjectOffice + ')'
                formulaItogo = formulaItogo + ',{0}' + str(formulaProjectOfficeRow + 1)
                formula_itogo_last_plan += ",{0}" + str(formulaProjectOfficeRow_end)
                # print('formulaProjectOffice = ',formulaProjectOffice)
                for colFormula in self.array_itogi_merge_office:
                    formula = formulaProjectOffice.format(xl_col_to_name(colFormula))
                    # print('formula = ', formula)
                    sheet.write_formula(formulaProjectOfficeRow, colFormula, formula, row_format_office)
                for colFormula in self.array_itogi_last_plan_office:
                    formula = formulaProjectOffice.format(xl_col_to_name(colFormula))
                    # print('formula = ', formula)
                    sheet.write_formula(formulaProjectOfficeRow_end-1, colFormula, formula, row_format_office)
                    formula = formulaProjectOffice_plan.format(xl_col_to_name(colFormula),xl_col_to_name(colFormula+1),xl_col_to_name(colFormula+2))
                    # print('formula = ', formula)
                    sheet.write_formula(formulaProjectOfficeRow_end, colFormula, formula, row_format_office)



        # row += 2
        # column = 0
        # sheet.write_string(row, column, 'ИТОГО по отчету' , row_format_number_itogo)
        formulaItogo = formulaItogo + ')'
        formula_itogo_last_plan = formula_itogo_last_plan + ')'
        for colFormula in self.array_itogi_merge_office:
            formula = formulaItogo.format(xl_col_to_name(colFormula))
            # print('formula = ', formula)
            sheet.write_formula(2, colFormula, formula, row_format_manager)
        for colFormula in self.array_itogi_last_plan_office:
            formula = formula_itogo_last_plan.format(xl_col_to_name(colFormula))
            # print('formula = ', formula)
            sheet.write_formula(formula_itogo_last_plan_Row_end - 1, colFormula, formula, row_format_manager)
            formula = "={0}"+str(formula_itogo_last_plan_Row_end)+" - {1}3 + {2}3"
            formula = formula.format(xl_col_to_name(colFormula), xl_col_to_name(colFormula + 1),xl_col_to_name(colFormula + 2))
            # print("formula = ",formula)
            # print("formula_itogo_last_plan_Row_end  = ",formula_itogo_last_plan_Row_end)
            sheet.write_formula(formula_itogo_last_plan_Row_end, colFormula, formula, row_format_manager)

        # for colFormula in range(1, 5):
        #     sheet.write_string(row, colFormula, '', row_format_number_itogo)
        # for colFormula in range(5, 79):
        #     formula = formulaItogo.format(xl_col_to_name(colFormula))
        #     # print('formula = ', formula)
        #     sheet.write_formula(row, colFormula, formula, row_format_number_itogo)

    def generate_xlsx_report(self, workbook, data, budgets):
        global YEARint
        YEARint = data['year']
        global year_end
        year_end = data['year_end']

        commercial_budget_id = data['commercial_budget_id']
        budget = self.env['project_budget.commercial_budget'].search([('id', '=', commercial_budget_id)])

        self.printworksheet(workbook, budget, 'Прогноз')
