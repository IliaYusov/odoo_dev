from odoo import models
import datetime
import xlsxwriter
from xlsxwriter.utility import xl_col_to_name
import logging

isdebug = False
logger = logging.getLogger("*___forecast_report___*")


class report_management_committee_excel(models.AbstractModel):
    _name = 'report.project_budget.report_management_committee_excel'
    _description = 'project_budget.report_management_committee_excel'
    _inherit = 'report.report_xlsx.abstract'

    strYEAR = '2023'
    YEARint = int(strYEAR)

    def get_currency_rate_by_project(self, project):
        project_currency_rates = self.env['project_budget.project_currency_rates']
        return project_currency_rates._get_currency_rate_for_project_in_company_currency(project)

    def isStepinYear(self, project, step):
        global strYEAR
        global YEARint

        years = (YEARint, YEARint + 1, YEARint + 2)

        if project:
            if step:
                if step.end_presale_project_month.year in years or step.end_sale_project_month.year in years:
                    return True
                for pds in project.planned_cash_flow_ids:
                    if pds.project_steps_id.id == step.id:
                        if pds.date_cash.year in years:
                            return True
                for pds in project.fact_cash_flow_ids:
                    if pds.project_steps_id.id == step.id:
                        if pds.date_cash.year in years:
                            return True
                for act in project.planned_acceptance_flow_ids:
                    if act.project_steps_id.id == step.id:
                        if act.date_cash.year in years:
                            return True
                for act in project.fact_acceptance_flow_ids:
                    if act.project_steps_id.id == step.id:
                        if act.date_cash.year in years:
                            return True
        return False

    def isProjectinYear(self, project):
        global strYEAR
        global YEARint

        years = (YEARint, YEARint + 1, YEARint + 2)

        if project:
            if project.project_have_steps == False:
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
            else:
                for step in project.project_steps_ids:
                    if self.isStepinYear(project, step):
                        return True

            etalon_project = self.get_etalon_project_first(
                project)  # поищем первый эталон в году и если контрактование или последняя отгрузка были в году, то надо проект в отчете показывать
            if etalon_project:
                if etalon_project.end_presale_project_month.year in years or project.end_sale_project_month.year in years:
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

    def get_etalon_project_first(self, spec):
        global strYEAR
        global YEARint

        datesearch = datetime.date(YEARint, 1, 1)  # будем искать первый утвержденный в году
        etalon_project = self.env['project_budget.projects'].search([('etalon_budget', '=', True),
                                                                     ('budget_state', '=', 'fixed'),
                                                                     ('project_id', '=', spec.project_id),
                                                                     ('date_actual', '>=', datesearch)
                                                                     ], limit=1, order='date_actual')
        return etalon_project

    def get_etalon_project(self, spec, quarter):
        global strYEAR
        global YEARint

        datesearch = datetime.date(YEARint, 1, 1)
        if 'Q1' in quarter:
            datesearch = datetime.date(YEARint, 1, 1)  # будем искать первый утвержденный в году
        if 'Q2' in quarter:
            datesearch = datetime.date(YEARint, 4, 1)  # будем искать первый утвержденный после марта
        if 'Q3' in quarter:
            datesearch = datetime.date(YEARint, 7, 1)  # будем искать первый утвержденный после июня
        if 'Q4' in quarter:
            datesearch = datetime.date(YEARint, 10, 1)  # будем искать первый утвержденный после сентября

        if isdebug:
            logger.info(' self.env[project_budget.projects].search ')
            logger.info(f'          etalon_budget = True')
            logger.info(f'          budget_state = fixed')
            logger.info(f'          project_id = {spec.project_id}')
            logger.info(f'          date_actual >= {datesearch}')
            logger.info(f'          limit=1, order= date_actual')

        etalon_project = self.env['project_budget.projects'].search([('etalon_budget', '=', True),
                                                                     ('budget_state', '=', 'fixed'),
                                                                     ('project_id', '=', spec.project_id),
                                                                     ('date_actual', '>=', datesearch)
                                                                     ], limit=1, order='date_actual')
        if etalon_project:
            if isdebug: logger.info(f'   etalon_project found by date ')
        else:  # если не нашли относительно даты, то поищем просто последний
            if isdebug: logger.info(f'   etalon_project NOT found by date ')
            etalon_project = self.env['project_budget.projects'].search([('etalon_budget', '=', True),
                                                                         ('budget_state', '=', 'fixed'),
                                                                         ('project_id', '=', spec.project_id)
                                                                         ], limit=1, order='date_actual desc')
        if isdebug:
            logger.info(f'  etalon_project.id = {etalon_project.id}')
            logger.info(f'  etalon_project.project_id = {etalon_project.project_id}')
            logger.info(f'  etalon_project.date_actual = {etalon_project.date_actual}')

        # print('etalon_project.project_id = ',etalon_project.project_id)
        # print('etalon_project.date_actual = ',etalon_project.date_actual)
        return etalon_project

    def get_etalon_step(self, step, quarter):
        global strYEAR
        global YEARint

        if isdebug:
            logger.info(f' start get_etalon_step')
            logger.info(f' quarter = {quarter}')
        if step is False:
            return False
        datesearch = datetime.date(YEARint, 1, 1)
        if 'Q1' in quarter:
            datesearch = datetime.date(YEARint, 1, 1)  # будем искать первый утвержденный в году
        if 'Q2' in quarter:
            datesearch = datetime.date(YEARint, 4, 1)  # будем искать первый утвержденный после марта
        if 'Q3' in quarter:
            datesearch = datetime.date(YEARint, 7, 1)  # будем искать первый утвержденный после июня
        if 'Q4' in quarter:
            datesearch = datetime.date(YEARint, 10, 1)  # будем искать первый утвержденный после сентября
        if isdebug:
            logger.info(f'   self.env[project_budget.projects].search ')
            logger.info(f'           etalon_budget = True')
            logger.info(f'           step_id = {step.step_id}')
            logger.info(f'           id != {step.id}')
            logger.info(f'           date_actual >= {datesearch}')
            logger.info(f'           limit = 1, order = date_actual')

        etalon_step = self.env['project_budget.project_steps'].search([('etalon_budget', '=', True),
                                                                       ('step_id', '=', step.step_id),
                                                                       ('id', '!=', step.id),
                                                                       ('date_actual', '>=', datesearch)
                                                                       ], limit=1, order='date_actual')
        if etalon_step:  # если не нашли относительно даты, то поищем просто последний
            if isdebug:
                logger.info(f'   !etalon_step found by date! ')
        else:  # если не нашли относительно даты, то поищем просто последний
            if isdebug:
                logger.info(f'   etalon_step NOT found by date ')
            etalon_step = self.env['project_budget.project_steps'].search([('etalon_budget', '=', True),
                                                                           ('step_id', '=', step.step_id),
                                                                           ('id', '!=', step.id)
                                                                           ], limit=1, order='date_actual desc')
        if isdebug:
            logger.info(f' step_id = {etalon_step.step_id}')
            logger.info(f' id = {etalon_step.id}')
            logger.info(f' date_actual = {etalon_step.date_actual}')
            logger.info(f' end_presale_project_month = {etalon_step.end_presale_project_month}')
            logger.info(f' estimated_probability_id = {etalon_step.estimated_probability_id}')
            logger.info(f' end get_etalon_step')
        return etalon_step

    def get_sum_fact_pds_project_step_year_quarter(self, project, step, year, quarter):

        sum_cash = 0

        if quarter:
            months = self.get_months_from_quarter(quarter)

        pds_list = project.fact_cash_flow_ids

        for pds in pds_list:
            if step:
                if pds.project_steps_id.id != step.id: continue
            if (not quarter or pds.date_cash.month in months) and pds.date_cash.year == year:
                sum_cash += pds.sum_cash

        return sum_cash

    def get_sum_plan_pds_project_step_year_quarter(self, project, step, year, quarter):
        global strYEAR
        global YEARint

        sum_cash = {'commitment': 0, 'reserve': 0, 'potential': 0}

        if quarter:
            months = self.get_months_from_quarter(quarter)

        pds_list = project.planned_cash_flow_ids

        for pds in pds_list:
            if step:
                if pds.project_steps_id.id != step.id: continue
            if (not quarter or pds.date_cash.month in months) and pds.date_cash.year == year:
                if pds.forecast == 'from_project':

                    if step:
                        estimated_probability_id_name = step.estimated_probability_id.name
                    else:
                        estimated_probability_id_name = project.estimated_probability_id.name

                    if estimated_probability_id_name in ('75', '100', '100(done)'):
                        sum_cash['commitment'] += pds.sum_cash
                    elif estimated_probability_id_name == '50':
                        sum_cash['reserve'] += pds.sum_cash
                    elif estimated_probability_id_name == '30':
                        sum_cash['potential'] += pds.sum_cash
                else:
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
                    addcolumn = 0
                    if 'HY2' in element or 'Q' in element:
                        addcolumn = -1

                    sheet.set_column(column, column + 5, 13)
                    if 'Q' in elementone:
                        sheet.set_column(column, column + 5, 13, False, {'hidden': 1, 'level': 2})
                    elif 'HY1' in elementone:
                        sheet.set_column(column, column + 5, 13, False, {'hidden': 1, 'level': 1})
                    elif 'HY2' in elementone:
                        sheet.set_column(column, column + 4, 13, False, {'hidden': 1, 'level': 1})

                    sheet.merge_range(row, column, row, column + 5 + addcolumn, element, head_format_month)

                    sheet.merge_range(row + 1, column, row + 2, column, "План " + element,
                                      head_format_month_itogo)
                    column += 1
                    sheet.merge_range(row + 1, column, row + 2, column, "План " + element + " 6+6",
                                      head_format_month_itogo_6_plus_6)

                    column += 1
                    sheet.merge_range(row + 1, column, row + 2, column, 'Факт', head_format_month_detail_fact)

                    if 'HY1' in element:
                        column += 1
                        sheet.merge_range(row + 1, column, row + 2, column, "% исполнения плана 6+6 " + element,
                                          head_format_month_itogo_percent)

                    if element == YEAR:
                        column += 1
                        sheet.merge_range(row + 1, column, row + 2, column, "% исполнения плана 6+6 " + element,
                                          head_format_month_itogo_percent)

                    column += 1
                    sheet.merge_range(row + 1, column, row + 1, column + 1, 'Прогноз до конца периода (на дату отчета)',
                                      head_format_month_detail)
                    sheet.write_string(row + 2, column, 'Обязательство', head_format_month_detail)
                    column += 1
                    sheet.write_string(row + 2, column, 'Резерв', head_format_month_detail)
                    column += 1

                elif element == 'NEXT':
                    sheet.merge_range(row, column, row, column + 2, 'Q1 ' + str(YEARint + 1), head_format_month_dark)
                    sheet.set_column(column, column + 3, 13, False, {'hidden': 1, 'level': 1})
                    sheet.merge_range(row + 1, column, row + 1, column + 2, 'Прогноз до конца периода (на дату отчета)',
                                      head_format_month_detail_next)
                    sheet.write_string(row + 2, column, 'Обязательство', head_format_month_detail_next)
                    column += 1
                    sheet.write_string(row + 2, column, 'Резерв', head_format_month_detail_next)
                    column += 1
                    sheet.write_string(row + 2, column, 'Потенциал', head_format_month_detail_next)
                    column += 1
                    sheet.merge_range(row, column, row, column + 2,str(YEARint + 1), head_format_month)
                    sheet.set_column(column, column + 3, 13, False, {'hidden': 1, 'level': 1})
                    sheet.merge_range(row + 1, column, row + 1, column + 2, 'Прогноз ' + str(YEARint + 1),
                                      head_format_month_detail_next)
                    sheet.write_string(row + 2, column, 'Обязательство', head_format_month_detail_next)
                    column += 1
                    sheet.write_string(row + 2, column, 'Резерв', head_format_month_detail_next)
                    column += 1
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

    # def print_month_head_revenue_margin(self,workbook,sheet,row,column,YEAR):
    #     global strYEAR
    #     global YEARint
    #
    #     for x in self.dict_revenue_margin.items():
    #         y = list(x[1].values())
    #         head_format_month = workbook.add_format({
    #             'border': 1,
    #             'text_wrap': True,
    #             'align': 'center',
    #             'valign': 'vcenter',
    #             "bold": True,
    #             "fg_color": y[1],
    #             "font_size": 11,
    #         })
    #         head_format_month_itogo = workbook.add_format({
    #             'border': 1,
    #             'text_wrap': True,
    #             'align': 'center',
    #             'valign': 'vcenter',
    #             "bold": True,
    #             "fg_color": '#D9E1F2',
    #             "font_size": 12,
    #         })
    #         head_format_month_itogo_6_plus_6 = workbook.add_format({
    #             'border': 1,
    #             'text_wrap': True,
    #             'align': 'center',
    #             'valign': 'vcenter',
    #             "bold": True,
    #             "fg_color": '#00b0f0',
    #             "font_size": 12,
    #         })
    #         head_format_month_itogo_percent = workbook.add_format({
    #             'border': 1,
    #             'text_wrap': True,
    #             'align': 'center',
    #             'valign': 'vcenter',
    #             "bold": True,
    #             "fg_color": '#ffff99',
    #             "font_size": 12,
    #         })
    #         head_format_month_detail = workbook.add_format({
    #             'border': 1,
    #             'text_wrap': True,
    #             'align': 'center',
    #             'valign': 'vcenter',
    #             "bold": False,
    #             "fg_color": '#E2EFDA',
    #             "font_size": 8,
    #         })
    #         head_format_month_detail_fact = workbook.add_format({
    #             'border': 1,
    #             'text_wrap': True,
    #             'align': 'center',
    #             'valign': 'vcenter',
    #             "bold": True,
    #             "fg_color": '#C6E0B4',
    #             "font_size": 8,
    #         })
    #
    #         colbeg = column
    #         for elementone in self.quarter_rus_name:
    #
    #             element = elementone.replace('YEAR', YEAR)
    #
    #             addcolumn = 0
    #             if 'HY2' in element or 'Q' in element:
    #                 addcolumn = -1
    #
    #             if elementone.find('Q') != -1:
    #                 sheet.set_column(column, column + 5, False, False, {'hidden': 1, 'level': 2})
    #
    #             if elementone.find('HY') != -1:
    #                 sheet.set_column(column, column + 5 + addcolumn, False, False, {'hidden': 1, 'level': 1})
    #
    #             sheet.merge_range(row, column, row, column + 5 + addcolumn, element, head_format_month)
    #
    #
    #             sheet.merge_range(row + 1, column, row + 2, column, "План " + element,
    #                               head_format_month_itogo)
    #             column += 1
    #
    #             sheet.merge_range(row + 1, column, row + 2, column, "План " + element + " 6+6",
    #                               head_format_month_itogo_6_plus_6)
    #             column += 1
    #             sheet.merge_range(row + 1, column, row + 2, column, 'Факт', head_format_month_detail_fact)
    #
    #
    #             if 'HY1' in element:
    #                 column += 1
    #                 sheet.merge_range(row + 1, column, row + 2, column, "% исполнения плана 6+6 " + element,
    #                                   head_format_month_itogo_percent)
    #             if element == YEAR:
    #                 column += 1
    #                 sheet.merge_range(row + 1, column, row + 2, column, "% исполнения плана 6+6 " + element,
    #                                   head_format_month_itogo_percent)
    #             column += 1
    #             sheet.merge_range(row + 1, column, row + 1, column + 1, 'Прогноз до конца периода (на дату отчета)',
    #                               head_format_month_detail)
    #             sheet.write_string(row + 2, column, 'Обязательство', head_format_month_detail)
    #             column += 1
    #             sheet.write_string(row + 2, column, 'Резерв', head_format_month_detail)
    #             column += 1
    #         sheet.merge_range(row-1, colbeg, row-1, column - 1, y[0], head_format_month)
    #     return column

    # def print_month_revenue_project(self, sheet, row, column, month, project, step, row_format_number, row_format_number_color_fact):
    #     global strYEAR
    #     global YEARint
    #
    #     sum75tmpetalon = 0
    #     sum50tmpetalon = 0
    #     sum100tmp = 0
    #     sum75tmp = 0
    #     sum50tmp = 0
    #     if month:
    #         project_etalon = self.get_etalon_project(project, self.get_quarter_from_month(month))
    #         if step == False:
    #             if project_etalon:
    #                 if month == project_etalon.end_presale_project_month.month and YEARint == project_etalon.end_presale_project_month.year:
    #                     if project_etalon.estimated_probability_id.name == '75':
    #                         sheet.write_number(row, column + 0, project_etalon.total_amount_of_revenue_with_vat, row_format_number)
    #                         sum75tmpetalon += project_etalon.total_amount_of_revenue_with_vat
    #                     if project_etalon.estimated_probability_id.name == '50':
    #                         sheet.write_number(row, column + 1, project_etalon.total_amount_of_revenue_with_vat, row_format_number)
    #                         sum50tmpetalon += project_etalon.total_amount_of_revenue_with_vat
    #
    #             if month == project.end_presale_project_month.month and YEARint == project.end_presale_project_month.year:
    #                 if project.estimated_probability_id.name in ('100','100(done)'):
    #                     sheet.write_number(row, column + 2, project.total_amount_of_revenue_with_vat, row_format_number_color_fact)
    #                     sum100tmp += project.total_amount_of_revenue_with_vat
    #                 if project.estimated_probability_id.name == '75':
    #                     sheet.write_number(row, column + 3, project.total_amount_of_revenue_with_vat, row_format_number)
    #                     sum75tmp += project.total_amount_of_revenue_with_vat
    #                 if project.estimated_probability_id.name == '50':
    #                     sheet.write_number(row, column + 4, project.total_amount_of_revenue_with_vat, row_format_number)
    #                     sum50tmp += project.total_amount_of_revenue_with_vat
    #         else:
    #             step_etalon  = self.get_etalon_step(step, self.get_quarter_from_month(month))
    #             if step_etalon:
    #                 if month == step_etalon.end_presale_project_month.month and YEARint == step_etalon.end_presale_project_month.year:
    #                     if step_etalon.estimated_probability_id.name == '75':
    #                         sheet.write_number(row, column + 0, step_etalon.total_amount_of_revenue_with_vat, row_format_number)
    #                         sum75tmpetalon = step_etalon.total_amount_of_revenue_with_vat
    #                     if step_etalon.estimated_probability_id.name == '50':
    #                         sheet.write_number(row, column + 1, step_etalon.total_amount_of_revenue_with_vat, row_format_number)
    #                         sum50tmpetalon = step_etalon.total_amount_of_revenue_with_vat
    #             else:
    #                 if project_etalon: # если нет жталонного этапа, то данные берем из проекта, да это будет увеличивать сумму на количество этапов, но что делать я ХЗ
    #                     if month == project_etalon.end_presale_project_month.month and YEARint == project_etalon.end_presale_project_month.year:
    #                         if project_etalon.estimated_probability_id.name == '75':
    #                             sheet.write_number(row, column + 0, project_etalon.total_amount_of_revenue_with_vat,
    #                                                row_format_number)
    #                             sum75tmpetalon += project_etalon.total_amount_of_revenue_with_vat
    #                         if project_etalon.estimated_probability_id.name == '50':
    #                             sheet.write_number(row, column + 1, project_etalon.total_amount_of_revenue_with_vat,
    #                                                row_format_number)
    #                             sum50tmpetalon += project_etalon.total_amount_of_revenue_with_vat
    #
    #             if month == step.end_presale_project_month.month and YEARint == step.end_presale_project_month.year:
    #                 if step.estimated_probability_id.name in ('100','100(done)'):
    #                     sheet.write_number(row, column + 2, step.total_amount_of_revenue_with_vat, row_format_number_color_fact)
    #                     sum100tmp = step.total_amount_of_revenue_with_vat
    #                 if step.estimated_probability_id.name == '75':
    #                     sheet.write_number(row, column + 3, step.total_amount_of_revenue_with_vat, row_format_number)
    #                     sum75tmp = step.total_amount_of_revenue_with_vat
    #                 if step.estimated_probability_id.name == '50':
    #                     sheet.write_number(row, column + 4, step.total_amount_of_revenue_with_vat, row_format_number)
    #                     sum50tmp = step.total_amount_of_revenue_with_vat
    #
    #     return sum75tmpetalon, sum50tmpetalon, sum100tmp, sum75tmp, sum50tmp

    def print_quarter_revenue_project(self, sheet, row, column, element, project, step, project_office, params, row_format_number, row_format_number_color_fact):
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

            if step == False:

                if project.end_presale_project_month.month in months and YEARint == project.end_presale_project_month.year:
                    currency_rate = self.get_currency_rate_by_project(project)
                    if project.estimated_probability_id.name in ('100','100(done)'):
                        sheet.write_number(row, column + 2, project.total_amount_of_revenue_with_vat * currency_rate, row_format_number_color_fact)
                        sum100tmp += project.total_amount_of_revenue_with_vat * currency_rate
                    if project.estimated_probability_id.name == '75':
                        sheet.write_number(row, column + 3, project.total_amount_of_revenue_with_vat * currency_rate, row_format_number)
                        sum75tmp += project.total_amount_of_revenue_with_vat * currency_rate
                    if project.estimated_probability_id.name == '50':
                        sheet.write_number(row, column + 4, project.total_amount_of_revenue_with_vat * currency_rate, row_format_number)
                        sum50tmp += project.total_amount_of_revenue_with_vat * currency_rate

            else:

                if ((project.legal_entity_signing_id.different_project_offices_in_steps and step.project_office_id == project_office)
                        or ((not project.legal_entity_signing_id.different_project_offices_in_steps or not step.project_office_id) and project.project_office_id == project_office)):

                    if step.end_presale_project_month.month in months  and YEARint == step.end_presale_project_month.year:
                        currency_rate = self.get_currency_rate_by_project(step.projects_id)
                        if step.estimated_probability_id.name in ('100','100(done)'):
                            sheet.write_number(row, column + 2, step.total_amount_of_revenue_with_vat * currency_rate, row_format_number_color_fact)
                            sum100tmp = step.total_amount_of_revenue_with_vat * currency_rate
                        if step.estimated_probability_id.name == '75':
                            sheet.write_number(row, column + 3, step.total_amount_of_revenue_with_vat * currency_rate, row_format_number)
                            sum75tmp = step.total_amount_of_revenue_with_vat * currency_rate
                        if step.estimated_probability_id.name == '50':
                            sheet.write_number(row, column + 4, step.total_amount_of_revenue_with_vat * currency_rate, row_format_number)
                            sum50tmp = step.total_amount_of_revenue_with_vat * currency_rate

        elif element == 'NEXT':
            if step == False:
                currency_rate = self.get_currency_rate_by_project(project)
                if project.end_presale_project_month.year == YEARint + 1 and project.end_presale_project_month.month in self.get_months_from_quarter('Q1'):
                    if project.estimated_probability_id.name in ('75', '100'):
                        sheet.write_number(row, column + 0,
                                           project.total_amount_of_revenue_with_vat * currency_rate,
                                           row_format_number)
                        sum_next_75_tmp = project.total_amount_of_revenue_with_vat * currency_rate
                    if project.estimated_probability_id.name == '50':
                        sheet.write_number(row, column + 1,
                                           project.total_amount_of_revenue_with_vat * params['50'] * currency_rate,
                                           row_format_number)
                        sum_next_50_tmp = project.total_amount_of_revenue_with_vat * params['50'] * currency_rate
                    if project.estimated_probability_id.name == '30':
                        sheet.write_number(row, column + 2,
                                           project.total_amount_of_revenue_with_vat * params['30'] * currency_rate,
                                           row_format_number)
                        sum_next_30_tmp = project.total_amount_of_revenue_with_vat * params['30'] * currency_rate
                if project.end_presale_project_month.year == YEARint + 1:
                    if project.estimated_probability_id.name in ('75', '100'):
                        sheet.write_number(row, column + 3,
                                           project.total_amount_of_revenue_with_vat * currency_rate,
                                           row_format_number)
                        sum_next_75_tmp = project.total_amount_of_revenue_with_vat * currency_rate
                    if project.estimated_probability_id.name == '50':
                        sheet.write_number(row, column + 4,
                                           project.total_amount_of_revenue_with_vat * params['50'] * currency_rate,
                                           row_format_number)
                        sum_next_50_tmp = project.total_amount_of_revenue_with_vat * params['50'] * currency_rate
                    if project.estimated_probability_id.name == '30':
                        sheet.write_number(row, column + 5,
                                           project.total_amount_of_revenue_with_vat * params['30'] * currency_rate,
                                           row_format_number)
                        sum_next_30_tmp = project.total_amount_of_revenue_with_vat * params['30'] * currency_rate
                elif project.end_presale_project_month.year == YEARint + 2:
                    if project.estimated_probability_id.name in ('75', '100'):
                        sum_after_next_tmp = project.total_amount_of_revenue_with_vat * currency_rate
                    if project.estimated_probability_id.name == '50':
                        sum_after_next_tmp = project.total_amount_of_revenue_with_vat * params[
                            '50'] * currency_rate
                    if project.estimated_probability_id.name == '30':
                        sum_after_next_tmp = project.total_amount_of_revenue_with_vat * params[
                            '30'] * currency_rate
                    sheet.write_number(row, column + 6,
                                       sum_after_next_tmp,
                                       row_format_number)

            else:

                if ((
                        project.legal_entity_signing_id.different_project_offices_in_steps and step.project_office_id == project_office)
                        or ((
                                    not project.legal_entity_signing_id.different_project_offices_in_steps or not step.project_office_id) and project.project_office_id == project_office)):

                    currency_rate = self.get_currency_rate_by_project(step.projects_id)
                    if step.end_presale_project_month.year == YEARint + 1 and step.end_presale_project_month.month in self.get_months_from_quarter('Q1'):
                        if step.estimated_probability_id.name in ('75', '100'):
                            sheet.write_number(row, column + 0,
                                               step.total_amount_of_revenue_with_vat * currency_rate,
                                               row_format_number)
                            sum_next_75_tmp += step.total_amount_of_revenue_with_vat * currency_rate
                        if step.estimated_probability_id.name == '50':
                            sheet.write_number(row, column + 1,
                                               step.total_amount_of_revenue_with_vat * params[
                                                   '50'] * currency_rate,
                                               row_format_number)
                            sum_next_50_tmp += step.total_amount_of_revenue_with_vat * params[
                                '50'] * currency_rate
                        if step.estimated_probability_id.name == '30':
                            sheet.write_number(row, column + 2,
                                               step.total_amount_of_revenue_with_vat * params[
                                                   '30'] * currency_rate,
                                               row_format_number)
                            sum_next_30_tmp += step.total_amount_of_revenue_with_vat * params[
                                '30'] * currency_rate
                    if step.end_presale_project_month.year == YEARint + 1:
                        if step.estimated_probability_id.name in ('75', '100'):
                            sheet.write_number(row, column + 3,
                                               step.total_amount_of_revenue_with_vat * currency_rate,
                                               row_format_number)
                            sum_next_75_tmp += step.total_amount_of_revenue_with_vat * currency_rate
                        if step.estimated_probability_id.name == '50':
                            sheet.write_number(row, column + 4,
                                               step.total_amount_of_revenue_with_vat * params[
                                                   '50'] * currency_rate,
                                               row_format_number)
                            sum_next_50_tmp += step.total_amount_of_revenue_with_vat * params[
                                '50'] * currency_rate
                        if step.estimated_probability_id.name == '30':
                            sheet.write_number(row, column + 5,
                                               step.total_amount_of_revenue_with_vat * params[
                                                   '30'] * currency_rate,
                                               row_format_number)
                            sum_next_30_tmp += step.total_amount_of_revenue_with_vat * params[
                                '30'] * currency_rate
                    elif step.end_presale_project_month.year == YEARint + 2:
                        if step.estimated_probability_id.name in ('75', '100'):
                            sum_after_next_tmp += step.total_amount_of_revenue_with_vat * currency_rate
                        if step.estimated_probability_id.name == '50':
                            sum_after_next_tmp += step.total_amount_of_revenue_with_vat * params[
                                '50'] * currency_rate
                        if step.estimated_probability_id.name == '30':
                            sum_after_next_tmp += step.total_amount_of_revenue_with_vat * params[
                                '30'] * currency_rate
                        sheet.write_number(row, column + 6,
                                           sum_after_next_tmp,
                                           row_format_number)

        return sum75tmpetalon, sum50tmpetalon, sum100tmp, sum75tmp, sum50tmp

    def calculate_quarter_revenue(self, element, project, project_office, params):
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

            if not project.project_have_steps:

                if project.end_presale_project_month.month in months and YEARint == project.end_presale_project_month.year:
                    currency_rate = self.get_currency_rate_by_project(project)
                    if project.estimated_probability_id.name in ('100', '100(done)'):
                        sum100tmp = project.total_amount_of_revenue_with_vat * currency_rate
                    if project.estimated_probability_id.name == '75':
                        sum75tmp = project.total_amount_of_revenue_with_vat * currency_rate
                    if project.estimated_probability_id.name == '50':
                        sum50tmp = project.total_amount_of_revenue_with_vat * currency_rate

            else:
                for step in project.project_steps_ids:

                    if ((
                            project.legal_entity_signing_id.different_project_offices_in_steps and step.project_office_id == project_office)
                            or ((
                                        not project.legal_entity_signing_id.different_project_offices_in_steps or not step.project_office_id) and project.project_office_id == project_office)):

                        if step.end_presale_project_month.month in months and YEARint == step.end_presale_project_month.year:
                            currency_rate = self.get_currency_rate_by_project(step.projects_id)
                            if step.estimated_probability_id.name in ('100', '100(done)'):
                                sum100tmp += step.total_amount_of_revenue_with_vat * currency_rate
                            if step.estimated_probability_id.name == '75':
                                sum75tmp += step.total_amount_of_revenue_with_vat * currency_rate
                            if step.estimated_probability_id.name == '50':
                                sum50tmp += step.total_amount_of_revenue_with_vat * currency_rate

        elif 'NEXT' in element:
            if not project.project_have_steps:
                if project.end_presale_project_month.year == YEARint + 1 and project.end_presale_project_month.month in self.get_months_from_quarter('Q1'):
                    currency_rate = self.get_currency_rate_by_project(project)
                    if project.estimated_probability_id.name in ('75', '100'):
                        sum_next_75_q1_tmp = project.total_amount_of_revenue_with_vat * currency_rate
                    if project.estimated_probability_id.name == '50':
                        sum_next_50_q1_tmp = project.total_amount_of_revenue_with_vat * params['50'] * currency_rate
                    if project.estimated_probability_id.name == '30':
                        sum_next_30_q1_tmp = project.total_amount_of_revenue_with_vat * params['30'] * currency_rate
                if project.end_presale_project_month.year == YEARint + 1:
                    currency_rate = self.get_currency_rate_by_project(project)
                    if project.estimated_probability_id.name in ('75', '100'):
                        sum_next_75_tmp = project.total_amount_of_revenue_with_vat * currency_rate
                    if project.estimated_probability_id.name == '50':
                        sum_next_50_tmp = project.total_amount_of_revenue_with_vat * params['50'] * currency_rate
                    if project.estimated_probability_id.name == '30':
                        sum_next_30_tmp = project.total_amount_of_revenue_with_vat * params['30'] * currency_rate
                elif project.end_presale_project_month.year == YEARint + 2:
                    currency_rate = self.get_currency_rate_by_project(project)
                    if project.estimated_probability_id.name in ('75', '100'):
                        sum_after_next_tmp = project.total_amount_of_revenue_with_vat * currency_rate
                    if project.estimated_probability_id.name == '50':
                        sum_after_next_tmp = project.total_amount_of_revenue_with_vat * params[
                            '50'] * currency_rate
                    if project.estimated_probability_id.name == '30':
                        sum_after_next_tmp = project.total_amount_of_revenue_with_vat * params[
                            '30'] * currency_rate

            else:
                for step in project.project_steps_ids:

                    if ((
                            project.legal_entity_signing_id.different_project_offices_in_steps and step.project_office_id == project_office)
                            or ((
                                        not project.legal_entity_signing_id.different_project_offices_in_steps or not step.project_office_id) and project.project_office_id == project_office)):

                        currency_rate = self.get_currency_rate_by_project(step.projects_id)
                        if step.end_presale_project_month.year == YEARint + 1 and step.end_presale_project_month.month in self.get_months_from_quarter('Q1'):
                            if step.estimated_probability_id.name in ('75', '100'):
                                sum_next_75_q1_tmp += step.total_amount_of_revenue_with_vat * currency_rate
                            if step.estimated_probability_id.name == '50':
                                sum_next_50_q1_tmp += step.total_amount_of_revenue_with_vat * params[
                                    '50'] * currency_rate
                            if step.estimated_probability_id.name == '30':
                                sum_next_30_q1_tmp += step.total_amount_of_revenue_with_vat * params[
                                    '30'] * currency_rate
                        if step.end_presale_project_month.year == YEARint + 1:
                            if step.estimated_probability_id.name in ('75', '100'):
                                sum_next_75_tmp += step.total_amount_of_revenue_with_vat * currency_rate
                            if step.estimated_probability_id.name == '50':
                                sum_next_50_tmp += step.total_amount_of_revenue_with_vat * params[
                                    '50'] * currency_rate
                            if step.estimated_probability_id.name == '30':
                                sum_next_30_tmp += step.total_amount_of_revenue_with_vat * params[
                                    '30'] * currency_rate
                        elif step.end_presale_project_month.year == YEARint + 2:
                            if step.estimated_probability_id.name in ('75', '100'):
                                sum_after_next_tmp += step.total_amount_of_revenue_with_vat * currency_rate
                            if step.estimated_probability_id.name == '50':
                                sum_after_next_tmp += step.total_amount_of_revenue_with_vat * params[
                                    '50'] * currency_rate
                            if step.estimated_probability_id.name == '30':
                                sum_after_next_tmp += step.total_amount_of_revenue_with_vat * params[
                                    '30'] * currency_rate

        return (sum75tmpetalon, sum50tmpetalon,
                sum100tmp, sum75tmp, sum50tmp,
                sum_next_75_q1_tmp, sum_next_50_q1_tmp, sum_next_30_q1_tmp,
                sum_next_75_tmp, sum_next_50_tmp, sum_next_30_tmp,
                sum_after_next_tmp)

    def get_pds_forecast_from_distributions(self, sum, project, step, year, months):

        sum_distribution_pds = 0
        sum_ostatok_pds = {'commitment': 0, 'reserve': 0, 'potential': 0}

        for planned_cash in project.planned_cash_flow_ids:
            if ((not step or planned_cash.project_steps_id.id == step.id)
                    and (not months or planned_cash.date_cash.month in months)
                    and planned_cash.date_cash.year == year):
                sum_distribution_pds += planned_cash.distribution_sum_without_vat
                if planned_cash.forecast == 'from_project':
                    estimated_probability_id_name = project.estimated_probability_id.name
                    if step:
                        estimated_probability_id_name = step.estimated_probability_id.name
                    if estimated_probability_id_name in ('75', '100', '100(done)'):
                        sum_ostatok_pds['commitment'] += planned_cash.distribution_sum_with_vat_ostatok
                    elif estimated_probability_id_name == '50':
                        sum_ostatok_pds['reserve'] += planned_cash.distribution_sum_with_vat_ostatok
                    elif estimated_probability_id_name == '30':
                        sum_ostatok_pds['potential'] += planned_cash.distribution_sum_with_vat_ostatok
                else:
                    sum_ostatok_pds[planned_cash.forecast] += planned_cash.distribution_sum_with_vat_ostatok

        if sum_distribution_pds != 0:  # если есть распределение, то остаток = остатку распределения
            sum = sum_ostatok_pds
            for key in sum:
                sum[key] = max(sum[key], 0)

        return sum

    def print_quarter_pds_project(self, sheet, row, column, element, project, step, project_office, params, row_format_number, row_format_number_color_fact):
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

            if step:

                if ((
                        project.legal_entity_signing_id.different_project_offices_in_steps and step.project_office_id == project_office)
                        or ((
                                    not project.legal_entity_signing_id.different_project_offices_in_steps or not step.project_office_id) and project.project_office_id == project_office)):

                    sum100tmp_step = self.get_sum_fact_pds_project_step_year_quarter(project, step, YEARint, element)
                    sheet.write_number(row, column + 2, sum100tmp_step, row_format_number_color_fact)

                    sum100tmp += sum100tmp_step

                    sum = self.get_sum_plan_pds_project_step_year_quarter(project, step, YEARint, element)

                    if sum100tmp_step >= sum['commitment']:
                        sum100tmp_step_ostatok = sum100tmp_step - sum['commitment']
                        sum['commitment'] = 0
                        sum['reserve'] = max(sum['reserve'] - sum100tmp_step_ostatok, 0)
                    else:
                        sum['commitment'] = sum['commitment'] - sum100tmp_step

                    # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                    sum = self.get_pds_forecast_from_distributions(sum, project, step, YEARint, months)

                    sheet.write_number(row, column + 3, sum['commitment'], row_format_number)
                    sum75tmp += sum['commitment']
                    sheet.write_number(row, column + 4, sum['reserve'], row_format_number)
                    sum50tmp += sum['reserve']
            else:
                sum100tmp = self.get_sum_fact_pds_project_step_year_quarter(project, False, YEARint,element)
                sheet.write_number(row, column + 2, sum100tmp, row_format_number_color_fact)

                sum = self.get_sum_plan_pds_project_step_year_quarter(project, False, YEARint, element)

                if sum100tmp >= sum['commitment']:
                    sum100tmp_ostatok = sum100tmp - sum['commitment']
                    sum['commitment'] = 0
                    sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                else:
                    sum['commitment'] = sum['commitment'] - sum100tmp

                # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                sum = self.get_pds_forecast_from_distributions(sum, project, False, YEARint, months)

                sheet.write_number(row, column + 3, sum['commitment'], row_format_number)
                sum75tmp += sum['commitment']
                sheet.write_number(row, column + 4, sum['reserve'], row_format_number)
                sum50tmp += sum['reserve']

        elif element == 'NEXT':
            if step:

                if ((
                        project.legal_entity_signing_id.different_project_offices_in_steps and step.project_office_id == project_office)
                        or ((
                                    not project.legal_entity_signing_id.different_project_offices_in_steps or not step.project_office_id) and project.project_office_id == project_office)):

                    sum100tmp_q1_step = self.get_sum_fact_pds_project_step_year_quarter(project, step, YEARint + 1, 'Q1')
                    sum100tmp_step = self.get_sum_fact_pds_project_step_year_quarter(project, step, YEARint + 1, False)
                    sum100tmp += sum100tmp_step
                    sum_q1 = self.get_sum_plan_pds_project_step_year_quarter(project, step, YEARint + 1, 'Q1')
                    sum = self.get_sum_plan_pds_project_step_year_quarter(project, step, YEARint + 1, False)

                    if sum100tmp_q1_step >= sum_q1['commitment']:
                        sum100tmp_q1_step_ostatok = sum100tmp_q1_step - sum_q1['commitment']
                        sum_q1['commitment'] = 0
                        sum_q1['reserve'] = max(sum_q1['reserve'] - sum100tmp_q1_step_ostatok, 0)
                    else:
                        sum_q1['commitment'] = sum_q1['commitment'] - sum100tmp_q1_step

                    if sum100tmp_step >= sum['commitment']:
                        sum100tmp_step_ostatok = sum100tmp_step - sum['commitment']
                        sum['commitment'] = 0
                        sum['reserve'] = max(sum['reserve'] - sum100tmp_step_ostatok, 0)
                    else:
                        sum['commitment'] = sum['commitment'] - sum100tmp_step

                    # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                    sum_q1 = self.get_pds_forecast_from_distributions(sum_q1, project, step, YEARint + 1,
                                                                      self.get_months_from_quarter('Q1'))
                    sum = self.get_pds_forecast_from_distributions(sum, project, step, YEARint + 1, False)

                    sheet.write_number(row, column + 0, sum_q1['commitment'], row_format_number)
                    sum_next_75_q1_tmp += sum_q1['commitment']
                    sheet.write_number(row, column + 1, sum_q1['reserve'] * params['50'], row_format_number)
                    sum_next_50_q1_tmp += sum_q1['reserve'] * params['50']
                    sheet.write_number(row, column + 2, sum_q1['potential'] * params['30'], row_format_number)
                    sum_next_30_q1_tmp += sum_q1['potential'] * params['30']

                    sheet.write_number(row, column + 3, sum['commitment'], row_format_number)
                    sum_next_75_tmp += sum['commitment']
                    sheet.write_number(row, column + 4, sum['reserve'] * params['50'], row_format_number)
                    sum_next_50_tmp += sum['reserve'] * params['50']
                    sheet.write_number(row, column + 5, sum['potential'] * params['30'], row_format_number)
                    sum_next_30_tmp += sum['potential'] * params['30']
            else:
                sum100tmp_q1 = self.get_sum_fact_pds_project_step_year_quarter(project, False, YEARint + 1, 'Q1')
                sum100tmp = self.get_sum_fact_pds_project_step_year_quarter(project, False, YEARint + 1, False)
                sum_q1 = self.get_sum_plan_pds_project_step_year_quarter(project, False, YEARint + 1, 'Q1')
                sum = self.get_sum_plan_pds_project_step_year_quarter(project, False, YEARint + 1, False)

                if sum100tmp_q1 >= sum_q1['commitment']:
                    sum100tmp_q1_ostatok = sum100tmp_q1 - sum_q1['commitment']
                    sum_q1['commitment'] = 0
                    sum_q1['reserve'] = max(sum_q1['reserve'] - sum100tmp_q1_ostatok, 0)
                else:
                    sum_q1['commitment'] = sum_q1['commitment'] - sum100tmp_q1

                if sum100tmp >= sum['commitment']:
                    sum100tmp_ostatok = sum100tmp - sum['commitment']
                    sum['commitment'] = 0
                    sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                else:
                    sum['commitment'] = sum['commitment'] - sum100tmp

                # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                sum_q1 = self.get_pds_forecast_from_distributions(sum_q1, project, False, YEARint + 1, self.get_months_from_quarter('Q1'))
                sum = self.get_pds_forecast_from_distributions(sum, project, False, YEARint + 1, False)

                sheet.write_number(row, column + 0, sum_q1['commitment'], row_format_number)
                sum_next_75_tmp += sum_q1['commitment']
                sheet.write_number(row, column + 1, sum_q1['reserve'] * params['50'], row_format_number)
                sum_next_50_tmp += sum_q1['reserve'] * params['50']
                sheet.write_number(row, column + 2, sum_q1['potential'] * params['30'], row_format_number)
                sum_next_30_tmp += sum_q1['potential'] * params['30']
                sheet.write_number(row, column + 3, sum['commitment'], row_format_number)
                sum_next_75_tmp += sum['commitment']
                sheet.write_number(row, column + 4, sum['reserve'] * params['50'], row_format_number)
                sum_next_50_tmp += sum['reserve'] * params['50']
                sheet.write_number(row, column + 5, sum['potential'] * params['30'], row_format_number)
                sum_next_30_tmp += sum['potential'] * params['30']

        elif element == 'AFTER NEXT':
            if step:

                if ((
                        project.legal_entity_signing_id.different_project_offices_in_steps and step.project_office_id == project_office)
                        or ((
                                    not project.legal_entity_signing_id.different_project_offices_in_steps or not step.project_office_id) and project.project_office_id == project_office)):

                    sum100tmp_step = self.get_sum_fact_pds_project_step_year_quarter(project, step, YEARint + 2, False)
                    sum100tmp += sum100tmp_step
                    sum = self.get_sum_plan_pds_project_step_year_quarter(project, step, YEARint + 2, False)

                    if sum100tmp_step >= sum['commitment']:
                        sum100tmp_step_ostatok = sum100tmp_step - sum['commitment']
                        sum['commitment'] = 0
                        sum['reserve'] = max(sum['reserve'] - sum100tmp_step_ostatok, 0)
                    else:
                        sum['commitment'] = sum['commitment'] - sum100tmp_step

                    # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                    sum = self.get_pds_forecast_from_distributions(sum, project, step, YEARint + 2, False)

                    sum_after_next_tmp += sum['commitment']
                    sum_after_next_tmp += sum['reserve'] * params['50']
                    sum_after_next_tmp += sum['potential'] * params['30']
                    sheet.write_number(row, column + 0, sum_after_next_tmp, row_format_number)

            else:
                sum100tmp = self.get_sum_fact_pds_project_step_year_quarter(project, False, YEARint + 2, False)
                sum = self.get_sum_plan_pds_project_step_year_quarter(project, False, YEARint + 2, False)

                if sum100tmp >= sum['commitment']:
                    sum100tmp_ostatok = sum100tmp - sum['commitment']
                    sum['commitment'] = 0
                    sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                else:
                    sum['commitment'] = sum['commitment'] - sum100tmp

                # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                sum = self.get_pds_forecast_from_distributions(sum , project, False, YEARint + 2, False)

                sum_after_next_tmp += sum['commitment']
                sum_after_next_tmp += sum['reserve'] * params['50']
                sum_after_next_tmp += sum['potential'] * params['30']
                sheet.write_number(row, column + 0, sum_after_next_tmp, row_format_number)

        return sum75tmpetalon, sum50tmpetalon, sum100tmp, sum75tmp, sum50tmp

    def calculate_quarter_pds(self, element, project, project_office, params):
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

            if project.project_have_steps:
                for step in project.project_steps_ids:

                    if ((
                            project.legal_entity_signing_id.different_project_offices_in_steps and step.project_office_id == project_office)
                            or ((
                                        not project.legal_entity_signing_id.different_project_offices_in_steps or not step.project_office_id) and project.project_office_id == project_office)):

                        sum100tmp_step = self.get_sum_fact_pds_project_step_year_quarter(project, step, YEARint, element)

                        sum100tmp += sum100tmp_step

                        sum = self.get_sum_plan_pds_project_step_year_quarter(project, step, YEARint, element)

                        if sum100tmp_step >= sum['commitment']:
                            sum100tmp_step_ostatok = sum100tmp_step - sum['commitment']
                            sum['commitment'] = 0
                            sum['reserve'] = max(sum['reserve'] - sum100tmp_step_ostatok, 0)
                        else:
                            sum['commitment'] = sum['commitment'] - sum100tmp_step
                        # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                        sum = self.get_pds_forecast_from_distributions(sum, project, step, YEARint, months)

                        sum75tmp += sum['commitment']
                        sum50tmp += sum['reserve']

            else:
                sum100tmp = self.get_sum_fact_pds_project_step_year_quarter(project, False, YEARint, element)
                sum = self.get_sum_plan_pds_project_step_year_quarter(project, False, YEARint, element)

                if sum100tmp >= sum['commitment']:
                    sum100tmp_ostatok = sum100tmp - sum['commitment']
                    sum['commitment'] = 0
                    sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                else:
                    sum['commitment'] = sum['commitment'] - sum100tmp

                # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                sum = self.get_pds_forecast_from_distributions(sum, project, False, YEARint, months)

                sum75tmp += sum['commitment']
                sum50tmp += sum['reserve']

        elif element == 'NEXT':
            if project.project_have_steps:
                for step in project.project_steps_ids:

                    if ((
                            project.legal_entity_signing_id.different_project_offices_in_steps and step.project_office_id == project_office)
                            or ((
                                        not project.legal_entity_signing_id.different_project_offices_in_steps or not step.project_office_id) and project.project_office_id == project_office)):

                        sum100tmp_q1_step = self.get_sum_fact_pds_project_step_year_quarter(project, step, YEARint + 1, 'Q1')
                        sum100tmp_step = self.get_sum_fact_pds_project_step_year_quarter(project, step, YEARint + 1, False)
                        sum100tmp += sum100tmp_step
                        sum_q1 = self.get_sum_plan_pds_project_step_year_quarter(project, step, YEARint + 1, 'Q1')
                        sum = self.get_sum_plan_pds_project_step_year_quarter(project, step, YEARint + 1, False)

                        if sum100tmp_q1_step >= sum_q1['commitment']:
                            sum100tmp_q1_step_ostatok = sum100tmp_q1_step - sum_q1['commitment']
                            sum_q1['commitment'] = 0
                            sum_q1['reserve'] = max(sum_q1['reserve'] - sum100tmp_q1_step_ostatok, 0)
                        else:
                            sum_q1['commitment'] = sum_q1['commitment'] - sum100tmp_q1_step

                        if sum100tmp_step >= sum['commitment']:
                            sum100tmp_step_ostatok = sum100tmp_step - sum['commitment']
                            sum['commitment'] = 0
                            sum['reserve'] = max(sum['reserve'] - sum100tmp_step_ostatok, 0)
                        else:
                            sum['commitment'] = sum['commitment'] - sum100tmp_step

                        # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                        sum_q1 = self.get_pds_forecast_from_distributions(sum_q1, project, step, YEARint + 1, self.get_months_from_quarter('Q1'))
                        sum = self.get_pds_forecast_from_distributions(sum, project, step, YEARint + 1, False)

                        sum_next_75_q1_tmp += sum_q1['commitment']
                        sum_next_50_q1_tmp += sum_q1['reserve'] * params['50']
                        sum_next_30_q1_tmp += sum_q1['potential'] * params['30']

                        sum_next_75_tmp += sum['commitment']
                        sum_next_50_tmp += sum['reserve'] * params['50']
                        sum_next_30_tmp += sum['potential'] * params['30']
            else:
                sum100tmp_q1 = self.get_sum_fact_pds_project_step_year_quarter(project, False, YEARint + 1, 'Q1')
                sum100tmp = self.get_sum_fact_pds_project_step_year_quarter(project, False, YEARint + 1, False)
                sum_q1 = self.get_sum_plan_pds_project_step_year_quarter(project, False, YEARint + 1, 'Q1')
                sum = self.get_sum_plan_pds_project_step_year_quarter(project, False, YEARint + 1, False)

                if sum100tmp_q1 >= sum_q1['commitment']:
                    sum100tmp_q1_ostatok = sum100tmp_q1 - sum_q1['commitment']
                    sum_q1['commitment'] = 0
                    sum_q1['reserve'] = max(sum_q1['reserve'] - sum100tmp_q1_ostatok, 0)
                else:
                    sum_q1['commitment'] = sum_q1['commitment'] - sum100tmp_q1

                if sum100tmp >= sum['commitment']:
                    sum100tmp_ostatok = sum100tmp - sum['commitment']
                    sum['commitment'] = 0
                    sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                else:
                    sum['commitment'] = sum['commitment'] - sum100tmp

                # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                sum_q1 = self.get_pds_forecast_from_distributions(sum_q1, project, False, YEARint + 1, self.get_months_from_quarter('Q1'))
                sum = self.get_pds_forecast_from_distributions(sum, project, False, YEARint + 1, False)

                sum_next_75_q1_tmp += sum_q1['commitment']
                sum_next_50_q1_tmp += sum_q1['reserve'] * params['50']
                sum_next_30_q1_tmp += sum_q1['potential'] * params['30']

                sum_next_75_tmp += sum['commitment']
                sum_next_50_tmp += sum['reserve'] * params['50']
                sum_next_30_tmp += sum['potential'] * params['30']

        elif element == 'AFTER NEXT':
            if project.project_have_steps:
                for step in project.project_steps_ids:

                    if ((
                            project.legal_entity_signing_id.different_project_offices_in_steps and step.project_office_id == project_office)
                            or ((
                                        not project.legal_entity_signing_id.different_project_offices_in_steps or not step.project_office_id) and project.project_office_id == project_office)):

                        sum100tmp_step = self.get_sum_fact_pds_project_step_year_quarter(project, step, YEARint + 2, False)
                        sum100tmp += sum100tmp_step
                        sum = self.get_sum_plan_pds_project_step_year_quarter(project, step, YEARint + 2, False)

                        if sum100tmp_step >= sum['commitment']:
                            sum100tmp_step_ostatok = sum100tmp_step - sum['commitment']
                            sum['commitment'] = 0
                            sum['reserve'] = max(sum['reserve'] - sum100tmp_step_ostatok, 0)
                        else:
                            sum['commitment'] = sum['commitment'] - sum100tmp_step

                        # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                        sum = self.get_pds_forecast_from_distributions(sum, project, step, YEARint + 2, False)

                        sum_after_next_tmp += sum['commitment']
                        sum_after_next_tmp += sum['reserve'] * params['50']
                        sum_after_next_tmp += sum['potential'] * params['30']

            else:
                sum100tmp = self.get_sum_fact_pds_project_step_year_quarter(project, False, YEARint + 2, False)
                sum = self.get_sum_plan_pds_project_step_year_quarter(project, False, YEARint + 2, False)

                if sum100tmp >= sum['commitment']:
                    sum100tmp_ostatok = sum100tmp - sum['commitment']
                    sum['commitment'] = 0
                    sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                else:
                    sum['commitment'] = sum['commitment'] - sum100tmp

                # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                sum = self.get_pds_forecast_from_distributions(sum, project, False, YEARint + 2, False)

                sum_after_next_tmp += sum['commitment']
                sum_after_next_tmp += sum['reserve'] * params['50']
                sum_after_next_tmp += sum['potential'] * params['30']

        return (sum75tmpetalon, sum50tmpetalon,
                sum100tmp, sum75tmp, sum50tmp,
                sum_next_75_q1_tmp, sum_next_50_q1_tmp, sum_next_30_q1_tmp,
                sum_next_75_tmp, sum_next_50_tmp, sum_next_30_tmp,
                sum_after_next_tmp)

    def get_sum_fact_acceptance_project_step_year_quarter(self, project, step, year, quarter):
        sum_cash = 0

        acceptance_list = project.fact_acceptance_flow_ids

        if quarter:
            months = self.get_months_from_quarter(quarter)

        if acceptance_list:
            for acceptance in acceptance_list:
                if step:
                    if acceptance.project_steps_id.id != step.id: continue
                if (not quarter or acceptance.date_cash.month in months) and acceptance.date_cash.year == year:
                    sum_cash += acceptance.sum_cash_without_vat

        return sum_cash

    def get_sum_fact_margin_project_step_year_quarter(self, project, step, year, quarter):
        sum_cash = 0

        acceptance_list = project.fact_acceptance_flow_ids

        if quarter:
            months = self.get_months_from_quarter(quarter)

        if acceptance_list:
            for acceptance in acceptance_list:
                if step:
                    if acceptance.project_steps_id.id != step.id: continue
                if (not quarter or acceptance.date_cash.month in months) and acceptance.date_cash.year == year:
                    sum_cash += acceptance.margin

        return sum_cash

    def get_sum_planned_acceptance_project_step_year_quarter(self, project, step, year, quarter):

        sum_acceptance = {'commitment': 0, 'reserve': 0, 'potential': 0}

        if quarter:
            months = self.get_months_from_quarter(quarter)

        acceptance_list = project.planned_acceptance_flow_ids
        if acceptance_list:
            for acceptance in acceptance_list:
                if step:
                    if acceptance.project_steps_id.id != step.id: continue
                if (not quarter or acceptance.date_cash.month in months) and acceptance.date_cash.year == year:
                    if acceptance.forecast == 'from_project':
                        if step:
                            estimated_probability_id_name = step.estimated_probability_id.name
                        else:
                            estimated_probability_id_name = project.estimated_probability_id.name

                        if estimated_probability_id_name in ('75', '100', '100(done)'):
                            sum_acceptance['commitment'] += acceptance.sum_cash_without_vat
                        elif estimated_probability_id_name == '50':
                            sum_acceptance['reserve'] += acceptance.sum_cash_without_vat
                        elif estimated_probability_id_name == '30':
                            sum_acceptance['potential'] += acceptance.sum_cash_without_vat
                    else:
                        sum_acceptance[acceptance.forecast] += acceptance.sum_cash_without_vat
        return sum_acceptance

    def get_act_margin_forecast_from_distributions(self, sum, margin_sum, margin_plan, project, step, year, months):

        sum_distribution_acceptance = 0
        sum_ostatok_acceptance = {'commitment': 0, 'reserve': 0, 'potential': 0}

        for planned_acceptance in project.planned_acceptance_flow_ids:
            if ((not step or planned_acceptance.project_steps_id.id == step.id)
                    and (not months or planned_acceptance.date_cash.month in months)
                    and planned_acceptance.date_cash.year == year
            ):
                sum_distribution_acceptance += planned_acceptance.distribution_sum_without_vat

                if planned_acceptance.forecast == 'from_project':
                    estimated_probability_id_name = project.estimated_probability_id.name
                    if step:
                        estimated_probability_id_name = step.estimated_probability_id.name
                    if estimated_probability_id_name in ('75', '100', '100(done)'):
                        sum_ostatok_acceptance['commitment'] += planned_acceptance.distribution_sum_without_vat_ostatok
                    elif estimated_probability_id_name == '50':
                        sum_ostatok_acceptance['reserve'] += planned_acceptance.distribution_sum_without_vat_ostatok
                    elif estimated_probability_id_name == '30':
                        sum_ostatok_acceptance['potential'] += planned_acceptance.distribution_sum_without_vat_ostatok
                else:
                    sum_ostatok_acceptance[
                        planned_acceptance.forecast] += planned_acceptance.distribution_sum_without_vat_ostatok

                # суммируем доли маржи фактов в соотношении (сумма распределения/суммы факта)
                margin_distribution = 0
                for distribution in planned_acceptance.distribution_acceptance_ids:
                    if distribution.fact_acceptance_flow_id.sum_cash_without_vat != 0:
                        margin_distribution += (distribution.fact_acceptance_flow_id.margin
                                                * distribution.distribution_sum_without_vat
                                                / distribution.fact_acceptance_flow_id.sum_cash_without_vat)
                if planned_acceptance.forecast == 'from_project':
                    estimated_probability_id_name = project.estimated_probability_id.name
                    if step:
                        estimated_probability_id_name = step.estimated_probability_id.name
                    if estimated_probability_id_name in ('75', '100', '100(done)'):
                        margin_plan['commitment'] -= margin_distribution
                    elif estimated_probability_id_name == '50':
                        margin_plan['reserve'] -= margin_distribution
                else:
                    margin_plan[planned_acceptance.forecast] -= margin_distribution

        if sum_distribution_acceptance != 0:  # если есть распределение, то остаток = остатку распределения
            sum = sum_ostatok_acceptance
            margin_sum = margin_plan
            for key in sum:
                sum[key] = max(sum[key], 0)
                margin_sum[key] = max(margin_sum[key], 0)

        return  sum, margin_sum

    def print_quarter_planned_acceptance_project(self, sheet, row, column, element, project, step,  project_office, params, row_format_number, row_format_number_color_fact):
        global strYEAR
        global YEARint

        sum75tmpetalon = sum50tmpetalon = sum100tmp = sum100tmp_q1 = sum75tmp = sum50tmp = 0
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
            if step:
                if ((
                        project.legal_entity_signing_id.different_project_offices_in_steps and step.project_office_id == project_office)
                        or ((
                                    not project.legal_entity_signing_id.different_project_offices_in_steps or not step.project_office_id) and project.project_office_id == project_office)):

                    profitability = step.profitability

                    sum100tmp_step = self.get_sum_fact_acceptance_project_step_year_quarter(project, step, YEARint, element)
                    prof100tmp_step = self.get_sum_fact_margin_project_step_year_quarter(project, step, YEARint, element)
                    sheet.write_number(row, column + 2, sum100tmp_step, row_format_number)
                    sheet.write_number(row, column + 2 + 44, prof100tmp_step, row_format_number)

                    sum100tmp += sum100tmp_step
                    prof100tmp += prof100tmp_step

                    sum = self.get_sum_planned_acceptance_project_step_year_quarter(project, step, YEARint, element)

                    margin_plan = {'commitment': 0, 'reserve': 0, 'potential': 0}
                    margin_sum = {'commitment': 0, 'reserve': 0, 'potential': 0}

                    if sum:
                        for key in sum:
                            margin_plan[key] = sum[key] * profitability / 100

                    if sum100tmp_step >= sum['commitment']:
                        sum100tmp_step_ostatok = sum100tmp_step - sum['commitment']
                        sum['commitment'] = 0
                        sum['reserve'] = max(sum['reserve'] - sum100tmp_step_ostatok, 0)
                    else:
                        sum['commitment'] = sum['commitment'] - sum100tmp_step

                    if prof100tmp_step >= margin_plan['commitment']:  # маржа если нет распределения
                        prof100tmp_step_ostatok = prof100tmp_step - margin_plan['commitment']
                        margin_sum['commitment'] = 0
                        margin_sum['reserve'] = max(margin_plan['reserve'] - prof100tmp_step_ostatok, 0)
                    else:
                        margin_sum['commitment'] = margin_plan['commitment'] - prof100tmp_step

                    # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                    sum, margin_sum = self.get_act_margin_forecast_from_distributions(sum, margin_sum, margin_plan, project, step, YEARint, months)

                    sheet.write_number(row, column + 3, sum['commitment'], row_format_number)
                    sheet.write_number(row, column + 3 + 44, margin_sum['commitment'], row_format_number)
                    sum75tmp += sum['commitment']
                    prof75tmp += margin_sum['commitment']
                    sheet.write_number(row, column + 4, sum['reserve'], row_format_number)
                    sheet.write_number(row, column + 4 + 44, margin_sum['reserve'], row_format_number)
                    sum50tmp += sum['reserve']
                    prof50tmp += margin_sum['reserve']
            else:
                profitability = project.profitability

                sum100tmp_proj = self.get_sum_fact_acceptance_project_step_year_quarter(project, False, YEARint, element)
                prof100tmp_proj = self.get_sum_fact_margin_project_step_year_quarter(project, False, YEARint, element)
                sheet.write_number(row, column + 2, sum100tmp_proj, row_format_number)
                sheet.write_number(row, column + 2 + 44, prof100tmp_proj, row_format_number)

                sum100tmp += sum100tmp_proj
                prof100tmp += prof100tmp_proj

                sum = self.get_sum_planned_acceptance_project_step_year_quarter(project, False, YEARint, element)

                margin_plan = {'commitment': 0, 'reserve': 0, 'potential': 0}
                margin_sum = {'commitment': 0, 'reserve': 0, 'potential': 0}

                if sum:
                    for key in sum:
                        margin_plan[key] = sum[key] * profitability / 100

                if sum100tmp >= sum['commitment']:
                    sum100tmp_ostatok = sum100tmp - sum['commitment']
                    sum['commitment'] = 0
                    sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                else:
                    sum['commitment'] = sum['commitment'] - sum100tmp

                if prof100tmp >= margin_plan['commitment']:  # маржа если нет распределения
                    prof100tmp_ostatok = prof100tmp - margin_plan['commitment']
                    margin_sum['commitment'] = 0
                    margin_sum['reserve'] = max(margin_plan['reserve'] - prof100tmp_ostatok, 0)
                else:
                    margin_sum['commitment'] = margin_plan['commitment'] - prof100tmp

                # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                sum, margin_sum = self.get_act_margin_forecast_from_distributions(sum, margin_sum, margin_plan, project, False, YEARint, months)

                sheet.write_number(row, column + 3, sum['commitment'], row_format_number)
                sheet.write_number(row, column + 3 + 44, margin_sum['commitment'], row_format_number)
                sum75tmp += sum['commitment']
                prof75tmp += margin_sum['commitment']
                sheet.write_number(row, column + 4, sum['reserve'], row_format_number)
                sheet.write_number(row, column + 4 + 44, margin_sum['reserve'], row_format_number)
                sum50tmp += sum['reserve']
                prof50tmp += margin_sum['reserve']

        elif element == 'NEXT':
            if step:

                if ((project.legal_entity_signing_id.different_project_offices_in_steps and step.project_office_id == project_office)
                        or ((not project.legal_entity_signing_id.different_project_offices_in_steps or not step.project_office_id) and project.project_office_id == project_office)):

                    profitability = step.profitability

                    sum100tmp_q1_step = self.get_sum_fact_acceptance_project_step_year_quarter(project, step, YEARint + 1,
                                                                                            'Q1')
                    prof100tmp_q1_step = self.get_sum_fact_margin_project_step_year_quarter(project, step, YEARint + 1,
                                                                                         'Q1')
                    sum100tmp_step = self.get_sum_fact_acceptance_project_step_year_quarter(project, step, YEARint + 1, False)
                    prof100tmp_step = self.get_sum_fact_margin_project_step_year_quarter(project, step, YEARint + 1, False)

                    sum100tmp += sum100tmp_step
                    prof100tmp += prof100tmp_step

                    sum_q1 = self.get_sum_planned_acceptance_project_step_year_quarter(project, step, YEARint + 1, 'Q1')
                    sum = self.get_sum_planned_acceptance_project_step_year_quarter(project, step, YEARint + 1, False)

                    margin_plan_q1 = {'commitment': 0, 'reserve': 0, 'potential': 0}
                    margin_sum_q1 = {'commitment': 0, 'reserve': 0, 'potential': 0}
                    margin_plan = {'commitment': 0, 'reserve': 0, 'potential': 0}
                    margin_sum = {'commitment': 0, 'reserve': 0, 'potential': 0}

                    if sum:
                        for key in sum:
                            margin_plan[key] = sum[key] * profitability / 100

                    if sum_q1:
                        for key in sum_q1:
                            margin_plan_q1[key] = sum_q1[key] * profitability / 100

                    if sum100tmp_q1_step >= sum_q1['commitment']:
                        sum100tmp_q1_step_ostatok = sum100tmp_q1_step - sum_q1['commitment']
                        sum_q1['commitment'] = 0
                        sum_q1['reserve'] = max(sum_q1['reserve'] - sum100tmp_q1_step_ostatok, 0)
                    else:
                        sum_q1['commitment'] = sum_q1['commitment'] - sum100tmp_q1_step

                    if sum100tmp_step >= sum['commitment']:
                        sum100tmp_step_ostatok = sum100tmp_step - sum['commitment']
                        sum['commitment'] = 0
                        sum['reserve'] = max(sum['reserve'] - sum100tmp_step_ostatok, 0)
                    else:
                        sum['commitment'] = sum['commitment'] - sum100tmp_step

                    if prof100tmp_q1_step >= margin_plan_q1['commitment']:  # маржа если нет распределения
                        prof100tmp_q1_step_ostatok = prof100tmp_q1_step - margin_plan_q1['commitment']
                        margin_sum_q1['commitment'] = 0
                        margin_sum_q1['reserve'] = max(margin_plan_q1['reserve'] - prof100tmp_q1_step_ostatok, 0)
                    else:
                        margin_sum_q1['commitment'] = margin_plan_q1['commitment'] - prof100tmp_q1_step

                    if prof100tmp_step >= margin_plan['commitment']:  # маржа если нет распределения
                        prof100tmp_step_ostatok = prof100tmp_step - margin_plan['commitment']
                        margin_sum['commitment'] = 0
                        margin_sum['reserve'] = max(margin_plan['reserve'] - prof100tmp_step_ostatok, 0)
                    else:
                        margin_sum['commitment'] = margin_plan['commitment'] - prof100tmp_step

                    if (all(value == 0 for value in
                           sum_q1.values()) and step.end_sale_project_month.year == YEARint + 1
                            and step.end_sale_project_month.month in self.get_months_from_quarter('Q1')):  # если актирование 0, а месяц в нужном квартале, берем выручку
                        if step.estimated_probability_id.name in ('75', '100'):
                            sum_q1['commitment'] = step.total_amount_of_revenue
                        elif step.estimated_probability_id.name == '50':
                            sum_q1['reserve'] = step.total_amount_of_revenue
                        elif step.estimated_probability_id.name == '30':
                            sum_q1['potential'] = step.total_amount_of_revenue

                    if all(value == 0 for value in sum.values()) and step.end_sale_project_month.year == YEARint + 1:  # если актирование 0, а месяц в нужном году, берем выручку
                        if step.estimated_probability_id.name in ('75', '100'):
                            sum['commitment'] = step.total_amount_of_revenue
                        elif step.estimated_probability_id.name == '50':
                            sum['reserve'] = step.total_amount_of_revenue
                        elif step.estimated_probability_id.name == '30':
                            sum['potential'] = step.total_amount_of_revenue

                    # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                    sum_q1, margin_sum_q1 = self.get_act_margin_forecast_from_distributions(sum_q1, margin_sum_q1, margin_plan_q1,
                                                                                      project, step, YEARint + 1, self.get_months_from_quarter('Q1'))
                    sum, margin_sum = self.get_act_margin_forecast_from_distributions(sum, margin_sum, margin_plan, project, step, YEARint + 1, False)

                    sheet.write_number(row, column + 0, sum_q1['commitment'], row_format_number)
                    sheet.write_number(row, column + 0 + 44, sum_q1['commitment'] * profitability / 100, row_format_number)
                    sum_next_75_q1_tmp += sum_q1['commitment']
                    prof_next_75_q1_tmp += sum_q1['commitment'] * profitability / 100
                    sheet.write_number(row, column + 1, sum_q1['reserve'] * params['50'], row_format_number)
                    sheet.write_number(row, column + 1 + 44, sum_q1['reserve'] * params['50'] * profitability / 100, row_format_number)
                    sum_next_50_q1_tmp += sum_q1['reserve'] * params['50']
                    prof_next_50_q1_tmp += sum_q1['reserve'] * params['50'] * profitability / 100
                    sheet.write_number(row, column + 2, sum_q1['potential'] * params['30'], row_format_number)
                    sheet.write_number(row, column + 2 + 44, sum_q1['potential'] * params['30'] * profitability / 100, row_format_number)
                    sum_next_30_q1_tmp += sum_q1['potential'] * params['30']
                    prof_next_30_q1_tmp += sum_q1['potential'] * params['30'] * profitability / 100

                    sheet.write_number(row, column + 3, sum['commitment'], row_format_number)
                    sheet.write_number(row, column + 3 + 44, sum['commitment'] * profitability / 100, row_format_number)
                    sum_next_75_tmp += sum['commitment']
                    prof_next_75_tmp += sum['commitment'] * profitability / 100
                    sheet.write_number(row, column + 4, sum['reserve'] * params['50'], row_format_number)
                    sheet.write_number(row, column + 4 + 44, sum['reserve'] * params['50'] * profitability / 100, row_format_number)
                    sum_next_50_tmp += sum['reserve'] * params['50']
                    prof_next_50_tmp += sum['reserve'] * params['50'] * profitability / 100
                    sheet.write_number(row, column + 5, sum['potential'] * params['30'], row_format_number)
                    sheet.write_number(row, column + 5 + 44, sum['potential'] * params['30'] * profitability / 100, row_format_number)
                    sum_next_30_tmp += sum['potential'] * params['30']
                    prof_next_30_tmp += sum['potential'] * params['30'] * profitability / 100
            else:
                profitability = project.profitability

                sum100tmp_q1_proj = self.get_sum_fact_acceptance_project_step_year_quarter(project, False, YEARint + 1,
                                                                                        'Q1')
                prof100tmp_q1_proj = self.get_sum_fact_margin_project_step_year_quarter(project, False, YEARint + 1, 'Q1')

                sum100tmp_proj = self.get_sum_fact_acceptance_project_step_year_quarter(project, False, YEARint + 1, False)
                prof100tmp_proj = self.get_sum_fact_margin_project_step_year_quarter(project, False, YEARint + 1, False)

                sum100tmp_q1 += sum100tmp_q1_proj
                prof100tmp_q1 += prof100tmp_q1_proj
                sum100tmp += sum100tmp_proj
                prof100tmp += prof100tmp_proj

                sum_q1 = self.get_sum_planned_acceptance_project_step_year_quarter(project, False, YEARint + 1, 'Q1')
                sum = self.get_sum_planned_acceptance_project_step_year_quarter(project, False, YEARint + 1, False)

                margin_plan_q1 = {'commitment': 0, 'reserve': 0, 'potential': 0}
                margin_sum_q1 = {'commitment': 0, 'reserve': 0, 'potential': 0}
                margin_plan = {'commitment': 0, 'reserve': 0, 'potential': 0}
                margin_sum = {'commitment': 0, 'reserve': 0, 'potential': 0}

                if sum:
                    for key in sum:
                        margin_plan[key] = sum[key] * profitability / 100

                if sum_q1:
                    for key in sum_q1:
                        margin_plan_q1[key] = sum_q1[key] * profitability / 100

                if sum100tmp_q1 >= sum_q1['commitment']:
                    sum100tmp_q1_ostatok = sum100tmp_q1 - sum_q1['commitment']
                    sum_q1['commitment'] = 0
                    sum_q1['reserve'] = max(sum_q1['reserve'] - sum100tmp_q1_ostatok, 0)
                else:
                    sum_q1['commitment'] = sum_q1['commitment'] - sum100tmp_q1

                if sum100tmp >= sum['commitment']:
                    sum100tmp_ostatok = sum100tmp - sum['commitment']
                    sum['commitment'] = 0
                    sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                else:
                    sum['commitment'] = sum['commitment'] - sum100tmp

                if prof100tmp_q1 >= margin_plan_q1['commitment']:  # маржа если нет распределения
                    prof100tmp_q1_ostatok = prof100tmp_q1 - margin_plan_q1['commitment']
                    margin_sum_q1['commitment'] = 0
                    margin_sum_q1['reserve'] = max(margin_plan_q1['reserve'] - prof100tmp_q1_ostatok, 0)
                else:
                    margin_sum_q1['commitment'] = margin_plan_q1['commitment'] - prof100tmp_q1

                if prof100tmp >= margin_plan['commitment']:  # маржа если нет распределения
                    prof100tmp_ostatok = prof100tmp - margin_plan['commitment']
                    margin_sum['commitment'] = 0
                    margin_sum['reserve'] = max(margin_plan['reserve'] - prof100tmp_ostatok, 0)
                else:
                    margin_sum['commitment'] = margin_plan['commitment'] - prof100tmp

                if all(value == 0 for value in sum_q1.values()) and project.end_sale_project_month.year == YEARint + 1 and project.end_sale_project_month.month in self.get_months_from_quarter('Q1'):  # если актирование 0, а месяц в нужном году, берем выручку
                    if project.estimated_probability_id.name in ('75', '100'):
                        sum_q1['commitment'] = project.total_amount_of_revenue
                    elif project.estimated_probability_id.name == '50':
                        sum_q1['reserve'] = project.total_amount_of_revenue
                    elif project.estimated_probability_id.name == '30':
                        sum_q1['potential'] = project.total_amount_of_revenue

                if all(value == 0 for value in sum.values()) and project.end_sale_project_month.year == YEARint + 1:  # если актирование 0, а месяц в нужном году, берем выручку
                    if project.estimated_probability_id.name in ('75', '100'):
                        sum['commitment'] = project.total_amount_of_revenue
                    elif project.estimated_probability_id.name == '50':
                        sum['reserve'] = project.total_amount_of_revenue
                    elif project.estimated_probability_id.name == '30':
                        sum['potential'] = project.total_amount_of_revenue

                # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                sum_q1, margin_sum_q1 = self.get_act_margin_forecast_from_distributions(sum_q1, margin_sum_q1, margin_plan_q1, project, False, YEARint + 1, self.get_months_from_quarter('Q1'))
                sum, margin_sum = self.get_act_margin_forecast_from_distributions(sum, margin_sum, margin_plan, project, False, YEARint + 1, False)

                sheet.write_number(row, column + 0, sum_q1['commitment'], row_format_number)
                sheet.write_number(row, column + 0 + 44, sum_q1['commitment'] * profitability / 100,
                                   row_format_number)
                sum_next_75_q1_tmp += sum_q1['commitment']
                prof_next_75_q1_tmp += sum_q1['commitment'] * profitability / 100
                sheet.write_number(row, column + 1, sum_q1['reserve'] * params['50'], row_format_number)
                sheet.write_number(row, column + 1 + 44, sum_q1['reserve'] * params['50'] * profitability / 100,
                                   row_format_number)
                sum_next_50_q1_tmp += sum_q1['reserve'] * params['50']
                prof_next_50_q1_tmp += sum_q1['reserve'] * params['50'] * profitability / 100
                sheet.write_number(row, column + 2, sum_q1['potential'] * params['30'], row_format_number)
                sheet.write_number(row, column + 2 + 44, sum_q1['potential'] * params['30'] * profitability / 100,
                                   row_format_number)
                sum_next_30_q1_tmp += sum_q1['potential'] * params['30']
                prof_next_30_q1_tmp += sum_q1['potential'] * params['30'] * profitability / 100

                sheet.write_number(row, column + 3, sum['commitment'], row_format_number)
                sheet.write_number(row, column + 3 + 44, sum['commitment'] * profitability / 100,
                                   row_format_number)
                sum_next_75_tmp += sum['commitment']
                prof_next_75_tmp += sum['commitment'] * profitability / 100
                sheet.write_number(row, column + 4, sum['reserve'] * params['50'], row_format_number)
                sheet.write_number(row, column + 4 + 44, sum['reserve'] * params['50'] * profitability / 100,
                                   row_format_number)
                sum_next_50_tmp += sum['reserve'] * params['50']
                prof_next_50_tmp += sum['reserve'] * params['50'] * profitability / 100
                sheet.write_number(row, column + 5, sum['potential'] * params['30'], row_format_number)
                sheet.write_number(row, column + 5 + 44, sum['potential'] * params['30'] * profitability / 100,
                                   row_format_number)
                sum_next_30_tmp += sum['potential'] * params['30']
                prof_next_30_tmp += sum['potential'] * params['30'] * profitability / 100

        elif element == 'AFTER NEXT':
            if step:

                if ((project.legal_entity_signing_id.different_project_offices_in_steps and step.project_office_id == project_office)
                        or ((not project.legal_entity_signing_id.different_project_offices_in_steps or not step.project_office_id) and project.project_office_id == project_office)):

                    profitability = step.profitability

                    sum100tmp_step = self.get_sum_fact_acceptance_project_step_year_quarter(project, step, YEARint + 2, False)
                    prof100tmp_step = self.get_sum_fact_margin_project_step_year_quarter(project, step, YEARint + 2, False)

                    sum100tmp += sum100tmp_step
                    prof100tmp += prof100tmp_step

                    sum = self.get_sum_planned_acceptance_project_step_year_quarter(project, step, YEARint + 2, False)

                    margin_plan = {'commitment': 0, 'reserve': 0, 'potential': 0}
                    margin_sum = {'commitment': 0, 'reserve': 0, 'potential': 0}

                    if sum:
                        for key in sum:
                            margin_plan[key] = sum[key] * profitability / 100

                    if sum100tmp_step >= sum['commitment']:
                        sum100tmp_step_ostatok = sum100tmp_step - sum['commitment']
                        sum['commitment'] = 0
                        sum['reserve'] = max(sum['reserve'] - sum100tmp_step_ostatok, 0)
                    else:
                        sum['commitment'] = sum['commitment'] - sum100tmp_step

                    if prof100tmp_step >= margin_plan['commitment']:  # маржа если нет распределения
                        prof100tmp_step_ostatok = prof100tmp_step - margin_plan['commitment']
                        margin_sum['commitment'] = 0
                        margin_sum['reserve'] = max(margin_plan['reserve'] - prof100tmp_step_ostatok, 0)
                    else:
                        margin_sum['commitment'] = margin_plan['commitment'] - prof100tmp_step

                    if all(value == 0 for value in sum.values()) and step.end_sale_project_month.year == YEARint + 2:  # если актирование 0, а месяц в нужном году, берем выручку
                        if step.estimated_probability_id.name in ('75', '100'):
                            sum['commitment'] = step.total_amount_of_revenue
                        elif step.estimated_probability_id.name == '50':
                            sum['reserve'] = step.total_amount_of_revenue
                        elif step.estimated_probability_id.name == '30':
                            sum['potential'] = step.total_amount_of_revenue

                    # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                    sum, margin_sum = self.get_act_margin_forecast_from_distributions(sum, margin_sum, margin_plan, project, step, YEARint + 2, False)

                    sum_after_next_tmp += sum['commitment']
                    prof_after_next_tmp += sum['commitment'] * profitability / 100
                    sum_after_next_tmp += sum['reserve'] * params['50']
                    prof_after_next_tmp += sum['reserve'] * params['50'] * profitability / 100
                    sum_after_next_tmp += sum['potential'] * params['30']
                    prof_after_next_tmp += sum['potential'] * params['30'] * profitability / 100
                    sheet.write_number(row, column + 0, sum_after_next_tmp, row_format_number)
                    sheet.write_number(row, column + 0 + 44, prof_after_next_tmp,
                                       row_format_number)
            else:
                profitability = project.profitability

                sum100tmp_proj = self.get_sum_fact_acceptance_project_step_year_quarter(project, False, YEARint + 2, False)
                prof100tmp_proj = self.get_sum_fact_margin_project_step_year_quarter(project, False, YEARint + 2, False)

                sum100tmp += sum100tmp_proj
                prof100tmp += prof100tmp_proj

                sum = self.get_sum_planned_acceptance_project_step_year_quarter(project, False, YEARint + 2, False)

                margin_plan = {'commitment': 0, 'reserve': 0, 'potential': 0}
                margin_sum = {'commitment': 0, 'reserve': 0, 'potential': 0}

                if sum:
                    for key in sum:
                        margin_plan[key] = sum[key] * profitability / 100

                if sum100tmp >= sum['commitment']:
                    sum100tmp_ostatok = sum100tmp - sum['commitment']
                    sum['commitment'] = 0
                    sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                else:
                    sum['commitment'] = sum['commitment'] - sum100tmp

                if prof100tmp >= margin_plan['commitment']:  # маржа если нет распределения
                    prof100tmp_ostatok = prof100tmp - margin_plan['commitment']
                    margin_sum['commitment'] = 0
                    margin_sum['reserve'] = max(margin_plan['reserve'] - prof100tmp_ostatok, 0)
                else:
                    margin_sum['commitment'] = margin_plan['commitment'] - prof100tmp

                if all(value == 0 for value in sum.values()) and project.end_sale_project_month.year == YEARint + 2:  # если актирование 0, а месяц в нужном году, берем выручку
                    if project.estimated_probability_id.name in ('75', '100'):
                        sum['commitment'] = project.total_amount_of_revenue
                    elif project.estimated_probability_id.name == '50':
                        sum['reserve'] = project.total_amount_of_revenue
                    elif project.estimated_probability_id.name == '30':
                        sum['potential'] = project.total_amount_of_revenue

                # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                sum, margin_sum = self.get_act_margin_forecast_from_distributions(sum, margin_sum, margin_plan, project, False, YEARint + 2, False)

                sum_after_next_tmp += sum['commitment']
                prof_after_next_tmp += sum['commitment'] * profitability / 100
                sum_after_next_tmp += sum['reserve'] * params['50']
                prof_after_next_tmp += sum['reserve'] * params['50'] * profitability / 100
                sum_after_next_tmp += sum['potential'] * params['30']
                prof_after_next_tmp += sum['potential'] * params['30'] * profitability / 100
            sheet.write_number(row, column + 0, sum_after_next_tmp, row_format_number)
            sheet.write_number(row, column + 0 + 44, prof_after_next_tmp,
                               row_format_number)

        return sum75tmpetalon, sum50tmpetalon, sum100tmp, sum75tmp, sum50tmp

    def calculate_quarter_planned_acceptance(self, element, project, project_office, params):
        global strYEAR
        global YEARint

        sum75tmpetalon = sum50tmpetalon = sum100tmp = sum100tmp_q1 = sum75tmp = sum50tmp = 0
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
            if project.project_have_steps:
                for step in project.project_steps_ids:

                    if ((project.legal_entity_signing_id.different_project_offices_in_steps and step.project_office_id == project_office)
                            or ((not project.legal_entity_signing_id.different_project_offices_in_steps or not step.project_office_id) and project.project_office_id == project_office)):

                        profitability = step.profitability

                        sum100tmp_step = self.get_sum_fact_acceptance_project_step_year_quarter(project, step, YEARint, element)
                        prof100tmp_step = self.get_sum_fact_margin_project_step_year_quarter(project, step, YEARint, element)

                        sum100tmp += sum100tmp_step
                        prof100tmp += prof100tmp_step

                        sum = self.get_sum_planned_acceptance_project_step_year_quarter(project, step, YEARint, element)

                        margin_plan = {'commitment': 0, 'reserve': 0, 'potential': 0}
                        margin_sum = {'commitment': 0, 'reserve': 0, 'potential': 0}

                        if sum:
                            for key in sum:
                                margin_plan[key] = sum[key] * profitability / 100

                        if sum100tmp_step >= sum['commitment']:
                            sum100tmp_step_ostatok = sum100tmp_step - sum['commitment']
                            sum['commitment'] = 0
                            sum['reserve'] = max(sum['reserve'] - sum100tmp_step_ostatok, 0)
                        else:
                            sum['commitment'] = sum['commitment'] - sum100tmp_step

                        if prof100tmp_step >= margin_plan['commitment']:  # маржа если нет распределения
                            prof100tmp_step_ostatok = prof100tmp_step - margin_plan['commitment']
                            margin_sum['commitment'] = 0
                            margin_sum['reserve'] = max(margin_plan['reserve'] - prof100tmp_step_ostatok, 0)
                        else:
                            margin_sum['commitment'] = margin_plan['commitment'] - prof100tmp_step

                        # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                        sum, margin_sum = self.get_act_margin_forecast_from_distributions(sum, margin_sum, margin_plan, project, step, YEARint, months)

                        sum75tmp += sum['commitment']
                        prof75tmp += margin_sum['commitment']
                        sum50tmp += sum['reserve']
                        prof50tmp += margin_sum['reserve']
            else:
                profitability = project.profitability

                sum100tmp_proj = self.get_sum_fact_acceptance_project_step_year_quarter(project, False, YEARint, element)
                prof100tmp_proj = self.get_sum_fact_margin_project_step_year_quarter(project, False, YEARint, element)

                sum100tmp += sum100tmp_proj
                prof100tmp += prof100tmp_proj

                sum = self.get_sum_planned_acceptance_project_step_year_quarter(project, False, YEARint, element)

                margin_plan = {'commitment': 0, 'reserve': 0, 'potential': 0}
                margin_sum = {'commitment': 0, 'reserve': 0, 'potential': 0}

                if sum:
                    for key in sum:
                        margin_plan[key] = sum[key] * profitability / 100

                if sum100tmp >= sum['commitment']:
                    sum100tmp_ostatok = sum100tmp - sum['commitment']
                    sum['commitment'] = 0
                    sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                else:
                    sum['commitment'] = sum['commitment'] - sum100tmp

                if prof100tmp >= margin_plan['commitment']:  # маржа если нет распределения
                    prof100tmp_ostatok = prof100tmp - margin_plan['commitment']
                    margin_sum['commitment'] = 0
                    margin_sum['reserve'] = max(margin_plan['reserve'] - prof100tmp_ostatok, 0)
                else:
                    margin_sum['commitment'] = margin_plan['commitment'] - prof100tmp

                # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                sum, margin_sum = self.get_act_margin_forecast_from_distributions(sum, margin_sum, margin_plan, project, False, YEARint, months)

                sum75tmp += sum['commitment']
                prof75tmp += margin_sum['commitment']
                sum50tmp += sum['reserve']
                prof50tmp += margin_sum['reserve']

        elif element == 'NEXT':
            if project.project_have_steps:
                for step in project.project_steps_ids:

                    if ((project.legal_entity_signing_id.different_project_offices_in_steps and step.project_office_id == project_office)
                            or ((not project.legal_entity_signing_id.different_project_offices_in_steps or not step.project_office_id) and project.project_office_id == project_office)):

                        profitability = step.profitability

                        sum100tmp_q1_step = self.get_sum_fact_acceptance_project_step_year_quarter(project, step,
                                                                                                YEARint + 1, 'Q1')
                        prof100tmp_q1_step = self.get_sum_fact_margin_project_step_year_quarter(project, step, YEARint + 1,
                                                                                             'Q1')
                        sum100tmp_step = self.get_sum_fact_acceptance_project_step_year_quarter(project, step, YEARint + 1, False)
                        prof100tmp_step = self.get_sum_fact_margin_project_step_year_quarter(project, step, YEARint + 1, False)

                        sum100tmp_q1 += sum100tmp_q1_step
                        prof100tmp_q1 += prof100tmp_q1_step
                        sum100tmp += sum100tmp_step
                        prof100tmp += prof100tmp_step

                        sum_q1 = self.get_sum_planned_acceptance_project_step_year_quarter(project, step, YEARint + 1, 'Q1')
                        sum = self.get_sum_planned_acceptance_project_step_year_quarter(project, step, YEARint + 1, False)

                        margin_plan_q1 = {'commitment': 0, 'reserve': 0, 'potential': 0}
                        margin_sum_q1 = {'commitment': 0, 'reserve': 0, 'potential': 0}
                        margin_plan = {'commitment': 0, 'reserve': 0, 'potential': 0}
                        margin_sum = {'commitment': 0, 'reserve': 0, 'potential': 0}

                        if sum_q1:
                            for key in sum_q1:
                                margin_plan_q1[key] = sum_q1[key] * profitability / 100

                        if sum:
                            for key in sum:
                                margin_plan[key] = sum[key] * profitability / 100

                        if sum100tmp_q1_step >= sum_q1['commitment']:
                            sum100tmp_q1_step_ostatok = sum100tmp_q1_step - sum_q1['commitment']
                            sum_q1['commitment'] = 0
                            sum_q1['reserve'] = max(sum_q1['reserve'] - sum100tmp_q1_step_ostatok, 0)
                        else:
                            sum_q1['commitment'] = sum_q1['commitment'] - sum100tmp_q1_step

                        if sum100tmp_step >= sum['commitment']:
                            sum100tmp_step_ostatok = sum100tmp_step - sum['commitment']
                            sum['commitment'] = 0
                            sum['reserve'] = max(sum['reserve'] - sum100tmp_step_ostatok, 0)
                        else:
                            sum['commitment'] = sum['commitment'] - sum100tmp_step

                        if prof100tmp_q1_step >= margin_plan_q1['commitment']:  # маржа если нет распределения
                            prof100tmp_q1_step_ostatok = prof100tmp_q1_step - margin_plan_q1['commitment']
                            margin_sum_q1['commitment'] = 0
                            margin_sum_q1['reserve'] = max(margin_plan_q1['reserve'] - prof100tmp_q1_step_ostatok, 0)
                        else:
                            margin_sum_q1['commitment'] = margin_plan_q1['commitment'] - prof100tmp_q1_step

                        if prof100tmp_step >= margin_plan['commitment']:  # маржа если нет распределения
                            prof100tmp_step_ostatok = prof100tmp_step - margin_plan['commitment']
                            margin_sum['commitment'] = 0
                            margin_sum['reserve'] = max(margin_plan['reserve'] - prof100tmp_step_ostatok, 0)
                        else:
                            margin_sum['commitment'] = margin_plan['commitment'] - prof100tmp_step

                        if (all(value == 0 for value in sum_q1.values()) and step.end_sale_project_month.year == YEARint + 1
                                and step.end_sale_project_month.month in self.get_months_from_quarter('Q1')):  # если актирование 0, а месяц в нужном году, берем выручку
                            if step.estimated_probability_id.name in ('75', '100'):
                                sum_q1['commitment'] = step.total_amount_of_revenue
                            elif step.estimated_probability_id.name == '50':
                                sum_q1['reserve'] = step.total_amount_of_revenue
                            elif step.estimated_probability_id.name == '30':
                                sum_q1['potential'] = step.total_amount_of_revenue

                        if all(value == 0 for value in sum.values()) and step.end_sale_project_month.year == YEARint + 1:  # если актирование 0, а месяц в нужном году, берем выручку
                            if step.estimated_probability_id.name in ('75', '100'):
                                sum['commitment'] = step.total_amount_of_revenue
                            elif step.estimated_probability_id.name == '50':
                                sum['reserve'] = step.total_amount_of_revenue
                            elif step.estimated_probability_id.name == '30':
                                sum['potential'] = step.total_amount_of_revenue

                        # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                        sum_q1, margin_sum_q1 = self.get_act_margin_forecast_from_distributions(sum_q1, margin_sum_q1, margin_plan, project, step, YEARint + 1, self.get_months_from_quarter('Q1'))
                        sum, margin_sum = self.get_act_margin_forecast_from_distributions(sum, margin_sum, margin_plan, project, step, YEARint + 1, False)

                        sum_next_75_q1_tmp += sum_q1['commitment']
                        prof_next_75_q1_tmp += sum_q1['commitment'] * profitability / 100
                        sum_next_50_q1_tmp += sum_q1['reserve'] * params['50']
                        prof_next_50_q1_tmp += sum_q1['reserve'] * params['50'] * profitability / 100
                        sum_next_30_q1_tmp += sum_q1['potential'] * params['30']
                        prof_next_30_q1_tmp += sum_q1['potential'] * params['30'] * profitability / 100

                        sum_next_75_tmp += sum['commitment']
                        prof_next_75_tmp += sum['commitment'] * profitability / 100
                        sum_next_50_tmp += sum['reserve'] * params['50']
                        prof_next_50_tmp += sum['reserve'] * params['50'] * profitability / 100
                        sum_next_30_tmp += sum['potential'] * params['30']
                        prof_next_30_tmp += sum['potential'] * params['30'] * profitability / 100
            else:
                profitability = project.profitability

                sum100tmp_q1_proj = self.get_sum_fact_acceptance_project_step_year_quarter(project, False, YEARint + 1, 'Q1')
                prof100tmp_q1_proj = self.get_sum_fact_margin_project_step_year_quarter(project, False, YEARint + 1, 'Q1')
                sum100tmp_proj = self.get_sum_fact_acceptance_project_step_year_quarter(project, False, YEARint + 1, False)
                prof100tmp_proj = self.get_sum_fact_margin_project_step_year_quarter(project, False, YEARint + 1, False)

                sum100tmp_q1 += sum100tmp_q1_proj
                prof100tmp_q1 += prof100tmp_q1_proj
                sum100tmp += sum100tmp_proj
                prof100tmp += prof100tmp_proj

                sum_q1 = self.get_sum_planned_acceptance_project_step_year_quarter(project, False, YEARint + 1, 'Q1')
                sum = self.get_sum_planned_acceptance_project_step_year_quarter(project, False, YEARint + 1, False)

                margin_plan_q1 = {'commitment': 0, 'reserve': 0, 'potential': 0}
                margin_sum_q1 = {'commitment': 0, 'reserve': 0, 'potential': 0}
                margin_plan = {'commitment': 0, 'reserve': 0, 'potential': 0}
                margin_sum = {'commitment': 0, 'reserve': 0, 'potential': 0}

                if sum:
                    for key in sum:
                        margin_plan[key] = sum[key] * profitability / 100

                if sum_q1:
                    for key in sum_q1:
                        margin_plan_q1[key] = sum_q1[key] * profitability / 100

                if sum100tmp_q1 >= sum_q1['commitment']:
                    sum100tmp_q1_ostatok = sum100tmp_q1 - sum_q1['commitment']
                    sum_q1['commitment'] = 0
                    sum_q1['reserve'] = max(sum_q1['reserve'] - sum100tmp_q1_ostatok, 0)
                else:
                    sum_q1['commitment'] = sum_q1['commitment'] - sum100tmp_q1

                if sum100tmp >= sum['commitment']:
                    sum100tmp_ostatok = sum100tmp - sum['commitment']
                    sum['commitment'] = 0
                    sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                else:
                    sum['commitment'] = sum['commitment'] - sum100tmp

                if prof100tmp_q1 >= margin_plan_q1['commitment']:  # маржа если нет распределения
                    prof100tmp_q1_ostatok = prof100tmp_q1 - margin_plan_q1['commitment']
                    margin_sum_q1['commitment'] = 0
                    margin_sum_q1['reserve'] = max(margin_plan_q1['reserve'] - prof100tmp_q1_ostatok, 0)
                else:
                    margin_sum_q1['commitment'] = margin_plan_q1['commitment'] - prof100tmp_q1

                if prof100tmp >= margin_plan['commitment']:  # маржа если нет распределения
                    prof100tmp_ostatok = prof100tmp - margin_plan['commitment']
                    margin_sum['commitment'] = 0
                    margin_sum['reserve'] = max(margin_plan['reserve'] - prof100tmp_ostatok, 0)
                else:
                    margin_sum['commitment'] = margin_plan['commitment'] - prof100tmp

                if (all(value == 0 for value in sum_q1.values()) and project.end_sale_project_month.year == YEARint + 1
                        and project.end_sale_project_month.month in self.get_months_from_quarter('Q1')):  # если актирование 0, а месяц в нужном году, берем выручку
                    if project.estimated_probability_id.name in ('75', '100'):
                        sum_q1['commitment'] = project.total_amount_of_revenue
                    elif project.estimated_probability_id.name == '50':
                        sum_q1['reserve'] = project.total_amount_of_revenue
                    elif project.estimated_probability_id.name == '30':
                        sum_q1['potential'] = project.total_amount_of_revenue

                if all(value == 0 for value in sum.values()) and project.end_sale_project_month.year == YEARint + 1:  # если актирование 0, а месяц в нужном году, берем выручку
                    if project.estimated_probability_id.name in ('75', '100'):
                        sum['commitment'] = project.total_amount_of_revenue
                    elif project.estimated_probability_id.name == '50':
                        sum['reserve'] = project.total_amount_of_revenue
                    elif project.estimated_probability_id.name == '30':
                        sum['potential'] = project.total_amount_of_revenue

                # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                sum_q1, margin_sum_q1 = self.get_act_margin_forecast_from_distributions(sum_q1, margin_sum_q1, margin_plan_q1, project, False, YEARint + 1, self.get_months_from_quarter('Q1'))
                sum, margin_sum = self.get_act_margin_forecast_from_distributions(sum, margin_sum, margin_plan, project, False, YEARint + 1, False)

                sum_next_75_q1_tmp += sum_q1['commitment']
                prof_next_75_q1_tmp += sum_q1['commitment'] * profitability / 100
                sum_next_50_q1_tmp += sum_q1['reserve'] * params['50']
                prof_next_50_q1_tmp += sum_q1['reserve'] * params['50'] * profitability / 100
                sum_next_30_q1_tmp += sum_q1['potential'] * params['30']
                prof_next_30_q1_tmp += sum_q1['potential'] * params['30'] * profitability / 100

                sum_next_75_tmp += sum['commitment']
                prof_next_75_tmp += sum['commitment'] * profitability / 100
                sum_next_50_tmp += sum['reserve'] * params['50']
                prof_next_50_tmp += sum['reserve'] * params['50'] * profitability / 100
                sum_next_30_tmp += sum['potential'] * params['30']
                prof_next_30_tmp += sum['potential'] * params['30'] * profitability / 100

        elif element == 'AFTER NEXT':
            if project.project_have_steps:
                for step in project.project_steps_ids:

                    if ((project.legal_entity_signing_id.different_project_offices_in_steps and step.project_office_id == project_office)
                            or ((not project.legal_entity_signing_id.different_project_offices_in_steps or not step.project_office_id) and project.project_office_id == project_office)):

                        profitability = step.profitability

                        sum100tmp_step = self.get_sum_fact_acceptance_project_step_year_quarter(project, step, YEARint + 2, False)
                        prof100tmp_step = self.get_sum_fact_margin_project_step_year_quarter(project, step, YEARint + 2, False)

                        sum100tmp += sum100tmp_step
                        prof100tmp += prof100tmp_step

                        sum = self.get_sum_planned_acceptance_project_step_year_quarter(project, step, YEARint + 2, False)

                        margin_plan = {'commitment': 0, 'reserve': 0, 'potential': 0}
                        margin_sum = {'commitment': 0, 'reserve': 0, 'potential': 0}

                        if sum:
                            for key in sum:
                                margin_plan[key] = sum[key] * profitability / 100

                        if sum100tmp_step >= sum['commitment']:
                            sum100tmp_step_ostatok = sum100tmp_step - sum['commitment']
                            sum['commitment'] = 0
                            sum['reserve'] = max(sum['reserve'] - sum100tmp_step_ostatok, 0)
                        else:
                            sum['commitment'] = sum['commitment'] - sum100tmp_step

                        if prof100tmp_step >= margin_plan['commitment']:  # маржа если нет распределения
                            prof100tmp_step_ostatok = prof100tmp_step - margin_plan['commitment']
                            margin_sum['commitment'] = 0
                            margin_sum['reserve'] = max(margin_plan['reserve'] - prof100tmp_step_ostatok, 0)
                        else:
                            margin_sum['commitment'] = margin_plan['commitment'] - prof100tmp_step

                        if all(value == 0 for value in sum.values()) and step.end_sale_project_month.year == YEARint + 2:  # если актирование 0, а месяц в нужном году, берем выручку
                            if step.estimated_probability_id.name in ('75', '100'):
                                sum['commitment'] = step.total_amount_of_revenue
                            elif step.estimated_probability_id.name == '50':
                                sum['reserve'] = step.total_amount_of_revenue
                            elif step.estimated_probability_id.name == '30':
                                sum['potential'] = step.total_amount_of_revenue

                        # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                        sum, margin_sum = self.get_act_margin_forecast_from_distributions(sum, margin_sum, margin_plan, project, step, YEARint + 2, False)

                        sum_after_next_tmp += sum['commitment']
                        prof_after_next_tmp += sum['commitment'] * profitability / 100
                        sum_after_next_tmp += sum['reserve'] * params['50']
                        prof_after_next_tmp += sum['reserve'] * params['50'] * profitability / 100
                        sum_after_next_tmp += sum['potential'] * params['30']
                        prof_after_next_tmp += sum['potential'] * params['30'] * profitability / 100
            else:
                profitability = project.profitability

                sum100tmp_proj = self.get_sum_fact_acceptance_project_step_year_quarter(project, False, YEARint + 2, False)
                prof100tmp_proj = self.get_sum_fact_margin_project_step_year_quarter(project, False, YEARint + 2, False)

                sum100tmp += sum100tmp_proj
                prof100tmp += prof100tmp_proj

                sum = self.get_sum_planned_acceptance_project_step_year_quarter(project, False, YEARint + 2, False)

                margin_plan = {'commitment': 0, 'reserve': 0, 'potential': 0}
                margin_sum = {'commitment': 0, 'reserve': 0, 'potential': 0}

                if sum:
                    for key in sum:
                        margin_plan[key] = sum[key] * profitability / 100

                if sum100tmp >= sum['commitment']:
                    sum100tmp_ostatok = sum100tmp - sum['commitment']
                    sum['commitment'] = 0
                    sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                else:
                    sum['commitment'] = sum['commitment'] - sum100tmp

                if prof100tmp >= margin_plan['commitment']:  # маржа если нет распределения
                    prof100tmp_ostatok = prof100tmp - margin_plan['commitment']
                    margin_sum['commitment'] = 0
                    margin_sum['reserve'] = max(margin_plan['reserve'] - prof100tmp_ostatok, 0)
                else:
                    margin_sum['commitment'] = margin_plan['commitment'] - prof100tmp

                if all(value == 0 for value in sum.values()) and project.end_sale_project_month.year == YEARint + 2:  # если актирование 0, а месяц в нужном году, берем выручку
                    if project.estimated_probability_id.name in ('75', '100'):
                        sum['commitment'] = project.total_amount_of_revenue
                    elif project.estimated_probability_id.name == '50':
                        sum['reserve'] = project.total_amount_of_revenue
                    elif project.estimated_probability_id.name == '30':
                        sum['potential'] = project.total_amount_of_revenue

                # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                sum, margin_sum = self.get_act_margin_forecast_from_distributions(sum, margin_sum, margin_plan, project, False, YEARint + 2, False)

                sum_after_next_tmp += sum['commitment']
                prof_after_next_tmp += sum['commitment'] * profitability / 100
                sum_after_next_tmp += sum['reserve'] * params['50']
                prof_after_next_tmp += sum['reserve'] * params['50'] * profitability / 100
                sum_after_next_tmp += sum['potential'] * params['30']
                prof_after_next_tmp += sum['potential'] * params['30'] * profitability / 100
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

    def print_row_Values(self, workbook, sheet, row, column,  YEAR, project, step, project_office, params):
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

        if step:
            if step.estimated_probability_id.name == '0':
                row_format_number.set_font_color('red')
                row_format_number_color_fact.set_font_color('red')
                head_format_month_itogo.set_font_color('red')
        else:
            if project.estimated_probability_id.name == '0':
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

            # if element.find('итого') != -1:
            #     sheet.write_string(row, column, "", head_format_month_itogo)
            #     column += 1
            if 'NEXT' not in element:
                sheet.write_number(row, column + 0, 0, row_format_number)
                sheet.write_number(row, column + 1, 0, row_format_number)
                sheet.write_number(row, column + 2, 0, row_format_number_color_fact)
                sheet.write_number(row, column + 3, 0, row_format_number)
                sheet.write_number(row, column + 4, 0, row_format_number)
            elif element == 'NEXT':
                sheet.write_number(row, column + 0, 0, row_format_number)
                sheet.write_number(row, column + 1, 0, row_format_number)
                sheet.write_number(row, column + 2, 0, row_format_number)
                sheet.write_number(row, column + 3, 0, row_format_number)
                sheet.write_number(row, column + 4, 0, row_format_number)
                sheet.write_number(row, column + 5, 0, row_format_number)
                sheet.write_number(row, column + 6, 0, row_format_number)

            sumQ75tmpetalon, sumQ50tmpetalon, sumQ100tmp, sumQ75tmp, sumQ50tmp = self.print_quarter_revenue_project(sheet, row, column, element,
                                                                                    project, step, project_office, params, row_format_number, row_format_number_color_fact)
            sumQ75etalon += sumQ75tmpetalon
            sumQ50etalon += sumQ50tmpetalon
            sumQ100 += sumQ100tmp
            sumQ75 += sumQ75tmp
            sumQ50 += sumQ50tmp
            # if element.find('Q') != -1: #'Q1 итого' 'Q2 итого' 'Q3 итого' 'Q4 итого'
            #     if sumQ75etalon != 0 : sheet.write_number(row, column + 0, sumQ75etalon, row_format_number)
            #     if sumQ50etalon != 0 : sheet.write_number(row, column + 1, sumQ50etalon, row_format_number)
            #     if sumQ100 != 0 :      sheet.write_number(row, column + 2, sumQ100, row_format_number_color_fact)
            #     if sumQ75 != 0 :       sheet.write_number(row, column + 3, sumQ75, row_format_number)
            #     if sumQ50 != 0 :       sheet.write_number(row, column + 4, sumQ50, row_format_number)
            #
            #     formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1,xl_col_to_name(column - 16),xl_col_to_name(column - 11),xl_col_to_name(column - 6))
            #     sheet.write_formula(row, column + 0,formula, row_format_number)
            #     formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1,xl_col_to_name(column - 15),xl_col_to_name(column - 10),xl_col_to_name(column - 5))
            #     sheet.write_formula(row, column + 1,formula, row_format_number)
            #     formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1,xl_col_to_name(column - 14),xl_col_to_name(column - 9),xl_col_to_name(column - 4))
            #     sheet.write_formula(row, column + 2,formula, row_format_number_color_fact)
            #     formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1,xl_col_to_name(column - 13),xl_col_to_name(column - 8),xl_col_to_name(column - 3))
            #     sheet.write_formula(row, column + 3,formula, row_format_number)
            #     formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1,xl_col_to_name(column - 12),xl_col_to_name(column - 7),xl_col_to_name(column - 2))
            #     sheet.write_formula(row, column + 4,formula, row_format_number)
            #
            #     sumHY100etalon += sumQ100etalon
            #     sumHY75etalon += sumQ75etalon
            #     sumHY50etalon += sumQ50etalon
            #     sumHY100 += sumQ100
            #     sumHY75 += sumQ75
            #     sumHY50 += sumQ50
            #     sumQ100etalon = sumQ75etalon = sumQ50etalon = sumQ100 = sumQ75  = sumQ50  = 0

            if 'HY' in element:  # 'HY1/YEAR' 'HY2/YEAR'
                # if sumHY75etalon != 0: sheet.write_number(row, column + 0, sumHY75etalon, row_format_number)
                # if sumHY50etalon != 0: sheet.write_number(row, column + 1, sumHY50etalon, row_format_number)
                # if sumHY100 != 0:      sheet.write_number(row, column + 2, sumHY100, row_format_number_color_fact)
                # if sumHY75 != 0:       sheet.write_number(row, column + 3, sumHY75, row_format_number)
                # if sumHY50 != 0:       sheet.write_number(row, column + 4, sumHY50, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 10),xl_col_to_name(column - 5))
                sheet.write_formula(row, column + 0, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 9),xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8),xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)
                if 'HY1' in element:
                    column += 1
                    sheet.write_formula(
                        row,
                        column + 2,
                        f'=IFERROR({xl_col_to_name(column + 1)}{row + 1}/{xl_col_to_name(column)}{row + 1}," ")',
                        row_format_number_color_percent
                    )
                    formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8),
                                                           xl_col_to_name(column - 3))
                    sheet.write_formula(row, column + 3, formula, row_format_number)
                    formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 7),
                                                           xl_col_to_name(column - 2))
                    sheet.write_formula(row, column + 4, formula, row_format_number)
                else:
                    formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 7),xl_col_to_name(column - 2))
                    sheet.write_formula(row, column + 3, formula, row_format_number)
                    formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 6),xl_col_to_name(column - 1))
                    sheet.write_formula(row, column + 4, formula, row_format_number)


                sumYear100etalon += sumHY100etalon
                sumYear75etalon += sumHY75etalon
                sumYear50etalon += sumHY50etalon
                sumYear100 += sumHY100
                sumYear75 += sumHY75
                sumYear50 += sumHY50
                sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0

            elif element == 'YEAR':  # 'YEAR'
                # if sumYear75etalon != 0: sheet.write_number(row, column + 0, sumYear75etalon, row_format_number)
                # if sumYear50etalon != 0: sheet.write_number(row, column + 1, sumYear50etalon, row_format_number)
                # if sumYear100 != 0:      sheet.write_number(row, column + 2, sumYear100, row_format_number_color_fact)
                # if sumYear75 != 0:       sheet.write_number(row, column + 3, sumYear75, row_format_number)
                # if sumYear50 != 0:       sheet.write_number(row, column + 4, sumYear50, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 21), xl_col_to_name(column - 5))
                sheet.write_formula(row, column + 0, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 20), xl_col_to_name(column - 4))
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
                column += 1
            column += 4
        column -= 3
        #end печать Контрактование, с НДС
        # Поступление денежных средсв, с НДС
        sumYear100etalon = sumYear75etalon = sumYear50etalon = sumYear100 = sumYear75 = sumYear50 = 0
        sumQ100etalon = sumQ75etalon = sumQ50etalon = sumQ100 = sumQ75 = sumQ50 = 0
        sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0

        for element in self.quarter_rus_name:
            column += 1
            sumQ75tmpetalon = sumQ50tmpetalon = sumQ100tmp = sumQ75tmp = sumQ50tmp = 0

            # if element.find('итого') != -1:
            #     sheet.write_string(row, column, "", head_format_month_itogo)
            #     column += 1
            if 'NEXT' not in element:
                sheet.write_string(row, column + 0, "", row_format_number)
                sheet.write_string(row, column + 1, "", row_format_number)
                sheet.write_string(row, column + 2, "", row_format_number_color_fact)
                sheet.write_string(row, column + 3, "", row_format_number)
                sheet.write_string(row, column + 4, "", row_format_number)
            elif element == 'NEXT':
                sheet.write_string(row, column + 0, "", row_format_number)
                sheet.write_string(row, column + 1, "", row_format_number)
                sheet.write_string(row, column + 2, "", row_format_number)
                sheet.write_string(row, column + 3, "", row_format_number)



            sumQ75tmpetalon, sumQ50tmpetalon, sumQ100tmp, sumQ75tmp, sumQ50tmp = self.print_quarter_pds_project(sheet, row, column, element,
                                                                                    project, step, project_office, params, row_format_number, row_format_number_color_fact)

            sumQ75etalon += sumQ75tmpetalon
            sumQ50etalon += sumQ50tmpetalon
            sumQ100 += sumQ100tmp
            sumQ75 += sumQ75tmp
            sumQ50 += sumQ50tmp

            # if element.find('Q') != -1:  # 'Q1 итого' 'Q2 итого' 'Q3 итого' 'Q4 итого'
            #     if sumQ75etalon != 0: sheet.write_number(row, column + 0, sumQ75etalon, row_format_number)
            #     if sumQ50etalon != 0: sheet.write_number(row, column + 1, sumQ50etalon, row_format_number)
            #     if sumQ100 != 0:      sheet.write_number(row, column + 2, sumQ100, row_format_number_color_fact)
            #     if sumQ75 != 0:       sheet.write_number(row, column + 3, sumQ75, row_format_number)
            #     if sumQ50 != 0:       sheet.write_number(row, column + 4, sumQ50, row_format_number)
            #     sumHY100etalon += sumQ100etalon
            #     sumHY75etalon += sumQ75etalon
            #     sumHY50etalon += sumQ50etalon
            #     sumHY100 += sumQ100
            #     sumHY75 += sumQ75
            #     sumHY50 += sumQ50
            #     sumQ100etalon = sumQ75etalon = sumQ50etalon = sumQ100 = sumQ75 = sumQ50 = 0
            #     formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1, xl_col_to_name(column - 16),xl_col_to_name(column - 11), xl_col_to_name(column - 6))
            #     sheet.write_formula(row, column + 0, formula, row_format_number)
            #     formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1, xl_col_to_name(column - 15),xl_col_to_name(column - 10), xl_col_to_name(column - 5))
            #     sheet.write_formula(row, column + 1, formula, row_format_number)
            #     formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1, xl_col_to_name(column - 14),xl_col_to_name(column - 9), xl_col_to_name(column - 4))
            #     sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)
            #     formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1, xl_col_to_name(column - 13),xl_col_to_name(column - 8), xl_col_to_name(column - 3))
            #     sheet.write_formula(row, column + 3, formula, row_format_number)
            #     formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1, xl_col_to_name(column - 12),xl_col_to_name(column - 7), xl_col_to_name(column - 2))
            #     sheet.write_formula(row, column + 4, formula, row_format_number)

            if 'HY' in element:  # 'HY1/YEAR' 'HY2/YEAR'
                # if sumHY75etalon != 0: sheet.write_number(row, column + 0, sumHY75etalon, row_format_number)
                # if sumHY50etalon != 0: sheet.write_number(row, column + 1, sumHY50etalon, row_format_number)
                # if sumHY100 != 0:      sheet.write_number(row, column + 2, sumHY100, row_format_number_color_fact)
                # if sumHY75 != 0:       sheet.write_number(row, column + 3, sumHY75, row_format_number)
                # if sumHY50 != 0:       sheet.write_number(row, column + 4, sumHY50, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 10),xl_col_to_name(column - 5))
                sheet.write_formula(row, column + 0, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 9),xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8),xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)
                if 'HY1' in element:
                    column += 1
                    sheet.write_formula(
                        row,
                        column + 2,
                        f'=IFERROR({xl_col_to_name(column + 1)}{row + 1}/{xl_col_to_name(column)}{row + 1}," ")',
                        row_format_number_color_percent
                    )
                    formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8),
                                                           xl_col_to_name(column - 3))
                    sheet.write_formula(row, column + 3, formula, row_format_number)
                    formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 7),
                                                           xl_col_to_name(column - 2))
                    sheet.write_formula(row, column + 4, formula, row_format_number)
                else:
                    formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 7),xl_col_to_name(column - 2))
                    sheet.write_formula(row, column + 3, formula, row_format_number)
                    formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 6),xl_col_to_name(column - 1))
                    sheet.write_formula(row, column + 4, formula, row_format_number)

            elif element == 'YEAR':  # 'YEAR'
                # if sumYear75etalon != 0: sheet.write_number(row, column + 0, sumYear75etalon, row_format_number)
                # if sumYear50etalon != 0: sheet.write_number(row, column + 1, sumYear50etalon, row_format_number)
                # if sumYear100 != 0:      sheet.write_number(row, column + 2, sumYear100, row_format_number_color_fact)
                # if sumYear75 != 0:       sheet.write_number(row, column + 3, sumYear75, row_format_number)
                # if sumYear50 != 0:       sheet.write_number(row, column + 4, sumYear50, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 21), xl_col_to_name(column - 5))
                sheet.write_formula(row, column + 0, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 20), xl_col_to_name(column - 4))
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
                column += 1

            elif element == 'NEXT':
                column += 1
            column += 4
        column -= 4
        # end Поступление денежных средсв, с НДС

        # Валовая Выручка, без НДС
        sumYear100etalon = sumYear75etalon = sumYear50etalon = sumYear100 = sumYear75 = sumYear50 = 0
        sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0

        # if step == False:
        #     profitability = project.profitability
        # else:
        #     profitability = step.profitability
        #
        # project_etalon = self.get_etalon_project(project, element)
        # step_etalon = self.get_etalon_step(step, element)
        #
        # if step_etalon == False:
        #     profitability_etalon = project_etalon.profitability
        # else:
        #     profitability_etalon = step_etalon.profitability
        #
        # for element in self.quarter_rus_name:
        #     column += 1
        #     sheet.write_string(row, column, "", head_format_month_itogo)
        #     sheet.write_string(row, column + 43, "", head_format_month_itogo)
        #     if element.find('HY2') != -1:
        #         addcolumn = 1
        #         column += 1
        #         sheet.write_string(row, column, "", head_format_month_itogo)
        #         sheet.write_string(row, column + 43, "", head_format_month_itogo)
        #     column += 1
        #     sheet.write_string(row, column + 0, "", row_format_number)
        #     sheet.write_string(row, column + 1, "", row_format_number)
        #     sheet.write_string(row, column + 2, "", row_format_number_color_fact)
        #     sheet.write_string(row, column + 3, "", row_format_number)
        #     sheet.write_string(row, column + 4, "", row_format_number)
        #     sheet.write_string(row, column + 0 + 43, "", row_format_number)
        #     sheet.write_string(row, column + 1 + 43, "", row_format_number)
        #     sheet.write_string(row, column + 2 + 43, "", row_format_number_color_fact)
        #     sheet.write_string(row, column + 3 + 43, "", row_format_number)
        #     sheet.write_string(row, column + 4 + 43, "", row_format_number)

        for element in self.quarter_rus_name:

            column += 1

            if 'NEXT' not in element:
                sheet.write_string(row, column + 0, "", row_format_number)
                sheet.write_string(row, column + 1, "", row_format_number)
                sheet.write_string(row, column + 2, "", row_format_number_color_fact)
                sheet.write_string(row, column + 3, "", row_format_number)
                sheet.write_string(row, column + 4, "", row_format_number)
                sheet.write_string(row, column + 0 + 44, "", row_format_number)
                sheet.write_string(row, column + 1 + 44, "", row_format_number)
                sheet.write_string(row, column + 2 + 44, "", row_format_number_color_fact)
                sheet.write_string(row, column + 3 + 44, "", row_format_number)
                sheet.write_string(row, column + 4 + 44, "", row_format_number)
            elif element == 'NEXT':
                sheet.write_string(row, column + 0, "", row_format_number)
                sheet.write_string(row, column + 1, "", row_format_number)
                sheet.write_string(row, column + 2, "", row_format_number)
                sheet.write_string(row, column + 3, "", row_format_number)
                sheet.write_string(row, column + 4, "", row_format_number)
                sheet.write_string(row, column + 5, "", row_format_number)
                sheet.write_string(row, column + 6, "", row_format_number)
                sheet.write_string(row, column + 0 + 44, "", row_format_number)
                sheet.write_string(row, column + 1 + 44, "", row_format_number)
                sheet.write_string(row, column + 2 + 44, "", row_format_number)
                sheet.write_string(row, column + 3 + 44, "", row_format_number)
                sheet.write_string(row, column + 4 + 44, "", row_format_number)
                sheet.write_string(row, column + 5 + 44, "", row_format_number)
                sheet.write_string(row, column + 6 + 44, "", row_format_number)

            (sumQ75etalon, sumQ50etalon,
             sumQ100, sumQ75, sumQ50) = self.print_quarter_planned_acceptance_project(
                sheet,
                row,
                column,
                element,
                project,
                step,
                project_office,
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

            if 'HY' in element:  # 'HY1/YEAR' 'HY2/YEAR'
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 10),xl_col_to_name(column - 5))
                sheet.write_formula(row, column + 0, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 10 + 44), xl_col_to_name(column - 5 + 44))
                sheet.write_formula(row, column + 0 + 44, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 9),xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 9 + 44), xl_col_to_name(column - 4 + 44))
                sheet.write_formula(row, column + 1 + 44, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8),xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8 + 44), xl_col_to_name(column - 3 + 44))
                sheet.write_formula(row, column + 2 + 44, formula, row_format_number_color_fact)
                if 'HY1' in element:
                    column += 1
                    sheet.write_formula(
                        row,
                        column + 2,
                        f'=IFERROR({xl_col_to_name(column + 1)}{row + 1}/{xl_col_to_name(column)}{row + 1}," ")',
                        row_format_number_color_percent
                    )
                    sheet.write_formula(
                        row,
                        column + 2 + 44,
                        f'=IFERROR({xl_col_to_name(column + 1 + 44)}{row + 1}/{xl_col_to_name(column + 44)}{row + 1}," ")',
                        row_format_number_color_percent
                    )
                    formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8),
                                                           xl_col_to_name(column - 3))
                    sheet.write_formula(row, column + 3, formula, row_format_number)
                    formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8 + 44),
                                                           xl_col_to_name(column - 3 + 44))
                    sheet.write_formula(row, column + 3 + 44, formula, row_format_number)
                    formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 7),
                                                           xl_col_to_name(column - 2))
                    sheet.write_formula(row, column + 4, formula, row_format_number)
                    formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 7 + 44),
                                                           xl_col_to_name(column - 2 + 44))
                    sheet.write_formula(row, column + 4 + 44, formula, row_format_number)
                else:
                    formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 7),xl_col_to_name(column - 2))
                    sheet.write_formula(row, column + 3, formula, row_format_number)
                    formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 7 + 44),
                                                           xl_col_to_name(column - 2 + 44))
                    sheet.write_formula(row, column + 3 + 44, formula, row_format_number)
                    formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 6),xl_col_to_name(column - 1))
                    sheet.write_formula(row, column + 4, formula, row_format_number)
                    formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 6 + 44),
                                                           xl_col_to_name(column - 1 + 44))
                    sheet.write_formula(row, column + 4 + 44, formula, row_format_number)

            elif element == 'YEAR':  # 'YEAR'
                # if sumYear75etalon != 0: sheet.write_number(row, column + 0, sumYear75etalon, row_format_number)
                # if sumYear50etalon != 0: sheet.write_number(row, column + 1, sumYear50etalon, row_format_number)
                # if sumYear100 != 0:      sheet.write_number(row, column + 2, sumYear100, row_format_number_color_fact)
                # if sumYear75 != 0:       sheet.write_number(row, column + 3, sumYear75, row_format_number)
                # if sumYear50 != 0:       sheet.write_number(row, column + 4, sumYear50, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 21), xl_col_to_name(column - 5))
                sheet.write_formula(row, column + 0, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 21 + 44), xl_col_to_name(column - 5 + 44))
                sheet.write_formula(row, column + 0 + 44, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 20), xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 20 + 44), xl_col_to_name(column - 4 + 44))
                sheet.write_formula(row, column + 1 + 44, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 19), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 19 + 44), xl_col_to_name(column - 3 + 44))
                sheet.write_formula(row, column + 2 + 44, formula, row_format_number_color_fact)
                sheet.write_formula(
                    row,
                    column + 3,
                    f'=IFERROR({xl_col_to_name(column + 2)}{row + 1}/{xl_col_to_name(column + 1)}{row + 1}," ")',
                    row_format_number_color_percent
                )
                sheet.write_formula(
                    row,
                    column + 3 + 44,
                    f'=IFERROR({xl_col_to_name(column + 2 + 44)}{row + 1}/{xl_col_to_name(column + 1 + 44)}{row + 1}," ")',
                    row_format_number_color_percent
                )
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 17), xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 4, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 17 + 44), xl_col_to_name(column - 2 + 44))
                sheet.write_formula(row, column + 4 + 44, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 16), xl_col_to_name(column - 1))
                sheet.write_formula(row, column + 5, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 16 + 44), xl_col_to_name(column - 1 + 44))
                sheet.write_formula(row, column + 5 + 44, formula, row_format_number)
                column += 1

            elif element == 'NEXT':
                column += 1

            # elif element == 'AFTER NEXT':
            #     column += 6

            column += 4
        # end Валовая Выручка, без НДС

    def print_row_values_office(self, workbook, sheet, row, column, YEAR, projects, project_office, formula_offices,
                                params):
        global strYEAR
        global YEARint

        row_format_number = workbook.add_format({
            'border': 1,
            'font_size': 10,
            'num_format': '#,##0',
        })
        row_format_number_color_plan = workbook.add_format({
            "fg_color": '#D9E1F2',
            'border': 1,
            'font_size': 10,
            'num_format': '#,##0',
        })
        row_format_number_color_fact = workbook.add_format({
            "fg_color": '#C6E0B4',
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
            "fg_color": '#E2EFDA',
            'border': 1,
            'font_size': 10,
            'num_format': '#,##0',
        })
        row_format_number_color_next = workbook.add_format({
            "fg_color": '#F3F8F0',
            'border': 1,
            'font_size': 10,
            'num_format': '#,##0',
        })
        head_format_month_itogo = workbook.add_format({
            'border': 1,
            "fg_color": '#D9E1F2',
            'diag_type': 3
        })

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

            sheet.write_string(row, column + 0, "", row_format_number)
            sheet.write_string(row, column + 1, "", row_format_number)
            sheet.write_string(row, column + 2, "", row_format_number_color_fact)
            sheet.write_string(row, column + 3, "", row_format_number)
            sheet.write_string(row, column + 4, "", row_format_number)

            for project in projects:
                (sumM75tmpetalon, sumM50tmpetalon,
                 sumM100tmp, sumM75tmp, sumM50tmp,
                 sum_next_75_q1_tmp, sum_next_50_q1_tmp, sum_next_30_q1_tmp,
                 sum_next_75_tmp, sum_next_50_tmp, sum_next_30_tmp,
                 sum_after_next_tmp) = self.calculate_quarter_revenue(element, project, project_office, params)

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

            child_offices_rows = formula_offices.get('project_office_' + str(project_office.id)) or ''

            addcolumn = 0

            if 'Q' in element:
                # f_Q75etalon = 'sum(' + str(sumM75etalon) + child_offices_rows.format(xl_col_to_name(column)) + ')'
                # f_Q50etalon = 'sum(' + str(sumM50etalon) + child_offices_rows.format(xl_col_to_name(column + 1)) + ')'
                f_Q100 = 'sum(' + str(sumM100) + child_offices_rows.format(xl_col_to_name(column + 2)) + ')'
                f_Q75 = 'sum(' + str(sumM75) + child_offices_rows.format(xl_col_to_name(column + 3)) + ')'
                f_Q50 = 'sum(' + str(sumM50) + child_offices_rows.format(xl_col_to_name(column + 4)) + ')'

                po_plan_spec = self.env['project_budget.budget_plan_supervisor_spec'].search([
                    ('budget_plan_supervisor_id.year', '=', YEARint),
                    ('budget_plan_supervisor_id.project_office_id', '=', project_office.id),
                    ('type_row', '=', 'contracting'),
                ])

                po_q_plan = [po_plan_spec.q1_plan, po_plan_spec.q2_plan, po_plan_spec.q3_plan, po_plan_spec.q4_plan]
                po_q66_plan = [po_plan_spec.q1_plan_6_6, po_plan_spec.q2_plan_6_6, po_plan_spec.q3_plan_6_6, po_plan_spec.q4_plan_6_6]

                if child_offices_rows:
                    sheet.write_formula(row, column, 'sum(' + child_offices_rows.format(xl_col_to_name(column)) + ')',
                                        row_format_number_color_plan)
                    sheet.write_formula(row, column + 1,
                                        'sum(' + child_offices_rows.format(xl_col_to_name(column + 1)) + ')',
                                        row_format_number_color_plan)
                else:
                    sheet.write_number(row, column, po_q_plan[int(element[1]) - 1], row_format_number_color_plan)
                    sheet.write_number(row, column + 1, po_q66_plan[int(element[1]) - 1], row_format_number_color_plan)

                sheet.write_formula(row, column + 2, f_Q100, row_format_number_color_fact)
                sheet.write_formula(row, column + 3, f_Q75, row_format_number_color_forecast)
                sheet.write_formula(row, column + 4, f_Q50, row_format_number_color_forecast)

            elif 'HY' in element:  # 'HY1/YEAR' 'HY2/YEAR'
                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 12), xl_col_to_name(column - 6))
                # sheet.write_formula(row, column + 0, formula, row_format_number)
                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 11), xl_col_to_name(column - 5))
                # sheet.write_formula(row, column + 1, formula, row_format_number)

                formula = '=sum({1}{0},{2}{0})'.format(
                    row + 1,
                    xl_col_to_name(column - 10 + addcolumn),
                    xl_col_to_name(column - 5 + addcolumn)
                )
                sheet.write_formula(row, column, formula, row_format_number_color_plan)

                formula = '=sum({1}{0},{2}{0})'.format(
                    row + 1,
                    xl_col_to_name(column - 9 + addcolumn),
                    xl_col_to_name(column - 4 + addcolumn)
                )
                sheet.write_formula(row, column + 1, formula, row_format_number_color_plan)

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)

                if 'HY1' in element:  # 'HY1/YEAR''
                    sheet.write_formula(
                        row,
                        column + 3,
                        f'=IFERROR({xl_col_to_name(column + 2)}{row + 1}/{xl_col_to_name(column + 1)}{row + 1}," ")',
                        row_format_number_color_percent
                    )
                    column += 1
                    addcolumn = -1

                formula = '=sum({1}{0},{2}{0})'.format(
                    row + 1,
                    xl_col_to_name(column - 7 + addcolumn),
                    xl_col_to_name(column - 2 + addcolumn)
                )
                sheet.write_formula(row, column + 3, formula, row_format_number_color_forecast)
                formula = '=sum({1}{0},{2}{0})'.format(
                    row + 1,
                    xl_col_to_name(column - 6 + addcolumn),
                    xl_col_to_name(column - 1 + addcolumn)
                )
                sheet.write_formula(row, column + 4, formula, row_format_number_color_forecast)

            elif element == 'YEAR':  # 'YEAR'

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 21), xl_col_to_name(column - 5))
                sheet.write_formula(row, column, formula, row_format_number_color_plan)

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 20), xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 1, formula, row_format_number_color_plan)

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 19), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)

                column += 1
                sheet.write_formula(
                    row,
                    column + 2,
                    f'=IFERROR({xl_col_to_name(column + 1)}{row + 1}/{xl_col_to_name(column)}{row + 1}," ")',
                    row_format_number_color_percent
                )

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 18), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 3, formula, row_format_number_color_forecast)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 17), xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 4, formula, row_format_number_color_forecast)

            elif element == 'NEXT':
                f_sum_next_75_q1 = 'sum(' + str(sum_next_75_q1) + child_offices_rows.format(xl_col_to_name(column)) + ')'
                f_sum_next_50_q1 = 'sum(' + str(sum_next_50_q1) + child_offices_rows.format(xl_col_to_name(column + 1)) + ')'
                f_sum_next_30_q1 = 'sum(' + str(sum_next_30_q1) + child_offices_rows.format(xl_col_to_name(column + 2)) + ')'
                f_sum_next_75 = 'sum(' + str(sum_next_75) + child_offices_rows.format(xl_col_to_name(column + 3)) + ')'
                f_sum_next_50 = 'sum(' + str(sum_next_50) + child_offices_rows.format(xl_col_to_name(column + 4)) + ')'
                f_sum_next_30 = 'sum(' + str(sum_next_30) + child_offices_rows.format(xl_col_to_name(column + 5)) + ')'
                sheet.write_formula(row, column, f_sum_next_75_q1, row_format_number_color_next)
                sheet.write_formula(row, column + 1, f_sum_next_50_q1, row_format_number_color_next)
                sheet.write_formula(row, column + 2, f_sum_next_30_q1, row_format_number_color_next)
                sheet.write_formula(row, column + 3, f_sum_next_75, row_format_number_color_next)
                sheet.write_formula(row, column + 4, f_sum_next_50, row_format_number_color_next)
                sheet.write_formula(row, column + 5, f_sum_next_30, row_format_number_color_next)
                column += 1

            elif element == 'AFTER NEXT':
                f_sum_after_next = 'sum(' + str(sum_after_next) + child_offices_rows.format(
                    xl_col_to_name(column)) + ')'
                sheet.write_formula(row, column, f_sum_after_next, row_format_number_color_next)
                column -= 4

            column += 4
        # end печать Контрактование, с НДС

        # Поступление денежных средств, с НДС

        # sumYear100etalon = sumYear75etalon = sumYear50etalon = sumYear100 = sumYear75 = sumYear50 = 0
        # sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0
        # sumQ100etalon = sumQ75etalon = sumQ50etalon = sumQ100 = sumQ75 = sumQ50 = 0

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

            # sheet.write_string(row, column + 0, "", row_format_number)
            # sheet.write_string(row, column + 1, "", row_format_number)
            # sheet.write_string(row, column + 2, "", row_format_number_color_fact)
            # sheet.write_string(row, column + 3, "", row_format_number)
            # sheet.write_string(row, column + 4, "", row_format_number)

            for project in projects:
                (sumM75tmpetalon, sumM50tmpetalon,
                 sumM100tmp, sumM75tmp, sumM50tmp,
                 sum_next_75_q1_tmp, sum_next_50_q1_tmp, sum_next_30_q1_tmp,
                 sum_next_75_tmp, sum_next_50_tmp, sum_next_30_tmp,
                 sum_after_next_tmp) = self.calculate_quarter_pds(element, project, project_office, params)

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

            # sumQ75etalon += sumM75etalon
            # sumQ50etalon += sumM50etalon
            # sumQ100 += sumM100
            # sumQ75 += sumM75
            # sumQ50 += sumM50

            child_offices_rows = formula_offices.get('project_office_' + str(project_office.id)) or ''

            addcolumn = 0

            if 'Q' in element:
                # f_Q75etalon = 'sum(' + str(sumM75etalon) + child_offices_rows.format(xl_col_to_name(column)) + ')'
                # f_Q50etalon = 'sum(' + str(sumM50etalon) + child_offices_rows.format(xl_col_to_name(column + 1)) + ')'
                f_Q100 = 'sum(' + str(sumM100) + child_offices_rows.format(xl_col_to_name(column + 2)) + ')'
                f_Q75 = 'sum(' + str(sumM75) + child_offices_rows.format(xl_col_to_name(column + 3)) + ')'
                f_Q50 = 'sum(' + str(sumM50) + child_offices_rows.format(xl_col_to_name(column + 4)) + ')'

                po_plan_spec = self.env['project_budget.budget_plan_supervisor_spec'].search([
                    ('budget_plan_supervisor_id.year', '=', YEARint),
                    ('budget_plan_supervisor_id.project_office_id', '=', project_office.id),
                    ('type_row', '=', 'cash'),
                ])

                po_q_plan = [po_plan_spec.q1_plan, po_plan_spec.q2_plan, po_plan_spec.q3_plan, po_plan_spec.q4_plan]
                po_q66_plan = [po_plan_spec.q1_plan_6_6, po_plan_spec.q2_plan_6_6, po_plan_spec.q3_plan_6_6, po_plan_spec.q4_plan_6_6]

                if child_offices_rows:
                    sheet.write_formula(row, column, 'sum(' + child_offices_rows.format(xl_col_to_name(column)) + ')',
                                        row_format_number_color_plan)
                    sheet.write_formula(row, column + 1,
                                        'sum(' + child_offices_rows.format(xl_col_to_name(column + 1)) + ')',
                                        row_format_number_color_plan)
                else:
                    sheet.write_number(row, column, po_q_plan[int(element[1]) - 1], row_format_number_color_plan)
                    sheet.write_number(row, column + 1, po_q66_plan[int(element[1]) - 1], row_format_number_color_plan)

                sheet.write_formula(row, column + 2, f_Q100, row_format_number_color_fact)
                sheet.write_formula(row, column + 3, f_Q75, row_format_number_color_forecast)
                sheet.write_formula(row, column + 4, f_Q50, row_format_number_color_forecast)

            elif 'HY' in element:  # 'HY1/YEAR' 'HY2/YEAR'
                # if sumHY75etalon != 0: sheet.write_number(row, column + 0, sumHY75etalon, row_format_number)
                # if sumHY50etalon != 0: sheet.write_number(row, column + 1, sumHY50etalon, row_format_number)
                # if sumHY100 != 0:      sheet.write_number(row, column + 2, sumHY100, row_format_number_color_fact)
                # if sumHY75 != 0:       sheet.write_number(row, column + 3, sumHY75, row_format_number)
                # if sumHY50 != 0:       sheet.write_number(row, column + 4, sumHY50, row_format_number)
                # sumYear100etalon += sumHY100etalon
                # sumYear75etalon += sumHY75etalon
                # sumYear50etalon += sumHY50etalon
                # sumYear100 += sumHY100
                # sumYear75 += sumHY75
                # sumYear50 += sumHY50
                # sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0

                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 12),
                #                                        xl_col_to_name(column - 6))
                # sheet.write_formula(row, column + 0, formula, row_format_number)
                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 11),
                #                                        xl_col_to_name(column - 5))
                # sheet.write_formula(row, column + 1, formula, row_format_number)

                formula = '=sum({1}{0},{2}{0})'.format(
                    row + 1,
                    xl_col_to_name(column - 10 + addcolumn),
                    xl_col_to_name(column - 5 + addcolumn)
                )
                sheet.write_formula(row, column, formula, row_format_number_color_plan)

                formula = '=sum({1}{0},{2}{0})'.format(
                    row + 1,
                    xl_col_to_name(column - 9 + addcolumn),
                    xl_col_to_name(column - 4 + addcolumn)
                )
                sheet.write_formula(row, column + 1, formula, row_format_number_color_plan)

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8),
                                                       xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)

                if 'HY1' in element:  # 'HY1/YEAR''
                    sheet.write_formula(
                        row,
                        column + 3,
                        f'=IFERROR({xl_col_to_name(column + 2)}{row + 1}/{xl_col_to_name(column + 1)}{row + 1}," ")',
                        row_format_number_color_percent
                    )
                    column += 1
                    addcolumn = -1

                formula = '=sum({1}{0},{2}{0})'.format(
                    row + 1,
                    xl_col_to_name(column - 7 + addcolumn),
                    xl_col_to_name(column - 2 + addcolumn)
                )
                sheet.write_formula(row, column + 3, formula, row_format_number_color_forecast)

                formula = '=sum({1}{0},{2}{0})'.format(
                    row + 1,
                    xl_col_to_name(column - 6 + addcolumn),
                    xl_col_to_name(column - 1 + addcolumn)
                )
                sheet.write_formula(row, column + 4, formula, row_format_number_color_forecast)

            elif element == 'YEAR':  # 'YEAR'
                # if sumYear75etalon != 0: sheet.write_number(row, column + 0, sumYear75etalon, row_format_number)
                # if sumYear50etalon != 0: sheet.write_number(row, column + 1, sumYear50etalon, row_format_number)
                # if sumYear100 != 0:      sheet.write_number(row, column + 2, sumYear100,
                #                                             row_format_number_color_fact)
                # if sumYear75 != 0:       sheet.write_number(row, column + 3, sumYear75, row_format_number)
                # if sumYear50 != 0:       sheet.write_number(row, column + 4, sumYear50, row_format_number)
                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 23),
                #                                        xl_col_to_name(column - 6))
                # sheet.write_formula(row, column + 0, formula, row_format_number)
                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 22),
                #                                        xl_col_to_name(column - 5))
                # sheet.write_formula(row, column + 1, formula, row_format_number)

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 21),
                                                       xl_col_to_name(column - 5))
                sheet.write_formula(row, column, formula, row_format_number_color_plan)

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 20),
                                                       xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 1, formula, row_format_number_color_plan)

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 19),
                                                       xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)

                column += 1
                sheet.write_formula(
                    row,
                    column + 2,
                    f'=IFERROR({xl_col_to_name(column + 1)}{row + 1}/{xl_col_to_name(column)}{row + 1}," ")',
                    row_format_number_color_percent
                )

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 18),
                                                       xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 3, formula, row_format_number_color_forecast)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 17),
                                                       xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 4, formula, row_format_number_color_forecast)

            elif element == 'NEXT':
                f_sum_next_75_q1 = 'sum(' + str(sum_next_75_q1) + child_offices_rows.format(xl_col_to_name(column)) + ')'
                f_sum_next_50_q1 = 'sum(' + str(sum_next_50_q1) + child_offices_rows.format(xl_col_to_name(column + 1)) + ')'
                f_sum_next_30_q1 = 'sum(' + str(sum_next_30_q1) + child_offices_rows.format(xl_col_to_name(column + 2)) + ')'
                f_sum_next_75 = 'sum(' + str(sum_next_75) + child_offices_rows.format(xl_col_to_name(column + 3)) + ')'
                f_sum_next_50 = 'sum(' + str(sum_next_50) + child_offices_rows.format(xl_col_to_name(column + 4)) + ')'
                f_sum_next_30 = 'sum(' + str(sum_next_30) + child_offices_rows.format(xl_col_to_name(column + 5)) + ')'
                sheet.write_formula(row, column, f_sum_next_75_q1, row_format_number_color_next)
                sheet.write_formula(row, column + 1, f_sum_next_50_q1, row_format_number_color_next)
                sheet.write_formula(row, column + 2, f_sum_next_30_q1, row_format_number_color_next)
                sheet.write_formula(row, column + 3, f_sum_next_75, row_format_number_color_next)
                sheet.write_formula(row, column + 4, f_sum_next_50, row_format_number_color_next)
                sheet.write_formula(row, column + 5, f_sum_next_30, row_format_number_color_next)
                column += 1

            elif element == 'AFTER NEXT':
                f_sum_after_next = 'sum(' + str(sum_after_next) + child_offices_rows.format(
                    xl_col_to_name(column)) + ')'
                sheet.write_formula(row, column, f_sum_after_next, row_format_number_color_next)
                column -= 4

            column += 4
        # end Поступление денежных средсв, с НДС

        # Валовая Выручка, без НДС
        sumYear100etalon = sumYear75etalon = sumYear50etalon = sumYear100 = sumYear75 = sumYear50 = 0
        sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0

        for element in self.quarter_rus_name:

            column += 1
            addcolumn = 0

            sumQ100etalon = sumQ75etalon = sumQ50etalon = sumQ100 = sumQ75 = sumQ50 = 0
            profQ100etalon = profQ75etalon = profQ50etalon = profQ100 = profQ75 = profQ50 = 0
            sum_next_75_q1 = sum_next_50_q1 = sum_next_30_q1 = 0
            sum_next_75 = sum_next_50 = sum_next_30 = sum_after_next = 0
            prof_next_75_q1 = prof_next_50_q1 = prof_next_30_q1 = 0
            prof_next_75 = prof_next_50 = prof_next_30 = prof_after_next = 0


            # sheet.write_string(row, column + 0, "", row_format_number)
            # sheet.write_string(row, column + 1, "", row_format_number)
            # sheet.write_string(row, column + 2, "", row_format_number_color_fact)
            # sheet.write_string(row, column + 3, "", row_format_number)
            # sheet.write_string(row, column + 4, "", row_format_number)
            # sheet.write_string(row, column + 0 + 43, "", row_format_number)
            # sheet.write_string(row, column + 1 + 43, "", row_format_number)
            # sheet.write_string(row, column + 2 + 43, "", row_format_number_color_fact)
            # sheet.write_string(row, column + 3 + 43, "", row_format_number)
            # sheet.write_string(row, column + 4 + 43, "", row_format_number)

            for project in projects:
                (sum75tmpetalon, sum50tmpetalon, sum100tmp, sum75tmp, sum50tmp,
                 prof75tmpetalon, prof50tmpetalon, prof100tmp, prof75tmp, prof50tmp,
                 sum_next_75_q1_tmp, sum_next_50_q1_tmp, sum_next_30_q1_tmp,
                 sum_next_75_tmp, sum_next_50_tmp, sum_next_30_tmp, sum_after_next_tmp,
                 prof_next_75_q1_tmp, prof_next_50_q1_tmp, prof_next_30_q1_tmp,
                 prof_next_75_tmp, prof_next_50_tmp, prof_next_30_tmp, prof_after_next_tmp
                 ) = self.calculate_quarter_planned_acceptance(element, project, project_office, params)

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

            child_offices_rows = formula_offices.get('project_office_' + str(project_office.id)) or ''

            if 'Q' in element:

                po_plan_acc = self.env['project_budget.budget_plan_supervisor_spec'].search([
                    ('budget_plan_supervisor_id.year', '=', YEARint),
                    ('budget_plan_supervisor_id.project_office_id', '=', project_office.id),
                    ('type_row', '=', 'acceptance'),
                ])

                po_plan_margin = self.env['project_budget.budget_plan_supervisor_spec'].search([
                    ('budget_plan_supervisor_id.year', '=', YEARint),
                    ('budget_plan_supervisor_id.project_office_id', '=', project_office.id),
                    ('type_row', '=', 'margin_income'),
                ])

                po_q_plan_acc = [po_plan_acc.q1_plan, po_plan_acc.q2_plan, po_plan_acc.q3_plan, po_plan_acc.q4_plan]
                po_q66_plan_acc = [po_plan_acc.q1_plan_6_6, po_plan_acc.q2_plan_6_6, po_plan_acc.q3_plan_6_6, po_plan_acc.q4_plan_6_6]

                po_q_plan_margin = [po_plan_margin.q1_plan, po_plan_margin.q2_plan, po_plan_margin.q3_plan, po_plan_margin.q4_plan]
                po_q66_plan_margin = [po_plan_margin.q1_plan_6_6, po_plan_margin.q2_plan_6_6, po_plan_margin.q3_plan_6_6, po_plan_margin.q4_plan_6_6]

                if child_offices_rows:
                    sheet.write_formula(row, column, 'sum(' + child_offices_rows.format(xl_col_to_name(column)) + ')',
                                        row_format_number_color_plan)
                    sheet.write_formula(row, column + 1,
                                        'sum(' + child_offices_rows.format(xl_col_to_name(column + 1)) + ')',
                                        row_format_number_color_plan)
                    sheet.write_formula(row, column + 44,
                                        'sum(' + child_offices_rows.format(xl_col_to_name(column + 44)) + ')',
                                        row_format_number_color_plan)
                    sheet.write_formula(row, column + 1 + 44,
                                        'sum(' + child_offices_rows.format(xl_col_to_name(column + 1 + 44)) + ')',
                                        row_format_number_color_plan)
                else:
                    sheet.write_number(row, column, po_q_plan_acc[int(element[1]) - 1], row_format_number_color_plan)
                    sheet.write_number(row, column + 1, po_q66_plan_acc[int(element[1]) - 1], row_format_number_color_plan)
                    sheet.write_number(row, column + 44, po_q_plan_margin[int(element[1]) - 1], row_format_number_color_plan)
                    sheet.write_number(row, column + 1 + 44, po_q66_plan_margin[int(element[1]) - 1], row_format_number_color_plan)

                # f_sumQ75etalon = 'sum(' + str(sumQ75etalon) + child_offices_rows.format(xl_col_to_name(column)) + ')'
                # f_sumQ50etalon = 'sum(' + str(sumQ50etalon) + child_offices_rows.format(
                #     xl_col_to_name(column + 1)) + ')'
                f_sumQ100 = 'sum(' + str(sumQ100) + child_offices_rows.format(xl_col_to_name(column + 2)) + ')'
                f_sumQ75 = 'sum(' + str(sumQ75) + child_offices_rows.format(xl_col_to_name(column + 3)) + ')'
                f_sumQ50 = 'sum(' + str(sumQ50) + child_offices_rows.format(xl_col_to_name(column + 4)) + ')'

                # f_profQ75etalon = 'sum(' + str(profQ75etalon) + child_offices_rows.format(
                #     xl_col_to_name(column + 43)) + ')'
                # f_profQ50etalon = 'sum(' + str(profQ50etalon) + child_offices_rows.format(
                #     xl_col_to_name(column + 44)) + ')'
                f_profQ100 = 'sum(' + str(profQ100) + child_offices_rows.format(xl_col_to_name(column + 2 + 44)) + ')'
                f_profQ75 = 'sum(' + str(profQ75) + child_offices_rows.format(xl_col_to_name(column + 3 + 44)) + ')'
                f_profQ50 = 'sum(' + str(profQ50) + child_offices_rows.format(xl_col_to_name(column + 4 + 44)) + ')'

                # sheet.write_formula(row, column, f_sumQ75etalon, row_format_number)
                # sheet.write_formula(row, column + 43, f_profQ75etalon, row_format_number)
                # sheet.write_formula(row, column + 1, f_sumQ50etalon, row_format_number)
                # sheet.write_formula(row, column + 44, f_profQ50etalon, row_format_number)
                sheet.write_formula(row, column + 2, f_sumQ100, row_format_number_color_fact)
                sheet.write_formula(row, column + 2 + 44, f_profQ100, row_format_number_color_fact)
                sheet.write_formula(row, column + 3, f_sumQ75, row_format_number_color_forecast)
                sheet.write_formula(row, column + 3 + 44, f_profQ75, row_format_number_color_forecast)
                sheet.write_formula(row, column + 4, f_sumQ50, row_format_number_color_forecast)
                sheet.write_formula(row, column + 4 + 44, f_profQ50, row_format_number_color_forecast)

                # sumHY100etalon += sumQ100etalon
                # sumHY75etalon += sumQ75etalon
                # sumHY50etalon += sumQ50etalon
                # sumHY100 += sumQ100
                # sumHY75 += sumQ75
                # sumHY50 += sumQ50

            elif 'HY' in element:  # 'HY1/YEAR итого' 'HY2/YEAR итого'
                # sumYear100etalon += sumHY100etalon
                # sumYear75etalon += sumHY75etalon
                # sumYear50etalon += sumHY50etalon
                # sumYear100 += sumHY100
                # sumYear75 += sumHY75
                # sumYear50 += sumHY50

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 10), xl_col_to_name(column - 5))
                sheet.write_formula(row, column, formula, row_format_number_color_plan)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 9), xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 1, formula, row_format_number_color_plan)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 10 + 44),
                                                       xl_col_to_name(column - 5 + 44))
                sheet.write_formula(row, column + 44, formula, row_format_number_color_plan)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 9 + 44),
                                                       xl_col_to_name(column - 4 + 44))
                sheet.write_formula(row, column + 1 + 44, formula, row_format_number_color_plan)

                sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0

                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 12 - addcolumn), xl_col_to_name(column - 6 - addcolumn))
                # sheet.write_formula(row, column + 0, formula, row_format_number)
                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 11 - addcolumn), xl_col_to_name(column - 5 - addcolumn))
                # sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8 + 44),
                                                       xl_col_to_name(column - 3 + 44))
                sheet.write_formula(row, column + 2 + 44, formula, row_format_number_color_fact)

                if 'HY1' in element:  # 'HY1/YEAR''
                    sheet.write_formula(
                        row,
                        column + 3,
                        f'=IFERROR({xl_col_to_name(column + 2)}{row + 1}/{xl_col_to_name(column + 1)}{row + 1}," ")',
                        row_format_number_color_percent
                    )
                    sheet.write_formula(
                        row,
                        column + 3 + 44,
                        f'=IFERROR({xl_col_to_name(column + 2 + 44)}{row + 1}/{xl_col_to_name(column + 1 + 44)}{row + 1}," ")',
                        row_format_number_color_percent
                    )
                    column += 1
                    addcolumn = -1

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 7 + addcolumn),
                                                       xl_col_to_name(column - 2 + addcolumn))
                sheet.write_formula(row, column + 3, formula, row_format_number_color_forecast)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 6 + addcolumn),
                                                       xl_col_to_name(column - 1 + addcolumn))
                sheet.write_formula(row, column + 4, formula, row_format_number_color_forecast)

                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 12 + 43), xl_col_to_name(column - 6 + 43))
                # sheet.write_formula(row, column + 0 + 43, formula, row_format_number)
                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 11 + 43), xl_col_to_name(column - 5 + 43))
                # sheet.write_formula(row, column + 1 + 43, formula, row_format_number)

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 7 + 44 + addcolumn),
                                                       xl_col_to_name(column - 2 + 44 + addcolumn))
                sheet.write_formula(row, column + 3 + 44, formula, row_format_number_color_forecast)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 6 + 44 + addcolumn),
                                                       xl_col_to_name(column - 1 + 44 + addcolumn))
                sheet.write_formula(row, column + 4 + 44, formula, row_format_number_color_forecast)

            elif element == 'YEAR':  # 'YEAR'
                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 25), xl_col_to_name(column - 6))
                # sheet.write_formula(row, column + 0, formula, row_format_number)
                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 24), xl_col_to_name(column - 5))
                # sheet.write_formula(row, column + 1, formula, row_format_number)

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 21), xl_col_to_name(column - 5))
                sheet.write_formula(row, column, formula, row_format_number_color_plan)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 20), xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 1, formula, row_format_number_color_plan)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 21 + 44),
                                                       xl_col_to_name(column - 5 + 44))
                sheet.write_formula(row, column + 44, formula, row_format_number_color_plan)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 20 + 44),
                                                       xl_col_to_name(column - 4 + 44))
                sheet.write_formula(row, column + 1 + 44, formula, row_format_number_color_plan)

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 19), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 19 + 44),
                                                       xl_col_to_name(column - 3 + 44))
                sheet.write_formula(row, column + 2 + 44, formula, row_format_number_color_fact)

                column += 1
                sheet.write_formula(
                    row,
                    column + 2,
                    f'=IFERROR({xl_col_to_name(column + 1)}{row + 1}/{xl_col_to_name(column)}{row + 1}," ")',
                    row_format_number_color_percent
                )
                sheet.write_formula(
                    row,
                    column + 2 + 44,
                    f'=IFERROR({xl_col_to_name(column + 1 + 44)}{row + 1}/{xl_col_to_name(column + 44)}{row + 1}," ")',
                    row_format_number_color_percent
                )

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 18), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 3, formula, row_format_number_color_forecast)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 17), xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 4, formula, row_format_number_color_forecast)

                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 25 + 43), xl_col_to_name(column - 6 + 43))
                # sheet.write_formula(row, column + 0 + 43, formula, row_format_number)
                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 24 + 43), xl_col_to_name(column - 5 + 43))
                # sheet.write_formula(row, column + 1 + 43, formula, row_format_number)

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 18 + 44),
                                                       xl_col_to_name(column - 3 + 44))
                sheet.write_formula(row, column + 3 + 44, formula, row_format_number_color_forecast)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 17 + 44),
                                                       xl_col_to_name(column - 2 + 44))
                sheet.write_formula(row, column + 4 + 44, formula, row_format_number_color_forecast)

            elif element == 'NEXT':
                f_sum_next_75_q1 = 'sum(' + str(sum_next_75_q1) + child_offices_rows.format(xl_col_to_name(column)) + ')'
                f_sum_next_50_q1 = 'sum(' + str(sum_next_50_q1) + child_offices_rows.format(xl_col_to_name(column + 1)) + ')'
                f_sum_next_30_q1 = 'sum(' + str(sum_next_30_q1) + child_offices_rows.format(xl_col_to_name(column + 2)) + ')'
                f_sum_next_75 = 'sum(' + str(sum_next_75) + child_offices_rows.format(xl_col_to_name(column + 3)) + ')'
                f_sum_next_50 = 'sum(' + str(sum_next_50) + child_offices_rows.format(xl_col_to_name(column + 4)) + ')'
                f_sum_next_30 = 'sum(' + str(sum_next_30) + child_offices_rows.format(xl_col_to_name(column + 5)) + ')'
                sheet.write_formula(row, column, f_sum_next_75_q1, row_format_number_color_next)
                sheet.write_formula(row, column + 1, f_sum_next_50_q1, row_format_number_color_next)
                sheet.write_formula(row, column + 2, f_sum_next_30_q1, row_format_number_color_next)
                sheet.write_formula(row, column + 3, f_sum_next_75, row_format_number_color_next)
                sheet.write_formula(row, column + 4, f_sum_next_50, row_format_number_color_next)
                sheet.write_formula(row, column + 5, f_sum_next_30, row_format_number_color_next)
                f_prof_next_75_q1 = 'sum(' + str(prof_next_75_q1) + child_offices_rows.format(
                    xl_col_to_name(column + 44)) + ')'
                f_prof_next_50_q1 = 'sum(' + str(prof_next_50_q1) + child_offices_rows.format(
                    xl_col_to_name(column + 1 + 44)) + ')'
                f_prof_next_30_q1 = 'sum(' + str(prof_next_30_q1) + child_offices_rows.format(
                    xl_col_to_name(column + 2 + 44)) + ')'
                f_prof_next_75 = 'sum(' + str(prof_next_75) + child_offices_rows.format(
                    xl_col_to_name(column + 3 + 44)) + ')'
                f_prof_next_50 = 'sum(' + str(prof_next_50) + child_offices_rows.format(
                    xl_col_to_name(column + 4 + 44)) + ')'
                f_prof_next_30 = 'sum(' + str(prof_next_30) + child_offices_rows.format(
                    xl_col_to_name(column + 5 + 44)) + ')'
                sheet.write_formula(row, column + 44, f_prof_next_75_q1, row_format_number_color_next)
                sheet.write_formula(row, column + 1 + 44, f_prof_next_50_q1, row_format_number_color_next)
                sheet.write_formula(row, column + 2 + 44, f_prof_next_30_q1, row_format_number_color_next)
                sheet.write_formula(row, column + 3 + 44, f_prof_next_75, row_format_number_color_next)
                sheet.write_formula(row, column + 4 + 44, f_prof_next_50, row_format_number_color_next)
                sheet.write_formula(row, column + 5 + 44, f_prof_next_30, row_format_number_color_next)
                column += 1

            elif element == 'AFTER NEXT':
                f_sum_after_next = 'sum(' + str(sum_after_next) + child_offices_rows.format(
                    xl_col_to_name(column)) + ')'
                sheet.write_formula(row, column, f_sum_after_next, row_format_number_color_next)
                f_prof_after_next = 'sum(' + str(prof_after_next) + child_offices_rows.format(
                    xl_col_to_name(column + 44)) + ')'
                sheet.write_formula(row, column + 44, f_prof_after_next, row_format_number_color_next)
                column -= 4

            column += 4
        # end Валовая Выручка, без НДС

    def printrow(self, sheet, workbook, companies, project_offices, budget, row, formulaItogo, level, params):
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

        row_format_office = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": False,
            "num_format": '#,##0',
        })

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

        # project_offices = self.env['project_budget.project_office'].search([],order='name')  # для сортировки так делаем + берем сначала только верхние элементы

        isFoundProjectsByOffice = False
        isFoundProjectsByManager = False
        begRowProjectsByOffice = 0

        cur_budget_projects = self.env['project_budget.projects'].search([
            ('commercial_budget_id', '=', budget.id),
            ('is_parent_project', '=', False)],
            ).sorted(key=lambda r: (r.project_manager_id.name, r.estimated_probability_id.code))

        # cur_project_offices = project_offices.filtered(lambda r: r in cur_budget_projects.project_office_id or r in {office.parent_id for office in cur_budget_projects.project_office_id if office.parent_id in project_offices})
        cur_project_offices = project_offices
        # cur_project_managers = project_managers.filtered(lambda r: r in cur_budget_projects.project_manager_id)
        cur_companies = companies.filtered(lambda r: r in cur_project_offices.company_id)

        for company in cur_companies:
            print('company = ', company.name)
            isFoundProjectsByCompany = False
            formulaProjectCompany = '=sum(0'

            dict_formula['office_ids_not_empty'] = {}

            if company.id not in dict_formula['company_ids']:
                row += 1
                dict_formula['company_ids'][company.id] = row

            for project_office in cur_project_offices.filtered(lambda r: r in (office for office in self.env[
                'project_budget.project_office'].search([('company_id', '=', company.id), ]))):

                print('project_office.name = ', project_office.name)

                begRowProjectsByOffice = 0

                row0 = row

                child_project_offices = self.env['project_budget.project_office'].search(
                    [('parent_id', '=', project_office.id)], order='name')

                if project_office.child_ids:
                    row += 1
                    dict_formula['office_ids'][project_office.id] = row
                    row0, formulaItogo = self.printrow(sheet, workbook, company, child_project_offices, budget, row,
                                                       formulaItogo, level + 1, params)

                isFoundProjectsByOffice = False
                if row0 != row:
                    isFoundProjectsByOffice = True

                row = row0

                formulaProjectOffice = '=sum(0'
                # for project_manager in cur_project_managers:
                #     isFoundProjectsByManager = False
                #     formulaProjectManager = '=sum(0'
                #     column = -1

                # cur_budget_projects = self.env['project_budget.projects'].search([
                #     ('commercial_budget_id', '=', budget.id),
                #     ('project_office_id', '=', project_office.id),
                #     ('project_manager_id', '=', project_manager.id),
                #     ('estimated_probability_id', '=', estimated_probability.id),
                #     ('project_have_steps', '=', False),
                #     ])

                # for project in cur_budget_projects_with_steps:
                #     for step in project.project_steps_ids:
                #         if step.estimated_probability_id.code == str(estimated_probability.id):
                #             print('cur_budget_projects_1', cur_budget_projects, step)
                #             cur_budget_projects = cur_budget_projects + self.env['project_budget.projects'].search([('id', '=', step)])
                #             print('cur_budget_projects_2', cur_budget_projects, step)

                # row += 1
                # sheet.write_string(row, column, project_office.name, row_format)

                for spec in cur_budget_projects:
                    if spec.is_framework is True and spec.project_have_steps is False: continue  # рамка без этапов - пропускаем
                    if spec.vgo == '-':

                        if begRowProjectsByOffice == 0:
                            begRowProjectsByOffice = row

                        if spec.project_have_steps:
                            for step in spec.project_steps_ids:

                                if (((spec.legal_entity_signing_id.different_project_offices_in_steps and step.project_office_id == project_office)
                                     or ((not spec.legal_entity_signing_id.different_project_offices_in_steps or not step.project_office_id) and spec.project_office_id == project_office))
                                        and spec.company_id == company):

                                    if self.isStepinYear(spec, step) is False:
                                        continue

                                    isFoundProjectsByOffice = True
                                    isFoundProjectsByCompany = True

                                    # печатаем строки этапов проектов
                                    # row += 1
                                    # sheet.set_row(row, False, False, {'hidden': 1, 'level': max_level})
                                    # cur_row_format = row_format
                                    # cur_row_format_number = row_format_number
                                    # if step.estimated_probability_id.name == '0':
                                    #     cur_row_format = row_format_canceled_project
                                    #     cur_row_format_number = row_format_number_canceled_project
                                    # column = 0
                                    # sheet.write_string(row, column, '       ' * max_level + spec.project_office_id.name, cur_row_format)
                                    # column += 1
                                    # sheet.write_string(row, column, spec.project_manager_id.name, cur_row_format)
                                    # column += 1
                                    # sheet.write_string(row, column, spec.customer_organization_id.name, cur_row_format)
                                    # column += 1
                                    # sheet.write_string(row, column, step.essence_project, cur_row_format)
                                    # column += 1
                                    # sheet.write_string(row, column, (step.code or '') +' | '+ spec.project_id + " | "+step.step_id, cur_row_format)
                                    # column += 1
                                    # sheet.write_string(row, column, self.get_estimated_probability_name_forecast(step.estimated_probability_id.name), cur_row_format)
                                    # column += 1
                                    # sheet.write_number(row, column, step.total_amount_of_revenue_with_vat, cur_row_format_number)
                                    # column += 1
                                    # sheet.write_number(row, column, step.margin_income, cur_row_format_number)
                                    # column += 1
                                    # sheet.write_number(row, column, step.profitability, cur_row_format_number)
                                    # column += 1
                                    # sheet.write_string(row, column, step.dogovor_number or '', cur_row_format)
                                    # column += 1
                                    # sheet.write_string(row, column, step.vat_attribute_id.name, cur_row_format)
                                    # column += 1
                                    # sheet.write_string(row, column, '', head_format_1)
                                    # self.print_row_Values(workbook, sheet, row, column,  strYEAR, spec, step)
                        else:
                            if spec.project_office_id == project_office and spec.company_id == company:
                                if self.isProjectinYear(spec) is False:
                                    continue

                                isFoundProjectsByOffice = True
                                isFoundProjectsByCompany = True

                                # печатаем строки проектов
                                # row += 1
                                # sheet.set_row(row, False, False, {'hidden': 1, 'level': max_level})
                                # cur_row_format = row_format
                                # cur_row_format_number = row_format_number
                                # if spec.estimated_probability_id.name == '0':
                                #     cur_row_format = row_format_canceled_project
                                #     cur_row_format_number = row_format_number_canceled_project
                                # column = 0
                                # sheet.write_string(row, column, '       ' * max_level + spec.project_office_id.name, cur_row_format)
                                # column += 1
                                # sheet.write_string(row, column, spec.project_manager_id.name, cur_row_format)
                                # column += 1
                                # sheet.write_string(row, column, spec.customer_organization_id.name, cur_row_format)
                                # column += 1
                                # sheet.write_string(row, column, spec.essence_project, cur_row_format)
                                # column += 1
                                # sheet.write_string(row, column, (spec.step_project_number or '')+ ' | ' +(spec.project_id or ''), cur_row_format)
                                # column += 1
                                # sheet.write_string(row, column, self.get_estimated_probability_name_forecast(spec.estimated_probability_id.name), cur_row_format)
                                # column += 1
                                # sheet.write_number(row, column, spec.total_amount_of_revenue_with_vat, cur_row_format_number)
                                # column += 1
                                # sheet.write_number(row, column, spec.margin_income, cur_row_format_number)
                                # column += 1
                                # sheet.write_number(row, column, spec.profitability, cur_row_format_number)
                                # column += 1
                                # sheet.write_string(row, column, spec.dogovor_number or '', cur_row_format)
                                # column += 1
                                # sheet.write_string(row, column, spec.vat_attribute_id.name or '', cur_row_format)
                                # column += 1
                                # sheet.write_string(row, column, '', head_format_1)
                                # self.print_row_Values(workbook, sheet, row, column,  strYEAR, spec, False)

                    # if isFoundProjectsByProbability:
                    #     row += 1
                    #     column = 2
                    #     sheet.write_string(row, column, project_manager.name + ' ' + estimated_probability.name
                    #                        + ' %', row_format_probability)
                    #     sheet.set_row(row, False, False, {'hidden': 1, 'level': level})
                    #
                    #     formulaProjectManager = formulaProjectManager + ',{0}' + str(row + 1)
                    #     for colFormula in range(3, 12):
                    #         sheet.write_string(row, colFormula, '', row_format_probability)
                    #     for colFormula in range(12, 302):
                    #         formula = '=sum({2}{0}:{2}{1})'.format(begRowProjectsByProbability + 2, row,
                    #                                                xl_col_to_name(colFormula))
                    #         sheet.write_formula(row, colFormula, formula, row_format_probability)
                    #     for col in self.array_col_itogi75:
                    #         formula = '={1}{0} + {2}{0}'.format(row + 1, xl_col_to_name(col + 1),
                    #                                             xl_col_to_name(col + 2))
                    #         sheet.write_formula(row, col - 1, formula, head_format_month_itogo)
                    #     for col in self.array_col_itogi75NoFormula:
                    #         formula = '=0'
                    #         sheet.write_formula(row, col - 1, formula, head_format_month_itogo)

                    # if isFoundProjectsByManager:
                    #     row += 1
                    #     column = 1
                    #     sheet.write_string(row, column, 'ИТОГО ' + project_manager.name, row_format_manager)
                    #     sheet.set_row(row, False, False, {'hidden': 1, 'level': 4})
                    #     print('setrow manager  row = ', row)
                    #     print('setrow manager level = ', level)
                    #
                    #     formulaProjectOffice = formulaProjectOffice + ',{0}'+str(row + 1)
                    #
                    #     for colFormula in range(2, 12):
                    #         sheet.write_string(row, colFormula, '', row_format_manager)
                    #
                    #     for colFormula in range(12, 302):
                    #         formula = '=sum({2}{0}:{2}{1})'.format(begRowProjectsByManager + 2, row,
                    #                                                xl_col_to_name(colFormula))
                    #         sheet.write_formula(row, colFormula, formula, row_format_manager)
                    #
                    #     for col in self.array_col_itogi75:
                    #         formula = '={1}{0} + {2}{0}'.format(row+1,xl_col_to_name(col + 1),xl_col_to_name(col + 2))
                    #         sheet.write_formula(row, col - 1, formula, head_format_month_itogo)
                    #
                    #     for col in self.array_col_itogi75NoFormula:
                    #         formula = '=0'
                    #         sheet.write_formula(row, col - 1, formula, head_format_month_itogo)

                if project_office.parent_id:
                    isFoundProjectsByCompany = False

                if isFoundProjectsByOffice:

                    dict_formula['office_ids_not_empty'][project_office.id] = row

                    column = 0

                    if child_project_offices:
                        office_row = dict_formula['office_ids'].get(project_office.id)
                    else:
                        row += 1
                        office_row = row

                    office_name = project_office.report_name or project_office.name

                    sheet.write_string(office_row, column, '       ' * level + office_name, row_format_office)
                    if params['report_with_projects']:
                        sheet.merge_range(office_row, column + 1, office_row, column + params["shift"] , '', row_format_office)
                    sheet.set_row(office_row, False, False, {'hidden': 1, 'level': level})

                    str_project_office_id = 'project_office_' + str(int(project_office.parent_id))
                    if str_project_office_id in dict_formula:
                        dict_formula[str_project_office_id] = dict_formula[str_project_office_id] + ',{0}' + str(
                            office_row + 1)
                    else:
                        dict_formula[str_project_office_id] = ',{0}' + str(office_row + 1)

                    formulaProjectOffice += ',{0}' + f'{begRowProjectsByOffice + 2}' + ':{0}' + f'{office_row}'

                    str_project_office_id = 'project_office_' + str(int(project_office.id))
                    if str_project_office_id in dict_formula:
                        formulaProjectOffice = formulaProjectOffice + dict_formula[str_project_office_id] + ')'
                    else:
                        formulaProjectOffice = formulaProjectOffice + ')'

                    projects = self.env['project_budget.projects'].search(['&','&',
                                                                           ('commercial_budget_id', '=', budget.id),
                                                                           ('is_parent_project', '=', False),
                                                                           '|',
                                                                           (
                                                                           'project_office_id', '=', project_office.id),
                                                                           '&',
                                                                           (
                                                                           'legal_entity_signing_id.different_project_offices_in_steps',
                                                                           '=', True),
                                                                           ('project_have_steps', '=', True),
                                                                           ])

                    self.print_row_values_office(
                        workbook,
                        sheet,
                        office_row,
                        column + params["shift"] ,
                        strYEAR,
                        projects,
                        project_office,
                        dict_formula,
                        params,
                    )

                    if params['report_with_projects']:
                        for spec in cur_budget_projects:
                            if spec.is_framework is True and spec.project_have_steps is False: continue  # рамка без этапов - пропускаем
                            if spec.vgo == '-':

                                if spec.project_have_steps:
                                    for step in spec.project_steps_ids:

                                        if (((
                                                     spec.legal_entity_signing_id.different_project_offices_in_steps and step.project_office_id == project_office)
                                             or ((
                                                         not spec.legal_entity_signing_id.different_project_offices_in_steps or not step.project_office_id) and spec.project_office_id == project_office))
                                                and spec.company_id == company):

                                            if self.isStepinYear(spec, step) is False or step.estimated_probability_id.name in ('0', '10'):
                                                continue

                                            # печатаем строки этапов проектов
                                            row += 1
                                            sheet.set_row(row, False, False, {'hidden': 1, 'level': max_level})
                                            cur_row_format = row_format
                                            cur_row_format_number = row_format_number
                                            if step.estimated_probability_id.name == '0':
                                                cur_row_format = row_format_canceled_project
                                                cur_row_format_number = row_format_number_canceled_project
                                            column = 0
                                            sheet.write_string(row, column, '       ' * max_level + spec.project_manager_id.name, cur_row_format)
                                            column += 1
                                            sheet.write_string(row, column, spec.customer_organization_id.name,
                                                               cur_row_format)
                                            column += 1
                                            sheet.write_string(row, column, step.essence_project, cur_row_format)
                                            column += 1
                                            sheet.write_string(row, column, (
                                                        step.code or '') + ' | ' + spec.project_id + " | " + step.step_id,
                                                               cur_row_format)
                                            column += 1
                                            sheet.write_string(row, column, self.get_estimated_probability_name_forecast(
                                                step.estimated_probability_id.name), cur_row_format)
                                            column += 1
                                            sheet.write_number(row, column,
                                                               step.total_amount_of_revenue_with_vat * self.get_currency_rate_by_project(step.projects_id),
                                                               cur_row_format_number)
                                            column += 1
                                            sheet.write_number(row, column,
                                                               step.margin_income * self.get_currency_rate_by_project(step.projects_id),
                                                               cur_row_format_number)
                                            column += 1
                                            sheet.write_string(row, column, f'{step.profitability:.2f}' + '%', cur_row_format)
                                            column += 1
                                            sheet.write_string(row, column, step.dogovor_number or '', cur_row_format)
                                            column += 1
                                            sheet.write_string(row, column, step.vat_attribute_id.name or '', cur_row_format)
                                            column += 1
                                            sheet.write_string(row, column, '', cur_row_format)
                                            self.print_row_Values(workbook, sheet, row, column, strYEAR, spec, step, project_office, params)
                                else:
                                    if spec.project_office_id == project_office and spec.company_id == company:
                                        if self.isProjectinYear(spec) is False or spec.estimated_probability_id.name in ('0', '10'):
                                            continue

                                        # печатаем строки проектов
                                        row += 1
                                        sheet.set_row(row, False, False, {'hidden': 1, 'level': max_level})
                                        cur_row_format = row_format
                                        cur_row_format_number = row_format_number
                                        if spec.estimated_probability_id.name == '0':
                                            cur_row_format = row_format_canceled_project
                                            cur_row_format_number = row_format_number_canceled_project
                                        column = 0
                                        sheet.write_string(row, column, '       ' * max_level + spec.project_manager_id.name, cur_row_format)
                                        column += 1
                                        sheet.write_string(row, column, spec.customer_organization_id.name, cur_row_format)
                                        column += 1
                                        sheet.write_string(row, column, spec.essence_project, cur_row_format)
                                        column += 1
                                        sheet.write_string(row, column, (spec.step_project_number or '') + ' | ' + (
                                                    spec.project_id or ''), cur_row_format)
                                        column += 1
                                        sheet.write_string(row, column, self.get_estimated_probability_name_forecast(
                                            spec.estimated_probability_id.name), cur_row_format)
                                        column += 1
                                        sheet.write_number(row, column,
                                                           spec.total_amount_of_revenue_with_vat * self.get_currency_rate_by_project(spec),
                                                           cur_row_format_number)
                                        column += 1
                                        sheet.write_number(row, column,
                                                           spec.margin_income * self.get_currency_rate_by_project(spec),
                                                           cur_row_format_number)
                                        column += 1
                                        sheet.write_string(row, column, f'{spec.profitability:.2f}' + '%', cur_row_format)
                                        column += 1
                                        sheet.write_string(row, column, spec.dogovor_number or '', cur_row_format)
                                        column += 1
                                        sheet.write_string(row, column, spec.vat_attribute_id.name or '', cur_row_format)
                                        column += 1
                                        sheet.write_string(row, column, '', cur_row_format)
                                        self.print_row_Values(workbook, sheet, row, column, strYEAR, spec, False, project_office, params)

                    # for colFormula in range(12, 302):
                    #     formula = formulaProjectOffice.format(xl_col_to_name(colFormula))
                    #     sheet.write_formula(row, colFormula, formula, row_format_office)

                    # for col in self.array_col_itogi75:
                    #     formula = '={1}{0} + {2}{0}'.format(row+1, xl_col_to_name(col + 1), xl_col_to_name(col + 2))
                    #     sheet.write_formula(row, col - 1, formula, head_format_month_itogo)
                    #
                    # for col in self.array_col_itogi75NoFormula:
                    #     formula = '=0'
                    #     sheet.write_formula(row, col - 1, formula, head_format_month_itogo)

                    if not project_office.parent_id:
                        formulaProjectCompany += ',{0}' + f'{office_row + 1}'
                    if params['report_with_projects']:
                        row += 1
                        sheet.write_string(row, column, '', row_format_company_empty)
                        sheet.set_row(row, 14, row_format_company_empty, {'hidden': 1, 'level': level})
                else:
                    if project_office.child_ids:
                        if all(child.id not in dict_formula['office_ids_not_empty'] for child in
                               project_office.child_ids):
                            row -= 1

            if isFoundProjectsByCompany:
                column = 0

                company_row = dict_formula['company_ids'][company.id]

                sheet.write_string(company_row, column, company.name, row_format_company)
                if params['report_with_projects']:
                    sheet.merge_range(company_row, column + 1, company_row, column + params["shift"] , '', row_format_company)

                formulaProjectCompany += ')'

                shift = params["shift"]
                for i in range(0, 4):  # оформление строки Компания
                    for colFormula in range(0, 7):
                        formula = formulaProjectCompany.format(xl_col_to_name(i * 38 + colFormula * 5 + 1 + shift))
                        sheet.write_formula(company_row, i * 38 + colFormula * 5 + 1 + shift, formula,
                                            row_format_company_plan)
                        formula = formulaProjectCompany.format(xl_col_to_name(i * 38 + colFormula * 5 + 2 + shift))
                        sheet.write_formula(company_row, i * 38 + colFormula * 5 + 2 + shift, formula,
                                            row_format_company_plan)
                        formula = formulaProjectCompany.format(xl_col_to_name(i * 38 + colFormula * 5 + 3 + shift))
                        sheet.write_formula(company_row, i * 38 + colFormula * 5 + 3 + shift, formula,
                                            row_format_company_fact)
                        if colFormula in (2, 6):
                            formula = f'=IFERROR({xl_col_to_name(i * 38 + colFormula * 5 + 3 + shift)}{company_row + 1}/{xl_col_to_name(i * 38 + colFormula * 5 + 2 + shift)}{company_row + 1}," ")'
                            sheet.write_formula(company_row, i * 38 + colFormula * 5 + 4 + shift, formula,
                                                row_format_company_percent)
                            shift += 1
                        formula = formulaProjectCompany.format(xl_col_to_name(i * 38 + colFormula * 5 + 4 + shift))
                        sheet.write_formula(company_row, i * 38 + colFormula * 5 + 4 + shift, formula,
                                            row_format_company_forecast)
                        formula = formulaProjectCompany.format(xl_col_to_name(i * 38 + colFormula * 5 + 5 + shift))
                        sheet.write_formula(company_row, i * 38 + colFormula * 5 + 5 + shift, formula,
                                            row_format_company_forecast)
                    for x in range(7):
                        formula = formulaProjectCompany.format(xl_col_to_name((i + 1) * 38 + x + shift - 2))
                        sheet.write_formula(company_row, (i + 1) * 38 + x + shift - 2, formula, row_format_company_next)
                    shift += 4

        return row, formulaItogo

    def printworksheet(self, workbook, budget, namesheet, params):
        global strYEAR
        global YEARint
        global max_level
        print('YEARint=', YEARint)
        print('strYEAR =', strYEAR)

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
            ('commercial_budget_id', '=', budget.id),
            ('is_parent_project', '=', False),
        ])

        #  считаем max_level
        depth_dict = {}
        max_depth = 1
        parents = [False,]
        new_parents = []

        parent_offices = self.env['project_budget.project_office'].search([('parent_id', 'in', parents)])
        while parent_offices:
            for office in parent_offices:
                depth_dict[office] = max_depth
                new_parents.append(office.id)
            max_depth += 1
            parents = new_parents
            new_parents = []
            parent_offices = self.env['project_budget.project_office'].search([('parent_id', 'in', parents)])

        depth = 1

        # for project in cur_budget_projects:
        #     if project.project_have_steps:
        #         for step in project.project_steps_ids:
        #             if step.project_office_id.id:
        #                 depth = max(depth, depth_dict[step.project_office_id])
        #     else:
        #         depth = max(depth, depth_dict[project.project_office_id])
        #     if depth == max_depth:
        #         break

        for project in cur_budget_projects:
            depth = max(depth, depth_dict[project.project_office_id])
            if depth == max_depth:
                break

        max_level = depth + 1

        companies = self.env['res.company'].search([], order='name')
        project_offices = self.env['project_budget.project_office'].search([('parent_id', '=', False)],
                                                                           order='report_sort')  # для сортировки так делаем + берем сначала только верхние элементы
        # project_managers = self.env['project_budget.project_manager'].search([], order='name')  # для сортировки так делаем
        # estimated_probabilitys = self.env['project_budget.estimated_probability'].search([('name','!=','10')],order='code desc')  # для сортировки так делаем

        formulaItogo = '=sum(0'

        row, formulaItogo = self.printrow(sheet, workbook, companies, project_offices, budget, row, formulaItogo, 1,
                                          params)

        row += 1
        column = 0
        sheet.write_string(row, column, 'ИТОГО по отчету', row_format_number_itogo)
        if params['report_with_projects']:
            sheet.merge_range(row, column + 1, row, column + params["shift"] , '', row_format_number_itogo)
        for company_row in dict_formula['company_ids'].values():
            formulaItogo += ',{0}' + str(company_row + 1)
        formulaItogo = formulaItogo + ')'
        for colFormula in range(1 + params["shift"] , 177 + params["shift"] ):
            formula = formulaItogo.format(xl_col_to_name(colFormula))
            sheet.write_formula(row, colFormula, formula, row_format_number_itogo)
        for i in range(4):  # формулы для процентов выполнения
            for j in (14, 35):
                formula = f'=IFERROR({xl_col_to_name(i * 44 + j + params["shift"] - 1)}{row + 1}/{xl_col_to_name(i * 44 + j + params["shift"] - 2)}{row + 1}, " ")'
                sheet.write_formula(row, i * 44 + j + params['shift'], formula, row_format_number_itogo_percent)
        print('dict_formula = ', dict_formula)

    def generate_xlsx_report(self, workbook, data, budgets):

        global strYEAR
        strYEAR = str(data['year'])
        global YEARint
        YEARint = int(strYEAR)
        global dict_formula
        dict_formula = {'company_ids': {}, 'office_ids': {}, 'office_ids_not_empty': {}}
        global max_level

        print('YEARint=', YEARint)
        print('strYEAR =', strYEAR)

        params = {'50': data['koeff_reserve'], '30': data['koeff_potential'],
                       'report_with_projects': data['report_with_projects'], 'shift': 0}

        if data['report_with_projects']:
            params['shift'] = 10

        commercial_budget_id = data['commercial_budget_id']
        print('commercial_budget_id', commercial_budget_id)
        budget = self.env['project_budget.commercial_budget'].search([('id', '=', commercial_budget_id)])
        self.printworksheet(workbook, budget, 'Прогноз', params)
