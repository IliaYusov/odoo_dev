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

            etalon_project = self.get_etalon_project_first(project) # поищем первый эталон в году и если контрактование или последняя отгрузка были в году, то надо проект в отчете показывать
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

    def get_etalon_project_first(self,spec):
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
            datesearch = datetime.date(YEARint, 1, 1) # будем искать первый утвержденный в году
        if 'Q2' in quarter:
            datesearch = datetime.date(YEARint, 4, 1) # будем искать первый утвержденный после марта
        if 'Q3' in quarter:
            datesearch = datetime.date(YEARint, 7, 1) # будем искать первый утвержденный после июня
        if 'Q4' in quarter:
            datesearch = datetime.date(YEARint, 10, 1) # будем искать первый утвержденный после сентября

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
        else: # если не нашли относительно даты, то поищем просто последний
            if isdebug: logger.info(f'   etalon_project NOT found by date ')
            etalon_project = self.env['project_budget.projects'].search([('etalon_budget', '=', True),
                                                                     ('budget_state', '=', 'fixed'),
                                                                     ('project_id', '=', spec.project_id)
                                                                    ], limit=1, order='date_actual desc')
        if isdebug:
            logger.info(f'  etalon_project.id = { etalon_project.id}')
            logger.info(f'  etalon_project.project_id = {etalon_project.project_id}')
            logger.info(f'  etalon_project.date_actual = { etalon_project.date_actual}')

        # print('etalon_project.project_id = ',etalon_project.project_id)
        # print('etalon_project.date_actual = ',etalon_project.date_actual)
        return etalon_project

    def get_etalon_step(self,step, quarter):
        global strYEAR
        global YEARint

        if isdebug:
            logger.info(f' start get_etalon_step')
            logger.info(f' quarter = {quarter}')
        if step is False:
            return False
        datesearch = datetime.date(YEARint, 1, 1)
        if 'Q1' in quarter:
            datesearch = datetime.date(YEARint, 1, 1) # будем искать первый утвержденный в году
        if 'Q2' in quarter:
            datesearch = datetime.date(YEARint, 4, 1) # будем искать первый утвержденный после марта
        if 'Q3' in quarter:
            datesearch = datetime.date(YEARint, 7, 1) # будем искать первый утвержденный после июня
        if 'Q4' in quarter:
            datesearch = datetime.date(YEARint, 10, 1) # будем искать первый утвержденный после сентября
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
        else: # если не нашли относительно даты, то поищем просто последний
            if isdebug:
                logger.info(f'   etalon_step NOT found by date ')
            etalon_step = self.env['project_budget.project_steps'].search([('etalon_budget', '=', True),
                                                                       ('step_id','=',step.step_id),
                                                                       ('id','!=',step.id)
                                                                      ], limit=1, order='date_actual desc')
        if isdebug:
            logger.info(f' step_id = {etalon_step.step_id}')
            logger.info(f' id = {etalon_step.id}')
            logger.info(f' date_actual = {etalon_step.date_actual}')
            logger.info(f' end_presale_project_month = {etalon_step.end_presale_project_month}')
            logger.info(f' estimated_probability_id = {etalon_step.estimated_probability_id}')
            logger.info(f' end get_etalon_step')
        return etalon_step

    def get_sum_fact_pds_project_step_quarter(self, project, step, quarter):
        global strYEAR
        global YEARint

        sum_cash = 0
        
        months = self.get_months_from_quarter(quarter)
        
        
        pds_list = project.fact_cash_flow_ids
        # if step:
        #     pds_list = self.env['project_budget.fact_cash_flow'].search([('project_steps_id', '=', step.id)])
        # else:
        #     pds_list = self.env['project_budget.fact_cash_flow'].search([('projects_id', '=', project.id)])
        for pds in pds_list:
            if step:
                if pds.project_steps_id.id != step.id: continue
            if pds.date_cash.month in months and pds.date_cash.year == YEARint:
                sum_cash += pds.sum_cash
                
        return sum_cash

    def get_sum_fact_pds_project_step_year(self, project, step, year):

        sum_cash = 0

        pds_list = project.fact_cash_flow_ids

        for pds in pds_list:
            if step:
                if pds.project_steps_id.id != step.id: continue
            if pds.date_cash.year == year:
                sum_cash += pds.sum_cash

        return sum_cash

    def get_sum_plan_pds_project_step_quarter(self, project, step, quarter):
        global strYEAR
        global YEARint

        sum_cash = 0

        months = self.get_months_from_quarter(quarter)
        
        # if step:
        #     pds_list = self.env['project_budget.planned_cash_flow'].search([('project_steps_id', '=', step.id)])
        # else:
        #     pds_list = self.env['project_budget.planned_cash_flow'].search([('projects_id', '=', project.id)])
        pds_list = project.planned_cash_flow_ids
        for pds in pds_list:
            if step:
                if pds.project_steps_id.id != step.id: continue
            if pds.date_cash.month in months and pds.date_cash.year == YEARint:
                sum_cash += pds.sum_cash
        # else: # если нихрена нет планового ПДС, то берем сумму общую по дате окончания sale или по дате этапа
        #     print('step = ',step)
        #     print('project = ',project)
        #     if step == False or step == False:
        #         if project:
        #             if project.end_sale_project_month.month == month and project.end_sale_project_month.year == YEARint:
        #                 sum_cash = project.total_amount_of_revenue_with_vat
        #     else:
        #         if step:
        #             if step.end_sale_project_month.month == month and step.end_sale_project_month.year == YEARint:
        #                 sum_cash = step.total_amount_of_revenue_with_vat
        return sum_cash

    def get_sum_plan_pds_project_step_year(self, project, step, year):
        global strYEAR
        global YEARint

        sum_cash = 0

        pds_list = project.planned_cash_flow_ids

        for pds in pds_list:
            if step:
                if pds.project_steps_id.id != step.id: continue
            if pds.date_cash.year == year:
                sum_cash += pds.sum_cash
        return sum_cash

    # def get_sum_plan_acceptance_step_month(self,project, step, month):
    #     global strYEAR
    #     global YEARint
    # 
    #     sum_cash = 0
    #     # if project.project_have_steps == False:
    #     #     acceptance_list = self.env['project_budget.planned_acceptance_flow'].search([('projects_id', '=', project.id)])
    #     # if project.project_have_steps and step != False:
    #     #     acceptance_list = self.env['project_budget.planned_acceptance_flow'].search([('project_steps_id', '=', step.id)])
    # 
    #     acceptance_list = project.planned_acceptance_flow_ids
    #     for acceptance in acceptance_list:
    #         if step:
    #             if acceptance.project_steps_id.id != step.id: continue
    #         if acceptance.date_cash.month == month:
    #             sum_cash += acceptance.sum_cash_without_vat
    #     return sum_cash



    def print_quater_head(self,workbook,sheet,row,column,YEAR):
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

            for elementone in self.quarter_rus_name:

                element = elementone.replace('YEAR', strYEAR)

                sheet.set_row(row + 1, 25)
                sheet.set_row(row + 2, 25)

                if 'NEXT' not in element:
                    addcolumn = 0
                    if 'HY2' in element or 'Q' in element:
                        addcolumn = -1

                    if 'Q' in elementone:
                        sheet.set_column(column, column + 5, False, False, {'hidden': 1, 'level': 2})
                    elif 'HY1' in elementone:
                        sheet.set_column(column, column + 5, False, False, {'hidden': 1, 'level': 1})
                    elif 'HY2' in elementone:
                        sheet.set_column(column, column + 4, False, False, {'hidden': 1, 'level': 1})

                    sheet.merge_range(row, column, row, column + 5 + addcolumn, element, head_format_month)

                    sheet.merge_range(row + 1, column, row + 2, column, "План " + element,
                                      head_format_month_itogo)
                    column += 1
                    sheet.merge_range(row + 1, column, row + 2, column, "План " + element + " 6+6",
                                      head_format_month_itogo_6_plus_6)

                    column += 1
                    sheet.merge_range(row+1, column, row+2, column, 'Факт', head_format_month_detail_fact)

                    if 'HY1' in element:
                        column += 1
                        sheet.merge_range(row + 1, column, row + 2, column, "% исполнения плана 6+6 " + element,
                                          head_format_month_itogo_percent)

                    if element == YEAR:
                        column += 1
                        sheet.merge_range(row + 1, column, row + 2, column, "% исполнения плана 6+6 " + element,
                                          head_format_month_itogo_percent)

                    column += 1
                    sheet.merge_range(row + 1, column, row + 1, column + 1, 'Прогноз до конца периода (на дату отчета)',head_format_month_detail)
                    sheet.write_string(row + 2, column, 'Обязательство', head_format_month_detail)
                    column += 1
                    sheet.write_string(row + 2, column, 'Резерв', head_format_month_detail)
                    column += 1

                elif element == 'NEXT':
                    sheet.merge_range(row, column, row, column + 2, str(YEARint + 1), head_format_month)
                    sheet.merge_range(row + 1, column, row + 1, column + 2, 'Прогноз ' + str(YEARint + 1),
                                      head_format_month_detail)
                    sheet.write_string(row + 2, column, 'Обязательство', head_format_month_detail)
                    column += 1
                    sheet.write_string(row + 2, column, 'Резерв', head_format_month_detail)
                    column += 1
                    sheet.write_string(row + 2, column, 'Потенциал', head_format_month_detail)
                    column += 1

                elif element == 'AFTER NEXT':
                    sheet.write_string(row, column, str(YEARint + 2), head_format_month)
                    sheet.merge_range(row + 1, column, row + 2, column, 'Прогноз ' + str(YEARint + 2),
                                      head_format_month_detail)
                    column += 1

            sheet.merge_range(row-1, colbeg, row-1, column - 1, y[0], head_format_month)

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

    def calculate_quarter_revenue(self, element, project, multipliers):
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
            if not project.project_have_steps:
                if project_etalon:
                    if project_etalon.end_presale_project_month.month in months and YEARint == project_etalon.end_presale_project_month.year:
                        if project_etalon.estimated_probability_id.name == '75':
                            sum75tmpetalon = project_etalon.total_amount_of_revenue_with_vat
                        if project_etalon.estimated_probability_id.name == '50':
                            sum50tmpetalon = project_etalon.total_amount_of_revenue_with_vat

                if project.end_presale_project_month.month in months and YEARint == project.end_presale_project_month.year:
                    if project.estimated_probability_id.name in ('100', '100(done)'):
                        sum100tmp = project.total_amount_of_revenue_with_vat
                    if project.estimated_probability_id.name == '75':
                        sum75tmp = project.total_amount_of_revenue_with_vat
                    if project.estimated_probability_id.name == '50':
                        sum50tmp = project.total_amount_of_revenue_with_vat

            else:
                for step in project.project_steps_ids:
                    step_etalon = self.get_etalon_step(step, element)
                    if step_etalon:
                        if step_etalon.end_presale_project_month.month in months and YEARint == step_etalon.end_presale_project_month.year:
                            if step_etalon.estimated_probability_id.name == '75':
                                sum75tmpetalon += step_etalon.total_amount_of_revenue_with_vat
                            if step_etalon.estimated_probability_id.name == '50':
                                sum50tmpetalon += step_etalon.total_amount_of_revenue_with_vat
                    else:
                        if project_etalon: # если нет эталонного этапа, то данные берем из проекта, да это будет увеличивать сумму на количество этапов, но что делать я ХЗ
                            if project_etalon.end_presale_project_month.month in months and YEARint == project_etalon.end_presale_project_month.year:
                                if project_etalon.estimated_probability_id.name == '75':
                                    sum75tmpetalon = project_etalon.total_amount_of_revenue_with_vat
                                if project_etalon.estimated_probability_id.name == '50':
                                    sum50tmpetalon = project_etalon.total_amount_of_revenue_with_vat

                    if step.end_presale_project_month.month in months and YEARint == step.end_presale_project_month.year:
                        if step.estimated_probability_id.name in ('100', '100(done)'):
                            sum100tmp += step.total_amount_of_revenue_with_vat
                        if step.estimated_probability_id.name == '75':
                            sum75tmp += step.total_amount_of_revenue_with_vat
                        if step.estimated_probability_id.name == '50':
                            sum50tmp += step.total_amount_of_revenue_with_vat

        elif 'NEXT' in element:
            if not project.project_have_steps:
                if project.end_presale_project_month.year == YEARint + 1:
                    if project.estimated_probability_id.name in ('75', '100'):
                        sum_next_75_tmp = project.total_amount_of_revenue_with_vat
                    if project.estimated_probability_id.name == '50':
                        sum_next_50_tmp = project.total_amount_of_revenue_with_vat * multipliers['50']
                    if project.estimated_probability_id.name == '30':
                        sum_next_30_tmp = project.total_amount_of_revenue_with_vat * multipliers['30']
                elif project.end_presale_project_month.year == YEARint + 2:
                    if project.estimated_probability_id.name in ('75', '100'):
                        sum_after_next_tmp = project.total_amount_of_revenue_with_vat
                    if project.estimated_probability_id.name == '50':
                        sum_after_next_tmp = project.total_amount_of_revenue_with_vat * multipliers['50']
                    if project.estimated_probability_id.name == '30':
                        sum_after_next_tmp = project.total_amount_of_revenue_with_vat * multipliers['30']

            else:
                for step in project.project_steps_ids:
                    if step.end_presale_project_month.year == YEARint + 1:
                        if step.estimated_probability_id.name in ('75', '100'):
                            sum_next_75_tmp += step.total_amount_of_revenue_with_vat
                        if step.estimated_probability_id.name == '50':
                            sum_next_50_tmp += step.total_amount_of_revenue_with_vat * multipliers['50']
                        if step.estimated_probability_id.name == '30':
                            sum_next_30_tmp += step.total_amount_of_revenue_with_vat * multipliers['30']
                    elif step.end_presale_project_month.year == YEARint + 2:
                        if step.estimated_probability_id.name in ('75', '100'):
                            sum_after_next_tmp += step.total_amount_of_revenue_with_vat
                        if step.estimated_probability_id.name == '50':
                            sum_after_next_tmp += step.total_amount_of_revenue_with_vat * multipliers['50']
                        if step.estimated_probability_id.name == '30':
                            sum_after_next_tmp += step.total_amount_of_revenue_with_vat * multipliers['30']

        return (sum75tmpetalon, sum50tmpetalon,
                sum100tmp, sum75tmp, sum50tmp,
                sum_next_75_tmp, sum_next_50_tmp, sum_next_30_tmp,
                sum_after_next_tmp)

    # def print_month_pds_project(self, sheet, row, column, month, project, step, row_format_number, row_format_number_color_fact):
    #     global strYEAR
    #     global YEARint
    #
    #     sum75tmpetalon = sum50tmpetalon = sum100tmp = sum75tmp = sum50tmp = 0
    #     if month:
    #             project_etalon = self.get_etalon_project(project, self.get_quarter_from_month(month))
    #             step_etalon = self.get_etalon_step(step, self.get_quarter_from_month(month))
    #             sum = 0
    #             sum = self.get_sum_plan_pds_project_step_quarter(project_etalon, step_etalon, month)
    #
    #             if (step) and (not step_etalon): # есть этап сейчас, но нет в эталоне
    #                 sum = 0
    #
    #             estimated_probability_id_name = project_etalon.estimated_probability_id.name
    #             if step_etalon :
    #                 estimated_probability_id_name = step_etalon.estimated_probability_id.name
    #             if sum != 0:
    #                 if estimated_probability_id_name in('75','100','100(done)'):
    #                     sheet.write_number(row, column + 0, sum,row_format_number)
    #                     sum75tmpetalon += sum
    #                 if estimated_probability_id_name == '50':
    #                     sheet.write_number(row, column + 1, sum, row_format_number)
    #                     sum50tmpetalon += sum
    #
    #             sum100tmp = self.get_sum_fact_pds_project_step_quarter(project, step, month)
    #             if sum100tmp:
    #                 sheet.write_number(row, column + 2, sum100tmp, row_format_number_color_fact)
    #
    #             sum = self.get_sum_plan_pds_project_step_quarter(project, step, month)
    #             # print('----- project.id=',project.id)
    #             # print('sum100tmp = ',sum100tmp)
    #             # print('sum = ', sum)
    #             if sum100tmp >= sum:
    #                 sum = 0
    #             else:
    #                 sum = sum - sum100tmp
    #             # print('after: sum = ', sum)
    #             # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
    #             sum_ostatok_pds = sum_distribution_pds = 0
    #             for planned_cash_flow in project.planned_cash_flow_ids:
    #                 if step:
    #                     if planned_cash_flow.project_steps_id.id != step.id: continue
    #                 if planned_cash_flow.date_cash.month == month and planned_cash_flow.date_cash.year == YEARint:
    #                     sum_ostatok_pds += planned_cash_flow.distribution_sum_with_vat_ostatok
    #                     sum_distribution_pds += planned_cash_flow.distribution_sum_without_vat
    #             if sum_distribution_pds != 0 : # если есть распределение, то остаток = остатку распределения
    #                 sum = sum_ostatok_pds
    #                 if sum < 0 : sum = 0
    #
    #             estimated_probability_id_name = project.estimated_probability_id.name
    #             if step :
    #                 estimated_probability_id_name = step.estimated_probability_id.name
    #
    #             if sum != 0:
    #                 if estimated_probability_id_name in('75','100','100(done)'):
    #                     sheet.write_number(row, column + 3, sum,row_format_number)
    #                     sum75tmp += sum
    #                 if estimated_probability_id_name == '50':
    #                     sheet.write_number(row, column + 4, sum, row_format_number)
    #                     sum50tmp += sum
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
            
            if project.project_have_steps:
                for step in project.project_steps_ids:
                    project_etalon = self.get_etalon_project(project, element)
                    step_etalon = self.get_etalon_step(step, element)
                    sum = self.get_sum_plan_pds_project_step_quarter(project_etalon, step_etalon, element)

                    if not step_etalon:  # есть этап сейчас, но нет в эталоне
                        sum = 0

                    estimated_probability_id_name = step_etalon.estimated_probability_id.name

                    if sum != 0:
                        if estimated_probability_id_name in ('75', '100', '100(done)'):
                            sum75tmpetalon += sum
                        if estimated_probability_id_name == '50':
                            sum50tmpetalon += sum

                    sum100tmp_step = self.get_sum_fact_pds_project_step_quarter(project, step, element)

                    sum100tmp += sum100tmp_step

                    sum = self.get_sum_plan_pds_project_step_quarter(project, step, element)

                    if sum100tmp_step >= sum:
                        sum = 0
                    else:
                        sum = sum - sum100tmp_step
                    # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                    sum_ostatok_pds = sum_distribution_pds = 0
                    for planned_cash_flow in project.planned_cash_flow_ids:
                        if (planned_cash_flow.project_steps_id.id == step.id
                                and planned_cash_flow.date_cash.month in months
                                and planned_cash_flow.date_cash.year == YEARint):
                            sum_ostatok_pds += planned_cash_flow.distribution_sum_with_vat_ostatok
                            sum_distribution_pds += planned_cash_flow.distribution_sum_without_vat
                    if sum_distribution_pds != 0 : # если есть распределение, то остаток = остатку распределения
                        sum = sum_ostatok_pds
                        if sum < 0: sum = 0

                    estimated_probability_id_name = step.estimated_probability_id.name

                    if sum != 0:
                        if estimated_probability_id_name in ('75', '100', '100(done)'):
                            sum75tmp += sum
                        if estimated_probability_id_name == '50':
                            sum50tmp += sum
            else:
                project_etalon = self.get_etalon_project(project, element)

                sum = self.get_sum_plan_pds_project_step_quarter(project_etalon, False, element)

                estimated_probability_id_name = project_etalon.estimated_probability_id.name

                if sum != 0:
                    if estimated_probability_id_name in ('75', '100', '100(done)'):
                        sum75tmpetalon += sum
                    if estimated_probability_id_name == '50':
                        sum50tmpetalon += sum

                sum100tmp = self.get_sum_fact_pds_project_step_quarter(project, False, element)
                sum = self.get_sum_plan_pds_project_step_quarter(project, False, element)

                if sum100tmp >= sum:
                    sum = 0
                else:
                    sum = sum - sum100tmp

                # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                sum_ostatok_pds = sum_distribution_pds = 0
                for planned_cash_flow in project.planned_cash_flow_ids:
                    if planned_cash_flow.date_cash.month in months and planned_cash_flow.date_cash.year == YEARint:
                        sum_ostatok_pds += planned_cash_flow.distribution_sum_with_vat_ostatok
                        sum_distribution_pds += planned_cash_flow.distribution_sum_without_vat
                if sum_distribution_pds != 0:  # если есть распределение, то остаток = остатку распределения
                    sum = sum_ostatok_pds
                    if sum < 0: sum = 0

                estimated_probability_id_name = project.estimated_probability_id.name

                if sum != 0:
                    if estimated_probability_id_name in ('75', '100', '100(done)'):
                        sum75tmp += sum
                    if estimated_probability_id_name == '50':
                        sum50tmp += sum

        elif element == 'NEXT':
            if project.project_have_steps:
                for step in project.project_steps_ids:
                    sum100tmp_step = self.get_sum_fact_pds_project_step_year(project, step, YEARint + 1)
                    sum100tmp += sum100tmp_step
                    sum = self.get_sum_plan_pds_project_step_year(project, step, YEARint + 1)

                    if sum100tmp_step >= sum:
                        sum = 0
                    else:
                        sum = sum - sum100tmp_step

                    # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                    sum_ostatok_pds = sum_distribution_pds = 0

                    estimated_probability_id_name = step.estimated_probability_id.name

                    for planned_cash_flow in project.planned_cash_flow_ids:
                        if planned_cash_flow.project_steps_id.id == step.id and planned_cash_flow.date_cash.year == YEARint + 1:
                            sum_ostatok_pds += planned_cash_flow.distribution_sum_with_vat_ostatok
                            sum_distribution_pds += planned_cash_flow.distribution_sum_without_vat
                    if sum_distribution_pds != 0:  # если есть распределение, то остаток = остатку распределения
                        sum = sum_ostatok_pds
                        if sum < 0: sum = 0
                    if sum != 0:
                        if estimated_probability_id_name in ('75', '100'):
                            sum_next_75_tmp += sum
                        elif estimated_probability_id_name == '50':
                            sum_next_50_tmp += sum * multipliers['50']
                        elif estimated_probability_id_name == '30':
                            sum_next_30_tmp += sum * multipliers['30']
            else:
                sum100tmp = self.get_sum_fact_pds_project_step_year(project, False, YEARint + 1)
                sum = self.get_sum_plan_pds_project_step_year(project, False, YEARint + 1)

                if sum100tmp >= sum:
                    sum = 0
                else:
                    sum = sum - sum100tmp

                # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                sum_ostatok_pds = sum_distribution_pds = 0

                estimated_probability_id_name = project.estimated_probability_id.name

                for planned_cash_flow in project.planned_cash_flow_ids:
                    if planned_cash_flow.date_cash.year == YEARint + 1:
                        sum_ostatok_pds += planned_cash_flow.distribution_sum_with_vat_ostatok
                        sum_distribution_pds += planned_cash_flow.distribution_sum_without_vat
                if sum_distribution_pds != 0:  # если есть распределение, то остаток = остатку распределения
                    sum = sum_ostatok_pds
                    if sum < 0: sum = 0
                if sum != 0:
                    if estimated_probability_id_name in ('75', '100'):
                        sum_next_75_tmp += sum
                    elif estimated_probability_id_name == '50':
                        sum_next_50_tmp += sum * multipliers['50']
                    elif estimated_probability_id_name == '30':
                        sum_next_30_tmp += sum * multipliers['30']

        elif element == 'AFTER NEXT':
            if project.project_have_steps:
                for step in project.project_steps_ids:
                    sum100tmp_step = self.get_sum_fact_pds_project_step_year(project, step, YEARint + 2)
                    sum100tmp += sum100tmp_step
                    sum = self.get_sum_plan_pds_project_step_year(project, step, YEARint + 2)

                    if sum100tmp_step >= sum:
                        sum = 0
                    else:
                        sum = sum - sum100tmp_step

                    # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                    sum_ostatok_pds = sum_distribution_pds = 0

                    estimated_probability_id_name = step.estimated_probability_id.name

                    for planned_cash_flow in project.planned_cash_flow_ids:
                        if planned_cash_flow.project_steps_id.id == step.id and planned_cash_flow.date_cash.year == YEARint + 2:
                            sum_ostatok_pds += planned_cash_flow.distribution_sum_with_vat_ostatok
                            sum_distribution_pds += planned_cash_flow.distribution_sum_without_vat
                    if sum_distribution_pds != 0:  # если есть распределение, то остаток = остатку распределения
                        sum = sum_ostatok_pds
                        if sum < 0: sum = 0
                    if sum != 0:
                        if estimated_probability_id_name in ('75', '100'):
                            sum_after_next_tmp += sum
                        elif estimated_probability_id_name == '50':
                            sum_after_next_tmp += sum * multipliers['50']
                        elif estimated_probability_id_name == '30':
                            sum_after_next_tmp += sum * multipliers['30']

            else:
                sum100tmp = self.get_sum_fact_pds_project_step_year(project, False, YEARint + 2)
                sum = self.get_sum_plan_pds_project_step_year(project, False, YEARint + 2)

                if sum100tmp >= sum:
                    sum = 0
                else:
                    sum = sum - sum100tmp

                # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                sum_ostatok_pds = sum_distribution_pds = 0

                estimated_probability_id_name = project.estimated_probability_id.name

                for planned_cash_flow in project.planned_cash_flow_ids:
                    if planned_cash_flow.date_cash.year == YEARint + 2:
                        sum_ostatok_pds += planned_cash_flow.distribution_sum_with_vat_ostatok
                        sum_distribution_pds += planned_cash_flow.distribution_sum_without_vat
                if sum_distribution_pds != 0:  # если есть распределение, то остаток = остатку распределения
                    sum = sum_ostatok_pds
                    if sum < 0: sum = 0
                if sum != 0:
                    if estimated_probability_id_name in ('75', '100'):
                        sum_after_next_tmp += sum
                    elif estimated_probability_id_name == '50':
                        sum_after_next_tmp += sum * multipliers['50']
                    elif estimated_probability_id_name == '30':
                        sum_after_next_tmp += sum * multipliers['30']

        return (sum75tmpetalon, sum50tmpetalon,
                sum100tmp, sum75tmp, sum50tmp,
                sum_next_75_tmp, sum_next_50_tmp, sum_next_30_tmp,
                sum_after_next_tmp)

    def get_sum_fact_acceptance_project_step_quarter(self, project, step, element_name):
        global strYEAR
        global YEARint

        sum_cash = 0
        months = self.get_months_from_quarter(element_name)
        if months:
            acceptance_list = False
            # if step == False:
            #     acceptance_list = self.env['project_budget.fact_acceptance_flow'].search([('projects_id', '=', project.id)])
            # else:
            #     acceptance_list = self.env['project_budget.fact_acceptance_flow'].search([('project_steps_id', '=', step.id)])
            acceptance_list = project.fact_acceptance_flow_ids
            if acceptance_list:
                for acceptance in acceptance_list:
                    if step:
                        if acceptance.project_steps_id.id != step.id: continue
                    if acceptance.date_cash.month in months and acceptance.date_cash.year == YEARint:
                        sum_cash += acceptance.sum_cash_without_vat
        return sum_cash

    def get_sum_fact_margin_project_step_quarter(self, project, step, element_name):
        global strYEAR
        global YEARint

        sum_cash = 0
        months = self.get_months_from_quarter(element_name)
        if months:
            acceptance_list = project.fact_acceptance_flow_ids
            if acceptance_list:
                for acceptance in acceptance_list:
                    if step:
                        if acceptance.project_steps_id.id != step.id: continue
                    if acceptance.date_cash.month in months and acceptance.date_cash.year == YEARint:
                        sum_cash += acceptance.margin
        return sum_cash

    def get_sum_fact_acceptance_project_step_year(self, project, step, year):
        sum_cash = 0

        acceptance_list = project.fact_acceptance_flow_ids
        if acceptance_list:
            for acceptance in acceptance_list:
                if step:
                    if acceptance.project_steps_id.id != step.id: continue
                if acceptance.date_cash.year == year:
                    sum_cash += acceptance.sum_cash_without_vat

        return sum_cash

    def get_sum_fact_margin_project_step_year(self, project, step, year):
        sum_cash = 0

        acceptance_list = project.fact_acceptance_flow_ids
        if acceptance_list:
            for acceptance in acceptance_list:
                if step:
                    if acceptance.project_steps_id.id != step.id: continue
                if acceptance.date_cash.year == year:
                    sum_cash += acceptance.margin

        return sum_cash

    def get_sum_planned_acceptance_project_step_quarter(self, project, step, element_name):
        global strYEAR
        global YEARint

        sum_acceptance = 0

        months = self.get_months_from_quarter(element_name)

        if months:
            # if step == False:
            #     acceptance_list = self.env['project_budget.planned_acceptance_flow'].search([('projects_id', '=', project.id)])
            # else:
            #     acceptance_list = self.env['project_budget.planned_acceptance_flow'].search([('project_steps_id', '=', step.id),('projects_id', '=', project.id)])

            acceptance_list = project.planned_acceptance_flow_ids
            if acceptance_list:
                for acceptance in acceptance_list:
                    if step:
                        if acceptance.project_steps_id.id != step.id: continue
                    if acceptance.date_cash.month in months and acceptance.date_cash.year == YEARint:
                        sum_acceptance += acceptance.sum_cash_without_vat
                        # sum_acceptance += acceptance.sum_cash_without_vat / (1 + vatpercent / 100)
        return sum_acceptance

    def get_sum_planned_acceptance_project_step_year(self, project, step, year):

        sum_acceptance = 0

        acceptance_list = project.planned_acceptance_flow_ids
        if acceptance_list:
            for acceptance in acceptance_list:
                if step:
                    if acceptance.project_steps_id.id != step.id: continue
                if acceptance.date_cash.year == year:
                    sum_acceptance += acceptance.sum_cash_without_vat

        return sum_acceptance

    # def print_quarter_planned_acceptance_project(self, sheet, row, column, element_name, project, step, row_format_number, row_format_number_color_fact):
    #     global strYEAR
    #     global YEARint
    #
    #     sum75tmpetalon = sum50tmpetalon = sum100tmp = sum75tmp = sum50tmp = 0
    #     if element_name in ('Q1','Q2','Q3','Q4'):
    #         project_etalon = self.get_etalon_project(project, element_name)
    #         step_etalon = self.get_etalon_step(step, element_name)
    #
    #         if step == False:
    #             profitability = project.profitability
    #         else:
    #             profitability = step.profitability
    #
    #         if step_etalon == False:
    #             profitability_etalon = project_etalon.profitability
    #         else:
    #             profitability_etalon = step_etalon.profitability
    #
    #
    #         sum = 0
    #         sum = self.get_sum_planned_acceptance_project_step_quarter(project_etalon, step_etalon, element_name)
    #         if (step ) and (not step_etalon):
    #             sum = 0
    #
    #         estimated_probability_id_name = project_etalon.estimated_probability_id.name
    #         if step_etalon:
    #             estimated_probability_id_name = step_etalon.estimated_probability_id.name
    #
    #         if sum != 0:
    #             if estimated_probability_id_name in('75','100','100(done)'):
    #                 sheet.write_number(row, column + 0, sum, row_format_number)
    #                 sheet.write_number(row, column + 0 + 43, sum*profitability_etalon/100, row_format_number)
    #                 sum75tmpetalon += sum
    #             if estimated_probability_id_name == '50':
    #                 sheet.write_number(row, column + 1, sum, row_format_number)
    #                 sheet.write_number(row, column + 1 + 43 , sum*profitability_etalon/100, row_format_number)
    #                 sum50tmpetalon += sum
    #
    #         sum100tmp = self.get_sum_fact_acceptance_project_step_quarter(project, step, element_name)
    #
    #         if sum100tmp:
    #             sheet.write_number(row, column + 2, sum100tmp, row_format_number_color_fact)
    #             sheet.write_number(row, column + 2 + 43, sum100tmp*profitability/100, row_format_number_color_fact)
    #
    #
    #         sum = 0
    #         sum = self.get_sum_planned_acceptance_project_step_quarter(project, step, element_name)
    #         if sum100tmp >= sum:
    #             sum = 0
    #         else:
    #             sum = sum - sum100tmp
    #
    #         # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
    #         sum_ostatok_acceptance = sum_distribution_acceptance = 0
    #         months = self.get_months_from_quarter(element_name)
    #         for planned_acceptance_flow in project.planned_acceptance_flow_ids:
    #             if step:
    #                 if planned_acceptance_flow.project_steps_id.id != step.id: continue
    #             if planned_acceptance_flow.date_cash.month in months and planned_acceptance_flow.date_cash.year == YEARint:
    #                 sum_ostatok_acceptance += planned_acceptance_flow.distribution_sum_without_vat_ostatok
    #                 sum_distribution_acceptance += planned_acceptance_flow.distribution_sum_without_vat
    #         if sum_distribution_acceptance != 0 : # если есть распределение, то остаток = остатку распределения
    #             sum = sum_ostatok_acceptance
    #             if sum <= 0 : sum = 0
    #
    #         estimated_probability_id_name = project.estimated_probability_id.name
    #         if step:
    #             estimated_probability_id_name = step.estimated_probability_id.name
    #
    #         if sum != 0:
    #             if estimated_probability_id_name in('75','100','100(done)'):
    #                 sheet.write_number(row, column + 3, sum, row_format_number)
    #                 sheet.write_number(row, column + 3 + 43, sum*profitability/100, row_format_number)
    #                 sum75tmp += sum
    #             if estimated_probability_id_name == '50':
    #                 sheet.write_number(row, column + 4, sum, row_format_number)
    #                 sheet.write_number(row, column + 4 + 43, sum*profitability/100, row_format_number)
    #                 sum50tmp += sum
    #     return sum75tmpetalon, sum50tmpetalon, sum100tmp, sum75tmp, sum50tmp

    def calculate_quarter_planned_acceptance(self, element, project, multipliers):
        global strYEAR
        global YEARint

        sum75tmpetalon = sum50tmpetalon = sum100tmp = sum75tmp = sum50tmp = 0
        prof75tmpetalon = prof50tmpetalon = prof100tmp = prof75tmp = prof50tmp = 0
        sum_next_75_tmp = 0
        sum_next_50_tmp = 0
        sum_next_30_tmp = 0
        sum_after_next_tmp = 0
        prof_next_75_tmp = 0
        prof_next_50_tmp = 0
        prof_next_30_tmp = 0
        prof_after_next_tmp = 0

        if element in ('Q1', 'Q2', 'Q3', 'Q4'):

            if project.project_have_steps:
                for step in project.project_steps_ids:

                    project_etalon = self.get_etalon_project(project, element)
                    step_etalon = self.get_etalon_step(step, element)
                    profitability = step.profitability

                    if not step_etalon:
                        profitability_etalon = project_etalon.profitability
                    else:
                        profitability_etalon = step_etalon.profitability


                    sum = self.get_sum_planned_acceptance_project_step_quarter(project_etalon, step_etalon, element)

                    if not step_etalon:
                        sum = 0

                    estimated_probability_id_name = project_etalon.estimated_probability_id.name
                    if step_etalon:
                        estimated_probability_id_name = step_etalon.estimated_probability_id.name

                    if sum != 0:
                        if estimated_probability_id_name in ('75', '100', '100(done)'):
                            sum75tmpetalon += sum
                            prof75tmpetalon += sum * profitability_etalon / 100
                        if estimated_probability_id_name == '50':
                            sum50tmpetalon += sum
                            prof75tmpetalon += sum * profitability_etalon / 100

                    sum100tmp_step = self.get_sum_fact_acceptance_project_step_quarter(project, step, element)
                    prof100tmp_step = self.get_sum_fact_margin_project_step_quarter(project, step, element)

                    sum100tmp += sum100tmp_step
                    prof100tmp += prof100tmp_step

                    sum = self.get_sum_planned_acceptance_project_step_quarter(project, step, element)

                    if sum100tmp_step >= sum:
                        sum = 0
                    else:
                        sum = sum - sum100tmp_step

                    # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                    sum_ostatok_acceptance = sum_distribution_acceptance = 0
                    months = self.get_months_from_quarter(element)

                    for planned_acceptance_flow in project.planned_acceptance_flow_ids:
                        if (planned_acceptance_flow.project_steps_id.id == step.id
                                and planned_acceptance_flow.date_cash.month in months
                                and planned_acceptance_flow.date_cash.year == YEARint
                        ):
                            sum_ostatok_acceptance += planned_acceptance_flow.distribution_sum_without_vat_ostatok
                            sum_distribution_acceptance += planned_acceptance_flow.distribution_sum_without_vat

                    if sum_distribution_acceptance != 0:  # если есть распределение, то остаток = остатку распределения
                        sum = sum_ostatok_acceptance
                        if sum <= 0: sum = 0

                    estimated_probability_id_name = step.estimated_probability_id.name

                    if sum != 0:
                        if estimated_probability_id_name in ('75', '100', '100(done)'):
                            sum75tmp += sum
                            prof75tmp += sum * profitability / 100
                        if estimated_probability_id_name == '50':
                            sum50tmp += sum
                            prof50tmp += sum * profitability / 100
            else:
                project_etalon = self.get_etalon_project(project, element)
                profitability = project.profitability
                profitability_etalon = project_etalon.profitability

                sum = self.get_sum_planned_acceptance_project_step_quarter(project_etalon, False, element)

                estimated_probability_id_name = project_etalon.estimated_probability_id.name

                if sum != 0:
                    if estimated_probability_id_name in ('75', '100', '100(done)'):
                        sum75tmpetalon += sum
                        prof75tmpetalon += sum * profitability_etalon / 100
                    if estimated_probability_id_name == '50':
                        sum50tmpetalon += sum
                        prof50tmpetalon += sum * profitability_etalon / 100

                sum100tmp_proj = self.get_sum_fact_acceptance_project_step_quarter(project, False, element)
                prof100tmp_proj = self.get_sum_fact_margin_project_step_quarter(project, False, element)

                sum100tmp += sum100tmp_proj
                prof100tmp += prof100tmp_proj

                sum = self.get_sum_planned_acceptance_project_step_quarter(project, False, element)

                if sum100tmp >= sum:
                    sum = 0
                else:
                    sum = sum - sum100tmp

                # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                sum_ostatok_acceptance = sum_distribution_acceptance = 0
                months = self.get_months_from_quarter(element)
                for planned_acceptance_flow in project.planned_acceptance_flow_ids:
                    if planned_acceptance_flow.date_cash.month in months and planned_acceptance_flow.date_cash.year == YEARint:
                        sum_ostatok_acceptance += planned_acceptance_flow.distribution_sum_without_vat_ostatok
                        sum_distribution_acceptance += planned_acceptance_flow.distribution_sum_without_vat
                if sum_distribution_acceptance != 0:  # если есть распределение, то остаток = остатку распределения
                    sum = sum_ostatok_acceptance
                    if sum <= 0: sum = 0

                estimated_probability_id_name = project.estimated_probability_id.name

                if sum != 0:
                    if estimated_probability_id_name in ('75', '100', '100(done)'):
                        sum75tmp += sum
                        prof75tmp += sum * profitability / 100
                    if estimated_probability_id_name == '50':
                        sum50tmp += sum
                        prof50tmp += sum * profitability / 100

        elif element == 'NEXT':
            if project.project_have_steps:
                for step in project.project_steps_ids:

                    profitability = step.profitability

                    sum100tmp_step = self.get_sum_fact_acceptance_project_step_year(project, step, YEARint + 1)
                    prof100tmp_step = self.get_sum_fact_margin_project_step_year(project, step, YEARint + 1)

                    sum100tmp += sum100tmp_step
                    prof100tmp += prof100tmp_step

                    sum = self.get_sum_planned_acceptance_project_step_year(project, step, YEARint + 1)

                    if sum100tmp_step >= sum:
                        sum = 0
                    else:
                        sum = sum - sum100tmp_step

                    if sum == 0 and step.end_sale_project_month.year == YEARint + 1:  # если актирование 0, а месяц в нужном году, берем выручку
                        sum = step.total_amount_of_revenue

                    # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                    sum_ostatok_acceptance = sum_distribution_acceptance = 0

                    for planned_acceptance_flow in project.planned_acceptance_flow_ids:
                        if (
                                planned_acceptance_flow.project_steps_id.id == step.id
                                and planned_acceptance_flow.date_cash.year == YEARint + 1
                        ):
                            sum_ostatok_acceptance += planned_acceptance_flow.distribution_sum_without_vat_ostatok
                            sum_distribution_acceptance += planned_acceptance_flow.distribution_sum_without_vat

                    if sum_distribution_acceptance != 0:  # если есть распределение, то остаток = остатку распределения
                        sum = sum_ostatok_acceptance
                        if sum <= 0: sum = 0

                    estimated_probability_id_name = step.estimated_probability_id.name

                    if sum != 0:
                        if estimated_probability_id_name in ('75', '100'):
                            sum_next_75_tmp += sum
                            prof_next_75_tmp += sum * profitability / 100
                        elif estimated_probability_id_name == '50':
                            sum_next_50_tmp += sum * multipliers['50']
                            prof_next_50_tmp += sum * multipliers['50'] * profitability / 100
                        elif estimated_probability_id_name == '30':
                            sum_next_30_tmp += sum * multipliers['30']
                            prof_next_30_tmp += sum * multipliers['30'] * profitability / 100
            else:
                profitability = project.profitability

                sum100tmp_proj = self.get_sum_fact_acceptance_project_step_year(project, False, YEARint + 1)
                prof100tmp_proj = self.get_sum_fact_margin_project_step_year(project, False, YEARint + 1)

                sum100tmp += sum100tmp_proj
                prof100tmp += prof100tmp_proj

                sum = self.get_sum_planned_acceptance_project_step_year(project, False, YEARint + 1)

                if sum100tmp >= sum:
                    sum = 0
                else:
                    sum = sum - sum100tmp

                if sum == 0 and project.end_sale_project_month.year == YEARint + 1:  # если актирование 0, а месяц в нужном году, берем выручку
                    sum = project.total_amount_of_revenue

                # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                sum_ostatok_acceptance = sum_distribution_acceptance = 0

                for planned_acceptance_flow in project.planned_acceptance_flow_ids:
                    if planned_acceptance_flow.date_cash.year == YEARint + 1:
                        sum_ostatok_acceptance += planned_acceptance_flow.distribution_sum_without_vat_ostatok
                        sum_distribution_acceptance += planned_acceptance_flow.distribution_sum_without_vat

                if sum_distribution_acceptance != 0:  # если есть распределение, то остаток = остатку распределения
                    sum = sum_ostatok_acceptance
                    if sum <= 0: sum = 0

                estimated_probability_id_name = project.estimated_probability_id.name

                if sum != 0:
                    if estimated_probability_id_name in ('75', '100'):
                        sum_next_75_tmp += sum
                        prof_next_75_tmp += sum * profitability / 100
                    elif estimated_probability_id_name == '50':
                        sum_next_50_tmp += sum * multipliers['50']
                        prof_next_50_tmp += sum * multipliers['50'] * profitability / 100
                    elif estimated_probability_id_name == '30':
                        sum_next_30_tmp += sum * multipliers['30']
                        prof_next_30_tmp += sum * multipliers['30'] * profitability / 100

        elif element == 'AFTER NEXT':
            if project.project_have_steps:
                for step in project.project_steps_ids:

                    profitability = step.profitability

                    sum100tmp_step = self.get_sum_fact_acceptance_project_step_year(project, step, YEARint + 2)
                    prof100tmp_step = self.get_sum_fact_margin_project_step_year(project, step, YEARint + 2)

                    sum100tmp += sum100tmp_step
                    prof100tmp += prof100tmp_step

                    sum = self.get_sum_planned_acceptance_project_step_year(project, step, YEARint + 2)

                    if sum100tmp_step >= sum:
                        sum = 0
                    else:
                        sum = sum - sum100tmp_step

                    if sum == 0 and step.end_sale_project_month.year == YEARint + 2:  # если актирование 0, а месяц в нужном году, берем выручку
                        sum = step.total_amount_of_revenue

                    # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                    sum_ostatok_acceptance = sum_distribution_acceptance = 0

                    for planned_acceptance_flow in project.planned_acceptance_flow_ids:
                        if (
                                planned_acceptance_flow.project_steps_id.id == step.id
                                and planned_acceptance_flow.date_cash.year == YEARint + 2
                        ):
                            sum_ostatok_acceptance += planned_acceptance_flow.distribution_sum_without_vat_ostatok
                            sum_distribution_acceptance += planned_acceptance_flow.distribution_sum_without_vat

                    if sum_distribution_acceptance != 0:  # если есть распределение, то остаток = остатку распределения
                        sum = sum_ostatok_acceptance
                        if sum <= 0: sum = 0

                    estimated_probability_id_name = step.estimated_probability_id.name

                    if sum != 0:
                        if estimated_probability_id_name in ('75', '100'):
                            sum_after_next_tmp += sum
                            prof_after_next_tmp += sum * profitability / 100
                        elif estimated_probability_id_name == '50':
                            sum_after_next_tmp += sum * multipliers['50']
                            prof_after_next_tmp += sum * multipliers['50'] * profitability / 100
                        elif estimated_probability_id_name == '30':
                            sum_after_next_tmp += sum * multipliers['30']
                            prof_after_next_tmp += sum * multipliers['30'] * profitability / 100
            else:
                profitability = project.profitability

                sum100tmp_proj = self.get_sum_fact_acceptance_project_step_year(project, False, YEARint + 2)
                prof100tmp_proj = self.get_sum_fact_margin_project_step_year(project, False, YEARint + 2)

                sum100tmp += sum100tmp_proj
                prof100tmp += prof100tmp_proj

                sum = self.get_sum_planned_acceptance_project_step_year(project, False, YEARint + 2)

                if sum100tmp >= sum:
                    sum = 0
                else:
                    sum = sum - sum100tmp

                if sum == 0 and project.end_sale_project_month.year == YEARint + 2:  # если актирование 0, а месяц в нужном году, берем выручку
                    sum = project.total_amount_of_revenue

                # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                sum_ostatok_acceptance = sum_distribution_acceptance = 0

                for planned_acceptance_flow in project.planned_acceptance_flow_ids:
                    if planned_acceptance_flow.date_cash.year == YEARint + 2:
                        sum_ostatok_acceptance += planned_acceptance_flow.distribution_sum_without_vat_ostatok
                        sum_distribution_acceptance += planned_acceptance_flow.distribution_sum_without_vat

                if sum_distribution_acceptance != 0:  # если есть распределение, то остаток = остатку распределения
                    sum = sum_ostatok_acceptance
                    if sum <= 0: sum = 0

                estimated_probability_id_name = project.estimated_probability_id.name

                if sum != 0:
                    if estimated_probability_id_name in ('75', '100'):
                        sum_after_next_tmp += sum
                        prof_after_next_tmp += sum * profitability / 100
                    elif estimated_probability_id_name == '50':
                        sum_after_next_tmp += sum * multipliers['50']
                        prof_after_next_tmp += sum * multipliers['50'] * profitability / 100
                    elif estimated_probability_id_name == '30':
                        sum_after_next_tmp += sum * multipliers['30']
                        prof_after_next_tmp += sum * multipliers['30'] * profitability / 100
        return (
            sum75tmpetalon, sum50tmpetalon, sum100tmp, sum75tmp, sum50tmp,
            prof75tmpetalon, prof50tmpetalon, prof100tmp, prof75tmp, prof50tmp,
            sum_next_75_tmp, sum_next_50_tmp, sum_next_30_tmp, sum_after_next_tmp,
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

    # def print_row_Values(self, workbook, sheet, row, column,  YEAR, project, step):
    #     global strYEAR
    #     global YEARint
    #
    #     row_format_number = workbook.add_format({
    #         'border': 1,
    #         'font_size': 10,
    #     })
    #     row_format_number.set_num_format('#,##0')
    #     row_format_number_color_fact = workbook.add_format({
    #         "fg_color": '#C6E0B4',
    #         'border': 1,
    #         'font_size': 10,
    #     })
    #     row_format_number_color_fact.set_num_format('#,##0')
    #     head_format_month_itogo = workbook.add_format({
    #         'border': 1,
    #         "fg_color": '#D9E1F2',
    #         'diag_type': 3
    #     })
    #
    #     if step:
    #         if step.estimated_probability_id.name == '0':
    #             row_format_number.set_font_color('red')
    #             row_format_number_color_fact.set_font_color('red')
    #             head_format_month_itogo.set_font_color('red')
    #     else:
    #         if project.estimated_probability_id.name == '0':
    #             row_format_number.set_font_color('red')
    #             row_format_number_color_fact.set_font_color('red')
    #             head_format_month_itogo.set_font_color('red')
    #     sumQ100etalon =0
    #     sumQ75etalon = 0
    #     sumQ50etalon = 0
    #     sumQ100 =0
    #     sumQ75 = 0
    #     sumQ50 = 0
    #     sumHY100etalon =0
    #     sumHY75etalon = 0
    #     sumHY50etalon = 0
    #     sumHY100 =0
    #     sumHY75 = 0
    #     sumHY50 = 0
    #     sumYear100etalon =0
    #     sumYear75etalon = 0
    #     sumYear50etalon = 0
    #     sumYear100 =0
    #     sumYear75 = 0
    #     sumYear50 = 0
    #     # печать Контрактование, с НДС
    #     for element in self.quarter_rus_name:
    #         column += 1
    #         sumQ75tmpetalon = sumQ50tmpetalon = sumQ100tmp = sumQ75tmp = sumQ50tmp = 0
    #
    #         if element.find('итого') != -1:
    #             sheet.write_string(row, column, "", head_format_month_itogo)
    #             column += 1
    #         sheet.write_string(row, column + 0, "", row_format_number)
    #         sheet.write_string(row, column + 1, "", row_format_number)
    #         sheet.write_string(row, column + 2, "", row_format_number_color_fact)
    #         sheet.write_string(row, column + 3, "", row_format_number)
    #         sheet.write_string(row, column + 4, "", row_format_number)
    #
    #         sumQ75tmpetalon, sumQ50tmpetalon, sumQ100tmp, sumQ75tmp, sumQ50tmp = self.print_month_revenue_project(sheet, row, column, self.get_month_number_rus(element),
    #                                                                                 project,step, row_format_number,row_format_number_color_fact)
    #         sumQ75etalon += sumQ75tmpetalon
    #         sumQ50etalon += sumQ50tmpetalon
    #         sumQ100 += sumQ100tmp
    #         sumQ75 += sumQ75tmp
    #         sumQ50 += sumQ50tmp
    #         if element.find('Q') != -1: #'Q1 итого' 'Q2 итого' 'Q3 итого' 'Q4 итого'
    #             # if sumQ75etalon != 0 : sheet.write_number(row, column + 0, sumQ75etalon, row_format_number)
    #             # if sumQ50etalon != 0 : sheet.write_number(row, column + 1, sumQ50etalon, row_format_number)
    #             # if sumQ100 != 0 :      sheet.write_number(row, column + 2, sumQ100, row_format_number_color_fact)
    #             # if sumQ75 != 0 :       sheet.write_number(row, column + 3, sumQ75, row_format_number)
    #             # if sumQ50 != 0 :       sheet.write_number(row, column + 4, sumQ50, row_format_number)
    #
    #             formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1,xl_col_to_name(column - 16),xl_col_to_name(column - 11),xl_col_to_name(column - 6))
    #             sheet.write_formula(row, column + 0,formula, row_format_number)
    #             formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1,xl_col_to_name(column - 15),xl_col_to_name(column - 10),xl_col_to_name(column - 5))
    #             sheet.write_formula(row, column + 1,formula, row_format_number)
    #             formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1,xl_col_to_name(column - 14),xl_col_to_name(column - 9),xl_col_to_name(column - 4))
    #             sheet.write_formula(row, column + 2,formula, row_format_number_color_fact)
    #             formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1,xl_col_to_name(column - 13),xl_col_to_name(column - 8),xl_col_to_name(column - 3))
    #             sheet.write_formula(row, column + 3,formula, row_format_number)
    #             formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1,xl_col_to_name(column - 12),xl_col_to_name(column - 7),xl_col_to_name(column - 2))
    #             sheet.write_formula(row, column + 4,formula, row_format_number)
    #
    #             sumHY100etalon += sumQ100etalon
    #             sumHY75etalon += sumQ75etalon
    #             sumHY50etalon += sumQ50etalon
    #             sumHY100 += sumQ100
    #             sumHY75 += sumQ75
    #             sumHY50 += sumQ50
    #             sumQ100etalon = sumQ75etalon = sumQ50etalon = sumQ100 = sumQ75  = sumQ50  = 0
    #
    #         if element.find('HY') != -1:  # 'HY1/YEAR итого' 'HY2/YEAR итого'
    #             if sumHY75etalon != 0: sheet.write_number(row, column + 0, sumHY75etalon, row_format_number)
    #             if sumHY50etalon != 0: sheet.write_number(row, column + 1, sumHY50etalon, row_format_number)
    #             if sumHY100 != 0:      sheet.write_number(row, column + 2, sumHY100, row_format_number_color_fact)
    #             if sumHY75 != 0:       sheet.write_number(row, column + 3, sumHY75, row_format_number)
    #             if sumHY50 != 0:       sheet.write_number(row, column + 4, sumHY50, row_format_number)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 27),xl_col_to_name(column - 6))
    #             sheet.write_formula(row, column + 0, formula, row_format_number)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 26),xl_col_to_name(column - 5))
    #             sheet.write_formula(row, column + 1, formula, row_format_number)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 25),xl_col_to_name(column - 4))
    #             sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 24),xl_col_to_name(column - 3))
    #             sheet.write_formula(row, column + 3, formula, row_format_number)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 23),xl_col_to_name(column - 2))
    #             sheet.write_formula(row, column + 4, formula, row_format_number)
    #
    #
    #             sumYear100etalon += sumHY100etalon
    #             sumYear75etalon += sumHY75etalon
    #             sumYear50etalon += sumHY50etalon
    #             sumYear100 += sumHY100
    #             sumYear75 += sumHY75
    #             sumYear50 += sumHY50
    #             sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0
    #
    #         if element == 'YEAR итого':  # 'YEAR итого'
    #             if sumYear75etalon != 0: sheet.write_number(row, column + 0, sumYear75etalon, row_format_number)
    #             if sumYear50etalon != 0: sheet.write_number(row, column + 1, sumYear50etalon, row_format_number)
    #             if sumYear100 != 0:      sheet.write_number(row, column + 2, sumYear100, row_format_number_color_fact)
    #             if sumYear75 != 0:       sheet.write_number(row, column + 3, sumYear75, row_format_number)
    #             if sumYear50 != 0:       sheet.write_number(row, column + 4, sumYear50, row_format_number)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 54), xl_col_to_name(column - 6))
    #             sheet.write_formula(row, column + 0, formula, row_format_number)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 53), xl_col_to_name(column - 5))
    #             sheet.write_formula(row, column + 1, formula, row_format_number)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 52), xl_col_to_name(column - 4))
    #             sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 51), xl_col_to_name(column - 3))
    #             sheet.write_formula(row, column + 3, formula, row_format_number)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 50), xl_col_to_name(column - 2))
    #             sheet.write_formula(row, column + 4, formula, row_format_number)
    #         column += 4
    #     #end печать Контрактование, с НДС
    #     # Поступление денежных средсв, с НДС
    #     sumYear100etalon = sumYear75etalon = sumYear50etalon = sumYear100 = sumYear75 = sumYear50 = 0
    #     sumQ100etalon = sumQ75etalon = sumQ50etalon = sumQ100 = sumQ75 = sumQ50 = 0
    #     sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0
    #
    #     for element in self.quarter_rus_name:
    #         column += 1
    #         sumQ75tmpetalon = sumQ50tmpetalon = sumQ100tmp = sumQ75tmp = sumQ50tmp = 0
    #
    #         if element.find('итого') != -1:
    #             sheet.write_string(row, column, "", head_format_month_itogo)
    #             column += 1
    #         sheet.write_string(row, column + 0, "", row_format_number)
    #         sheet.write_string(row, column + 1, "", row_format_number)
    #         sheet.write_string(row, column + 2, "", row_format_number_color_fact)
    #         sheet.write_string(row, column + 3, "", row_format_number)
    #         sheet.write_string(row, column + 4, "", row_format_number)
    #
    #
    #         sumQ75tmpetalon, sumQ50tmpetalon, sumQ100tmp, sumQ75tmp, sumQ50tmp = self.print_month_pds_project(sheet, row, column, self.get_month_number_rus(element)
    #                                                                                     ,project, step, row_format_number, row_format_number_color_fact)
    #
    #         sumQ75etalon += sumQ75tmpetalon
    #         sumQ50etalon += sumQ50tmpetalon
    #         sumQ100 += sumQ100tmp
    #         sumQ75 += sumQ75tmp
    #         sumQ50 += sumQ50tmp
    #
    #         if element.find('Q') != -1:  # 'Q1 итого' 'Q2 итого' 'Q3 итого' 'Q4 итого'
    #             if sumQ75etalon != 0: sheet.write_number(row, column + 0, sumQ75etalon, row_format_number)
    #             if sumQ50etalon != 0: sheet.write_number(row, column + 1, sumQ50etalon, row_format_number)
    #             if sumQ100 != 0:      sheet.write_number(row, column + 2, sumQ100, row_format_number_color_fact)
    #             if sumQ75 != 0:       sheet.write_number(row, column + 3, sumQ75, row_format_number)
    #             if sumQ50 != 0:       sheet.write_number(row, column + 4, sumQ50, row_format_number)
    #             sumHY100etalon += sumQ100etalon
    #             sumHY75etalon += sumQ75etalon
    #             sumHY50etalon += sumQ50etalon
    #             sumHY100 += sumQ100
    #             sumHY75 += sumQ75
    #             sumHY50 += sumQ50
    #             sumQ100etalon = sumQ75etalon = sumQ50etalon = sumQ100 = sumQ75 = sumQ50 = 0
    #             formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1, xl_col_to_name(column - 16),xl_col_to_name(column - 11), xl_col_to_name(column - 6))
    #             sheet.write_formula(row, column + 0, formula, row_format_number)
    #             formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1, xl_col_to_name(column - 15),xl_col_to_name(column - 10), xl_col_to_name(column - 5))
    #             sheet.write_formula(row, column + 1, formula, row_format_number)
    #             formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1, xl_col_to_name(column - 14),xl_col_to_name(column - 9), xl_col_to_name(column - 4))
    #             sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)
    #             formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1, xl_col_to_name(column - 13),xl_col_to_name(column - 8), xl_col_to_name(column - 3))
    #             sheet.write_formula(row, column + 3, formula, row_format_number)
    #             formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1, xl_col_to_name(column - 12),xl_col_to_name(column - 7), xl_col_to_name(column - 2))
    #             sheet.write_formula(row, column + 4, formula, row_format_number)
    #
    #         if element.find('HY') != -1:  # 'HY1/YEAR итого' 'HY2/YEAR итого'
    #             if sumHY75etalon != 0: sheet.write_number(row, column + 0, sumHY75etalon, row_format_number)
    #             if sumHY50etalon != 0: sheet.write_number(row, column + 1, sumHY50etalon, row_format_number)
    #             if sumHY100 != 0:      sheet.write_number(row, column + 2, sumHY100, row_format_number_color_fact)
    #             if sumHY75 != 0:       sheet.write_number(row, column + 3, sumHY75, row_format_number)
    #             if sumHY50 != 0:       sheet.write_number(row, column + 4, sumHY50, row_format_number)
    #             sumYear100etalon += sumHY100etalon
    #             sumYear75etalon += sumHY75etalon
    #             sumYear50etalon += sumHY50etalon
    #             sumYear100 += sumHY100
    #             sumYear75 += sumHY75
    #             sumYear50 += sumHY50
    #             sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 27), xl_col_to_name(column - 6))
    #             sheet.write_formula(row, column + 0, formula, row_format_number)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 26), xl_col_to_name(column - 5))
    #             sheet.write_formula(row, column + 1, formula, row_format_number)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 25), xl_col_to_name(column - 4))
    #             sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 24), xl_col_to_name(column - 3))
    #             sheet.write_formula(row, column + 3, formula, row_format_number)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 23), xl_col_to_name(column - 2))
    #             sheet.write_formula(row, column + 4, formula, row_format_number)
    #
    #         if element == 'YEAR итого':  # 'YEAR итого'
    #             if sumYear75etalon != 0: sheet.write_number(row, column + 0, sumYear75etalon, row_format_number)
    #             if sumYear50etalon != 0: sheet.write_number(row, column + 1, sumYear50etalon, row_format_number)
    #             if sumYear100 != 0:      sheet.write_number(row, column + 2, sumYear100, row_format_number_color_fact)
    #             if sumYear75 != 0:       sheet.write_number(row, column + 3, sumYear75, row_format_number)
    #             if sumYear50 != 0:       sheet.write_number(row, column + 4, sumYear50, row_format_number)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 54), xl_col_to_name(column - 6))
    #             sheet.write_formula(row, column + 0, formula, row_format_number)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 53), xl_col_to_name(column - 5))
    #             sheet.write_formula(row, column + 1, formula, row_format_number)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 52), xl_col_to_name(column - 4))
    #             sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 51), xl_col_to_name(column - 3))
    #             sheet.write_formula(row, column + 3, formula, row_format_number)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 50), xl_col_to_name(column - 2))
    #             sheet.write_formula(row, column + 4, formula, row_format_number)
    #         column += 4
    #     # end Поступление денежных средсв, с НДС
    #
    #     # Валовая Выручка, без НДС
    #     sumYear100etalon = sumYear75etalon = sumYear50etalon = sumYear100 = sumYear75 = sumYear50 = 0
    #     sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0
    #
    #     if step == False:
    #         profitability = project.profitability
    #     else:
    #         profitability = step.profitability
    #
    #     project_etalon = self.get_etalon_project(project, False)
    #     step_etalon = self.get_etalon_step(step, False)
    #
    #     if step_etalon == False:
    #         profitability_etalon = project_etalon.profitability
    #     else:
    #         profitability_etalon = step_etalon.profitability
    #
    #     for element in self.quarter_rus_name:
    #         column += 1
    #         sheet.write_string(row, column, "", head_format_month_itogo)
    #         sheet.write_string(row, column + 43, "", head_format_month_itogo)
    #         if element.find('HY2') != -1:
    #             addcolumn = 1
    #             column += 1
    #             sheet.write_string(row, column, "", head_format_month_itogo)
    #             sheet.write_string(row, column + 43, "", head_format_month_itogo)
    #         column += 1
    #         sheet.write_string(row, column + 0, "", row_format_number)
    #         sheet.write_string(row, column + 1, "", row_format_number)
    #         sheet.write_string(row, column + 2, "", row_format_number_color_fact)
    #         sheet.write_string(row, column + 3, "", row_format_number)
    #         sheet.write_string(row, column + 4, "", row_format_number)
    #         sheet.write_string(row, column + 0 + 43, "", row_format_number)
    #         sheet.write_string(row, column + 1 + 43, "", row_format_number)
    #         sheet.write_string(row, column + 2 + 43, "", row_format_number_color_fact)
    #         sheet.write_string(row, column + 3 + 43, "", row_format_number)
    #         sheet.write_string(row, column + 4 + 43, "", row_format_number)
    #
    #         (sumQ75etalon, sumQ50etalon,
    #          sumQ100, sumQ75, sumQ50) = self.print_quarter_planned_acceptance_project(
    #             sheet,
    #             row,
    #             column,
    #             element,
    #             project,
    #             step,
    #             row_format_number,
    #             row_format_number_color_fact
    #         )
    #
    #         sumHY100etalon += sumQ100etalon
    #         sumHY75etalon += sumQ75etalon
    #         sumHY50etalon += sumQ50etalon
    #         sumHY100 += sumQ100
    #         sumHY75 += sumQ75
    #         sumHY50 += sumQ50
    #
    #         if element.find('HY') != -1:  # 'HY1/YEAR итого' 'HY2/YEAR итого'
    #             # if sumHY75etalon != 0:
    #             #     sheet.write_number(row, column + 0, sumHY75etalon, row_format_number)
    #             #     sheet.write_number(row, column + 0 + 43, sumHY75etalon*profitability_etalon / 100, row_format_number)
    #             # if sumHY50etalon != 0:
    #             #     sheet.write_number(row, column + 1, sumHY50etalon, row_format_number)
    #             #     sheet.write_number(row, column + 1 + 43, sumHY50etalon*profitability_etalon / 100, row_format_number)
    #             # if sumHY100 != 0:
    #             #     sheet.write_number(row, column + 2, sumHY100, row_format_number_color_fact)
    #             #     sheet.write_number(row, column + 2 + 43, sumHY100*profitability / 100, row_format_number_color_fact)
    #             # if sumHY75 != 0:
    #             #     sheet.write_number(row, column + 3, sumHY75, row_format_number)
    #             #     sheet.write_number(row, column + 3 + 43, sumHY75*profitability / 100, row_format_number)
    #             # if sumHY50 != 0:
    #             #     sheet.write_number(row, column + 4, sumHY50, row_format_number)
    #             #     sheet.write_number(row, column + 4 + 43, sumHY50*profitability / 100, row_format_number)
    #             addcolumn = 0
    #             if element.find('HY2') != -1:
    #                 addcolumn = 1
    #
    #             sumYear100etalon += sumHY100etalon
    #             sumYear75etalon += sumHY75etalon
    #             sumYear50etalon += sumHY50etalon
    #             sumYear100 += sumHY100
    #             sumYear75 += sumHY75
    #             sumYear50 += sumHY50
    #             sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0
    #
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 12 - addcolumn), xl_col_to_name(column - 6 - addcolumn))
    #             sheet.write_formula(row, column + 0, formula, row_format_number)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 11 - addcolumn), xl_col_to_name(column - 5 - addcolumn))
    #             sheet.write_formula(row, column + 1, formula, row_format_number)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 10 - addcolumn), xl_col_to_name(column - 4 - addcolumn))
    #             sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 9 - addcolumn),  xl_col_to_name(column - 3 - addcolumn))
    #             sheet.write_formula(row, column + 3, formula, row_format_number)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8 - addcolumn),  xl_col_to_name(column - 2 - addcolumn))
    #             sheet.write_formula(row, column + 4, formula, row_format_number)
    #
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 12 + 43 - addcolumn), xl_col_to_name(column - 6 + 43 - addcolumn))
    #             sheet.write_formula(row, column + 0 + 43, formula, row_format_number)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 11 + 43 - addcolumn), xl_col_to_name(column - 5 + 43 - addcolumn))
    #             sheet.write_formula(row, column + 1 + 43, formula, row_format_number)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 10 + 43 - addcolumn), xl_col_to_name(column - 4 + 43 - addcolumn))
    #             sheet.write_formula(row, column + 2 + 43, formula, row_format_number_color_fact)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 9 + 43 - addcolumn),  xl_col_to_name(column - 3 + 43 - addcolumn))
    #             sheet.write_formula(row, column + 3 + 43, formula, row_format_number)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8 + 43 - addcolumn),  xl_col_to_name(column - 2 + 43 - addcolumn))
    #             sheet.write_formula(row, column + 4 + 43, formula, row_format_number)
    #
    #
    #
    #         if element == 'YEAR':  # 'YEAR итого'
    #             # if sumYear75etalon != 0:
    #             #     sheet.write_number(row, column + 0, sumYear75etalon, row_format_number)
    #             #     sheet.write_number(row, column + 0 + 43, sumYear75etalon*profitability / 100, row_format_number)
    #             # if sumYear50etalon != 0:
    #             #     sheet.write_number(row, column + 1, sumYear50etalon, row_format_number)
    #             #     sheet.write_number(row, column + 1 + 43, sumYear50etalon*profitability / 100, row_format_number)
    #             # if sumYear100 != 0:
    #             #     sheet.write_number(row, column + 2, sumYear100, row_format_number_color_fact)
    #             #     sheet.write_number(row, column + 2 + 43, sumYear100*profitability / 100, row_format_number_color_fact)
    #             # if sumYear75 != 0:
    #             #     sheet.write_number(row, column + 3, sumYear75, row_format_number)
    #             #     sheet.write_number(row, column + 3 + 43, sumYear75*profitability / 100, row_format_number)
    #             # if sumYear50 != 0:
    #             #     sheet.write_number(row, column + 4, sumYear50, row_format_number)
    #             #     sheet.write_number(row, column + 4 + 43, sumYear50*profitability / 100, row_format_number)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 25), xl_col_to_name(column - 6))
    #             sheet.write_formula(row, column + 0, formula, row_format_number)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 24), xl_col_to_name(column - 5))
    #             sheet.write_formula(row, column + 1, formula, row_format_number)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 23), xl_col_to_name(column - 4))
    #             sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 22), xl_col_to_name(column - 3))
    #             sheet.write_formula(row, column + 3, formula, row_format_number)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 21), xl_col_to_name(column - 2))
    #             sheet.write_formula(row, column + 4, formula, row_format_number)
    #
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 25 + 43), xl_col_to_name(column - 6 + 43))
    #             sheet.write_formula(row, column + 0 + 43, formula, row_format_number)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 24 + 43), xl_col_to_name(column - 5 + 43))
    #             sheet.write_formula(row, column + 1 + 43, formula, row_format_number)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 23 + 43), xl_col_to_name(column - 4 + 43))
    #             sheet.write_formula(row, column + 2 + 43, formula, row_format_number_color_fact)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 22 + 43), xl_col_to_name(column - 3 + 43))
    #             sheet.write_formula(row, column + 3 + 43, formula, row_format_number)
    #             formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 21 + 43), xl_col_to_name(column - 2 + 43))
    #             sheet.write_formula(row, column + 4 + 43, formula, row_format_number)
    #
    #         column += 4
    #     # end Валовая Выручка, без НДС

    def print_row_values_office(self, workbook, sheet, row, column, YEAR, projects, project_office, formula_offices, multipliers):
        global strYEAR
        global YEARint

        row_format_number = workbook.add_format({
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

# печать Контрактование, с НДС

        for element in self.quarter_rus_name:

            column += 1

            sumM75etalon = 0
            sumM50etalon = 0
            sumM100 = 0
            sumM75 = 0
            sumM50 = 0
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
                 sum_next_75_tmp, sum_next_50_tmp, sum_next_30_tmp,
                 sum_after_next_tmp) = self.calculate_quarter_revenue(element, project, multipliers)

                sumM75etalon += sumM75tmpetalon
                sumM50etalon += sumM50tmpetalon
                sumM100 += sumM100tmp
                sumM75 += sumM75tmp
                sumM50 += sumM50tmp
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

                if child_offices_rows:
                    sheet.write_formula(row, column, 'sum(' + child_offices_rows.format(xl_col_to_name(column)) + ')', row_format_number_color_forecast)
                    sheet.write_formula(row, column + 1, 'sum(' + child_offices_rows.format(xl_col_to_name(column + 1)) + ')', row_format_number_color_forecast)
                else:
                    sheet.write_string(row, column, '', row_format_number_color_forecast)
                    sheet.write_string(row, column + 1, '', row_format_number_color_forecast)

                sheet.write_formula(row, column + 2, f_Q100, row_format_number_color_fact)
                sheet.write_formula(row, column + 3, f_Q75, row_format_number)
                sheet.write_formula(row, column + 4, f_Q50, row_format_number)

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
                sheet.write_formula(row, column, formula, row_format_number_color_forecast)

                formula = '=sum({1}{0},{2}{0})'.format(
                    row + 1,
                    xl_col_to_name(column - 9 + addcolumn),
                    xl_col_to_name(column - 4 + addcolumn)
                )
                sheet.write_formula(row, column + 1, formula, row_format_number_color_forecast)

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
                sheet.write_formula(row, column + 3, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(
                    row + 1,
                    xl_col_to_name(column - 6 + addcolumn),
                    xl_col_to_name(column - 1 + addcolumn)
                )
                sheet.write_formula(row, column + 4, formula, row_format_number)

            elif element == 'YEAR':  # 'YEAR'

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 21), xl_col_to_name(column - 5))
                sheet.write_formula(row, column, formula, row_format_number_color_forecast)

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 20), xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 1, formula, row_format_number_color_forecast)

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
                sheet.write_formula(row, column + 3, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 17), xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 4, formula, row_format_number)

            elif element == 'NEXT':
                f_sum_next_75 = 'sum(' + str(sum_next_75) + child_offices_rows.format(xl_col_to_name(column)) + ')'
                f_sum_next_50 = 'sum(' + str(sum_next_50) + child_offices_rows.format(xl_col_to_name(column + 1)) + ')'
                f_sum_next_30 = 'sum(' + str(sum_next_30) + child_offices_rows.format(xl_col_to_name(column + 2)) + ')'
                sheet.write_formula(row, column, f_sum_next_75, row_format_number_color_next)
                sheet.write_formula(row, column + 1, f_sum_next_50, row_format_number_color_next)
                sheet.write_formula(row, column + 2, f_sum_next_30, row_format_number_color_next)
                column -= 2

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
                 sum_next_75_tmp, sum_next_50_tmp, sum_next_30_tmp,
                 sum_after_next_tmp) = self.calculate_quarter_pds(element, project, multipliers)

                sumM75etalon += sumM75tmpetalon
                sumM50etalon += sumM50tmpetalon
                sumM100 += sumM100tmp
                sumM75 += sumM75tmp
                sumM50 += sumM50tmp
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

                if child_offices_rows:
                    sheet.write_formula(row, column, 'sum(' + child_offices_rows.format(xl_col_to_name(column)) + ')', row_format_number_color_forecast)
                    sheet.write_formula(row, column + 1, 'sum(' + child_offices_rows.format(xl_col_to_name(column + 1)) + ')', row_format_number_color_forecast)
                else:
                    sheet.write_string(row, column, '', row_format_number_color_forecast)
                    sheet.write_string(row, column + 1, '', row_format_number_color_forecast)

                sheet.write_formula(row, column + 2, f_Q100, row_format_number_color_fact)
                sheet.write_formula(row, column + 3, f_Q75, row_format_number)
                sheet.write_formula(row, column + 4, f_Q50, row_format_number)

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
                sheet.write_formula(row, column, formula, row_format_number_color_forecast)

                formula = '=sum({1}{0},{2}{0})'.format(
                    row + 1,
                    xl_col_to_name(column - 9 + addcolumn),
                    xl_col_to_name(column - 4 + addcolumn)
                )
                sheet.write_formula(row, column + 1, formula, row_format_number_color_forecast)

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
                sheet.write_formula(row, column + 3, formula, row_format_number)

                formula = '=sum({1}{0},{2}{0})'.format(
                    row + 1,
                    xl_col_to_name(column - 6 + addcolumn),
                    xl_col_to_name(column - 1 + addcolumn)
                )
                sheet.write_formula(row, column + 4, formula, row_format_number)

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
                sheet.write_formula(row, column, formula, row_format_number_color_forecast)

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 20),
                                                       xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 1, formula, row_format_number_color_forecast)

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
                sheet.write_formula(row, column + 3, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 17),
                                                       xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 4, formula, row_format_number)

            elif element == 'NEXT':
                f_sum_next_75 = 'sum(' + str(sum_next_75) + child_offices_rows.format(xl_col_to_name(column)) + ')'
                f_sum_next_50 = 'sum(' + str(sum_next_50) + child_offices_rows.format(xl_col_to_name(column + 1)) + ')'
                f_sum_next_30 = 'sum(' + str(sum_next_30) + child_offices_rows.format(xl_col_to_name(column + 2)) + ')'
                sheet.write_formula(row, column, f_sum_next_75, row_format_number_color_next)
                sheet.write_formula(row, column + 1, f_sum_next_50, row_format_number_color_next)
                sheet.write_formula(row, column + 2, f_sum_next_30, row_format_number_color_next)
                column -= 2

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
            sum_next_75 = sum_next_50 = sum_next_30 = sum_after_next = 0
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
                sum_next_75_tmp, sum_next_50_tmp, sum_next_30_tmp, sum_after_next_tmp,
                prof_next_75_tmp, prof_next_50_tmp, prof_next_30_tmp, prof_after_next_tmp
                ) = self.calculate_quarter_planned_acceptance(element, project, multipliers)

                sumQ75etalon += sum75tmpetalon
                sumQ50etalon += sum50tmpetalon
                sumQ100 += sum100tmp
                sumQ75 += sum75tmp
                sumQ50 += sum50tmp
                sum_next_75 += sum_next_75_tmp
                sum_next_50 += sum_next_50_tmp
                sum_next_30 += sum_next_30_tmp
                sum_after_next += sum_after_next_tmp

                profQ75etalon += prof75tmpetalon
                profQ50etalon += prof50tmpetalon
                profQ100 += prof100tmp
                profQ75 += prof75tmp
                profQ50 += prof50tmp
                prof_next_75 += prof_next_75_tmp
                prof_next_50 += prof_next_50_tmp
                prof_next_30 += prof_next_30_tmp
                prof_after_next += prof_after_next_tmp

            child_offices_rows = formula_offices.get('project_office_' + str(project_office.id)) or ''

            if 'Q' in element:

                if child_offices_rows:
                    sheet.write_formula(row, column, 'sum(' + child_offices_rows.format(xl_col_to_name(column)) + ')', row_format_number_color_forecast)
                    sheet.write_formula(row, column + 1, 'sum(' + child_offices_rows.format(xl_col_to_name(column + 1)) + ')', row_format_number_color_forecast)
                    sheet.write_formula(row, column + 41, 'sum(' + child_offices_rows.format(xl_col_to_name(column + 41)) + ')', row_format_number_color_forecast)
                    sheet.write_formula(row, column + 1 + 41, 'sum(' + child_offices_rows.format(xl_col_to_name(column + 1 + 41)) + ')', row_format_number_color_forecast)
                else:
                    sheet.write_string(row, column, '', row_format_number_color_forecast)
                    sheet.write_string(row, column + 1, '', row_format_number_color_forecast)
                    sheet.write_string(row, column + 41, '', row_format_number_color_forecast)
                    sheet.write_string(row, column + 1 + 41, '', row_format_number_color_forecast)

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
                f_profQ100 = 'sum(' + str(profQ100) + child_offices_rows.format(xl_col_to_name(column + 2 + 41)) + ')'
                f_profQ75 = 'sum(' + str(profQ75) + child_offices_rows.format(xl_col_to_name(column + 3 + 41)) + ')'
                f_profQ50 = 'sum(' + str(profQ50) + child_offices_rows.format(xl_col_to_name(column + 4 + 41)) + ')'

                # sheet.write_formula(row, column, f_sumQ75etalon, row_format_number)
                # sheet.write_formula(row, column + 43, f_profQ75etalon, row_format_number)
                # sheet.write_formula(row, column + 1, f_sumQ50etalon, row_format_number)
                # sheet.write_formula(row, column + 44, f_profQ50etalon, row_format_number)
                sheet.write_formula(row, column + 2, f_sumQ100, row_format_number_color_fact)
                sheet.write_formula(row, column + 2 + 41, f_profQ100, row_format_number_color_fact)
                sheet.write_formula(row, column + 3, f_sumQ75, row_format_number)
                sheet.write_formula(row, column + 3 + 41, f_profQ75, row_format_number)
                sheet.write_formula(row, column + 4, f_sumQ50, row_format_number)
                sheet.write_formula(row, column + 4 + 41, f_profQ50, row_format_number)

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
                sheet.write_formula(row, column, formula, row_format_number_color_forecast)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 9), xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 1, formula, row_format_number_color_forecast)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 10 + 41), xl_col_to_name(column - 5 + 41))
                sheet.write_formula(row, column + 41, formula, row_format_number_color_forecast)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 9 + 41), xl_col_to_name(column - 4 + 41))
                sheet.write_formula(row, column + 1 + 41, formula, row_format_number_color_forecast)

                sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0

                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 12 - addcolumn), xl_col_to_name(column - 6 - addcolumn))
                # sheet.write_formula(row, column + 0, formula, row_format_number)
                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 11 - addcolumn), xl_col_to_name(column - 5 - addcolumn))
                # sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8 + 41), xl_col_to_name(column - 3 + 41))
                sheet.write_formula(row, column + 2 + 41, formula, row_format_number_color_fact)

                if 'HY1' in element:  # 'HY1/YEAR''
                    sheet.write_formula(
                        row,
                        column + 3,
                        f'=IFERROR({xl_col_to_name(column + 2)}{row + 1}/{xl_col_to_name(column + 1)}{row + 1}," ")',
                        row_format_number_color_percent
                    )
                    sheet.write_formula(
                        row,
                        column + 3 + 41,
                        f'=IFERROR({xl_col_to_name(column + 2 + 41)}{row + 1}/{xl_col_to_name(column + 1 + 41)}{row + 1}," ")',
                        row_format_number_color_percent
                    )
                    column += 1
                    addcolumn = -1

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 7 + addcolumn),  xl_col_to_name(column - 2 + addcolumn))
                sheet.write_formula(row, column + 3, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 6 + addcolumn),  xl_col_to_name(column - 1 + addcolumn))
                sheet.write_formula(row, column + 4, formula, row_format_number)

                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 12 + 43), xl_col_to_name(column - 6 + 43))
                # sheet.write_formula(row, column + 0 + 43, formula, row_format_number)
                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 11 + 43), xl_col_to_name(column - 5 + 43))
                # sheet.write_formula(row, column + 1 + 43, formula, row_format_number)

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 7 + 41 + addcolumn),  xl_col_to_name(column - 2 + 41 + addcolumn))
                sheet.write_formula(row, column + 3 + 41, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 6 + 41 + addcolumn),  xl_col_to_name(column - 1 + 41 + addcolumn))
                sheet.write_formula(row, column + 4 + 41, formula, row_format_number)

            elif element == 'YEAR':  # 'YEAR'
                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 25), xl_col_to_name(column - 6))
                # sheet.write_formula(row, column + 0, formula, row_format_number)
                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 24), xl_col_to_name(column - 5))
                # sheet.write_formula(row, column + 1, formula, row_format_number)

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 21), xl_col_to_name(column - 5))
                sheet.write_formula(row, column, formula, row_format_number_color_forecast)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 20), xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 1, formula, row_format_number_color_forecast)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 21 + 41), xl_col_to_name(column - 5 + 41))
                sheet.write_formula(row, column + 41, formula, row_format_number_color_forecast)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 20 + 41), xl_col_to_name(column - 4 + 41))
                sheet.write_formula(row, column + 1 + 41, formula, row_format_number_color_forecast)

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 19), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 19 + 41), xl_col_to_name(column - 3 + 41))
                sheet.write_formula(row, column + 2 + 41, formula, row_format_number_color_fact)

                column += 1
                sheet.write_formula(
                    row,
                    column + 2,
                    f'=IFERROR({xl_col_to_name(column + 1)}{row + 1}/{xl_col_to_name(column)}{row + 1}," ")',
                    row_format_number_color_percent
                )
                sheet.write_formula(
                    row,
                    column + 2 + 41,
                    f'=IFERROR({xl_col_to_name(column + 1 + 41)}{row + 1}/{xl_col_to_name(column + 41)}{row + 1}," ")',
                    row_format_number_color_percent
                )

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 18), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 3, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 17), xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 4, formula, row_format_number)

                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 25 + 43), xl_col_to_name(column - 6 + 43))
                # sheet.write_formula(row, column + 0 + 43, formula, row_format_number)
                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 24 + 43), xl_col_to_name(column - 5 + 43))
                # sheet.write_formula(row, column + 1 + 43, formula, row_format_number)


                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 18 + 41), xl_col_to_name(column - 3 + 41))
                sheet.write_formula(row, column + 3 + 41, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 17 + 41), xl_col_to_name(column - 2 + 41))
                sheet.write_formula(row, column + 4 + 41, formula, row_format_number)

            elif element == 'NEXT':
                f_sum_next_75 = 'sum(' + str(sum_next_75) + child_offices_rows.format(xl_col_to_name(column)) + ')'
                f_sum_next_50 = 'sum(' + str(sum_next_50) + child_offices_rows.format(xl_col_to_name(column + 1)) + ')'
                f_sum_next_30 = 'sum(' + str(sum_next_30) + child_offices_rows.format(xl_col_to_name(column + 2)) + ')'
                sheet.write_formula(row, column, f_sum_next_75, row_format_number_color_next)
                sheet.write_formula(row, column + 1, f_sum_next_50, row_format_number_color_next)
                sheet.write_formula(row, column + 2, f_sum_next_30, row_format_number_color_next)
                f_prof_next_75 = 'sum(' + str(prof_next_75) + child_offices_rows.format(xl_col_to_name(column + 41)) + ')'
                f_prof_next_50 = 'sum(' + str(prof_next_50) + child_offices_rows.format(xl_col_to_name(column + 1 + 41)) + ')'
                f_prof_next_30 = 'sum(' + str(prof_next_30) + child_offices_rows.format(xl_col_to_name(column + 2 + 41)) + ')'
                sheet.write_formula(row, column + 41, f_prof_next_75, row_format_number_color_next)
                sheet.write_formula(row, column + 1 + 41, f_prof_next_50, row_format_number_color_next)
                sheet.write_formula(row, column + 2 + 41, f_prof_next_30, row_format_number_color_next)
                column -= 2

            elif element == 'AFTER NEXT':
                f_sum_after_next = 'sum(' + str(sum_after_next) + child_offices_rows.format(
                    xl_col_to_name(column)) + ')'
                sheet.write_formula(row, column, f_sum_after_next, row_format_number_color_next)
                f_prof_after_next = 'sum(' + str(prof_after_next) + child_offices_rows.format(
                    xl_col_to_name(column + 41)) + ')'
                sheet.write_formula(row, column + 41, f_prof_after_next, row_format_number_color_next)
                column -= 4

            column += 4
        # end Валовая Выручка, без НДС

    def printrow(self, sheet, workbook, companies, project_offices, budget, row, formulaItogo, level, multipliers):
        global strYEAR
        global YEARint
        global dict_formula

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
            ('commercial_budget_id', '=', budget.id),
        ])

        cur_project_offices = project_offices.filtered(lambda r: r in cur_budget_projects.project_office_id or r in {office.parent_id for office in cur_budget_projects.project_office_id if office.parent_id in project_offices})
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

                child_project_offices = self.env['project_budget.project_office'].search([('parent_id', '=', project_office.id)], order='name')

                if project_office.child_ids:
                    row += 1
                    dict_formula['office_ids'][project_office.id] = row
                    row0, formulaItogo = self.printrow(sheet, workbook, company, child_project_offices, budget, row, formulaItogo, level + 1, multipliers)

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
                    if spec.is_framework is True and spec.project_have_steps is False: continue # рамка без этапов - пропускаем
                    if spec.vgo == '-':

                        if begRowProjectsByOffice == 0:
                            begRowProjectsByOffice = row

                        if spec.project_have_steps:
                            for step in spec.project_steps_ids:
                                if spec.project_office_id == project_office and spec.company_id == company:
                                    if self.isStepinYear(spec, step) is False:
                                        continue

                                    isFoundProjectsByOffice = True
                                    isFoundProjectsByCompany = True

                                    # печатаем строки этапов проектов
                                    # row += 1
                                    # sheet.set_row(row, False, False, {'hidden': 1, 'level': level})
                                    # cur_row_format = row_format
                                    # cur_row_format_number = row_format_number
                                    # if step.estimated_probability_id.name == '0':
                                    #     cur_row_format = row_format_canceled_project
                                    #     cur_row_format_number = row_format_number_canceled_project
                                    # column = 0
                                    # sheet.write_string(row, column, spec.project_office_id.name, cur_row_format)
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
                                # sheet.set_row(row, False, False, {'hidden': 1, 'level': level})
                                # cur_row_format = row_format
                                # cur_row_format_number = row_format_number
                                # if spec.estimated_probability_id.name == '0':
                                #     cur_row_format = row_format_canceled_project
                                #     cur_row_format_number = row_format_number_canceled_project
                                # column = 0
                                # sheet.write_string(row, column, spec.project_office_id.name, cur_row_format)
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
                                # sheet.write_string(row, column, spec.vat_attribute_id.name, cur_row_format)
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
                    sheet.set_row(office_row, False, False, {'hidden': 1, 'level': level})

                    str_project_office_id = 'project_office_' + str(int(project_office.parent_id))
                    if str_project_office_id in dict_formula:
                        dict_formula[str_project_office_id] = dict_formula[str_project_office_id] + ',{0}' + str(office_row+1)
                    else:
                        dict_formula[str_project_office_id] = ',{0}'+str(office_row+1)

                    formulaProjectOffice += ',{0}' + f'{begRowProjectsByOffice + 2}' + ':{0}' + f'{office_row}'

                    str_project_office_id = 'project_office_' + str(int(project_office.id))
                    if str_project_office_id in dict_formula:
                        formulaProjectOffice = formulaProjectOffice + dict_formula[str_project_office_id] + ')'
                    else:
                        formulaProjectOffice = formulaProjectOffice + ')'

                    projects = self.env['project_budget.projects'].search(['&',
                                                                           ('commercial_budget_id', '=', budget.id),
                                                                           ('project_office_id', '=', project_office.id)
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
                else:
                    if project_office.child_ids:
                        if all(child.id not in dict_formula['office_ids_not_empty'] for child in project_office.child_ids):
                            row -= 1

            if isFoundProjectsByCompany:
                column = 0

                company_row = dict_formula['company_ids'][company.id]

                sheet.write_string(company_row, column, company.name, row_format_company)

                formulaProjectCompany += ')'

                shift = 0
                for i in range(0, 4):  # оформление строки Компания
                    for colFormula in range(0, 7):
                        formula = formulaProjectCompany.format(xl_col_to_name(i * 38 + colFormula * 5 + 1 + shift))
                        sheet.write_formula(company_row, i * 38 + colFormula * 5 + 1 + shift, formula, row_format_company_forecast)
                        formula = formulaProjectCompany.format(xl_col_to_name(i * 38 + colFormula * 5 + 2 + shift))
                        sheet.write_formula(company_row, i * 38 + colFormula * 5 + 2 + shift, formula, row_format_company_forecast)
                        formula = formulaProjectCompany.format(xl_col_to_name(i * 38 + colFormula * 5 + 3 + shift))
                        sheet.write_formula(company_row, i * 38 + colFormula * 5 + 3 + shift, formula, row_format_company_fact)
                        if colFormula in (2, 6):
                            formula = f'=IFERROR({xl_col_to_name(i * 38 + colFormula * 5 + 3 + shift)}{company_row + 1}/{xl_col_to_name(i * 38 + colFormula * 5 + 2 + shift)}{company_row + 1}," ")'
                            sheet.write_formula(company_row, i * 38 + colFormula * 5 + 4 + shift, formula, row_format_company_percent)
                            shift += 1
                        formula = formulaProjectCompany.format(xl_col_to_name(i * 38 + colFormula * 5 + 4 + shift))
                        sheet.write_formula(company_row, i * 38 + colFormula * 5 + 4 + shift, formula, row_format_company)
                        formula = formulaProjectCompany.format(xl_col_to_name(i * 38 + colFormula * 5 + 5 + shift))
                        sheet.write_formula(company_row, i * 38 + colFormula * 5 + 5 + shift, formula, row_format_company)
                    for x in range(4):
                        formula = formulaProjectCompany.format(xl_col_to_name((i + 1) * 38 + x + shift - 2))
                        sheet.write_formula(company_row, (i + 1) * 38 + x + shift - 2, formula, row_format_company_next)
                    shift += 1

        return row, formulaItogo

    def printworksheet(self, workbook, budget, namesheet, multipliers):
        global strYEAR
        global YEARint
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
        sheet.merge_range(row + 1, 0, row + 2, 0, "БЮ/Проектный офис", head_format_1)
        sheet.set_column(column, column, 40)
        # column += 1
        # sheet.write_string(row, column, "", head_format)
        # sheet.write_string(row+1, column, "КАМ", head_format_1)
        # sheet.write_string(row + 2, column, "", head_format_1)
        # sheet.set_column(column, column, 19.75)
        # column += 1
        # sheet.write_string(row, column, "", head_format)
        # sheet.write_string(row+1, column, "Заказчик", head_format_1)
        # sheet.write_string(row + 2, column, "", head_format_1)
        # sheet.set_column(column, column, 25)
        # column += 1
        # sheet.write_string(row, column, "", head_format)
        # sheet.write_string(row+1, column, "Наименование Проекта", head_format_1)
        # sheet.write_string(row + 2, column, "", head_format_1)
        # sheet.set_column(column, column, 12.25)
        # column += 1
        # sheet.write_string(row, column, "", head_format)
        # sheet.write_string(row+1, column, "Номер этапа проекта", head_format_1)
        # sheet.write_string(row + 2, column, "", head_format_1)
        # # sheet.set_column(column, column, 15)
        # column += 1
        # sheet.write_string(row, column, "", head_format)
        # sheet.write_string(row+1, column, "Стадия продажи", head_format_1)
        # sheet.write_string(row + 2, column, "", head_format_1)
        # # sheet.set_column(column, column, 16.88)
        # column += 1
        # sheet.write_string(row, column, "", head_format)
        # sheet.write_string(row+1, column, "Сумма проекта, вруб", head_format_1)
        # sheet.write_string(row + 2, column, "", head_format_1)
        # # sheet.set_column(column, column, 14)
        # column += 1
        # sheet.write_string(row, column, "", head_format)
        # sheet.write_string(row+1, column, "Валовая прибыль экспертно, в руб", head_format_1)
        # sheet.write_string(row + 2, column, "", head_format_1)
        # # sheet.set_column(column, column, 14)
        # column += 1
        # sheet.write_string(row, column, "", head_format)
        # sheet.write_string(row+1, column, "Прибыльность, экспертно, %", head_format_1)
        # sheet.write_string(row + 2, column, "", head_format_1)
        # # sheet.set_column(column, column, 9)
        # column += 1
        # sheet.write_string(row, column, "", head_format)
        # sheet.write_string(row+1, column, "Номер договора", head_format_1)
        # sheet.write_string(row + 2, column, "", head_format_1)
        # # sheet.set_column(column, column, 11.88)
        # column += 1
        # sheet.write_string(row, column, "", head_format)
        # sheet.write_string(row+1, column, "НДС", head_format_1)
        # sheet.write_string(row + 2, column, "", head_format_1)
        # # sheet.set_column(column, column, 7)
        # sheet.set_column(4, 10, False, False, {'hidden': 1, 'level': 4})
        # column += 1
        # sheet.write_string(row, column, "", head_format)
        # sheet.write_string(row+1, column, "", head_format_1)
        # sheet.write_string(row + 2, column, "", head_format_1)
        # sheet.set_column(column, column, 2)
        #
        sheet.freeze_panes(5, 1)
        column += 1
        column = self.print_quater_head(workbook, sheet, row, column,  strYEAR)
        row += 2

        companies = self.env['res.company'].search([], order='name')
        project_offices = self.env['project_budget.project_office'].search([('parent_id', '=', False)], order='report_sort')  # для сортировки так делаем + берем сначала только верхние элементы
        # project_managers = self.env['project_budget.project_manager'].search([], order='name')  # для сортировки так делаем
        # estimated_probabilitys = self.env['project_budget.estimated_probability'].search([('name','!=','10')],order='code desc')  # для сортировки так делаем

        formulaItogo = '=sum(0'

        row, formulaItogo = self.printrow(sheet, workbook, companies, project_offices, budget, row, formulaItogo, 1, multipliers)

        row += 1
        column = 0
        sheet.write_string(row, column, 'ИТОГО по отчету', row_format_number_itogo)
        for company_row in dict_formula['company_ids'].values():
            formulaItogo += ',{0}' + str(company_row + 1)
        formulaItogo = formulaItogo + ')'
        for colFormula in range(1, 165):
            formula = formulaItogo.format(xl_col_to_name(colFormula))
            sheet.write_formula(row, colFormula, formula, row_format_number_itogo)
        for i in range(4):  # формулы для процентов выполнения
            for j in (14, 35):
                formula = f'=IFERROR({xl_col_to_name(i * 41 + j - 1)}{row + 1}/{xl_col_to_name(i * 41 + j - 2)}{row + 1}, " ")'
                sheet.write_formula(row, i * 41 + j, formula, row_format_number_itogo_percent)
        print('dict_formula = ', dict_formula)

    def generate_xlsx_report(self, workbook, data, budgets):

        global strYEAR
        strYEAR = str(data['year'])
        global YEARint
        YEARint = int(strYEAR)
        global dict_formula
        dict_formula = {'company_ids': {}, 'office_ids': {}, 'office_ids_not_empty': {}}
        print('YEARint=', YEARint)
        print('strYEAR =', strYEAR)
        
        multipliers = {'50': data['koeff_reserve'], '30': data['koeff_potential']}

        commercial_budget_id = data['commercial_budget_id']
        print('commercial_budget_id', commercial_budget_id)
        budget = self.env['project_budget.commercial_budget'].search([('id', '=', commercial_budget_id)])
        self.printworksheet(workbook, budget, 'Прогноз', multipliers)
