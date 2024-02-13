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
    def isStepinYear(self, project, step):
        global YEARint

        if project:
            if step:
                if step.estimated_probability_id.name == '0':  # проверяем последний зафиксированный бюджет в предыдущих годах
                    last_fixed_step = self.env['project_budget.project_steps'].search(
                        [('date_actual', '<', datetime.date(YEARint,1,1)),
                         ('budget_state', '=', 'fixed'),
                         ('step_id', '=', step.step_id),
                         ], limit=1, order='date_actual desc')
                    if last_fixed_step and last_fixed_step.estimated_probability_id.name == '0':
                        return False

                if (step.end_presale_project_month.year >= YEARint and step.end_presale_project_month.year <= YEARint + 2)\
                        or (step.end_sale_project_month.year >= YEARint and step.end_sale_project_month.year <= YEARint + 2)\
                        or (step.end_presale_project_month.year <= YEARint and step.end_sale_project_month.year >= YEARint + 2):
                    return True
                for pds in project.planned_cash_flow_ids:
                    if pds.project_steps_id.id == step.id:
                        if pds.date_cash.year >= YEARint and pds.date_cash.year <= YEARint + 2 :
                            return True
                for pds in project.fact_cash_flow_ids:
                    if pds.project_steps_id.id == step.id:
                        if pds.date_cash.year >= YEARint and pds.date_cash.year <= YEARint + 2:
                            return True
                for act in project.planned_acceptance_flow_ids:
                    if act.project_steps_id.id == step.id:
                        if act.date_cash.year >= YEARint and act.date_cash.year <= YEARint + 2:
                            return True
                for act in project.fact_acceptance_flow_ids:
                    if act.project_steps_id.id == step.id:
                        if act.date_cash.year >= YEARint and act.date_cash.year <= YEARint + 2:
                            return True
        return False

    def isProjectinYear(self, project):
        global YEARint

        if project:
            if project.estimated_probability_id.name == '0':  # проверяем последний зафиксированный бюджет в предыдущих годах
                last_fixed_project = self.env['project_budget.projects'].search(
                    [('date_actual', '<', datetime.date(YEARint,1,1)),
                     ('budget_state', '=', 'fixed'),
                     ('project_id', '=', project.project_id),
                     ], limit=1, order='date_actual desc')
                if last_fixed_project and last_fixed_project.estimated_probability_id.name == '0':
                    return False

            if project.project_have_steps == False:
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
            else:
                for step in project.project_steps_ids:
                    if self.isStepinYear(project, step):
                        return True

            # etalon_project = self.get_etalon_project_first(project) # поищем первый эталон в году и если контрактование или последняя отгрузка были в году, то надо проект в отчете показывать
            # if etalon_project:
            #     if (etalon_project.end_presale_project_month.year >= YEARint and  etalon_project.end_presale_project_month.year <= year_end)\
            #             or (project.end_sale_project_month.year >= YEARint and project.end_sale_project_month.year <= year_end):
            #         return True

        return False

    month_rus_name_contract_pds = ['Январь','Февраль','Март','Q1 итого','Апрель','Май','Июнь','Q2 итого','HY1/YEAR итого',
                                    'Июль','Август','Сентябрь','Q3 итого','Октябрь','Ноябрь','Декабрь','Q4 итого',
                                   'HY2/YEAR итого','YEAR итого']
    month_rus_name_revenue_margin = ['Q1','Q2','HY1/YEAR','Q3','Q4','HY2/YEAR','YEAR итого']

    # array_col_itogi = [28, 49, 55, 76, 97, 103, 109, 130, 151, 157, 178, 199, 205, 211, 217, 223, 229, 235, 241, 254, 260, 266, 272, 278, 284, 297,]
    #
    # array_col_itogi75 = [247, 291,]
    #
    # array_col_itogi75NoFormula = [248, 292,]

    dict_formula = {}
    # dict_contract_pds = {
    #     1: {'name': 'Контрактование, с НДС', 'color': '#FFD966'},
    #     2: {'name': 'Поступление денежных средсв, с НДС', 'color': '#D096BF'}
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

    def get_etalon_project_first(self,spec):
        global YEARint

        datesearch = datetime.date(YEARint, 1, 1)  # будем искать первый утвержденный в году
        etalon_project = self.env['project_budget.projects'].search([('etalon_budget', '=', True),
                                                                     ('budget_state', '=', 'fixed'),
                                                                     ('project_id', '=', spec.project_id),
                                                                     ('date_actual', '>=', datesearch)
                                                                     ], limit=1, order='date_actual')
        return etalon_project

    def get_etalon_project(self,spec, quater):
        global YEARint

        datesearch = datetime.date(YEARint, 1, 1)
        if quater == 'Q1':
            datesearch = datetime.date(YEARint, 1, 1) # будем искать первый утвержденный в году
        if quater == 'Q2':
            datesearch = datetime.date(YEARint, 4, 1) # будем искать первый утвержденный после марта
        if quater == 'Q3':
            datesearch = datetime.date(YEARint, 7, 1) # будем искать первый утвержденный после июня
        if quater == 'Q4':
            datesearch = datetime.date(YEARint, 10, 1) # будем искать первый утвержденный после сентября

        if isdebug:
            logger.info(' self.env[project_budget.projects].search ')
            logger.info(f'          etalon_budget = True')
            logger.info(f'          budget_state = fixed')
            logger.info(f'          project_id = { spec.project_id}')
            logger.info(f'          date_actual >= { datesearch}')
            logger.info(f'          limit=1, order= date_actual')

        etalon_project = self.env['project_budget.projects'].search([('etalon_budget', '=', True),
                                                                     ('budget_state','=','fixed'),
                                                                     ('project_id','=',spec.project_id),
                                                                     ('date_actual','>=',datesearch)
                                                                    ], limit=1, order='date_actual')
        if etalon_project:
            if isdebug: logger.info(f'   etalon_project found by date ')
        else: # если не нашли относительно даты, то поищем просто последний
            if isdebug: logger.info(f'   etalon_project NOT found by date ')
            etalon_project = self.env['project_budget.projects'].search([('etalon_budget', '=', True),
                                                                     ('budget_state','=','fixed'),
                                                                     ('project_id','=',spec.project_id),
                                                                     ('date_actual', '>=', datetime.date(YEARint, 1, 1)),
                                                                    ], limit=1, order='date_actual desc')
        if isdebug:
            logger.info(f'  etalon_project.id = { etalon_project.id}')
            logger.info(f'  etalon_project.project_id = {etalon_project.project_id}')
            logger.info(f'  etalon_project.date_actual = { etalon_project.date_actual}')

        # print('etalon_project.project_id = ',etalon_project.project_id)
        # print('etalon_project.date_actual = ',etalon_project.date_actual)
        return etalon_project

    def get_etalon_step(self,step, quater):
        global YEARint

        if isdebug:
            logger.info(f' start get_etalon_step')
            logger.info(f' quater = {quater}')
        if step == False:
            return False
        datesearch = datetime.date(YEARint, 1, 1)
        if quater == 'Q1':
            datesearch = datetime.date(YEARint, 1, 1) # будем искать первый утвержденный в году
        if quater == 'Q2':
            datesearch = datetime.date(YEARint, 4, 1) # будем искать первый утвержденный после марта
        if quater == 'Q3':
            datesearch = datetime.date(YEARint, 7, 1) # будем искать первый утвержденный после июня
        if quater == 'Q4':
            datesearch = datetime.date(YEARint, 10, 1) # будем искать первый утвержденный после сентября
        if isdebug:
            logger.info(f'   self.env[project_budget.projects].search ')
            logger.info(f'           etalon_budget = True')
            logger.info(f'           step_id = {step.step_id}')
            logger.info(f'           id != {step.id}')
            logger.info(f'           date_actual >= {datesearch}')
            logger.info(f'           limit = 1, order = date_actual')

        etalon_step = self.env['project_budget.project_steps'].search([('etalon_budget', '=', True),
                                                                       ('step_id','=',step.step_id),
                                                                       ('id','!=',step.id),
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
                                                                       ('id','!=',step.id),
                                                                       ('date_actual', '>=', datetime.date(YEARint, 1, 1)),
                                                                      ], limit=1, order='date_actual desc')
        if isdebug:
            logger.info(f' step_id = {etalon_step.step_id}')
            logger.info(f' id = {etalon_step.id}')
            logger.info(f' date_actual = {etalon_step.date_actual}')
            logger.info(f' end_presale_project_month = {etalon_step.end_presale_project_month}')
            logger.info(f' estimated_probability_id = {etalon_step.estimated_probability_id}')
            logger.info(f' end get_etalon_step')
        return etalon_step

    def get_sum_fact_pds_project_step_month(self,project, step, year, month):
        sum_cash = 0
        if month:
            pds_list = project.fact_cash_flow_ids
            # if step:
            #     pds_list = self.env['project_budget.fact_cash_flow'].search([('project_steps_id', '=', step.id)])
            # else:
            #     pds_list = self.env['project_budget.fact_cash_flow'].search([('projects_id', '=', project.id)])
            for pds in pds_list:
                if step:
                    if pds.project_steps_id.id != step.id: continue
                if pds.date_cash.month == month and pds.date_cash.year == year:
                    sum_cash += pds.sum_cash
        if month == False:
            pds_list = project.fact_cash_flow_ids
            # if step:
            #     pds_list = self.env['project_budget.fact_cash_flow'].search([('project_steps_id', '=', step.id)])
            # else:
            #     pds_list = self.env['project_budget.fact_cash_flow'].search([('projects_id', '=', project.id)])
            for pds in pds_list:
                if step:
                    if pds.project_steps_id.id != step.id: continue
                if pds.date_cash.year == year:
                    sum_cash += pds.sum_cash

        return sum_cash

    def get_sum_plan_pds_project_step_month(self,project, step, year, month):
        sum_cash = {'commitment': 0, 'reserve':0}
        if month:
            # if step:
            #     pds_list = self.env['project_budget.planned_cash_flow'].search([('project_steps_id', '=', step.id)])
            # else:
            #     pds_list = self.env['project_budget.planned_cash_flow'].search([('projects_id', '=', project.id)])
            pds_list = project.planned_cash_flow_ids
            for pds in pds_list:
                if step:
                    if pds.project_steps_id.id != step.id: continue
                if pds.date_cash.month == month and pds.date_cash.year == year:
                    if step:
                        estimated_probability_id_name = step.estimated_probability_id.name
                    else:
                        estimated_probability_id_name = project.estimated_probability_id.name

                    if pds.forecast == 'from_project':

                        if estimated_probability_id_name in ('75', '100', '100(done)'):
                            sum_cash['commitment'] = sum_cash.get('commitment', 0) + pds.sum_cash
                        elif estimated_probability_id_name == '50':
                            sum_cash['reserve'] = sum_cash.get('reserve', 0) + pds.sum_cash
                    else:
                        if estimated_probability_id_name != '0':
                            sum_cash[pds.forecast] = sum_cash.get(pds.forecast, 0) + pds.sum_cash
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
        if month == False:
            # if step:
            #     pds_list = self.env['project_budget.planned_cash_flow'].search([('project_steps_id', '=', step.id)])
            # else:
            #     pds_list = self.env['project_budget.planned_cash_flow'].search([('projects_id', '=', project.id)])
            pds_list = project.planned_cash_flow_ids
            for pds in pds_list:
                if step:
                    if pds.project_steps_id.id != step.id: continue
                if pds.date_cash.year == year:
                    if step:
                        estimated_probability_id_name = step.estimated_probability_id.name
                    else:
                        estimated_probability_id_name = project.estimated_probability_id.name

                    if pds.forecast == 'from_project':
                        if estimated_probability_id_name in ('75', '100', '100(done)'):
                            sum_cash['commitment'] = sum_cash.get('commitment', 0) + pds.sum_cash
                        elif estimated_probability_id_name == '50':
                            sum_cash['reserve'] = sum_cash.get('reserve', 0) + pds.sum_cash
                    else:
                        if estimated_probability_id_name != '0':
                            sum_cash[pds.forecast] = sum_cash.get(pds.forecast, 0) + pds.sum_cash
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

    def get_sum_plan_acceptance_step_month(self,project, step, year, month):
        global YEARint
        sum_cash = 0
        # if project.project_have_steps == False:
        #     acceptance_list = self.env['project_budget.planned_acceptance_flow'].search([('projects_id', '=', project.id)])
        # if project.project_have_steps and step != False:
        #     acceptance_list = self.env['project_budget.planned_acceptance_flow'].search([('project_steps_id', '=', step.id)])

        acceptance_list = project.planned_acceptance_flow_ids
        for acceptance in acceptance_list:
            if step:
                if acceptance.project_steps_id.id != step.id: continue
            if acceptance.date_cash.month == month and acceptance.date_cash.year == year:
                sum_cash += acceptance.sum_cash_without_vat
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
            if element.find('итого') != -1:
                if elementone.find('Q') != -1:
                    sheet.set_column(column, column + 4, False, False, {'hidden': 1, 'level': 2})
                if elementone.find('HY') != -1:
                    sheet.set_column(column, column + 4, False, False, {'hidden': 1, 'level': 1})

                if next:
                    sheet.merge_range(row, column, row, column + 3, element, head_format_month)
                else:
                    sheet.merge_range(row, column, row, column + 4, element, head_format_month)

                sheet.merge_range(row + 1, column, row + 2, column, "План "+element.replace(' итого',''), head_format_month_itogo)
                column += 1
            else:
                sheet.merge_range(row, column, row, column + 3, element, head_format_month)
                sheet.set_column(column, column+4, False, False, {'hidden': 1, 'level': 3})
            # sheet.merge_range(row+1, column, row+1, column + 1, 'Прогноз на начало периода (эталонный)', head_format_month_detail)
            # sheet.write_string(row+2, column, 'Обязательство', head_format_month_detail)
            # column += 1
            # sheet.write_string(row + 2, column, 'Резерв', head_format_month_detail)
            # column += 1
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
            if elementone.find('Q') != -1 or elementone.find('НY') != -1 or elementone.find('YEAR') != -1:
                colbegQ = column

            if elementone.find('НY') != -1 or elementone.find('YEAR') != -1:
                colbegH = column
        sheet.merge_range(row-1, colbeg, row-1, column - 1, y[0], head_format_month)

        return column

    def print_month_head_pds(self, workbook, sheet, row, column, year, elements, next):

        x = {'name': 'Поступление денежных средсв, с НДС', 'color': '#D096BF'}

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
            if element.find('итого') != -1:
                if elementone.find('Q') != -1:
                    sheet.set_column(column, column + 3, False, False, {'hidden': 1, 'level': 2})
                if elementone.find('HY') != -1:
                    sheet.set_column(column, column + 3, False, False, {'hidden': 1, 'level': 1})

                if next:
                    sheet.merge_range(row, column, row, column + 2, element, head_format_month)
                else:
                    sheet.merge_range(row, column, row, column + 3, element, head_format_month)

                sheet.merge_range(row + 1, column, row + 2, column, "План "+element.replace(' итого',''), head_format_month_itogo)
                column += 1
            else:
                sheet.merge_range(row, column, row, column + 2, element, head_format_month)
                sheet.set_column(column, column+4, False, False, {'hidden': 1, 'level': 3})
            # sheet.merge_range(row+1, column, row+1, column + 1, 'Прогноз на начало периода (эталонный)', head_format_month_detail)
            # sheet.write_string(row+2, column, 'Обязательство', head_format_month_detail)
            # column += 1
            # sheet.write_string(row + 2, column, 'Резерв', head_format_month_detail)
            # column += 1
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

                addcolumn = potential_column = 0
                if element.find('HY2') != -1:
                    addcolumn = 1
                elif 'итого' in element and x[0] == 1:
                    potential_column = 1

                if elementone.find('Q') != -1:
                    sheet.set_column(column, column + 3, False, False, {'hidden': 1, 'level': 2})

                if elementone.find('HY') != -1:
                    sheet.set_column(column, column + 3 + addcolumn, False, False, {'hidden': 1, 'level': 1})

                if next:
                    sheet.merge_range(row, column, row, column + 2 + addcolumn + potential_column, element, head_format_month)
                else:
                    sheet.merge_range(row, column, row, column + 3 + addcolumn + potential_column, element,
                                      head_format_month)


                sheet.merge_range(row + 1, column, row + 2, column, "План " + element.replace(' итого', ''),
                                  head_format_month_itogo)
                column += 1

                if element.find('HY2') != -1:
                    sheet.merge_range(row + 1, column, row + 2, column, "План HY2/"+strYEARprint+ " 6+6"
                                      , head_format_month_itogo)
                    column += 1

                # sheet.merge_range(row + 1, column , row + 1, column + 1 , 'Прогноз на начало периода (эталонный)',
                #                   head_format_month_detail)
                #
                # sheet.write_string(row + 2, column , 'Обязательство', head_format_month_detail)
                # column += 1
                # sheet.write_string(row + 2, column , 'Резерв', head_format_month_detail)
                # column += 1
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

    def print_month_revenue_project(self, sheet, row, column, month, project, step, year, row_format_number,row_format_number_color_fact, next):
        global koeff_reserve
        global koeff_potential

        sum75tmpetalon = 0
        sum50tmpetalon = 0
        sum100tmp = 0
        sum75tmp = 0
        sum50tmp = 0
        sum30tmp = 0

        if month:
            # project_etalon = self.get_etalon_project(project, self.get_quater_from_month(month))
            if step == False:
            #     if project_etalon:
            #         currency_rate = self.get_currency_rate_by_project(project_etalon)
            #         if month == project_etalon.end_presale_project_month.month\
            #                 and project_etalon.end_presale_project_month.year >= YEARint\
            #                 and project_etalon.end_presale_project_month.year <= year_end:
            #             if project_etalon.estimated_probability_id.name == '75':
            #                 sheet.write_number(row, column + 0, project_etalon.total_amount_of_revenue_with_vat*currency_rate, row_format_number)
            #                 sum75tmpetalon += project_etalon.total_amount_of_revenue_with_vat*currency_rate
            #             if project_etalon.estimated_probability_id.name == '50':
            #                 sheet.write_number(row, column + 1, project_etalon.total_amount_of_revenue_with_vat * koeff_reserve*currency_rate, row_format_number)
            #                 sum50tmpetalon += project_etalon.total_amount_of_revenue_with_vat * koeff_reserve*currency_rate

                if month == project.end_presale_project_month.month and project.end_presale_project_month.year == year:
                    currency_rate = self.get_currency_rate_by_project(project)
                    if not next:
                        if project.estimated_probability_id.name in ('100','100(done)'):
                            sheet.write_number(row, column + 0, project.total_amount_of_revenue_with_vat * currency_rate, row_format_number_color_fact)
                            sum100tmp += project.total_amount_of_revenue_with_vat * currency_rate
                        if project.estimated_probability_id.name == '75':
                            sheet.write_number(row, column + 1, project.total_amount_of_revenue_with_vat * currency_rate, row_format_number)
                            sum75tmp += project.total_amount_of_revenue_with_vat * currency_rate
                        if project.estimated_probability_id.name == '50':
                            sheet.write_number(row, column + 2, project.total_amount_of_revenue_with_vat * koeff_reserve * currency_rate, row_format_number)
                            sum50tmp += project.total_amount_of_revenue_with_vat * koeff_reserve*currency_rate
                        if project.estimated_probability_id.name == '30':
                            sheet.write_number(row, column + 3, project.total_amount_of_revenue_with_vat * koeff_potential * currency_rate, row_format_number)
                            sum30tmp += project.total_amount_of_revenue_with_vat * koeff_potential * currency_rate
                    else:
                        if project.estimated_probability_id.name == '75':
                            sheet.write_number(row, column + 0, project.total_amount_of_revenue_with_vat * currency_rate, row_format_number)
                        if project.estimated_probability_id.name == '50':
                            sheet.write_number(row, column + 1, project.total_amount_of_revenue_with_vat * koeff_reserve * currency_rate, row_format_number)
                        if project.estimated_probability_id.name == '30':
                            sheet.write_number(row, column + 2, project.total_amount_of_revenue_with_vat * koeff_potential * currency_rate, row_format_number)
            else:
                # step_etalon  = self.get_etalon_step(step, self.get_quater_from_month(month))
                # if step_etalon:
                #     if month == step_etalon.end_presale_project_month.month \
                #             and step_etalon.end_presale_project_month.year >= YEARint\
                #             and step_etalon.end_presale_project_month.year <= year_end:
                #         currency_rate = self.get_currency_rate_by_project(step_etalon.projects_id)
                #         if step_etalon.estimated_probability_id.name == '75':
                #             sheet.write_number(row, column + 0, step_etalon.total_amount_of_revenue_with_vat*currency_rate, row_format_number)
                #             sum75tmpetalon = step_etalon.total_amount_of_revenue_with_vat*currency_rate*currency_rate
                #         if step_etalon.estimated_probability_id.name == '50':
                #             sheet.write_number(row, column + 1, step_etalon.total_amount_of_revenue_with_vat * koeff_reserve*currency_rate, row_format_number)
                #             sum50tmpetalon = step_etalon.total_amount_of_revenue_with_vat * koeff_reserve*currency_rate*currency_rate
                # else:
                #     if project_etalon: # если нет жталонного этапа, то данные берем из проекта, да это будет увеличивать сумму на количество этапов, но что делать я ХЗ
                #         if month == project_etalon.end_presale_project_month.month \
                #                 and project_etalon.end_presale_project_month.year >= YEARint \
                #                 and project_etalon.end_presale_project_month.year <= year_end:
                #             currency_rate = self.get_currency_rate_by_project(project_etalon)
                #             if project_etalon.estimated_probability_id.name == '75':
                #                 sheet.write_number(row, column + 0, project_etalon.total_amount_of_revenue_with_vat*currency_rate,
                #                                    row_format_number)
                #                 sum75tmpetalon += project_etalon.total_amount_of_revenue_with_vat*currency_rate
                #             if project_etalon.estimated_probability_id.name == '50':
                #                 sheet.write_number(row, column + 1, project_etalon.total_amount_of_revenue_with_vat * koeff_reserve*currency_rate,
                #                                    row_format_number)
                #                 sum50tmpetalon += project_etalon.total_amount_of_revenue_with_vat * koeff_reserve*currency_rate

                if month == step.end_presale_project_month.month and step.end_presale_project_month.year == year:
                    currency_rate = self.get_currency_rate_by_project(step.projects_id)
                    if not next:
                        if step.estimated_probability_id.name in ('100','100(done)'):
                            sheet.write_number(row, column + 0, step.total_amount_of_revenue_with_vat * currency_rate, row_format_number_color_fact)
                            sum100tmp = step.total_amount_of_revenue_with_vat * currency_rate
                        if step.estimated_probability_id.name == '75':
                            sheet.write_number(row, column + 1, step.total_amount_of_revenue_with_vat * currency_rate, row_format_number)
                            sum75tmp = step.total_amount_of_revenue_with_vat * currency_rate
                        if step.estimated_probability_id.name == '50':
                            sheet.write_number(row, column + 2, step.total_amount_of_revenue_with_vat * koeff_reserve * currency_rate, row_format_number)
                            sum50tmp = step.total_amount_of_revenue_with_vat * koeff_reserve * currency_rate
                        if step.estimated_probability_id.name == '30':
                            sheet.write_number(row, column + 3, step.total_amount_of_revenue_with_vat * koeff_potential * currency_rate, row_format_number)
                            sum30tmp = step.total_amount_of_revenue_with_vat * koeff_potential * currency_rate
                    else:
                        if step.estimated_probability_id.name == '75':
                            sheet.write_number(row, column + 0, step.total_amount_of_revenue_with_vat * currency_rate, row_format_number)
                        if step.estimated_probability_id.name == '50':
                            sheet.write_number(row, column + 1, step.total_amount_of_revenue_with_vat * koeff_reserve * currency_rate, row_format_number)
                        if step.estimated_probability_id.name == '30':
                            sheet.write_number(row, column + 2, step.total_amount_of_revenue_with_vat * koeff_potential * currency_rate, row_format_number)
        return sum75tmpetalon, sum50tmpetalon, sum100tmp, sum75tmp, sum50tmp, sum30tmp

    def print_year_pds_project(self, sheet, row, column, project, step, year, row_format_number, row_format_number_color_fact, next):
        global koeff_reserve

        sum75tmpetalon = sum50tmpetalon = sum100tmp = sum75tmp = sum50tmp = 0
        if year:
            # project_etalon = self.get_etalon_project(project, self.get_quater_from_month(month))
            # step_etalon = self.get_etalon_step(step, self.get_quater_from_month(month))
            sum = {'commitment': 0, 'reserve': 0, 'potential': 0}
            # sum = self.get_sum_plan_pds_project_step_month(project_etalon, step_etalon, month)
            #
            # if (step) and (not step_etalon): # есть этап сейчас, но нет в эталоне
            #     sum = {'commitment': 0, 'reserve':0, 'potential': 0}
            #
            # if sum:
            #     sheet.write_number(row, column + 0, sum.get('commitment', 0), row_format_number)
            #     sum75tmpetalon += sum.get('commitment', 0)
            #     sheet.write_number(row, column + 1, sum.get('reserve', 0) * koeff_reserve, row_format_number)
            #     sum50tmpetalon += sum.get('reserve', 0) * koeff_reserve

            sum100tmp = self.get_sum_fact_pds_project_step_month(project, step, year, False)

            if sum100tmp:
                if not next:
                    sheet.write_number(row, column + 0, sum100tmp, row_format_number_color_fact)

            sum = self.get_sum_plan_pds_project_step_month(project, step, year, False)
            # print('----- project.id=',project.id)
            # print('sum100tmp = ',sum100tmp)
            # print('sum = ', sum)

            if not project.is_correction_project:
                if sum100tmp >= sum.get('commitment', 0):
                    sum100tmp_ostatok = sum100tmp - sum['commitment']
                    sum['commitment'] = 0
                    sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                else:
                    sum['commitment'] = sum['commitment'] - sum100tmp

            # print('after: sum = ', sum)
            # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
            sum_ostatok_pds = {'commitment': 0, 'reserve':0, 'potential': 0}
            sum_distribution_pds = 0
            for planned_cash_flow in project.planned_cash_flow_ids:
                if step:
                    if planned_cash_flow.project_steps_id.id != step.id: continue
                if planned_cash_flow.date_cash.year == year:
                    sum_distribution_pds += planned_cash_flow.distribution_sum_without_vat
                    estimated_probability_id_name = project.estimated_probability_id.name
                    if step:
                        estimated_probability_id_name = step.estimated_probability_id.name

                    if planned_cash_flow.forecast == 'from_project':
                        if estimated_probability_id_name in ('75', '100', '100(done)'):
                            sum_ostatok_pds['commitment'] = sum_ostatok_pds.get('commitment', 0) + planned_cash_flow.distribution_sum_with_vat_ostatok
                        elif estimated_probability_id_name == '50':
                            sum_ostatok_pds['reserve'] = sum_ostatok_pds.get('reserve', 0) + planned_cash_flow.distribution_sum_with_vat_ostatok
                    else:
                        if estimated_probability_id_name != '0':
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
    def print_month_pds_project(self, sheet, row, column, month, project, step, year, row_format_number, row_format_number_color_fact, next):
        global koeff_reserve

        sum75tmpetalon = sum50tmpetalon = sum100tmp = sum75tmp = sum50tmp = 0
        if month:
            # project_etalon = self.get_etalon_project(project, self.get_quater_from_month(month))
            # step_etalon = self.get_etalon_step(step, self.get_quater_from_month(month))
            sum = {'commitment': 0, 'reserve': 0, 'potential': 0}
            # sum = self.get_sum_plan_pds_project_step_month(project_etalon, step_etalon, month)
            #
            # if (step) and (not step_etalon): # есть этап сейчас, но нет в эталоне
            #     sum = {'commitment': 0, 'reserve':0, 'potential': 0}
            #
            # if sum:
            #     sheet.write_number(row, column + 0, sum.get('commitment', 0), row_format_number)
            #     sum75tmpetalon += sum.get('commitment', 0)
            #     sheet.write_number(row, column + 1, sum.get('reserve', 0) * koeff_reserve, row_format_number)
            #     sum50tmpetalon += sum.get('reserve', 0) * koeff_reserve

            sum100tmp = self.get_sum_fact_pds_project_step_month(project, step, year, month)

            if sum100tmp:
                if not next:
                    sheet.write_number(row, column + 0, sum100tmp, row_format_number_color_fact)

            sum = self.get_sum_plan_pds_project_step_month(project, step, year, month)
            # print('----- project.id=',project.id)
            # print('sum100tmp = ',sum100tmp)
            # print('sum = ', sum)

            if not project.is_correction_project:
                if sum100tmp >= sum.get('commitment', 0):
                    sum100tmp_ostatok = sum100tmp - sum['commitment']
                    sum['commitment'] = 0
                    sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
                else:
                    sum['commitment'] = sum['commitment'] - sum100tmp

            # print('after: sum = ', sum)
            # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
            sum_ostatok_pds = {'commitment': 0, 'reserve':0, 'potential': 0}
            sum_distribution_pds = 0
            for planned_cash_flow in project.planned_cash_flow_ids:
                if step:
                    if planned_cash_flow.project_steps_id.id != step.id: continue
                if planned_cash_flow.date_cash.month == month and planned_cash_flow.date_cash.year == year:
                    sum_distribution_pds += planned_cash_flow.distribution_sum_without_vat
                    estimated_probability_id_name = project.estimated_probability_id.name
                    if step:
                        estimated_probability_id_name = step.estimated_probability_id.name

                    if planned_cash_flow.forecast == 'from_project':
                        if estimated_probability_id_name in ('75', '100', '100(done)'):
                            sum_ostatok_pds['commitment'] = sum_ostatok_pds.get('commitment', 0) + planned_cash_flow.distribution_sum_with_vat_ostatok
                        elif estimated_probability_id_name == '50':
                            sum_ostatok_pds['reserve'] = sum_ostatok_pds.get('reserve', 0) + planned_cash_flow.distribution_sum_with_vat_ostatok
                    else:
                        if estimated_probability_id_name != '0':
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

    def get_sum_fact_acceptance_project_step_quater(self, project, step, year, element_name):
        sum_cash = 0
        months = self.get_months_from_quater(element_name)
        if months:
            acceptance_list = project.fact_acceptance_flow_ids
            if acceptance_list:
                for acceptance in acceptance_list:
                    if step:
                        if acceptance.project_steps_id.id != step.id: continue
                    if acceptance.date_cash.month in months and acceptance.date_cash.year == year:
                        sum_cash += acceptance.sum_cash_without_vat
        if element_name == False:
            acceptance_list = project.fact_acceptance_flow_ids
            if acceptance_list:
                for acceptance in acceptance_list:
                    if step:
                        if acceptance.project_steps_id.id != step.id: continue
                    if acceptance.date_cash.year == year:
                        sum_cash += acceptance.sum_cash_without_vat
        return sum_cash

    def get_sum_fact_margin_project_step_quarter(self, project, step, year, element_name):
        sum_cash = 0
        months = self.get_months_from_quater(element_name)
        if project.is_parent_project:
            for child_project in project.child_project_ids:
                if child_project.project_have_steps:
                    for child_step in child_project.project_steps_ids:
                        sum_cash += self.get_sum_fact_margin_project_step_quarter(child_project, child_step, year,
                                                                                  element_name) * child_project.margin_rate_for_parent
                else:
                    sum_cash += self.get_sum_fact_margin_project_step_quarter(child_project, False, year, element_name) * child_project.margin_rate_for_parent
            return sum_cash
        if months:
            acceptance_list = project.fact_acceptance_flow_ids
            if acceptance_list:
                for acceptance in acceptance_list:
                    if step:
                        if acceptance.project_steps_id.id != step.id: continue
                    if acceptance.date_cash.month in months and acceptance.date_cash.year == year:
                        sum_cash += acceptance.margin
        if element_name == False:
            acceptance_list = project.fact_acceptance_flow_ids
            if acceptance_list:
                for acceptance in acceptance_list:
                    if step:
                        if acceptance.project_steps_id.id != step.id: continue
                    if acceptance.date_cash.year == year:
                        sum_cash += acceptance.margin

        return sum_cash

    def get_sum_planned_acceptance_project_step_quater(self, project, step, year, element_name):
        sum_acceptance = {'commitment': 0, 'reserve':0, 'potential': 0}

        months = self.get_months_from_quater(element_name)

        if months:
            acceptance_list = project.planned_acceptance_flow_ids
            if acceptance_list:
                for acceptance in acceptance_list:
                    if step:
                        if acceptance.project_steps_id.id != step.id: continue
                    if acceptance.date_cash.month in months and acceptance.date_cash.year == year:
                        if step:
                            estimated_probability_id_name = step.estimated_probability_id.name
                        else:
                            estimated_probability_id_name = project.estimated_probability_id.name

                        if acceptance.forecast == 'from_project':
                            if estimated_probability_id_name in ('75', '100', '100(done)'):
                                sum_acceptance['commitment'] = sum_acceptance.get('commitment', 0) + acceptance.sum_cash_without_vat
                            elif estimated_probability_id_name == '50':
                                sum_acceptance['reserve'] = sum_acceptance.get('reserve', 0) + acceptance.sum_cash_without_vat
                        else:
                            if estimated_probability_id_name != '0':
                                sum_acceptance[acceptance.forecast] = sum_acceptance.get(acceptance.forecast, 0) + acceptance.sum_cash_without_vat
        if element_name == False:
            acceptance_list = project.planned_acceptance_flow_ids
            if acceptance_list:
                for acceptance in acceptance_list:
                    if step:
                        if acceptance.project_steps_id.id != step.id: continue
                    if acceptance.date_cash.year == year:
                        if step:
                            estimated_probability_id_name = step.estimated_probability_id.name
                        else:
                            estimated_probability_id_name = project.estimated_probability_id.name

                        if acceptance.forecast == 'from_project':
                            if estimated_probability_id_name in ('75', '100', '100(done)'):
                                sum_acceptance['commitment'] = sum_acceptance.get('commitment', 0) + acceptance.sum_cash_without_vat
                            elif estimated_probability_id_name == '50':
                                sum_acceptance['reserve'] = sum_acceptance.get('reserve', 0) + acceptance.sum_cash_without_vat
                        else:
                            if estimated_probability_id_name !='0' :
                                sum_acceptance[acceptance.forecast] = sum_acceptance.get(acceptance.forecast, 0) + acceptance.sum_cash_without_vat
        return sum_acceptance

    def get_sum_planned_margin_project_step_quater(self, project, step, year, element_name):
        sum_margin = {'commitment': 0, 'reserve': 0, 'potential': 0}

        months = self.get_months_from_quater(element_name)
        if project.is_parent_project:
            for child_project in project.child_project_ids:
                if child_project.project_have_steps:
                    for child_step in child_project.project_steps_ids:
                        for key in sum_margin:
                            sum_margin[key] += self.get_sum_planned_margin_project_step_quater(child_project, child_step, year,
                                                                                  element_name)[key] * child_project.margin_rate_for_parent
                else:
                    for key in sum_margin:
                        sum_margin[key] += self.get_sum_planned_margin_project_step_quater(child_project, False, year, element_name)[key] * child_project.margin_rate_for_parent
            return sum_margin
        if months:
            acceptance_list = project.planned_acceptance_flow_ids
            if acceptance_list:
                for acceptance in acceptance_list:
                    if step:
                        if acceptance.project_steps_id.id != step.id: continue
                        estimated_probability_id_name = step.estimated_probability_id.name
                        profitability = step.profitability
                    else:
                        estimated_probability_id_name = project.estimated_probability_id.name
                        profitability = project.profitability
                    if acceptance.date_cash.month in months and acceptance.date_cash.year == year:
                        if acceptance.forecast == 'from_project':
                            if estimated_probability_id_name in ('75', '100', '100(done)'):
                                sum_margin['commitment'] += acceptance.sum_cash_without_vat * profitability / 100
                            elif estimated_probability_id_name == '50':
                                sum_margin['reserve'] += acceptance.sum_cash_without_vat * profitability / 100
                        else:
                            if estimated_probability_id_name != '0':
                                sum_margin[acceptance.forecast] += acceptance.sum_cash_without_vat * profitability / 100
        if element_name == False:
            acceptance_list = project.planned_acceptance_flow_ids
            if acceptance_list:
                for acceptance in acceptance_list:
                    if step:
                        if acceptance.project_steps_id.id != step.id: continue
                        estimated_probability_id_name = step.estimated_probability_id.name
                        profitability = step.profitability
                    else:
                        estimated_probability_id_name = project.estimated_probability_id.name
                        profitability = project.profitability
                    if acceptance.date_cash.year == year:
                        if acceptance.forecast == 'from_project':
                            if estimated_probability_id_name in ('75', '100', '100(done)'):
                                sum_margin['commitment'] += acceptance.sum_cash_without_vat * profitability / 100
                            elif estimated_probability_id_name == '50':
                                sum_margin['reserve'] += acceptance.sum_cash_without_vat * profitability / 100
                        else:
                            if estimated_probability_id_name != '0':
                                sum_margin[acceptance.forecast] += acceptance.sum_cash_without_vat * profitability / 100
        return sum_margin

    def get_margin_forecast_from_distributions(self, planned_acceptance, margin_plan, project, step, margin_rate_for_parent):
        # суммируем доли маржи фактов в соотношении (сумма распределения/суммы факта)
        margin_distribution = 0
        for distribution in planned_acceptance.distribution_acceptance_ids:
            if distribution.fact_acceptance_flow_id.sum_cash_without_vat != 0:
                margin_distribution += distribution.fact_acceptance_flow_id.margin * distribution.distribution_sum_without_vat / distribution.fact_acceptance_flow_id.sum_cash_without_vat
        estimated_probability_id_name = project.estimated_probability_id.name
        if step:
            estimated_probability_id_name = step.estimated_probability_id.name

        if planned_acceptance.forecast == 'from_project':
            if estimated_probability_id_name in ('75', '100', '100(done)'):
                margin_plan['commitment'] -= margin_distribution * margin_rate_for_parent
            elif estimated_probability_id_name == '50':
                margin_plan['reserve'] -= margin_distribution * margin_rate_for_parent
        else:
            if estimated_probability_id_name != '0':
                margin_plan[planned_acceptance.forecast] -= margin_distribution * margin_rate_for_parent
        return  margin_plan

    def get_sum_planned_acceptance_project_step_from_distribution(self, project, step, year, element_name):
        # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
        sum_ostatok_acceptance = {'commitment': 0, 'reserve': 0, 'potential': 0}
        sum_distribution_acceptance = 0
        months = self.get_months_from_quater(element_name)
        if months:
            for planned_acceptance_flow in project.planned_acceptance_flow_ids:
                if step:
                    if planned_acceptance_flow.project_steps_id.id != step.id: continue
                if planned_acceptance_flow.date_cash.month in months and planned_acceptance_flow.date_cash.year == year:
                    sum_distribution_acceptance += planned_acceptance_flow.distribution_sum_without_vat

                    estimated_probability_id_name = project.estimated_probability_id.name
                    if step:
                        estimated_probability_id_name = step.estimated_probability_id.name

                    if planned_acceptance_flow.forecast == 'from_project':
                        if estimated_probability_id_name in ('75', '100', '100(done)'):
                            sum_ostatok_acceptance['commitment'] = sum_ostatok_acceptance.get('commitment',
                                                                                              0) + planned_acceptance_flow.distribution_sum_without_vat_ostatok
                        elif estimated_probability_id_name == '50':
                            sum_ostatok_acceptance['reserve'] = sum_ostatok_acceptance.get('reserve',
                                                                                           0) + planned_acceptance_flow.distribution_sum_without_vat_ostatok
                    else:
                        if estimated_probability_id_name != '0':
                            sum_ostatok_acceptance[planned_acceptance_flow.forecast] = sum_ostatok_acceptance.get(
                                planned_acceptance_flow.forecast,
                                0) + planned_acceptance_flow.distribution_sum_without_vat_ostatok

        if element_name == False:
            for planned_acceptance_flow in project.planned_acceptance_flow_ids:
                if step:
                    if planned_acceptance_flow.project_steps_id.id != step.id: continue
                if planned_acceptance_flow.date_cash.year == year:
                    sum_distribution_acceptance += planned_acceptance_flow.distribution_sum_without_vat

                    estimated_probability_id_name = project.estimated_probability_id.name
                    if step:
                        estimated_probability_id_name = step.estimated_probability_id.name

                    if planned_acceptance_flow.forecast == 'from_project':
                        if estimated_probability_id_name in ('75', '100', '100(done)'):
                            sum_ostatok_acceptance['commitment'] = sum_ostatok_acceptance.get('commitment',
                                                                                              0) + planned_acceptance_flow.distribution_sum_without_vat_ostatok
                        elif estimated_probability_id_name == '50':
                            sum_ostatok_acceptance['reserve'] = sum_ostatok_acceptance.get('reserve',
                                                                                           0) + planned_acceptance_flow.distribution_sum_without_vat_ostatok
                    else:
                        if estimated_probability_id_name != '0':
                            sum_ostatok_acceptance[planned_acceptance_flow.forecast] = sum_ostatok_acceptance.get(
                                planned_acceptance_flow.forecast,
                                0) + planned_acceptance_flow.distribution_sum_without_vat_ostatok

        if sum_distribution_acceptance:  # если есть распределение, то остаток = остатку распределения
            return sum_ostatok_acceptance
        else:
            return False

    def get_sum_planned_margin_project_step_from_distribution(self, project, step, year, element_name, margin_plan, margin_rate_for_parent):
        # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
        sum_distribution_acceptance = 0
        new_margin_plan = margin_plan.copy()
        months = self.get_months_from_quater(element_name)

        if project.is_parent_project:
            for child_project in project.child_project_ids:
                if child_project.project_have_steps:
                    for child_step in child_project.project_steps_ids:
                        new_margin_plan =  self.get_sum_planned_margin_project_step_from_distribution(child_project, child_step, year,
                                                                              element_name, margin_plan, child_project.margin_rate_for_parent)
                        if new_margin_plan:
                            margin_plan = new_margin_plan
                else:
                    new_margin_plan = self.get_sum_planned_margin_project_step_from_distribution(child_project, False, year, element_name, margin_plan, child_project.margin_rate_for_parent)
                    if new_margin_plan:
                        margin_plan = new_margin_plan

            return margin_plan
        if months:
            for planned_acceptance_flow in project.planned_acceptance_flow_ids:
                if step:
                    if planned_acceptance_flow.project_steps_id.id != step.id: continue
                if planned_acceptance_flow.date_cash.month in months and planned_acceptance_flow.date_cash.year == year:
                    sum_distribution_acceptance += planned_acceptance_flow.distribution_sum_without_vat

                    new_margin_plan = self.get_margin_forecast_from_distributions(planned_acceptance_flow, new_margin_plan, project,
                                                                              step, margin_rate_for_parent)
        if element_name == False:
            for planned_acceptance_flow in project.planned_acceptance_flow_ids:
                if step:
                    if planned_acceptance_flow.project_steps_id.id != step.id: continue
                if planned_acceptance_flow.date_cash.year == year:
                    sum_distribution_acceptance += planned_acceptance_flow.distribution_sum_without_vat

                    new_margin_plan = self.get_margin_forecast_from_distributions(planned_acceptance_flow,
                                                                                  new_margin_plan, project,
                                                                                  step, margin_rate_for_parent)

        if sum_distribution_acceptance:  # если есть распределение, то остаток = остатку распределения
            return new_margin_plan
        else:
            return False

    def print_year_planned_acceptance_project(self, sheet, row, column, project, step, year, row_format_number, row_format_number_color_fact,margin_shift,next):

        sum75tmpetalon = sum50tmpetalon = sum100tmp = sum75tmp = sum50tmp = 0
        if year:
            # project_etalon = self.get_etalon_project(project, element_name)
            # step_etalon = self.get_etalon_step(step, element_name)

            if step == False:
                profitability = project.profitability
            else:
                profitability = step.profitability

            margin_rate_for_child = 1
            if project.is_child_project:
                margin_rate_for_child = (1 - project.margin_rate_for_parent)

            # sum = self.get_sum_planned_acceptance_project_step_quater(project_etalon, step_etalon, element_name)
            # margin_sum = self.get_sum_planned_margin_project_step_quater(project_etalon, step_etalon, element_name)
            # if step and not step_etalon:
            #     sum = {'commitment': 0, 'reserve': 0, 'potential': 0}
            #     margin_sum = {'commitment': 0, 'reserve': 0, 'potential': 0}

            # if sum:
            #     sheet.write_number(row, column + 0, sum.get('commitment', 0), row_format_number)
            #     sheet.write_number(row, column + 0 + margin_shift, margin_sum.get('commitment', 0) * margin_rate_for_child, row_format_number)
            #     sum75tmpetalon += sum.get('commitment', 0)
            #     sheet.write_number(row, column + 1, sum.get('reserve', 0) * koeff_reserve, row_format_number)
            #     sheet.write_number(row, column + 1 + margin_shift , margin_sum.get('reserve', 0) * koeff_reserve * margin_rate_for_child, row_format_number)
            #     sum50tmpetalon += sum.get('reserve', 0) * koeff_reserve

            sum100tmp = self.get_sum_fact_acceptance_project_step_quater(project, step, year, False)
            margin100tmp = self.get_sum_fact_margin_project_step_quarter(project, step, year, False)

            if not next:
                if sum100tmp:
                    sheet.write_number(row, column + 0, sum100tmp, row_format_number_color_fact)
                if margin100tmp:
                    sheet.write_number(row, column + 0 + margin_shift, margin100tmp * margin_rate_for_child, row_format_number_color_fact)

            sum = self.get_sum_planned_acceptance_project_step_quater(project, step, year, False)
            margin_sum = self.get_sum_planned_margin_project_step_quater(project, step, year, False)

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

            sum_ostatok_acceptance = self.get_sum_planned_acceptance_project_step_from_distribution(project, step, year, False)
            new_margin_plan = self.get_sum_planned_margin_project_step_from_distribution(project, step, year, False, margin_plan, 1)

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
    def print_quater_planned_acceptance_project(self, sheet, row, column, element_name, project, step, year, row_format_number, row_format_number_color_fact,margin_shift,next):

        sum75tmpetalon = sum50tmpetalon = sum100tmp = sum75tmp = sum50tmp = 0
        if element_name in ('Q1','Q2','Q3','Q4'):
            # project_etalon = self.get_etalon_project(project, element_name)
            # step_etalon = self.get_etalon_step(step, element_name)

            if step == False:
                profitability = project.profitability
            else:
                profitability = step.profitability

            margin_rate_for_child = 1
            if project.is_child_project:
                margin_rate_for_child = (1 - project.margin_rate_for_parent)

            # sum = self.get_sum_planned_acceptance_project_step_quater(project_etalon, step_etalon, element_name)
            # margin_sum = self.get_sum_planned_margin_project_step_quater(project_etalon, step_etalon, element_name)
            # if step and not step_etalon:
            #     sum = {'commitment': 0, 'reserve': 0, 'potential': 0}
            #     margin_sum = {'commitment': 0, 'reserve': 0, 'potential': 0}

            # if sum:
            #     sheet.write_number(row, column + 0, sum.get('commitment', 0), row_format_number)
            #     sheet.write_number(row, column + 0 + margin_shift, margin_sum.get('commitment', 0) * margin_rate_for_child, row_format_number)
            #     sum75tmpetalon += sum.get('commitment', 0)
            #     sheet.write_number(row, column + 1, sum.get('reserve', 0) * koeff_reserve, row_format_number)
            #     sheet.write_number(row, column + 1 + margin_shift , margin_sum.get('reserve', 0) * koeff_reserve * margin_rate_for_child, row_format_number)
            #     sum50tmpetalon += sum.get('reserve', 0) * koeff_reserve

            sum100tmp = self.get_sum_fact_acceptance_project_step_quater(project, step, year, element_name)
            margin100tmp = self.get_sum_fact_margin_project_step_quarter(project, step, year, element_name)

            if not next:
                if sum100tmp:
                    sheet.write_number(row, column + 0, sum100tmp, row_format_number_color_fact)
                if margin100tmp:
                    sheet.write_number(row, column + 0 + margin_shift, margin100tmp * margin_rate_for_child, row_format_number_color_fact)

            sum = self.get_sum_planned_acceptance_project_step_quater(project, step, year, element_name)
            margin_sum = self.get_sum_planned_margin_project_step_quater(project, step, year, element_name)

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

            sum_ostatok_acceptance = self.get_sum_planned_acceptance_project_step_from_distribution(project, step, year, element_name)
            new_margin_plan = self.get_sum_planned_margin_project_step_from_distribution(project, step, year, element_name, margin_plan, 1)

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

    def print_row_values(self, workbook, sheet, row, column,  project, step, margin_shift, next_margin_shift):
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

        if step and step.estimated_probability_id.name not in ('100', '100(done)') or not step and project.estimated_probability_id.name not in ('100', '100(done)'):
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

        for shifts in plan_shift.values():
            sheet.write_string(row, shifts['NEXT'], "", head_format_month_itogo)
            sheet.write_string(row, shifts['AFTER_NEXT'], "", head_format_month_itogo)
        sheet.write_string(row, 217 + 0, "", row_format_number)
        sheet.write_string(row, 217 + 1, "", row_format_number)
        sheet.write_string(row, 217 + 2, "", row_format_number)
        sheet.write_string(row, 232 + 0, "", row_format_number)
        sheet.write_string(row, 232 + 1, "", row_format_number)
        sheet.write_string(row, 232 + 2, "", row_format_number)

        # печать Контрактование, с НДС
        for element in self.month_rus_name_contract_pds:
            column += 1
            sumQ75tmpetalon = sumQ50tmpetalon = sumQ100tmp = sumQ75tmp = sumQ50tmp = sumQ30tmp = 0

            if 'итого' in element:
                sheet.write_string(row, column, "", head_format_month_itogo)
                column += 1
            sheet.write_string(row, column + 0, "", row_format_number_color_fact)
            sheet.write_string(row, column + 1, "", row_format_number)
            sheet.write_string(row, column + 2, "", row_format_number)
            sheet.write_string(row, column + 3, "", row_format_number)
            fact_columns.add(column)

            sumQ75tmpetalon, sumQ50tmpetalon, sumQ100tmp, sumQ75tmp, sumQ50tmp, sumQ30tmp= self.print_month_revenue_project(sheet, row, column, self.get_month_number_rus(element),
                                                                                    project,step, YEARint, row_format_number, row_format_number_color_fact, False)
            _, _, _, _, _, _= self.print_month_revenue_project(sheet, row, 217, self.get_month_number_rus(element),
                                                                                    project,step, YEARint + 1, row_format_number, row_format_number_color_fact, True)
            _, _, _, _, _, _= self.print_month_revenue_project(sheet, row, 232, self.get_month_number_rus(element),
                                                                                    project,step, YEARint + 2, row_format_number, row_format_number_color_fact, True)
            sumQ75etalon += sumQ75tmpetalon
            sumQ50etalon += sumQ50tmpetalon
            sumQ100 += sumQ100tmp
            sumQ75 += sumQ75tmp
            sumQ50 += sumQ50tmp
            sumQ30 += sumQ30tmp

            if element.find('Q') != -1: #'Q1 итого' 'Q2 итого' 'Q3 итого' 'Q4 итого'
                # if sumQ75etalon != 0 : sheet.write_number(row, column + 0, sumQ75etalon, row_format_number)
                # if sumQ50etalon != 0 : sheet.write_number(row, column + 1, sumQ50etalon, row_format_number)
                # if sumQ100 != 0 :      sheet.write_number(row, column + 2, sumQ100, row_format_number_color_fact)
                # if sumQ75 != 0 :       sheet.write_number(row, column + 3, sumQ75, row_format_number)
                # if sumQ50 != 0 :       sheet.write_number(row, column + 4, sumQ50, row_format_number)

                formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1,xl_col_to_name(column - 13),xl_col_to_name(column - 9),xl_col_to_name(column - 5))
                sheet.write_formula(row, column + 0,formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1,xl_col_to_name(column - 12),xl_col_to_name(column - 8),xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 1,formula, row_format_number)
                formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1,xl_col_to_name(column - 11),xl_col_to_name(column - 7),xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 2,formula, row_format_number)
                formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1,xl_col_to_name(column - 10),xl_col_to_name(column - 6),xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 3,formula, row_format_number)

                sumHY100etalon += sumQ100etalon
                sumHY75etalon += sumQ75etalon
                sumHY50etalon += sumQ50etalon
                sumHY100 += sumQ100
                sumHY75 += sumQ75
                sumHY50 += sumQ50
                sumHY30 += sumQ30
                sumQ100etalon = sumQ75etalon = sumQ50etalon = sumQ100 = sumQ75  = sumQ50  = sumQ50 = 0

            if element.find('HY') != -1:  # 'HY1/YEAR итого' 'HY2/YEAR итого'
                # if sumHY75etalon != 0: sheet.write_number(row, column + 0, sumHY75etalon, row_format_number)
                # if sumHY50etalon != 0: sheet.write_number(row, column + 1, sumHY50etalon, row_format_number)
                # if sumHY100 != 0:      sheet.write_number(row, column + 2, sumHY100, row_format_number_color_fact)
                # if sumHY75 != 0:       sheet.write_number(row, column + 3, sumHY75, row_format_number)
                # if sumHY50 != 0:       sheet.write_number(row, column + 4, sumHY50, row_format_number)
                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 27),xl_col_to_name(column - 6))
                # sheet.write_formula(row, column + 0, formula, row_format_number)
                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 26),xl_col_to_name(column - 5))
                # sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 22),xl_col_to_name(column - 5))
                sheet.write_formula(row, column + 0, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 21),xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 20),xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 2, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 19),xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 3, formula, row_format_number)


                sumYear100etalon += sumHY100etalon
                sumYear75etalon += sumHY75etalon
                sumYear50etalon += sumHY50etalon
                sumYear100 += sumHY100
                sumYear75 += sumHY75
                sumYear50 += sumHY50
                sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0

            if element == 'YEAR итого':  # 'YEAR итого'
                # if sumYear75etalon != 0: sheet.write_number(row, column + 0, sumYear75etalon, row_format_number)
                # if sumYear50etalon != 0: sheet.write_number(row, column + 1, sumYear50etalon, row_format_number)
                # if sumYear100 != 0:      sheet.write_number(row, column + 2, sumYear100, row_format_number_color_fact)
                # if sumYear75 != 0:       sheet.write_number(row, column + 3, sumYear75, row_format_number)
                # # if sumYear50 != 0:       sheet.write_number(row, column + 4, sumYear50, row_format_number)
                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 54), xl_col_to_name(column - 6))
                # sheet.write_formula(row, column + 0, formula, row_format_number)
                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 53), xl_col_to_name(column - 5))
                # sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 44), xl_col_to_name(column - 5))
                sheet.write_formula(row, column + 0, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 43), xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 42), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 2, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 41), xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 3, formula, row_format_number)
            column += 3
        #end печать Контрактование, с НДС
        # Поступление денежных средсв, с НДС
        sumYear100etalon = sumYear75etalon = sumYear50etalon = sumYear100 = sumYear75 = sumYear50 = 0
        sumQ100etalon = sumQ75etalon = sumQ50etalon = sumQ100 = sumQ75 = sumQ50 = 0
        sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0

        for element in self.month_rus_name_contract_pds:
            column += 1
            sumQ75tmpetalon = sumQ50tmpetalon = sumQ100tmp = sumQ75tmp = sumQ50tmp = 0

            if element.find('итого') != -1:
                sheet.write_string(row, column, "", head_format_month_itogo)
                column += 1
            sheet.write_string(row, column + 0, "", row_format_number_color_fact)
            sheet.write_string(row, column + 1, "", row_format_number)
            sheet.write_string(row, column + 2, "", row_format_number)
            fact_columns.add(column)


            sumQ75tmpetalon, sumQ50tmpetalon, sumQ100tmp, sumQ75tmp, sumQ50tmp = self.print_month_pds_project(sheet, row, column, self.get_month_number_rus(element)
                                                                                        ,project, step, YEARint, row_format_number, row_format_number_color_fact, False)
            # _, _, _, _, _ = self.print_year_pds_project(sheet, row, 221, project, step, YEARint + 1, row_format_number, row_format_number_color_fact, True)
            # _, _, _, _, _ = self.print_yesr_pds_project(sheet, row, 236, project, step, YEARint + 2, row_format_number, row_format_number_color_fact, True)

            sumQ75etalon += sumQ75tmpetalon
            sumQ50etalon += sumQ50tmpetalon
            sumQ100 += sumQ100tmp
            sumQ75 += sumQ75tmp
            sumQ50 += sumQ50tmp

            if element.find('Q') != -1:  # 'Q1 итого' 'Q2 итого' 'Q3 итого' 'Q4 итого'
                # if sumQ75etalon != 0: sheet.write_number(row, column + 0, sumQ75etalon, row_format_number)
                # if sumQ50etalon != 0: sheet.write_number(row, column + 1, sumQ50etalon, row_format_number)
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
                # formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1, xl_col_to_name(column - 16),xl_col_to_name(column - 11), xl_col_to_name(column - 6))
                # sheet.write_formula(row, column + 0, formula, row_format_number)
                # formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1, xl_col_to_name(column - 15),xl_col_to_name(column - 10), xl_col_to_name(column - 5))
                # sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1, xl_col_to_name(column - 10),xl_col_to_name(column - 7), xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 0, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1, xl_col_to_name(column - 9),xl_col_to_name(column - 6), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1, xl_col_to_name(column - 8),xl_col_to_name(column - 5), xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 2, formula, row_format_number)

            if element.find('HY') != -1:  # 'HY1/YEAR итого' 'HY2/YEAR итого'
                # if sumHY75etalon != 0: sheet.write_number(row, column + 0, sumHY75etalon, row_format_number)
                # if sumHY50etalon != 0: sheet.write_number(row, column + 1, sumHY50etalon, row_format_number)
                # if sumHY100 != 0:      sheet.write_number(row, column + 2, sumHY100, row_format_number_color_fact)
                # if sumHY75 != 0:       sheet.write_number(row, column + 3, sumHY75, row_format_number)
                # if sumHY50 != 0:       sheet.write_number(row, column + 4, sumHY50, row_format_number)
                sumYear100etalon += sumHY100etalon
                sumYear75etalon += sumHY75etalon
                sumYear50etalon += sumHY50etalon
                sumYear100 += sumHY100
                sumYear75 += sumHY75
                sumYear50 += sumHY50
                sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0
                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 27), xl_col_to_name(column - 6))
                # sheet.write_formula(row, column + 0, formula, row_format_number)
                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 26), xl_col_to_name(column - 5))
                # sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 17), xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 0, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 16), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 15), xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 2, formula, row_format_number)

            if element == 'YEAR итого':  # 'YEAR итого'
                # if sumYear75etalon != 0: sheet.write_number(row, column + 0, sumYear75etalon, row_format_number)
                # if sumYear50etalon != 0: sheet.write_number(row, column + 1, sumYear50etalon, row_format_number)
                # if sumYear100 != 0:      sheet.write_number(row, column + 2, sumYear100, row_format_number_color_fact)
                # if sumYear75 != 0:       sheet.write_number(row, column + 3, sumYear75, row_format_number)
                # if sumYear50 != 0:       sheet.write_number(row, column + 4, sumYear50, row_format_number)
                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 54), xl_col_to_name(column - 6))
                # sheet.write_formula(row, column + 0, formula, row_format_number)
                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 53), xl_col_to_name(column - 5))
                # sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 34), xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 0, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 33), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 32), xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 2, formula, row_format_number)
            column += 2
        _, _, _, _, _ = self.print_year_pds_project(sheet, row, 221, project, step, YEARint + 1, row_format_number,
                                                    row_format_number_color_fact, True)
        _, _, _, _, _ = self.print_year_pds_project(sheet, row, 236, project, step, YEARint + 2, row_format_number,
                                                    row_format_number_color_fact, True)

        # end Поступление денежных средсв, с НДС

        # Валовая Выручка, без НДС
        sumYear100etalon = sumYear75etalon = sumYear50etalon = sumYear100 = sumYear75 = sumYear50 = 0
        sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0

        if step == False:
            profitability = project.profitability
        else:
            profitability = step.profitability

        # project_etalon = self.get_etalon_project(project, False)
        # step_etalon = self.get_etalon_step(step, False)
        #
        # if step_etalon == False:
        #     profitability_etalon = project_etalon.profitability
        # else:
        #     profitability_etalon = step_etalon.profitability

        for element in self.month_rus_name_revenue_margin:
            column += 1
            sheet.write_string(row, column, "", head_format_month_itogo)
            sheet.write_string(row, column + margin_shift, "", head_format_month_itogo)
            if element.find('HY2') != -1:
                addcolumn = 1
                column += 1
                sheet.write_string(row, column, "", head_format_month_itogo)
                sheet.write_string(row, column + margin_shift, "", head_format_month_itogo)
            column += 1
            # sheet.write_string(row, column + 0, "", row_format_number)
            # sheet.write_string(row, column + 1, "", row_format_number)
            sheet.write_string(row, column + 0, "", row_format_number_color_fact)
            sheet.write_string(row, column + 1, "", row_format_number)
            sheet.write_string(row, column + 2, "", row_format_number)
            # sheet.write_string(row, column + 0 + margin_shift, "", row_format_number)
            # sheet.write_string(row, column + 1 + margin_shift, "", row_format_number)
            sheet.write_string(row, column + 0 + margin_shift, "", row_format_number_color_fact)
            sheet.write_string(row, column + 1 + margin_shift, "", row_format_number)
            sheet.write_string(row, column + 2 + margin_shift, "", row_format_number)
            fact_columns.add(column)
            fact_columns.add(column + margin_shift)

            sumQ75etalon, sumQ50etalon, sumQ100, sumQ75, sumQ50 = self.print_quater_planned_acceptance_project(sheet,row,column,element
                                                                                                              ,project,step,YEARint,row_format_number,row_format_number_color_fact,margin_shift, False)

            sumHY100etalon += sumQ100etalon
            sumHY75etalon += sumQ75etalon
            sumHY50etalon += sumQ50etalon
            sumHY100 += sumQ100
            sumHY75 += sumQ75
            sumHY50 += sumQ50

            if element.find('HY') != -1:  # 'HY1/YEAR итого' 'HY2/YEAR итого'
                # if sumHY75etalon != 0:
                #     sheet.write_number(row, column + 0, sumHY75etalon, row_format_number)
                #     sheet.write_number(row, column + 0 + margin_shift, sumHY75etalon*profitability_etalon / 100, row_format_number)
                # if sumHY50etalon != 0:
                #     sheet.write_number(row, column + 1, sumHY50etalon, row_format_number)
                #     sheet.write_number(row, column + 1 + margin_shift, sumHY50etalon*profitability_etalon / 100, row_format_number)
                # if sumHY100 != 0:
                #     sheet.write_number(row, column + 2, sumHY100, row_format_number_color_fact)
                #     sheet.write_number(row, column + 2 + margin_shift, sumHY100*profitability / 100, row_format_number_color_fact)
                # if sumHY75 != 0:
                #     sheet.write_number(row, column + 3, sumHY75, row_format_number)
                #     sheet.write_number(row, column + 3 + margin_shift, sumHY75*profitability / 100, row_format_number)
                # if sumHY50 != 0:
                #     sheet.write_number(row, column + 4, sumHY50, row_format_number)
                #     sheet.write_number(row, column + 4 + margin_shift, sumHY50*profitability / 100, row_format_number)
                addcolumn = 0
                if element.find('HY2') != -1:
                    addcolumn = 1

                sumYear100etalon += sumHY100etalon
                sumYear75etalon += sumHY75etalon
                sumYear50etalon += sumHY50etalon
                sumYear100 += sumHY100
                sumYear75 += sumHY75
                sumYear50 += sumHY50
                sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0

                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 12 - addcolumn), xl_col_to_name(column - 6 - addcolumn))
                # sheet.write_formula(row, column + 0, formula, row_format_number)
                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 11 - addcolumn), xl_col_to_name(column - 5 - addcolumn))
                # sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8 - addcolumn), xl_col_to_name(column - 4 - addcolumn))
                sheet.write_formula(row, column + 0, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 7 - addcolumn),  xl_col_to_name(column - 3 - addcolumn))
                sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 6 - addcolumn),  xl_col_to_name(column - 2 - addcolumn))
                sheet.write_formula(row, column + 2, formula, row_format_number)

                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 12 + margin_shift - addcolumn), xl_col_to_name(column - 6 + margin_shift - addcolumn))
                # sheet.write_formula(row, column + 0 + margin_shift, formula, row_format_number)
                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 11 + margin_shift - addcolumn), xl_col_to_name(column - 5 + margin_shift - addcolumn))
                # sheet.write_formula(row, column + 1 + margin_shift, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8 + margin_shift - addcolumn), xl_col_to_name(column - 4 + margin_shift - addcolumn))
                sheet.write_formula(row, column + 0 + margin_shift, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 7 + margin_shift - addcolumn),  xl_col_to_name(column - 3 + margin_shift - addcolumn))
                sheet.write_formula(row, column + 1 + margin_shift, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 6 + margin_shift - addcolumn),  xl_col_to_name(column - 2 + margin_shift - addcolumn))
                sheet.write_formula(row, column + 2 + margin_shift, formula, row_format_number)



            if element == 'YEAR итого':  # 'YEAR итого'
                # if sumYear75etalon != 0:
                #     sheet.write_number(row, column + 0, sumYear75etalon, row_format_number)
                #     sheet.write_number(row, column + 0 + margin_shift, sumYear75etalon*profitability / 100, row_format_number)
                # if sumYear50etalon != 0:
                #     sheet.write_number(row, column + 1, sumYear50etalon, row_format_number)
                #     sheet.write_number(row, column + 1 + margin_shift, sumYear50etalon*profitability / 100, row_format_number)
                # if sumYear100 != 0:
                #     sheet.write_number(row, column + 2, sumYear100, row_format_number_color_fact)
                #     sheet.write_number(row, column + 2 + margin_shift, sumYear100*profitability / 100, row_format_number_color_fact)
                # if sumYear75 != 0:
                #     sheet.write_number(row, column + 3, sumYear75, row_format_number)
                #     sheet.write_number(row, column + 3 + margin_shift, sumYear75*profitability / 100, row_format_number)
                # if sumYear50 != 0:
                #     sheet.write_number(row, column + 4, sumYear50, row_format_number)
                #     sheet.write_number(row, column + 4 + margin_shift, sumYear50*profitability / 100, row_format_number)
                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 25), xl_col_to_name(column - 6))
                # sheet.write_formula(row, column + 0, formula, row_format_number)
                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 24), xl_col_to_name(column - 5))
                # sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 17), xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 0, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 16), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 15), xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 2, formula, row_format_number)

                self.print_acceptance_potential(sheet, row, column, project, step, YEARint, row_format_number)
                self.print_acceptance_potential(sheet, row, 223, project, step, YEARint + 1, row_format_number)
                self.print_acceptance_potential(sheet, row, 238, project, step, YEARint + 2, row_format_number)

                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 25 + margin_shift), xl_col_to_name(column - 6 + margin_shift))
                # sheet.write_formula(row, column + 0 + margin_shift, formula, row_format_number)
                # formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 24 + margin_shift), xl_col_to_name(column - 5 + margin_shift))
                # sheet.write_formula(row, column + 1 + margin_shift, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 17 + margin_shift), xl_col_to_name(column - 4 + margin_shift))
                sheet.write_formula(row, column + 0 + margin_shift, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 16 + margin_shift), xl_col_to_name(column - 3 + margin_shift))
                sheet.write_formula(row, column + 1 + margin_shift, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 15 + margin_shift), xl_col_to_name(column - 2 + margin_shift))
                sheet.write_formula(row, column + 2 + margin_shift, formula, row_format_number)

            column += 2
        _, _, _, _, _ = self.print_year_planned_acceptance_project(sheet,row,224,project,step,YEARint + 1,row_format_number,row_format_number_color_fact,next_margin_shift, True)
        _, _, _, _, _ = self.print_year_planned_acceptance_project(sheet,row,239,project,step,YEARint + 2,row_format_number,row_format_number_color_fact,next_margin_shift, True)

        # end Валовая Выручка, без НДС

    def print_acceptance_potential(self, sheet, row, column, project, step, year, format):
        year_acceptance_30 = 0
        if step:
            potential_acceptances = (self.env['project_budget.planned_acceptance_flow'].
                                     search(['&', '&', '&',
                                             ('project_steps_id', '=', step.id),
                                             ('date_cash', '>=', datetime.date(year, 1, 1)),
                                             ('date_cash', '<=', datetime.date(year, 12, 31)),
                                             '|', '&', ('forecast', '=', 'potential'),
                                             ('project_steps_id.estimated_probability_id.name', '!=', '0'),
                                             '&', ('forecast', '=', 'from_project'),
                                             ('project_steps_id.estimated_probability_id.name', '=', '30'),
                                             ]))
            if potential_acceptances:
                for acceptance in potential_acceptances:
                    year_acceptance_30 += acceptance.sum_cash_without_vat
            elif step.estimated_probability_id.name == '30' and step.end_sale_project_month.year == year:
                year_acceptance_30 = step.total_amount_of_revenue
        else:
            potential_acceptances = (self.env['project_budget.planned_acceptance_flow'].
                                     search(['&', '&', '&',
                                             ('projects_id', '=', project.id),
                                             ('date_cash', '>=', datetime.date(year, 1, 1)),
                                             ('date_cash', '<=', datetime.date(year, 12, 31)),
                                             '|', '&', ('forecast', '=', 'potential'),
                                             ('projects_id.estimated_probability_id.name', '!=', '0'),
                                             '&', ('forecast', '=', 'from_project'),
                                             ('projects_id.estimated_probability_id.name', '=', '30'),
                                             ]))
            if potential_acceptances:
                for acceptance in potential_acceptances:
                    year_acceptance_30 += acceptance.sum_cash_without_vat
            elif project.estimated_probability_id.name == '30' and project.end_sale_project_month.year == year:
                year_acceptance_30 = project.total_amount_of_revenue

        sheet.write_number(row, column + 3, year_acceptance_30, format)

    def print_estimated_rows(self, sheet, row, format, format_cross):

        for colFormula in range(2, 9):
            sheet.write_string(row, colFormula, '', format)

        for colFormula in list(range(9, 215)) + list(range(216, 230)) + list(range(231, 245)):
            sheet.write_string(row, colFormula, '', format)

        for type in plan_shift:  # формулы расчетных планов
            start_column = 9
            if type in ('revenue', 'pds'):
                shift = 0
                if type == 'revenue':
                    width = 4
                elif type == 'pds':
                    start_column += 83
                    width = 3
                for element in range(len(self.month_rus_name_contract_pds)):
                    if element in [3, 7, 8, 12, 16, 17, 18]:  # учитываем колонки планов
                        shift += 1
                    formula = '={1}{0}+{2}{0}*D1+{3}{0}*D2'.format(
                        row,
                        xl_col_to_name(start_column + shift + element * width),
                        xl_col_to_name(start_column + shift + element * width + 1),
                        xl_col_to_name(start_column + shift + element * width + 2),
                    )
                    sheet.merge_range(
                        row,
                        start_column + shift + element * width,
                        row,
                        start_column + shift + element * width + 2,
                        formula,
                        format
                    )
                    if type == 'revenue':
                        sheet.write_string(row, start_column + shift + element * width + 3, '',
                                           format_cross)
            else:
                shift = 0
                if type == 'acceptance':
                    start_column += 148
                    width = 4
                elif type == 'margin':
                    start_column += 178
                    width = 4
                for element in range(len(self.month_rus_name_revenue_margin)):
                    if element in [5]:  # учитываем колонки планов
                        shift += 1
                    formula = '={1}{0}+{2}{0}*D1+{3}{0}*D2'.format(
                        row,
                        xl_col_to_name(start_column + shift + element * width),
                        xl_col_to_name(start_column + shift + element * width + 1),
                        xl_col_to_name(start_column + shift + element * width + 2),
                    )
                    sheet.merge_range(
                        row,
                        start_column + shift + element * width,
                        row,
                        start_column + shift + element * width + 2,
                        formula,
                        format
                    )
                if type == 'acceptance':
                    sheet.write_string(row, start_column + shift + element * width + 3, '',
                                       format_cross)
        for type,shifts in plan_shift.items():
            formula = '={1}{0}*D1+{2}{0}*D2'.format(
                row,
                xl_col_to_name(shifts['NEXT'] + 1),
                xl_col_to_name(shifts['NEXT'] + 2),
            )
            sheet.merge_range(row, shifts['NEXT'] + 1, row, shifts['NEXT'] + 2, formula, format)
            formula = '={1}{0}*D1+{2}{0}*D2'.format(
                row,
                xl_col_to_name(shifts['AFTER_NEXT'] + 1),
                xl_col_to_name(shifts['AFTER_NEXT'] + 2),
            )
            sheet.merge_range(row, shifts['AFTER_NEXT'] + 1, row, shifts['AFTER_NEXT'] + 2, formula, format)
            if type in ('revenue', 'acceptance'):
                sheet.write_string(row, shifts['NEXT'] + 3, '', format_cross)
                sheet.write_string(row, shifts['AFTER_NEXT'] + 3, '', format_cross)

    def print_row(self, sheet, workbook, project_offices, project_managers, estimated_probabilitys, budget, row, formulaItogo, level):
        global YEARint
        global dict_formula
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

        # if isdebug:
        #     logger.info(f' def print_row | office_parent_id = { office_parent_id }')

        #project_offices = self.env['project_budget.project_office'].search([],order='name')  # для сортировки так делаем + берем сначала только верхние элементы

        isFoundProjectsByOffice = False
        isFoundProjectsByManager = False
        begRowProjectsByManager = 0

        cur_budget_projects = self.env['project_budget.projects'].search([
            ('commercial_budget_id', '=', budget.id),
        ])

        # cur_project_offices = project_offices.filtered(lambda r: r in cur_budget_projects.project_office_id or r in {office.parent_id for office in cur_budget_projects.project_office_id if office.parent_id in project_offices})
        cur_project_offices = project_offices
        cur_project_managers = project_managers.filtered(lambda r: r in cur_budget_projects.project_manager_id)
        cur_estimated_probabilities = estimated_probabilitys.filtered(lambda r: r in cur_budget_projects.estimated_probability_id)
        # print('cur_budget_projects=',cur_budget_projects)
        # print('****')
        # print('project_offices=',project_offices)
        # print('project_managers=',project_managers)
        # print('cur_project_offices=',cur_project_offices)
        # print('cur_project_managers=', cur_project_managers)
        # print('cur_estimated_probabilities=', cur_estimated_probabilities)

        for project_office in cur_project_offices:
            print('project_office.name = ', project_office.name)
            row0 = row

            child_project_offices = self.env['project_budget.project_office'].search([('parent_id', '=', project_office.id)], order='name')

            row0, formulaItogo = self.print_row(sheet, workbook, child_project_offices, project_managers, estimated_probabilitys, budget, row, formulaItogo, level)

            isFoundProjectsByOffice = False
            if row0 != row:
                isFoundProjectsByOffice = True

            row = row0

            formulaProjectOffice = '=sum(0'
            for project_manager in cur_project_managers:
                #print('project_manager = ', project_manager.name)
                isFoundProjectsByManager = False
                begRowProjectsByManager = 0
                formulaProjectManager = '=sum(0'
                column = -1
                for estimated_probability in cur_estimated_probabilities:
                    isFoundProjectsByProbability = False
                    begRowProjectsByProbability = 0

                    # print('estimated_probability.name = ', estimated_probability.name)
                    # print('estimated_probability.code = ', estimated_probability.code)

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
                        if spec.id in dict_formula['printed_projects']:
                            continue
                        if not ((spec.project_office_id == project_office or (spec.legal_entity_signing_id.different_project_offices_in_steps and spec.project_have_steps)) and spec.project_manager_id == project_manager):
                            continue
                        # if spec.estimated_probability_id.name != '0':
                        # if spec.is_framework == True and spec.project_have_steps == False: continue # рамка без этапов - пропускаем
                        if spec.vgo == '-':
                            cur_project_rate = self.get_currency_rate_by_project(spec)

                            if begRowProjectsByManager == 0:
                                begRowProjectsByManager = row

                            if begRowProjectsByProbability == 0:
                                begRowProjectsByProbability = row

                            if spec.project_have_steps:
                                for step in spec.project_steps_ids:
                                    if step.id in dict_formula['printed_steps']:
                                        continue

                                    if ((spec.legal_entity_signing_id.different_project_offices_in_steps and step.project_office_id == project_office)
                                            or ((not spec.legal_entity_signing_id.different_project_offices_in_steps or not step.project_office_id) and spec.project_office_id == project_office)):

                                        if step.estimated_probability_id == estimated_probability:
                                            if self.isStepinYear(spec, step) == False:
                                                continue
                                            isFoundProjectsByManager = True
                                            isFoundProjectsByOffice = True
                                            isFoundProjectsByProbability = True

                                            row += 1
                                            sheet.set_row(row, False, False, {'hidden': 1, 'level': level + 2})
                                            cur_row_format = row_format
                                            cur_row_format_number = row_format_number
                                            cur_row_format_date = row_format_date
                                            if step.estimated_probability_id.name == '0':
                                                cur_row_format = row_format_canceled_project
                                                cur_row_format_number = row_format_number_canceled_project
                                                cur_row_format_date = row_format_date_canceled_project
                                            column = 0
                                            if spec.legal_entity_signing_id.different_project_offices_in_steps and step.project_office_id:
                                                sheet.write_string(row, column, step.project_office_id.name, cur_row_format)
                                            else:
                                                sheet.write_string(row, column, spec.project_office_id.name, cur_row_format)
                                            column += 1
                                            sheet.write_string(row, column, spec.project_manager_id.name, cur_row_format)
                                            column += 1
                                            sheet.write_string(row, column, spec.partner_id.name, cur_row_format)
                                            column += 1
                                            sheet.write_string(row, column, (step.essence_project or ''), cur_row_format)
                                            column += 1
                                            sheet.write_string(row, column, (step.code or '') +' | '+ spec.project_id + " | " + step.step_id, cur_row_format)
                                            column += 1
                                            sheet.write_number(row, column, step.total_amount_of_revenue_with_vat*cur_project_rate, cur_row_format_number)
                                            column += 1
                                            if step.estimated_probability_id.name == '100':
                                                sheet.write_datetime(row, column, step.end_presale_project_month, cur_row_format_date)
                                            else:
                                                sheet.write(row, column, None, cur_row_format)
                                            column += 1
                                            sheet.write_number(row, column, step.profitability, cur_row_format_number)
                                            column += 1
                                            sheet.write_string(row, column, '', head_format_1)
                                            self.print_row_values(workbook, sheet, row, column,  spec, step, 30, 4)
                                            dict_formula['printed_steps'].add(step.id)
                            else:
                                if spec.project_office_id == project_office and spec.estimated_probability_id == estimated_probability:
                                    if self.isProjectinYear(spec) == False:
                                        continue
                                    row += 1
                                    isFoundProjectsByManager = True
                                    isFoundProjectsByOffice = True
                                    isFoundProjectsByProbability = True
                                    sheet.set_row(row, False, False, {'hidden': 1, 'level': level + 2})
                                    cur_row_format = row_format
                                    cur_row_format_number = row_format_number
                                    cur_row_format_date = row_format_date
                                    if spec.estimated_probability_id.name == '0':
                                        cur_row_format = row_format_canceled_project
                                        cur_row_format_number = row_format_number_canceled_project
                                        cur_row_format_date = row_format_date_canceled_project
                                    column = 0
                                    sheet.write_string(row, column, spec.project_office_id.name, cur_row_format)
                                    column += 1
                                    sheet.write_string(row, column, spec.project_manager_id.name, cur_row_format)
                                    column += 1
                                    sheet.write_string(row, column, spec.partner_id.name, cur_row_format)
                                    column += 1
                                    sheet.write_string(row, column, (spec.essence_project or ''), cur_row_format)
                                    column += 1
                                    sheet.write_string(row, column, (spec.step_project_number or '')+ ' | ' +(spec.project_id or ''), cur_row_format)
                                    column += 1
                                    sheet.write_number(row, column, spec.total_amount_of_revenue_with_vat*cur_project_rate, cur_row_format_number)
                                    column += 1
                                    if spec.estimated_probability_id.name == '100':
                                        sheet.write_datetime(row, column, spec.end_presale_project_month, cur_row_format_date)
                                    else:
                                        sheet.write(row, column, None, cur_row_format)
                                    column += 1
                                    sheet.write_number(row, column, spec.profitability, cur_row_format_number)
                                    column += 1
                                    sheet.write_string(row, column, '', head_format_1)
                                    self.print_row_values(workbook, sheet, row, column,  spec, False, 30, 4)
                                    dict_formula['printed_projects'].add(spec.id)

                    if isFoundProjectsByProbability:
                        row += 1
                        column = 0
                        sheet.write_string(row, column, project_manager.name + ' ' + estimated_probability.name
                                           + ' %', row_format_probability)
                        sheet.write_string(row, column + 1, project_manager.name + ' ' + estimated_probability.name
                                           + ' %', row_format_probability)
                        sheet.set_row(row, False, False, {'hidden': 1, 'level': level + 2})

                        formulaProjectManager = formulaProjectManager + ',{0}' + str(row + 1)
                        for colFormula in range(2, 9):
                            sheet.write_string(row, colFormula, '', row_format_probability)
                        for colFormula in list(range(9, 215)) + list(range(216, 230)) + list(range(231, 245)):
                            formula = '=sum({2}{0}:{2}{1})'.format(begRowProjectsByProbability + 2, row,
                                                                   xl_col_to_name(colFormula))
                            if colFormula in fact_columns and estimated_probability.name not in ('100', '100(done)'):
                                sheet.write_formula(row, colFormula, formula, row_format_fact_cross)  # кресты в фактах где вероятности < 100
                            else:
                                sheet.write_formula(row, colFormula, formula, row_format_probability)

                        for type in plan_shift: # кресты в планах
                            for c in plan_shift[type].values():
                                sheet.write_string(row, c, '', row_format_plan_cross)

                if isFoundProjectsByManager:
                    row += 1
                    column = 0
                    sheet.write_string(row, column, 'ИТОГО: ' + project_manager.name, row_format_manager)
                    sheet.write_string(row, column + 1, 'ИТОГО: ' + project_manager.name, row_format_manager)
                    sheet.set_row(row, False, False, {'hidden': 1, 'level': level + 1})
                    # print('setrow manager  row = ', row)
                    # print('setrow manager level = ', level)

                    formulaProjectOffice = formulaProjectOffice + ',{0}'+str(row + 1)

                    for colFormula in range(2, 9):
                        sheet.write_string(row, colFormula, '', row_format_manager)

                    for colFormula in list(range(9, 215)) + list(range(216, 230)) + list(range(231, 245)):
                        formula = formulaProjectManager.format(xl_col_to_name(colFormula)) + ')'
                        sheet.write_formula(row, colFormula, formula, row_format_manager)

                    # расчетный план КАМа
                    row += 1
                    column = 0
                    sheet.write_string(row, column, 'ИТОГО: Расчетный План по ' + project_manager.name, row_format_manager_estimated_plan_left)
                    sheet.write_string(row, column + 1, 'ИТОГО: Расчетный План по ' + project_manager.name, row_format_manager_estimated_plan_left)
                    sheet.set_row(row, False, False, {'hidden': 1, 'level': level})

                    self.print_estimated_rows(sheet, row, row_format_manager_estimated_plan, row_format_manager_estimated_plan_cross)

                    for type in plan_shift: # кресты в планах
                        for c in plan_shift[type].values():
                            sheet.write_string(row - 1, c, '', row_format_plan_cross)
                            sheet.write_string(row, c, '', row_format_plan_cross)

                    # планы КАМов
                    plan_revenue = self.env['project_budget.budget_plan_kam_spec'].search([
                        ('budget_plan_kam_id.year', '=', YEARint),
                        ('budget_plan_kam_id.kam_id', '=', project_manager.id),
                        ('type_row', '=', 'contracting'),
                    ])
                    plan_pds = self.env['project_budget.budget_plan_kam_spec'].search([
                        ('budget_plan_kam_id.year', '=', YEARint),
                        ('budget_plan_kam_id.kam_id', '=', project_manager.id),
                        ('type_row', '=', 'cash'),
                    ])
                    plan_acceptance = self.env['project_budget.budget_plan_kam_spec'].search([
                        ('budget_plan_kam_id.year', '=', YEARint),
                        ('budget_plan_kam_id.kam_id', '=', project_manager.id),
                        ('type_row', '=', 'acceptance'),
                    ])
                    plan_margin = self.env['project_budget.budget_plan_kam_spec'].search([
                        ('budget_plan_kam_id.year', '=', YEARint),
                        ('budget_plan_kam_id.kam_id', '=', project_manager.id),
                        ('type_row', '=', 'margin_income'),
                    ])

                    plan_revenue_next = self.env['project_budget.budget_plan_kam_spec'].search([
                        ('budget_plan_kam_id.year', '=', YEARint + 1),
                        ('budget_plan_kam_id.kam_id', '=', project_manager.id),
                        ('type_row', '=', 'contracting'),
                    ])
                    plan_pds_next = self.env['project_budget.budget_plan_kam_spec'].search([
                        ('budget_plan_kam_id.year', '=', YEARint + 1),
                        ('budget_plan_kam_id.kam_id', '=', project_manager.id),
                        ('type_row', '=', 'cash'),
                    ])
                    plan_acceptance_next = self.env['project_budget.budget_plan_kam_spec'].search([
                        ('budget_plan_kam_id.year', '=', YEARint + 1),
                        ('budget_plan_kam_id.kam_id', '=', project_manager.id),
                        ('type_row', '=', 'acceptance'),
                    ])
                    plan_margin_next = self.env['project_budget.budget_plan_kam_spec'].search([
                        ('budget_plan_kam_id.year', '=', YEARint + 1),
                        ('budget_plan_kam_id.kam_id', '=', project_manager.id),
                        ('type_row', '=', 'margin_income'),
                    ])
                    plan_revenue_after_next = self.env['project_budget.budget_plan_kam_spec'].search([
                        ('budget_plan_kam_id.year', '=', YEARint + 2),
                        ('budget_plan_kam_id.kam_id', '=', project_manager.id),
                        ('type_row', '=', 'contracting'),
                    ])
                    plan_pds_after_next = self.env['project_budget.budget_plan_kam_spec'].search([
                        ('budget_plan_kam_id.year', '=', YEARint + 2),
                        ('budget_plan_kam_id.kam_id', '=', project_manager.id),
                        ('type_row', '=', 'cash'),
                    ])
                    plan_acceptance_after_next = self.env['project_budget.budget_plan_kam_spec'].search([
                        ('budget_plan_kam_id.year', '=', YEARint + 2),
                        ('budget_plan_kam_id.kam_id', '=', project_manager.id),
                        ('type_row', '=', 'acceptance'),
                    ])
                    plan_margin_after_next = self.env['project_budget.budget_plan_kam_spec'].search([
                        ('budget_plan_kam_id.year', '=', YEARint + 2),
                        ('budget_plan_kam_id.kam_id', '=', project_manager.id),
                        ('type_row', '=', 'margin_income'),
                    ])

                    for plan in (
                            {'column': plan_shift['revenue']['Q1'], 'formula': f'{plan_revenue.q1_plan}'},
                            {'column': plan_shift['revenue']['Q2'], 'formula': f'{plan_revenue.q2_plan}'},
                            {'column': plan_shift['revenue']['Q3'], 'formula': f'{plan_revenue.q3_plan}'},
                            {'column': plan_shift['revenue']['Q4'], 'formula': f'{plan_revenue.q4_plan}'},
                            {'column': plan_shift['pds']['Q1'], 'formula': f'{plan_pds.q1_plan}'},
                            {'column': plan_shift['pds']['Q2'], 'formula': f'{plan_pds.q2_plan}'},
                            {'column': plan_shift['pds']['Q3'], 'formula': f'{plan_pds.q3_plan}'},
                            {'column': plan_shift['pds']['Q4'], 'formula': f'{plan_pds.q4_plan}'},
                            {'column': plan_shift['acceptance']['Q1'], 'formula': f'{plan_acceptance.q1_plan}'},
                            {'column': plan_shift['acceptance']['Q2'], 'formula': f'{plan_acceptance.q2_plan}'},
                            {'column': plan_shift['acceptance']['Q3'], 'formula': f'{plan_acceptance.q3_plan}'},
                            {'column': plan_shift['acceptance']['Q4'], 'formula': f'{plan_acceptance.q4_plan}'},
                            {'column': plan_shift['acceptance']['6+6'],
                             'formula': f'{plan_acceptance.q3_plan_6_6} + {plan_acceptance.q4_plan_6_6}'},
                            {'column': plan_shift['margin']['Q1'], 'formula': f'{plan_margin.q1_plan}'},
                            {'column': plan_shift['margin']['Q2'], 'formula': f'{plan_margin.q2_plan}'},
                            {'column': plan_shift['margin']['Q3'], 'formula': f'{plan_margin.q3_plan}'},
                            {'column': plan_shift['margin']['Q4'], 'formula': f'{plan_margin.q4_plan}'},
                            {'column': plan_shift['margin']['6+6'],
                             'formula': f'{plan_margin.q3_plan_6_6} + {plan_margin.q4_plan_6_6}'},
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

                    for plan in (
                            {'column': plan_shift['revenue']['HY1'],
                             'formula': f"={xl_col_to_name(plan_shift['revenue']['Q1'])}{row + 1} + {xl_col_to_name(plan_shift['revenue']['Q2'])}{row + 1}"},
                            {'column': plan_shift['revenue']['HY2'],
                             'formula': f"={xl_col_to_name(plan_shift['revenue']['Q3'])}{row + 1} + {xl_col_to_name(plan_shift['revenue']['Q4'])}{row + 1}"},
                            {'column': plan_shift['revenue']['Y'],
                             'formula': f"={xl_col_to_name(plan_shift['revenue']['HY1'])}{row + 1} + {xl_col_to_name(plan_shift['revenue']['HY2'])}{row + 1}"},
                            {'column': plan_shift['pds']['HY1'],
                             'formula': f"={xl_col_to_name(plan_shift['pds']['Q1'])}{row + 1} + {xl_col_to_name(plan_shift['pds']['Q2'])}{row + 1}"},
                            {'column': plan_shift['pds']['HY2'],
                             'formula': f"={xl_col_to_name(plan_shift['pds']['Q3'])}{row + 1} + {xl_col_to_name(plan_shift['pds']['Q4'])}{row + 1}"},
                            {'column': plan_shift['pds']['Y'],
                             'formula': f"={xl_col_to_name(plan_shift['pds']['HY1'])}{row + 1} + {xl_col_to_name(plan_shift['pds']['HY2'])}{row + 1}"},
                            {'column': plan_shift['acceptance']['HY1'],
                             'formula': f"={xl_col_to_name(plan_shift['acceptance']['Q1'])}{row + 1} + {xl_col_to_name(plan_shift['acceptance']['Q2'])}{row + 1}"},
                            {'column': plan_shift['acceptance']['HY2'],
                             'formula': f"={xl_col_to_name(plan_shift['acceptance']['Q3'])}{row + 1} + {xl_col_to_name(plan_shift['acceptance']['Q4'])}{row + 1}"},
                            {'column': plan_shift['acceptance']['Y'],
                             'formula': f"={xl_col_to_name(plan_shift['acceptance']['HY1'])}{row + 1} + {xl_col_to_name(plan_shift['acceptance']['HY2'])}{row + 1}"},
                            {'column': plan_shift['margin']['HY1'],
                             'formula': f"={xl_col_to_name(plan_shift['margin']['Q1'])}{row + 1} + {xl_col_to_name(plan_shift['margin']['Q2'])}{row + 1}"},
                            {'column': plan_shift['margin']['HY2'],
                             'formula': f"={xl_col_to_name(plan_shift['margin']['Q3'])}{row + 1} + {xl_col_to_name(plan_shift['margin']['Q4'])}{row + 1}"},
                            {'column': plan_shift['margin']['Y'],
                             'formula': f"={xl_col_to_name(plan_shift['margin']['HY1'])}{row + 1} + {xl_col_to_name(plan_shift['margin']['HY2'])}{row + 1}"},
                    ):
                        sheet.write_formula(row, plan['column'], plan['formula'], row_format_plan)

            if isFoundProjectsByOffice:
                row += 1
                column = 0
                sheet.write_string(row, column, 'ИТОГО ' + project_office.name, row_format_office)
                sheet.write_string(row, column + 1, 'ИТОГО ' + project_office.name, row_format_office)
                sheet.set_row(row, False, False, {'hidden': 1, 'level': level})
                str_project_office_id = 'project_office_' + str(int(project_office.parent_id))
                if str_project_office_id in dict_formula:
                    dict_formula[str_project_office_id] = dict_formula[str_project_office_id] + ',{0}' + str(row+1)
                else:
                    dict_formula[str_project_office_id] = ',{0}'+str(row+1)

                str_project_office_id = 'project_office_' + str(int(project_office.id))

                print('formulaProjectOffice',formulaProjectOffice)

                if str_project_office_id in dict_formula:
                    formulaProjectOffice = formulaProjectOffice + dict_formula[str_project_office_id]+')'
                else:
                    formulaProjectOffice = formulaProjectOffice + ')'

                # print('project_office = ', project_office, dict_formula)
                formulaItogo = formulaItogo + ',{0}' + str(row + 1)
                # print('formulaProjectOffice = ',formulaProjectOffice)
                for colFormula in range(2, 9):
                    sheet.write_string(row, colFormula, '', row_format_office)

                for colFormula in list(range(9, 215)) + list(range(216, 230)) + list(range(231, 245)):
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
                sheet.write_string(row, column, 'ИТОГО ' + project_office.name + ' Расчетный План:', row_format_office_estimated_plan_left)
                sheet.write_string(row, column + 1, 'ИТОГО ' + project_office.name  + ' Расчетный План:', row_format_office_estimated_plan_left)

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

                for plan in (
                        {'column': plan_shift['revenue']['Q1'], 'formula': f'{plan_revenue.q1_plan}'},
                        {'column': plan_shift['revenue']['Q2'], 'formula': f'{plan_revenue.q2_plan}'},
                        {'column': plan_shift['revenue']['Q3'], 'formula': f'{plan_revenue.q3_plan}'},
                        {'column': plan_shift['revenue']['Q4'], 'formula': f'{plan_revenue.q4_plan}'},
                        {'column': plan_shift['pds']['Q1'], 'formula': f'{plan_pds.q1_plan}'},
                        {'column': plan_shift['pds']['Q2'], 'formula': f'{plan_pds.q2_plan}'},
                        {'column': plan_shift['pds']['Q3'], 'formula': f'{plan_pds.q3_plan}'},
                        {'column': plan_shift['pds']['Q4'], 'formula': f'{plan_pds.q4_plan}'},
                        {'column': plan_shift['acceptance']['Q1'], 'formula': f'{plan_acceptance.q1_plan}'},
                        {'column': plan_shift['acceptance']['Q2'], 'formula': f'{plan_acceptance.q2_plan}'},
                        {'column': plan_shift['acceptance']['Q3'], 'formula': f'{plan_acceptance.q3_plan}'},
                        {'column': plan_shift['acceptance']['Q4'], 'formula': f'{plan_acceptance.q4_plan}'},
                        {'column': plan_shift['acceptance']['6+6'],
                         'formula': f'{plan_acceptance.q3_plan_6_6} + {plan_acceptance.q4_plan_6_6}'},
                        {'column': plan_shift['margin']['Q1'], 'formula': f'{plan_margin.q1_plan}'},
                        {'column': plan_shift['margin']['Q2'], 'formula': f'{plan_margin.q2_plan}'},
                        {'column': plan_shift['margin']['Q3'], 'formula': f'{plan_margin.q3_plan}'},
                        {'column': plan_shift['margin']['Q4'], 'formula': f'{plan_margin.q4_plan}'},
                        {'column': plan_shift['margin']['6+6'],
                         'formula': f'{plan_margin.q3_plan_6_6} + {plan_margin.q4_plan_6_6}'},
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

                    sheet.write_formula(row, plan['column'], office_formula, row_format_plan)

                for plan in (
                        {'column': plan_shift['revenue']['HY1'],
                         'formula': f"={xl_col_to_name(plan_shift['revenue']['Q1'])}{row + 1} + {xl_col_to_name(plan_shift['revenue']['Q2'])}{row + 1}"},
                        {'column': plan_shift['revenue']['HY2'],
                         'formula': f"={xl_col_to_name(plan_shift['revenue']['Q3'])}{row + 1} + {xl_col_to_name(plan_shift['revenue']['Q4'])}{row + 1}"},
                        {'column': plan_shift['revenue']['Y'],
                         'formula': f"={xl_col_to_name(plan_shift['revenue']['HY1'])}{row + 1} + {xl_col_to_name(plan_shift['revenue']['HY2'])}{row + 1}"},
                        {'column': plan_shift['pds']['HY1'],
                         'formula': f"={xl_col_to_name(plan_shift['pds']['Q1'])}{row + 1} + {xl_col_to_name(plan_shift['pds']['Q2'])}{row + 1}"},
                        {'column': plan_shift['pds']['HY2'],
                         'formula': f"={xl_col_to_name(plan_shift['pds']['Q3'])}{row + 1} + {xl_col_to_name(plan_shift['pds']['Q4'])}{row + 1}"},
                        {'column': plan_shift['pds']['Y'],
                         'formula': f"={xl_col_to_name(plan_shift['pds']['HY1'])}{row + 1} + {xl_col_to_name(plan_shift['pds']['HY2'])}{row + 1}"},
                        {'column': plan_shift['acceptance']['HY1'],
                         'formula': f"={xl_col_to_name(plan_shift['acceptance']['Q1'])}{row + 1} + {xl_col_to_name(plan_shift['acceptance']['Q2'])}{row + 1}"},
                        {'column': plan_shift['acceptance']['HY2'],
                         'formula': f"={xl_col_to_name(plan_shift['acceptance']['Q3'])}{row + 1} + {xl_col_to_name(plan_shift['acceptance']['Q4'])}{row + 1}"},
                        {'column': plan_shift['acceptance']['Y'],
                         'formula': f"={xl_col_to_name(plan_shift['acceptance']['HY1'])}{row + 1} + {xl_col_to_name(plan_shift['acceptance']['HY2'])}{row + 1}"},
                        {'column': plan_shift['margin']['HY1'],
                         'formula': f"={xl_col_to_name(plan_shift['margin']['Q1'])}{row + 1} + {xl_col_to_name(plan_shift['margin']['Q2'])}{row + 1}"},
                        {'column': plan_shift['margin']['HY2'],
                         'formula': f"={xl_col_to_name(plan_shift['margin']['Q3'])}{row + 1} + {xl_col_to_name(plan_shift['margin']['Q4'])}{row + 1}"},
                        {'column': plan_shift['margin']['Y'],
                         'formula': f"={xl_col_to_name(plan_shift['margin']['HY1'])}{row + 1} + {xl_col_to_name(plan_shift['margin']['HY2'])}{row + 1}"},
                ):
                    sheet.write_formula(row, plan['column'], plan['formula'], row_format_plan)
        return row, formulaItogo

    def printworksheet(self,workbook,budget,namesheet, estimated_probabilities):
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
        sheet.write_string(row + 1, column, "Номер этапа проекта", head_format_1)
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

        sheet.freeze_panes(5, 9)
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
        project_offices = self.env['project_budget.project_office'].search([('parent_id', '=', False)], order='name')  # для сортировки так делаем + берем сначала только верхние элементы
        project_managers = self.env['project_budget.project_manager'].search([], order='name')  # для сортировки так делаем

        formulaItogo = '=sum(0'

        row, formulaItogo = self.print_row(sheet, workbook, project_offices, project_managers, estimated_probabilities, budget, row, formulaItogo, 1)

        row += 1
        column = 0
        sheet.write_string(row, column, 'ИТОГО по отчету' , row_format_number_itogo)
        sheet.write_string(row, column + 1, 'ИТОГО по отчету', row_format_number_itogo)
        sheet.set_row(row, False, False, {'hidden': 1, 'level': 1})
        formulaItogo = formulaItogo + ')'
        if 'project_office_0' in dict_formula:
            formulaItogo = '=sum(' + dict_formula['project_office_0'] + ')'
            formula_plan = '=sum(,' + ','.join(('{0}' + str(int(c[3:]) + 1)) for c in dict_formula['project_office_0'].strip(',').split(',')) + ')'  # увеличиваем все номера строк на 1
        for colFormula in range(2, 9):
            sheet.write_string(row, colFormula, '', row_format_number_itogo)
        for colFormula in list(range(9, 215)) + list(range(216, 230)) + list(range(231, 245)):
            formula = formulaItogo.format(xl_col_to_name(colFormula))
            # print('formula = ', formula)
            sheet.write_formula(row, colFormula, formula, row_format_number_itogo)

        # расчетный план по отчету
        row += 1
        column = 0
        sheet.write_string(row, column, 'ИТОГО: Расчетный План по отчету' , row_format_itogo_estimated_plan_left)
        sheet.write_string(row, column + 1, 'ИТОГО: Расчетный План по отчету', row_format_itogo_estimated_plan_left)

        self.print_estimated_rows(sheet, row, row_format_itogo_estimated_plan,
                                  row_format_itogo_estimated_plan_cross)

        for type in plan_shift:  # кресты в планах
            for c in plan_shift[type].values():
                formula = formula_plan.format(xl_col_to_name(c))
                sheet.write_string(row - 1, c, '', row_format_plan_cross)
                sheet.write_formula(row, c, formula, row_format_plan)

        last_row = row
        row += 2
        sheet.merge_range(row, 1, row, 2, 'Контрактование, с НДС', summary_format_border_top_center)
        sheet.write_string(row, 3, '', summary_format_border_top)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(YEARint)}:', summary_format_border_top)
        sheet.write_formula(row, 3, '=CK{0}+CL{0}+CM{0}'.format(last_row), summary_format_border_top)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(YEARint)}:', summary_format_border_bottom)
        sheet.write_formula(row, 3, '=CK{0}'.format(last_row + 1), summary_format_border_bottom)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(YEARint + 1)}:', summary_format_border_top)
        sheet.write_formula(row, 3, '=HJ{0}+HK{0}'.format(last_row), summary_format_border_top)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(YEARint + 1)}:', summary_format_border_bottom)
        sheet.write_formula(row, 3, '=HJ{0}'.format(last_row + 1), summary_format_border_bottom)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(YEARint + 2)}:', summary_format_border_top)
        sheet.write_formula(row, 3, '=HY{0}+HZ{0}'.format(last_row), summary_format_border_top)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(YEARint + 2)}:', summary_format_border_bottom)
        sheet.write_formula(row, 3, '=HY{0}'.format(last_row + 1), summary_format_border_bottom)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'Итого по Компании {str(YEARint)}-{str(YEARint + 2)}:', summary_format_border_top)
        sheet.write_formula(row, 3, '=D{0}+D{1}+D{2}'.format(row - 1, row - 3, row - 5), summary_format_border_top)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'Итого Расчетный План по Компании {str(YEARint)}-{str(YEARint + 2)}:', summary_format_border_bottom)
        sheet.write_formula(row, 3, '=CK{0}+HJ{0}+HY{0}'.format(last_row + 1), summary_format_border_bottom)
        row += 2
        sheet.merge_range(row, 1, row, 2, 'Валовая выручка, без НДС', summary_format_border_top_center)
        sheet.write_string(row, 3, '', summary_format_border_top)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(YEARint)}:', summary_format_border_top)
        sheet.write_formula(row, 3, '=GA{0}+GB{0}+GC{0}'.format(last_row), summary_format_border_top)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(YEARint)}:', summary_format_border_bottom)
        sheet.write_formula(row, 3, '=GA{0}'.format(last_row + 1), summary_format_border_bottom)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(YEARint + 1)}:', summary_format_border_top)
        sheet.write_formula(row, 3, '=HQ{0}+HR{0}'.format(last_row), summary_format_border_top)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(YEARint + 1)}:', summary_format_border_bottom)
        sheet.write_formula(row, 3, '=HQ{0}'.format(last_row + 1), summary_format_border_bottom)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(YEARint + 2)}:', summary_format_border_top)
        sheet.write_formula(row, 3, '=IF{0}+IG{0}'.format(last_row), summary_format_border_top)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(YEARint + 2)}:', summary_format_border_bottom)
        sheet.write_formula(row, 3, '=IF{0}'.format(last_row + 1), summary_format_border_bottom)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'Итого по Компании {str(YEARint)}-{str(YEARint + 2)}:', summary_format_border_top)
        sheet.write_formula(row, 3, '=D{0}+D{1}+D{2}'.format(row - 1, row - 3, row - 5), summary_format_border_top)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'Итого Расчетный План по Компании {str(YEARint)}-{str(YEARint + 2)}:', summary_format_border_bottom)
        sheet.write_formula(row, 3, '=D{0}+D{1}+D{2}'.format(row - 1, row - 3, row - 5), summary_format_border_bottom)
        row += 2
        sheet.merge_range(row, 1, row, 2, 'ПДС, с НДС', summary_format_border_top_center)
        sheet.write_string(row, 3, '', summary_format_border_top)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(YEARint)}:', summary_format_border_top)
        sheet.write_formula(row, 3, '=EX{0}+EY{0}+EZ{0}'.format(last_row), summary_format_border_top)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(YEARint)}:', summary_format_border_bottom)
        sheet.write_formula(row, 3, '=EX{0}'.format(last_row + 1), summary_format_border_bottom)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(YEARint + 1)}:', summary_format_border_top)
        sheet.write_formula(row, 3, '=HN{0}+HO{0}'.format(last_row), summary_format_border_top)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(YEARint + 1)}:', summary_format_border_bottom)
        sheet.write_formula(row, 3, '=HN{0}'.format(last_row + 1), summary_format_border_bottom)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(YEARint + 2)}:', summary_format_border_top)
        sheet.write_formula(row, 3, '=IC{0}+ID{0}'.format(last_row), summary_format_border_top)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(YEARint + 2)}:', summary_format_border_bottom)
        sheet.write_formula(row, 3, '=IC{0}'.format(last_row + 1), summary_format_border_bottom)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'Итого по Компании {str(YEARint)}-{str(YEARint + 2)}:', summary_format_border_top)
        sheet.write_formula(row, 3, '=D{0}+D{1}+D{2}'.format(row - 1, row - 3, row - 5), summary_format_border_top)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'Итого Расчетный План по Компании {str(YEARint)}-{str(YEARint + 2)}:', summary_format_border_bottom)
        sheet.write_formula(row, 3, '=D{0}+D{1}+D{2}'.format(row - 1, row - 3, row - 5), summary_format_border_bottom)
        row += 2
        sheet.merge_range(row, 1, row, 2, 'Валовая прибыль (М1), без НДС', summary_format_border_top_center)
        sheet.write_string(row, 3, '', summary_format_border_top)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(YEARint)}:', summary_format_border_top)
        sheet.write_formula(row, 3, '=HE{0}+HF{0}+HG{0}'.format(last_row), summary_format_border_top)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(YEARint)}:', summary_format_border_bottom)
        sheet.write_formula(row, 3, '=HE{0}'.format(last_row + 1), summary_format_border_bottom)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(YEARint + 1)}:', summary_format_border_top)
        sheet.write_formula(row, 3, '=HU{0}+HV{0}'.format(last_row), summary_format_border_top)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(YEARint + 1)}:', summary_format_border_bottom)
        sheet.write_formula(row, 3, '=HU{0}'.format(last_row + 1), summary_format_border_bottom)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(YEARint + 2)}:', summary_format_border_top)
        sheet.write_formula(row, 3, '=IJ{0}+IK{0}'.format(last_row), summary_format_border_top)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(YEARint + 2)}:', summary_format_border_bottom)
        sheet.write_formula(row, 3, '=IJ{0}'.format(last_row + 1), summary_format_border_bottom)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'Итого по Компании {str(YEARint)}-{str(YEARint + 2)}:', summary_format_border_top)
        sheet.write_formula(row, 3, '=D{0}+D{1}+D{2}'.format(row - 1, row - 3, row - 5), summary_format_border_top)
        row += 1
        sheet.merge_range(row, 1, row, 2, f'Итого Расчетный План по Компании {str(YEARint)}-{str(YEARint + 2)}:', summary_format_border_bottom)
        sheet.write_formula(row, 3, '=D{0}+D{1}+D{2}'.format(row - 1, row - 3, row - 5), summary_format_border_bottom)

        print('dict_formula = ', dict_formula)

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
        koeff_reserve = data['koeff_reserve']
        koeff_potential = data['koeff_potential']
        fact_columns = set()

        plan_shift = {
            'revenue': {
                'Q1': 21,
                'Q2': 21 + 17,
                'HY1': 21 + 22,
                'Q3': 21 + 39,
                'Q4': 21 + 56,
                'HY2': 21 + 61,
                'Y': 21 + 66,
                'NEXT': 216,
                'AFTER_NEXT': 231,
            },
            'pds': {
                'Q1': 101,
                'Q2': 101 + 13,
                'HY1': 101 + 17,
                'Q3': 101 + 30,
                'Q4': 101 + 43,
                'HY2': 101 + 47,
                'Y': 101 + 51,
                'NEXT': 220,
                'AFTER_NEXT': 235,
            },
            'acceptance': {
                'Q1': 156,
                'Q2': 156 + 4,
                'HY1': 156 + 8,
                'Q3': 156 + 12,
                'Q4': 156 + 16,
                'HY2': 156 + 20,
                '6+6': 156 + 21,
                'Y': 156 + 25,
                'NEXT': 223,
                'AFTER_NEXT': 238,
            },
            'margin': {
                'Q1': 186,
                'Q2': 186 + 4,
                'HY1': 186 + 8,
                'Q3': 186 + 12,
                'Q4': 186 + 16,
                'HY2': 186 + 20,
                '6+6': 186 + 21,
                'Y': 186 + 25,
                'NEXT': 227,
                'AFTER_NEXT': 242,
            },
        }

        print('YEARint=',YEARint)

        commercial_budget_id = data['commercial_budget_id']

        dict_formula = {'printed_projects': set(), 'printed_steps': set()}
        budget = self.env['project_budget.commercial_budget'].search([('id', '=', commercial_budget_id)])
        estimated_probabilities = self.env['project_budget.estimated_probability'].search([('name', '!=', '10')], order='code desc')  # для сортировки так делаем
        self.printworksheet(workbook, budget, 'Прогноз', estimated_probabilities)
        dict_formula = {'printed_projects': set(), 'printed_steps': set()}
        estimated_probabilities = self.env['project_budget.estimated_probability'].search([('name', '=', '10')], order='code desc')  # для сортировки так делаем
        self.printworksheet(workbook, budget, '10%', estimated_probabilities)
