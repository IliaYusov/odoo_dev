from odoo import models
import datetime
import xlsxwriter
from xlsxwriter.utility import xl_col_to_name
import logging

isdebug = False
logger = logging.getLogger("*___forecast_report___*")

class report_budget_forecast_excel(models.AbstractModel):
    _name = 'report.project_budget.report_budget_forecast_excel'
    _description = 'project_budget.report_budget_forecast_excel'
    _inherit = 'report.report_xlsx.abstract'

    strYEAR = '2023'
    YEARint = int(strYEAR)

    def isStepinYear(self, project, step):
        if project:
            if step:
                if step.end_presale_project_month.year == self.YEARint or step.end_sale_project_month.year == self.YEARint:
                    return True
                for pds in project.planned_cash_flow_ids:
                    if pds.project_steps_id.id == step.id:
                        if pds.date_cash.year == self.YEARint:
                            return True
                for pds in project.fact_cash_flow_ids:
                    if pds.project_steps_id.id == step.id:
                        if pds.date_cash.year == self.YEARint:
                            return True
                for act in project.planned_acceptance_flow_ids:
                    if act.project_steps_id.id == step.id:
                        if act.date_cash.year == self.YEARint:
                            return True
                for act in project.fact_acceptance_flow_ids:
                    if act.project_steps_id.id == step.id:
                        if act.date_cash.year == self.YEARint:
                            return True
        return False

    def isProjectinYear(self, project):
        if project:
            if project.project_have_steps == False:
                if project.end_presale_project_month.year == self.YEARint or project.end_sale_project_month.year == self.YEARint:
                    return True
                for pds in project.planned_cash_flow_ids:
                    if pds.date_cash.year == self.YEARint:
                        return True
                for pds in project.fact_cash_flow_ids:
                    if pds.date_cash.year == self.YEARint:
                        return True
                for act in project.planned_acceptance_flow_ids:
                    if act.date_cash.year == self.YEARint:
                        return True
                for act in project.fact_acceptance_flow_ids:
                    if act.date_cash.year == self.YEARint:
                        return True
            else:
                for step in project.project_steps_ids:
                    if self.isStepinYear(project, step):
                        return True
        return False

    month_rus_name_contract_pds = ['Январь','Февраль','Март','Q1 итого','Апрель','Май','Июнь','Q2 итого','HY1/YEAR итого',
                                    'Июль','Август','Сентябрь','Q3 итого','Октябрь','Ноябрь','Декабрь','Q4 итого',
                                   'HY2/YEAR итого','YEAR итого']
    month_rus_name_revenue_margin = ['Q1','Q2','HY1/YEAR','Q3','Q4','HY2/YEAR','YEAR']

    array_col_itogi = [28, 49, 55, 76, 97, 103, 109, 130, 151, 157, 178, 199, 205, 211, 217, 223, 229, 235, 241, 254, 260, 266, 272, 278, 284, 297,]

    array_col_itogi75 = [247, 290,]

    array_col_itogi75NoFormula = [248, 291,]

    dict_formula = {}
    dict_contract_pds = {
        1: {'name': 'Контрактование, с НДС', 'color': '#FFD966'},
        2: {'name': 'Поступление денежных средсв, с НДС', 'color': '#D096BF'}
    }

    dict_revenue_margin= {
        1: {'name': 'Валовая Выручка, без НДС', 'color': '#B4C6E7'},
        2: {'name': 'Валовая прибыль (Маржа 1), без НДС', 'color': '#F4FD9F'}
    }

    def get_estimated_probability_name_forecast(self, name):
     result = ''
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

    def get_etalon_project(self,spec, quater):
        datesearch = datetime.date(self.YEARint, 1, 1)
        if quater == 'Q1':
            datesearch = datetime.date(self.YEARint, 1, 1) # будем искать первый утвержденный в году
        if quater == 'Q2':
            datesearch = datetime.date(self.YEARint, 4, 1) # будем искать первый утвержденный после марта
        if quater == 'Q3':
            datesearch = datetime.date(self.YEARint, 7, 1) # будем искать первый утвержденный после июня
        if quater == 'Q4':
            datesearch = datetime.date(self.YEARint, 10, 1) # будем искать первый утвержденный после сентября

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
                                                                     ('project_id','=',spec.project_id)
                                                                    ], limit=1, order='date_actual desc')
        if isdebug:
            logger.info(f'  etalon_project.id = { etalon_project.id}')
            logger.info(f'  etalon_project.project_id = {etalon_project.project_id}')
            logger.info(f'  etalon_project.date_actual = { etalon_project.date_actual}')

        # print('etalon_project.project_id = ',etalon_project.project_id)
        # print('etalon_project.date_actual = ',etalon_project.date_actual)
        return etalon_project

    def get_etalon_step(self,step, quater):
        if isdebug:
            logger.info(f' start get_etalon_step')
            logger.info(f' quater = {quater}')
        if step == False:
            return False
        datesearch = datetime.date(self.YEARint, 1, 1)
        if quater == 'Q1':
            datesearch = datetime.date(self.YEARint, 1, 1) # будем искать первый утвержденный в году
        if quater == 'Q2':
            datesearch = datetime.date(self.YEARint, 4, 1) # будем искать первый утвержденный после марта
        if quater == 'Q3':
            datesearch = datetime.date(self.YEARint, 7, 1) # будем искать первый утвержденный после июня
        if quater == 'Q4':
            datesearch = datetime.date(self.YEARint, 10, 1) # будем искать первый утвержденный после сентября
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

    def get_sum_fact_pds_project_step_month(self,project, step, month):
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
                if pds.date_cash.month == month and pds.date_cash.year == self.YEARint:
                    sum_cash += pds.sum_cash
        return sum_cash

    def get_sum_plan_pds_project_step_month(self,project, step, month):
        sum_cash = 0
        if month:
            # if step:
            #     pds_list = self.env['project_budget.planned_cash_flow'].search([('project_steps_id', '=', step.id)])
            # else:
            #     pds_list = self.env['project_budget.planned_cash_flow'].search([('projects_id', '=', project.id)])
            pds_list = project.planned_cash_flow_ids
            for pds in pds_list:
                if step:
                    if pds.project_steps_id.id != step.id: continue
                if pds.date_cash.month == month and pds.date_cash.year == self.YEARint:
                    sum_cash += pds.sum_cash
            # else: # если нихрена нет планового ПДС, то берем сумму общую по дате окончания sale или по дате этапа
            #     print('step = ',step)
            #     print('project = ',project)
            #     if step == False or step == False:
            #         if project:
            #             if project.end_sale_project_month.month == month and project.end_sale_project_month.year == self.YEARint:
            #                 sum_cash = project.total_amount_of_revenue_with_vat
            #     else:
            #         if step:
            #             if step.end_sale_project_month.month == month and step.end_sale_project_month.year == self.YEARint:
            #                 sum_cash = step.total_amount_of_revenue_with_vat
        return sum_cash

    def get_sum_plan_acceptance_step_month(self,project, step, month):
        sum_cash = 0
        # if project.project_have_steps == False:
        #     acceptance_list = self.env['project_budget.planned_acceptance_flow'].search([('projects_id', '=', project.id)])
        # if project.project_have_steps and step != False:
        #     acceptance_list = self.env['project_budget.planned_acceptance_flow'].search([('project_steps_id', '=', step.id)])

        acceptance_list = project.planned_acceptance_flow_ids
        for acceptance in acceptance_list:
            if step:
                if acceptance.project_steps_id.id != step.id: continue
            if acceptance.date_cash.month == month:
                sum_cash += acceptance.sum_cash_without_vat
        return sum_cash



    def print_month_head_contract_pds(self,workbook,sheet,row,column,YEAR):
        for x in self.dict_contract_pds.items():
            y = list(x[1].values())
            head_format_month = workbook.add_format({
                'border': 1,
                'text_wrap': True,
                'align': 'center',
                'valign': 'vcenter',
                "bold" : True,
                "fg_color" : y[1],
                "font_size" : 11,
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




            for elementone in self.month_rus_name_contract_pds:

                element = elementone.replace('YEAR',YEAR)
                if element.find('итого') != -1:
                    if elementone.find('Q') != -1:
                        sheet.set_column(column, column + 5, False, False, {'hidden': 1, 'level': 2})
                    if elementone.find('HY') != -1:
                        sheet.set_column(column, column + 5, False, False, {'hidden': 1, 'level': 1})
                    sheet.merge_range(row, column, row, column + 5, element, head_format_month)
                    sheet.merge_range(row + 1, column, row + 2, column, "План "+element.replace('итого',''), head_format_month_itogo)
                    column += 1
                else:
                    sheet.merge_range(row, column, row, column + 4, element, head_format_month)
                    sheet.set_column(column, column+4, False, False, {'hidden': 1, 'level': 3})
                sheet.merge_range(row+1, column, row+1, column + 1, 'Прогноз на начало периода (эталонный)', head_format_month_detail)
                sheet.write_string(row+2, column, 'Обязательство', head_format_month_detail)
                column += 1
                sheet.write_string(row + 2, column, 'Резерв', head_format_month_detail)
                column += 1
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

    def print_month_head_revenue_margin(self,workbook,sheet,row,column,YEAR):
        for x in self.dict_revenue_margin.items():
            y = list(x[1].values())
            head_format_month = workbook.add_format({
                'border': 1,
                'text_wrap': True,
                'align': 'center',
                'valign': 'vcenter',
                "bold" : True,
                "fg_color" : y[1],
                "font_size" : 11,
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
            for elementone in self.month_rus_name_revenue_margin:
                element = elementone.replace('YEAR', YEAR)
                addcolumn = 0
                if element.find('HY2') != -1:
                    addcolumn = 1

                if elementone.find('Q') != -1:
                    sheet.set_column(column, column + 5, False, False, {'hidden': 1, 'level': 2})

                if elementone.find('HY') != -1:
                    sheet.set_column(column, column + 5 + addcolumn, False, False, {'hidden': 1, 'level': 1})

                sheet.merge_range(row, column, row, column + 5 + addcolumn, element, head_format_month)


                sheet.merge_range(row + 1, column, row + 2, column, "План " + element.replace('итого', ''),
                                  head_format_month_itogo)
                column += 1

                if element.find('HY2') != -1:
                    sheet.merge_range(row + 1, column, row + 2, column, "План HY2/"+YEAR+ " 7+5"
                                      , head_format_month_itogo)
                    column += 1

                sheet.merge_range(row + 1, column , row + 1, column + 1 , 'Прогноз на начало периода (эталонный)',
                                  head_format_month_detail)

                sheet.write_string(row + 2, column , 'Обязательство', head_format_month_detail)
                column += 1
                sheet.write_string(row + 2, column , 'Резерв', head_format_month_detail)
                column += 1
                sheet.merge_range(row + 1, column , row + 2, column , 'Факт', head_format_month_detail_fact)
                column += 1
                sheet.merge_range(row + 1, column , row + 1, column + 1 , 'Прогноз до конца периода (на дату отчета)',
                                  head_format_month_detail)
                sheet.write_string(row + 2, column , 'Обязательство', head_format_month_detail)
                column += 1
                sheet.write_string(row + 2, column, 'Резерв', head_format_month_detail)
                column += 1
            sheet.merge_range(row-1, colbeg, row-1, column - 1, y[0], head_format_month)
        return column

    def print_month_revenue_project(self, sheet, row, column, month, project, step, row_format_number,row_format_number_color_fact):

        sum75tmpetalon = 0
        sum50tmpetalon = 0
        sum100tmp = 0
        sum75tmp = 0
        sum50tmp = 0
        if month:
            project_etalon = self.get_etalon_project(project, self.get_quater_from_month(month))
            if step == False:
                if project_etalon:
                    if month == project_etalon.end_presale_project_month.month and self.YEARint == project_etalon.end_presale_project_month.year:
                        if project_etalon.estimated_probability_id.name == '75':
                            sheet.write_number(row, column + 0, project_etalon.total_amount_of_revenue_with_vat, row_format_number)
                            sum75tmpetalon += project_etalon.total_amount_of_revenue_with_vat
                        if project_etalon.estimated_probability_id.name == '50':
                            sheet.write_number(row, column + 1, project_etalon.total_amount_of_revenue_with_vat, row_format_number)
                            sum50tmpetalon += project_etalon.total_amount_of_revenue_with_vat

                if month == project.end_presale_project_month.month and self.YEARint == project.end_presale_project_month.year:
                    if project.estimated_probability_id.name in ('100','100(done)'):
                        sheet.write_number(row, column + 2, project.total_amount_of_revenue_with_vat, row_format_number_color_fact)
                        sum100tmp += project.total_amount_of_revenue_with_vat
                    if project.estimated_probability_id.name == '75':
                        sheet.write_number(row, column + 3, project.total_amount_of_revenue_with_vat, row_format_number)
                        sum75tmp += project.total_amount_of_revenue_with_vat
                    if project.estimated_probability_id.name == '50':
                        sheet.write_number(row, column + 4, project.total_amount_of_revenue_with_vat, row_format_number)
                        sum50tmp += project.total_amount_of_revenue_with_vat
            else:
                step_etalon  = self.get_etalon_step(step, self.get_quater_from_month(month))
                if step_etalon:
                    if month == step_etalon.end_presale_project_month.month and self.YEARint == step_etalon.end_presale_project_month.year:
                        if step_etalon.estimated_probability_id.name == '75':
                            sheet.write_number(row, column + 0, step_etalon.total_amount_of_revenue_with_vat, row_format_number)
                            sum75tmpetalon = step_etalon.total_amount_of_revenue_with_vat
                        if step_etalon.estimated_probability_id.name == '50':
                            sheet.write_number(row, column + 1, step_etalon.total_amount_of_revenue_with_vat, row_format_number)
                            sum50tmpetalon = step_etalon.total_amount_of_revenue_with_vat
                else:
                    if project_etalon: # если нет жталонного этапа, то данные берем из проекта, да это будет увеличивать сумму на количество этапов, но что делать я ХЗ
                        if month == project_etalon.end_presale_project_month.month and self.YEARint == project_etalon.end_presale_project_month.year:
                            if project_etalon.estimated_probability_id.name == '75':
                                sheet.write_number(row, column + 0, project_etalon.total_amount_of_revenue_with_vat,
                                                   row_format_number)
                                sum75tmpetalon += project_etalon.total_amount_of_revenue_with_vat
                            if project_etalon.estimated_probability_id.name == '50':
                                sheet.write_number(row, column + 1, project_etalon.total_amount_of_revenue_with_vat,
                                                   row_format_number)
                                sum50tmpetalon += project_etalon.total_amount_of_revenue_with_vat

                if month == step.end_presale_project_month.month and self.YEARint == step.end_presale_project_month.year:
                    if step.estimated_probability_id.name in ('100','100(done)'):
                        sheet.write_number(row, column + 2, step.total_amount_of_revenue_with_vat, row_format_number_color_fact)
                        sum100tmp = step.total_amount_of_revenue_with_vat
                    if step.estimated_probability_id.name == '75':
                        sheet.write_number(row, column + 3, step.total_amount_of_revenue_with_vat, row_format_number)
                        sum75tmp = step.total_amount_of_revenue_with_vat
                    if step.estimated_probability_id.name == '50':
                        sheet.write_number(row, column + 4, step.total_amount_of_revenue_with_vat, row_format_number)
                        sum50tmp = step.total_amount_of_revenue_with_vat

        return sum75tmpetalon, sum50tmpetalon, sum100tmp, sum75tmp, sum50tmp

    def print_month_pds_project(self, sheet, row, column, month, project, step, row_format_number, row_format_number_color_fact):
        sum75tmpetalon = sum50tmpetalon = sum100tmp = sum75tmp = sum50tmp = 0
        if month:
                project_etalon = self.get_etalon_project(project, self.get_quater_from_month(month))
                step_etalon = self.get_etalon_step(step, self.get_quater_from_month(month))
                sum = 0
                sum = self.get_sum_plan_pds_project_step_month(project_etalon, step_etalon, month)

                if (step) and (not step_etalon): # есть этап сейчас, но нет в эталоне
                    sum = 0

                estimated_probability_id_name = project_etalon.estimated_probability_id.name
                if step_etalon :
                    estimated_probability_id_name = step_etalon.estimated_probability_id.name
                if sum != 0:
                    if estimated_probability_id_name in('75','100','100(done)'):
                        sheet.write_number(row, column + 0, sum,row_format_number)
                        sum75tmpetalon += sum
                    if estimated_probability_id_name == '50':
                        sheet.write_number(row, column + 1, sum, row_format_number)
                        sum50tmpetalon += sum

                sum100tmp = self.get_sum_fact_pds_project_step_month(project, step, month)
                if sum100tmp:
                    sheet.write_number(row, column + 2, sum100tmp, row_format_number_color_fact)

                sum = self.get_sum_plan_pds_project_step_month(project, step, month)
                # print('----- project.id=',project.id)
                # print('sum100tmp = ',sum100tmp)
                # print('sum = ', sum)
                if sum100tmp >= sum:
                    sum = 0
                else:
                    sum = sum - sum100tmp
                # print('after: sum = ', sum)
                # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
                sum_ostatok_pds = sum_distribution_pds = 0
                for planned_cash_flow in project.planned_cash_flow_ids:
                    if step:
                        if planned_cash_flow.project_steps_id.id != step.id: continue
                    if planned_cash_flow.date_cash.month == month and planned_cash_flow.date_cash.year == self.YEARint:
                        sum_ostatok_pds += planned_cash_flow.distribution_sum_with_vat_ostatok
                        sum_distribution_pds += planned_cash_flow.distribution_sum_without_vat
                if sum_distribution_pds != 0 : # если есть распределение, то остаток = остатку распределения
                    sum = sum_ostatok_pds
                    if sum < 0 : sum = 0

                estimated_probability_id_name = project.estimated_probability_id.name
                if step :
                    estimated_probability_id_name = step.estimated_probability_id.name

                if sum != 0:
                    if estimated_probability_id_name in('75','100','100(done)'):
                        sheet.write_number(row, column + 3, sum,row_format_number)
                        sum75tmp += sum
                    if estimated_probability_id_name == '50':
                        sheet.write_number(row, column + 4, sum, row_format_number)
                        sum50tmp += sum
        return sum75tmpetalon, sum50tmpetalon, sum100tmp, sum75tmp, sum50tmp

    def get_sum_fact_acceptance_project_step_quater(self, project, step, element_name):
        sum_cash = 0
        months = self.get_months_from_quater(element_name)
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
                    if acceptance.date_cash.month in months and acceptance.date_cash.year == self.YEARint:
                        sum_cash += acceptance.sum_cash_without_vat
        return sum_cash

    def get_sum_planned_acceptance_project_step_quater(self, project, step, element_name):
        sum_acceptance = 0

        months = self.get_months_from_quater(element_name)

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
                    if acceptance.date_cash.month in months and acceptance.date_cash.year == self.YEARint:
                        sum_acceptance += acceptance.sum_cash_without_vat
                        # sum_acceptance += acceptance.sum_cash_without_vat / (1 + vatpercent / 100)

        return sum_acceptance

    def print_quater_planned_acceptance_project(self, sheet, row, column, element_name, project, step, row_format_number, row_format_number_color_fact):
        sum75tmpetalon = sum50tmpetalon = sum100tmp = sum75tmp = sum50tmp = 0
        if element_name in ('Q1','Q2','Q3','Q4'):
            project_etalon = self.get_etalon_project(project, element_name)
            step_etalon = self.get_etalon_step(step, element_name)

            if step == False:
                profitability = project.profitability
            else:
                profitability = step.profitability

            if step_etalon == False:
                profitability_etalon = project_etalon.profitability
            else:
                profitability_etalon = step_etalon.profitability


            sum = 0
            sum = self.get_sum_planned_acceptance_project_step_quater(project_etalon, step_etalon, element_name)
            if (step ) and (not step_etalon):
                sum = 0

            estimated_probability_id_name = project_etalon.estimated_probability_id.name
            if step_etalon:
                estimated_probability_id_name = step_etalon.estimated_probability_id.name

            if sum != 0:
                if estimated_probability_id_name in('75','100','100(done)'):
                    sheet.write_number(row, column + 0, sum, row_format_number)
                    sheet.write_number(row, column + 0 + 43, sum*profitability_etalon/100, row_format_number)
                    sum75tmpetalon += sum
                if estimated_probability_id_name == '50':
                    sheet.write_number(row, column + 1, sum, row_format_number)
                    sheet.write_number(row, column + 1 + 43 , sum*profitability_etalon/100, row_format_number)
                    sum50tmpetalon += sum

            sum100tmp = self.get_sum_fact_acceptance_project_step_quater(project, step, element_name)

            if sum100tmp:
                sheet.write_number(row, column + 2, sum100tmp, row_format_number_color_fact)
                sheet.write_number(row, column + 2 + 43, sum100tmp*profitability/100, row_format_number_color_fact)


            sum = 0
            sum = self.get_sum_planned_acceptance_project_step_quater(project, step, element_name)
            if sum100tmp >= sum:
                sum = 0
            else:
                sum = sum - sum100tmp

            # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
            sum_ostatok_acceptance = sum_distribution_acceptance = 0
            months = self.get_months_from_quater(element_name)
            for planned_acceptance_flow in project.planned_acceptance_flow_ids:
                if step:
                    if planned_acceptance_flow.project_steps_id.id != step.id: continue
                if planned_acceptance_flow.date_cash.month in months and planned_acceptance_flow.date_cash.year == self.YEARint:
                    sum_ostatok_acceptance += planned_acceptance_flow.distribution_sum_without_vat_ostatok
                    sum_distribution_acceptance += planned_acceptance_flow.distribution_sum_without_vat
            if sum_distribution_acceptance != 0 : # если есть распределение, то остаток = остатку распределения
                sum = sum_ostatok_acceptance
                if sum <= 0 : sum = 0

            estimated_probability_id_name = project.estimated_probability_id.name
            if step:
                estimated_probability_id_name = step.estimated_probability_id.name

            if sum != 0:
                if estimated_probability_id_name in('75','100','100(done)'):
                    sheet.write_number(row, column + 3, sum, row_format_number)
                    sheet.write_number(row, column + 3 + 43, sum*profitability/100, row_format_number)
                    sum75tmp += sum
                if estimated_probability_id_name == '50':
                    sheet.write_number(row, column + 4, sum, row_format_number)
                    sheet.write_number(row, column + 4 + 43, sum*profitability/100, row_format_number)
                    sum50tmp += sum
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

    def print_row_Values(self, workbook, sheet, row, column,  YEAR, project, step):

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

        if step:
            if project.estimated_probability_id.name == '0':
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
        for element in self.month_rus_name_contract_pds:
            column += 1
            sumQ75tmpetalon = sumQ50tmpetalon = sumQ100tmp = sumQ75tmp = sumQ50tmp = 0

            if element.find('итого') != -1:
                sheet.write_string(row, column, "", head_format_month_itogo)
                column += 1
            sheet.write_string(row, column + 0, "", row_format_number)
            sheet.write_string(row, column + 1, "", row_format_number)
            sheet.write_string(row, column + 2, "", row_format_number_color_fact)
            sheet.write_string(row, column + 3, "", row_format_number)
            sheet.write_string(row, column + 4, "", row_format_number)

            sumQ75tmpetalon, sumQ50tmpetalon, sumQ100tmp, sumQ75tmp, sumQ50tmp = self.print_month_revenue_project(sheet, row, column, self.get_month_number_rus(element),
                                                                                    project,step, row_format_number,row_format_number_color_fact)
            sumQ75etalon += sumQ75tmpetalon
            sumQ50etalon += sumQ50tmpetalon
            sumQ100 += sumQ100tmp
            sumQ75 += sumQ75tmp
            sumQ50 += sumQ50tmp
            if element.find('Q') != -1: #'Q1 итого' 'Q2 итого' 'Q3 итого' 'Q4 итого'
                # if sumQ75etalon != 0 : sheet.write_number(row, column + 0, sumQ75etalon, row_format_number)
                # if sumQ50etalon != 0 : sheet.write_number(row, column + 1, sumQ50etalon, row_format_number)
                # if sumQ100 != 0 :      sheet.write_number(row, column + 2, sumQ100, row_format_number_color_fact)
                # if sumQ75 != 0 :       sheet.write_number(row, column + 3, sumQ75, row_format_number)
                # if sumQ50 != 0 :       sheet.write_number(row, column + 4, sumQ50, row_format_number)

                formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1,xl_col_to_name(column - 16),xl_col_to_name(column - 11),xl_col_to_name(column - 6))
                sheet.write_formula(row, column + 0,formula, row_format_number)
                formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1,xl_col_to_name(column - 15),xl_col_to_name(column - 10),xl_col_to_name(column - 5))
                sheet.write_formula(row, column + 1,formula, row_format_number)
                formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1,xl_col_to_name(column - 14),xl_col_to_name(column - 9),xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 2,formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1,xl_col_to_name(column - 13),xl_col_to_name(column - 8),xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 3,formula, row_format_number)
                formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1,xl_col_to_name(column - 12),xl_col_to_name(column - 7),xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 4,formula, row_format_number)

                sumHY100etalon += sumQ100etalon
                sumHY75etalon += sumQ75etalon
                sumHY50etalon += sumQ50etalon
                sumHY100 += sumQ100
                sumHY75 += sumQ75
                sumHY50 += sumQ50
                sumQ100etalon = sumQ75etalon = sumQ50etalon = sumQ100 = sumQ75  = sumQ50  = 0

            if element.find('HY') != -1:  # 'HY1/YEAR итого' 'HY2/YEAR итого'
                if sumHY75etalon != 0: sheet.write_number(row, column + 0, sumHY75etalon, row_format_number)
                if sumHY50etalon != 0: sheet.write_number(row, column + 1, sumHY50etalon, row_format_number)
                if sumHY100 != 0:      sheet.write_number(row, column + 2, sumHY100, row_format_number_color_fact)
                if sumHY75 != 0:       sheet.write_number(row, column + 3, sumHY75, row_format_number)
                if sumHY50 != 0:       sheet.write_number(row, column + 4, sumHY50, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 27),xl_col_to_name(column - 6))
                sheet.write_formula(row, column + 0, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 26),xl_col_to_name(column - 5))
                sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 25),xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 24),xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 3, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 23),xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 4, formula, row_format_number)


                sumYear100etalon += sumHY100etalon
                sumYear75etalon += sumHY75etalon
                sumYear50etalon += sumHY50etalon
                sumYear100 += sumHY100
                sumYear75 += sumHY75
                sumYear50 += sumHY50
                sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0

            if element == 'YEAR итого':  # 'YEAR итого'
                if sumYear75etalon != 0: sheet.write_number(row, column + 0, sumYear75etalon, row_format_number)
                if sumYear50etalon != 0: sheet.write_number(row, column + 1, sumYear50etalon, row_format_number)
                if sumYear100 != 0:      sheet.write_number(row, column + 2, sumYear100, row_format_number_color_fact)
                if sumYear75 != 0:       sheet.write_number(row, column + 3, sumYear75, row_format_number)
                if sumYear50 != 0:       sheet.write_number(row, column + 4, sumYear50, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 54), xl_col_to_name(column - 6))
                sheet.write_formula(row, column + 0, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 53), xl_col_to_name(column - 5))
                sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 52), xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 51), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 3, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 50), xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 4, formula, row_format_number)
            column += 4
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
            sheet.write_string(row, column + 0, "", row_format_number)
            sheet.write_string(row, column + 1, "", row_format_number)
            sheet.write_string(row, column + 2, "", row_format_number_color_fact)
            sheet.write_string(row, column + 3, "", row_format_number)
            sheet.write_string(row, column + 4, "", row_format_number)


            sumQ75tmpetalon, sumQ50tmpetalon, sumQ100tmp, sumQ75tmp, sumQ50tmp = self.print_month_pds_project(sheet, row, column, self.get_month_number_rus(element)
                                                                                        ,project, step, row_format_number, row_format_number_color_fact)

            sumQ75etalon += sumQ75tmpetalon
            sumQ50etalon += sumQ50tmpetalon
            sumQ100 += sumQ100tmp
            sumQ75 += sumQ75tmp
            sumQ50 += sumQ50tmp

            if element.find('Q') != -1:  # 'Q1 итого' 'Q2 итого' 'Q3 итого' 'Q4 итого'
                if sumQ75etalon != 0: sheet.write_number(row, column + 0, sumQ75etalon, row_format_number)
                if sumQ50etalon != 0: sheet.write_number(row, column + 1, sumQ50etalon, row_format_number)
                if sumQ100 != 0:      sheet.write_number(row, column + 2, sumQ100, row_format_number_color_fact)
                if sumQ75 != 0:       sheet.write_number(row, column + 3, sumQ75, row_format_number)
                if sumQ50 != 0:       sheet.write_number(row, column + 4, sumQ50, row_format_number)
                sumHY100etalon += sumQ100etalon
                sumHY75etalon += sumQ75etalon
                sumHY50etalon += sumQ50etalon
                sumHY100 += sumQ100
                sumHY75 += sumQ75
                sumHY50 += sumQ50
                sumQ100etalon = sumQ75etalon = sumQ50etalon = sumQ100 = sumQ75 = sumQ50 = 0
                formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1, xl_col_to_name(column - 16),xl_col_to_name(column - 11), xl_col_to_name(column - 6))
                sheet.write_formula(row, column + 0, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1, xl_col_to_name(column - 15),xl_col_to_name(column - 10), xl_col_to_name(column - 5))
                sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1, xl_col_to_name(column - 14),xl_col_to_name(column - 9), xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1, xl_col_to_name(column - 13),xl_col_to_name(column - 8), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 3, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0},{3}{0})'.format(row + 1, xl_col_to_name(column - 12),xl_col_to_name(column - 7), xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 4, formula, row_format_number)

            if element.find('HY') != -1:  # 'HY1/YEAR итого' 'HY2/YEAR итого'
                if sumHY75etalon != 0: sheet.write_number(row, column + 0, sumHY75etalon, row_format_number)
                if sumHY50etalon != 0: sheet.write_number(row, column + 1, sumHY50etalon, row_format_number)
                if sumHY100 != 0:      sheet.write_number(row, column + 2, sumHY100, row_format_number_color_fact)
                if sumHY75 != 0:       sheet.write_number(row, column + 3, sumHY75, row_format_number)
                if sumHY50 != 0:       sheet.write_number(row, column + 4, sumHY50, row_format_number)
                sumYear100etalon += sumHY100etalon
                sumYear75etalon += sumHY75etalon
                sumYear50etalon += sumHY50etalon
                sumYear100 += sumHY100
                sumYear75 += sumHY75
                sumYear50 += sumHY50
                sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 27), xl_col_to_name(column - 6))
                sheet.write_formula(row, column + 0, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 26), xl_col_to_name(column - 5))
                sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 25), xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 24), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 3, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 23), xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 4, formula, row_format_number)

            if element == 'YEAR итого':  # 'YEAR итого'
                if sumYear75etalon != 0: sheet.write_number(row, column + 0, sumYear75etalon, row_format_number)
                if sumYear50etalon != 0: sheet.write_number(row, column + 1, sumYear50etalon, row_format_number)
                if sumYear100 != 0:      sheet.write_number(row, column + 2, sumYear100, row_format_number_color_fact)
                if sumYear75 != 0:       sheet.write_number(row, column + 3, sumYear75, row_format_number)
                if sumYear50 != 0:       sheet.write_number(row, column + 4, sumYear50, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 54), xl_col_to_name(column - 6))
                sheet.write_formula(row, column + 0, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 53), xl_col_to_name(column - 5))
                sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 52), xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 51), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 3, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 50), xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 4, formula, row_format_number)
            column += 4
        # end Поступление денежных средсв, с НДС

        # Валовая Выручка, без НДС
        sumYear100etalon = sumYear75etalon = sumYear50etalon = sumYear100 = sumYear75 = sumYear50 = 0
        sumHY100etalon = sumHY75etalon = sumHY50etalon = sumHY100 = sumHY75 = sumHY50 = 0

        if step == False:
            profitability = project.profitability
        else:
            profitability = step.profitability

        project_etalon = self.get_etalon_project(project, False)
        step_etalon = self.get_etalon_step(step, False)

        if step_etalon == False:
            profitability_etalon = project_etalon.profitability
        else:
            profitability_etalon = step_etalon.profitability

        for element in self.month_rus_name_revenue_margin:
            column += 1
            sheet.write_string(row, column, "", head_format_month_itogo)
            sheet.write_string(row, column + 43, "", head_format_month_itogo)
            if element.find('HY2') != -1:
                addcolumn = 1
                column += 1
                sheet.write_string(row, column, "", head_format_month_itogo)
                sheet.write_string(row, column + 43, "", head_format_month_itogo)
            column += 1
            sheet.write_string(row, column + 0, "", row_format_number)
            sheet.write_string(row, column + 1, "", row_format_number)
            sheet.write_string(row, column + 2, "", row_format_number_color_fact)
            sheet.write_string(row, column + 3, "", row_format_number)
            sheet.write_string(row, column + 4, "", row_format_number)
            sheet.write_string(row, column + 0 + 43, "", row_format_number)
            sheet.write_string(row, column + 1 + 43, "", row_format_number)
            sheet.write_string(row, column + 2 + 43, "", row_format_number_color_fact)
            sheet.write_string(row, column + 3 + 43, "", row_format_number)
            sheet.write_string(row, column + 4 + 43, "", row_format_number)

            sumQ75etalon, sumQ50etalon, sumQ100, sumQ75, sumQ50 = self.print_quater_planned_acceptance_project(sheet,row,column,element
                                                                                                              ,project,step,row_format_number,row_format_number_color_fact)

            sumHY100etalon += sumQ100etalon
            sumHY75etalon += sumQ75etalon
            sumHY50etalon += sumQ50etalon
            sumHY100 += sumQ100
            sumHY75 += sumQ75
            sumHY50 += sumQ50

            if element.find('HY') != -1:  # 'HY1/YEAR итого' 'HY2/YEAR итого'
                # if sumHY75etalon != 0:
                #     sheet.write_number(row, column + 0, sumHY75etalon, row_format_number)
                #     sheet.write_number(row, column + 0 + 43, sumHY75etalon*profitability_etalon / 100, row_format_number)
                # if sumHY50etalon != 0:
                #     sheet.write_number(row, column + 1, sumHY50etalon, row_format_number)
                #     sheet.write_number(row, column + 1 + 43, sumHY50etalon*profitability_etalon / 100, row_format_number)
                # if sumHY100 != 0:
                #     sheet.write_number(row, column + 2, sumHY100, row_format_number_color_fact)
                #     sheet.write_number(row, column + 2 + 43, sumHY100*profitability / 100, row_format_number_color_fact)
                # if sumHY75 != 0:
                #     sheet.write_number(row, column + 3, sumHY75, row_format_number)
                #     sheet.write_number(row, column + 3 + 43, sumHY75*profitability / 100, row_format_number)
                # if sumHY50 != 0:
                #     sheet.write_number(row, column + 4, sumHY50, row_format_number)
                #     sheet.write_number(row, column + 4 + 43, sumHY50*profitability / 100, row_format_number)
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

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 12 - addcolumn), xl_col_to_name(column - 6 - addcolumn))
                sheet.write_formula(row, column + 0, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 11 - addcolumn), xl_col_to_name(column - 5 - addcolumn))
                sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 10 - addcolumn), xl_col_to_name(column - 4 - addcolumn))
                sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 9 - addcolumn),  xl_col_to_name(column - 3 - addcolumn))
                sheet.write_formula(row, column + 3, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8 - addcolumn),  xl_col_to_name(column - 2 - addcolumn))
                sheet.write_formula(row, column + 4, formula, row_format_number)

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 12 + 43 - addcolumn), xl_col_to_name(column - 6 + 43 - addcolumn))
                sheet.write_formula(row, column + 0 + 43, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 11 + 43 - addcolumn), xl_col_to_name(column - 5 + 43 - addcolumn))
                sheet.write_formula(row, column + 1 + 43, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 10 + 43 - addcolumn), xl_col_to_name(column - 4 + 43 - addcolumn))
                sheet.write_formula(row, column + 2 + 43, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 9 + 43 - addcolumn),  xl_col_to_name(column - 3 + 43 - addcolumn))
                sheet.write_formula(row, column + 3 + 43, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 8 + 43 - addcolumn),  xl_col_to_name(column - 2 + 43 - addcolumn))
                sheet.write_formula(row, column + 4 + 43, formula, row_format_number)



            if element == 'YEAR':  # 'YEAR итого'
                # if sumYear75etalon != 0:
                #     sheet.write_number(row, column + 0, sumYear75etalon, row_format_number)
                #     sheet.write_number(row, column + 0 + 43, sumYear75etalon*profitability / 100, row_format_number)
                # if sumYear50etalon != 0:
                #     sheet.write_number(row, column + 1, sumYear50etalon, row_format_number)
                #     sheet.write_number(row, column + 1 + 43, sumYear50etalon*profitability / 100, row_format_number)
                # if sumYear100 != 0:
                #     sheet.write_number(row, column + 2, sumYear100, row_format_number_color_fact)
                #     sheet.write_number(row, column + 2 + 43, sumYear100*profitability / 100, row_format_number_color_fact)
                # if sumYear75 != 0:
                #     sheet.write_number(row, column + 3, sumYear75, row_format_number)
                #     sheet.write_number(row, column + 3 + 43, sumYear75*profitability / 100, row_format_number)
                # if sumYear50 != 0:
                #     sheet.write_number(row, column + 4, sumYear50, row_format_number)
                #     sheet.write_number(row, column + 4 + 43, sumYear50*profitability / 100, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 25), xl_col_to_name(column - 6))
                sheet.write_formula(row, column + 0, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 24), xl_col_to_name(column - 5))
                sheet.write_formula(row, column + 1, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 23), xl_col_to_name(column - 4))
                sheet.write_formula(row, column + 2, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 22), xl_col_to_name(column - 3))
                sheet.write_formula(row, column + 3, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 21), xl_col_to_name(column - 2))
                sheet.write_formula(row, column + 4, formula, row_format_number)

                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 25 + 43), xl_col_to_name(column - 6 + 43))
                sheet.write_formula(row, column + 0 + 43, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 24 + 43), xl_col_to_name(column - 5 + 43))
                sheet.write_formula(row, column + 1 + 43, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 23 + 43), xl_col_to_name(column - 4 + 43))
                sheet.write_formula(row, column + 2 + 43, formula, row_format_number_color_fact)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 22 + 43), xl_col_to_name(column - 3 + 43))
                sheet.write_formula(row, column + 3 + 43, formula, row_format_number)
                formula = '=sum({1}{0},{2}{0})'.format(row + 1, xl_col_to_name(column - 21 + 43), xl_col_to_name(column - 2 + 43))
                sheet.write_formula(row, column + 4 + 43, formula, row_format_number)

            column += 4
        # end Валовая Выручка, без НДС

    def printworksheet(self,workbook,budget,namesheet):
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
            "font_size": 8,
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
            'border': 1,
            'font_size': 9,
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
            "fg_color": '#D9E1F2',
            "font_size": 9,
        })
        head_format_month_itogo.set_num_format('#,##0')

        date_format = workbook.add_format({'num_format': 'd mmmm yyyy'})
        row = 0
        sheet.merge_range(row,0,row,3, budget.name, bold)
        row = 6
        column = 0
        sheet.write_string(row, column, "Прогноз",head_format)
        sheet.write_string(row+1, column, "Проектный офис", head_format_1)
        sheet.write_string(row + 2, column, "", head_format_1)
        sheet.set_column(column, column, 21.5)
        column += 1
        sheet.write_string(row, column, "", head_format)
        sheet.write_string(row+1, column, "КАМ", head_format_1)
        sheet.write_string(row + 2, column, "", head_format_1)
        sheet.set_column(column, column, 19.75)
        column += 1
        sheet.write_string(row, column, "", head_format)
        sheet.write_string(row+1, column, "Заказчик", head_format_1)
        sheet.write_string(row + 2, column, "", head_format_1)
        sheet.set_column(column, column, 25)
        column += 1
        sheet.write_string(row, column, "", head_format)
        sheet.write_string(row+1, column, "Наименование Проекта", head_format_1)
        # sheet.write_string(row + 2, column, "", head_format_1)
        sheet.set_column(column, column, 12.25)
        column += 1
        sheet.write_string(row, column, "", head_format)
        sheet.write_string(row+1, column, "Номер этапа проекта", head_format_1)
        sheet.write_string(row + 2, column, "", head_format_1)
        # sheet.set_column(column, column, 15)
        column += 1
        sheet.write_string(row, column, "", head_format)
        sheet.write_string(row+1, column, "Стадия продажи", head_format_1)
        sheet.write_string(row + 2, column, "", head_format_1)
        # sheet.set_column(column, column, 16.88)
        column += 1
        sheet.write_string(row, column, "", head_format)
        sheet.write_string(row+1, column, "Сумма проекта, вруб", head_format_1)
        sheet.write_string(row + 2, column, "", head_format_1)
        # sheet.set_column(column, column, 14)
        column += 1
        sheet.write_string(row, column, "", head_format)
        sheet.write_string(row+1, column, "Валовая прибыль экспертно, в руб", head_format_1)
        sheet.write_string(row + 2, column, "", head_format_1)
        # sheet.set_column(column, column, 14)
        column += 1
        sheet.write_string(row, column, "", head_format)
        sheet.write_string(row+1, column, "Прибыльность, экспертно, %", head_format_1)
        sheet.write_string(row + 2, column, "", head_format_1)
        # sheet.set_column(column, column, 9)
        column += 1
        sheet.write_string(row, column, "", head_format)
        sheet.write_string(row+1, column, "Номер договора", head_format_1)
        sheet.write_string(row + 2, column, "", head_format_1)
        # sheet.set_column(column, column, 11.88)
        column += 1
        sheet.write_string(row, column, "", head_format)
        sheet.write_string(row+1, column, "НДС", head_format_1)
        sheet.write_string(row + 2, column, "", head_format_1)
        # sheet.set_column(column, column, 7)
        sheet.set_column(4, 10, False, False, {'hidden': 1, 'level': 1})
        column += 1
        sheet.write_string(row, column, "", head_format)
        sheet.write_string(row+1, column, "", head_format_1)
        sheet.write_string(row + 2, column, "", head_format_1)
        sheet.set_column(column, column, 2)

        sheet.freeze_panes(9, 12)
        column += 1
        column = self.print_month_head_contract_pds(workbook, sheet, row, column,  self.strYEAR)
        column = self.print_month_head_revenue_margin(workbook, sheet, row, column,  self.strYEAR)
        row += 2

        # project_offices  = self.env['project_budget.project_office'].search([('parent_id','=',False)], order='name')  # для сортировки так делаем + берем сначала только верхние элементы
        project_offices = self.env['project_budget.project_office'].search([],order='name')  # для сортировки так делаем + берем сначала только верхние элементы
        project_managers = self.env['project_budget.project_manager'].search([], order='name')  # для сортировки так делаем
        estimated_probabilitys = self.env['project_budget.estimated_probability'].search([],order='name desc')  # для сортировки так делаем

        isFoundProjectsByOffice = False
        isFoundProjectsByManager = False
        begRowProjectsByManager = 0
        formulaItogo = '=sum(0'
        for project_office in project_offices:
            isFoundProjectsByOffice = False
            formulaProjectOffice = '=sum(0,'
            for project_manager in project_managers:
                # print('project_manager = ', project_manager.name)
                isFoundProjectsByManager = False
                begRowProjectsByManager = 0
                column = -1
                for estimated_probability in estimated_probabilitys:
                    # print('estimated_probability.name = ', estimated_probability.name)
                    cur_budget_projects = self.env['project_budget.projects'].search([('commercial_budget_id', '=', budget.id)
                                                                                     ,('project_office_id','=',project_office.id)
                                                                                     ,('project_manager_id','=',project_manager.id)
                                                                                     ,('estimated_probability_id','=',estimated_probability.id)]
                                                                                    )
                    # row += 1
                    # sheet.write_string(row, column, project_office.name, row_format)
                    for spec in cur_budget_projects:
                        # if spec.estimated_probability_id.name != '0':
                        if spec.is_framework == True and spec.project_have_steps == False: continue # рамка без этапов - пропускаем
                        if spec.vgo == '-':

                            if begRowProjectsByManager == 0:
                                begRowProjectsByManager = row
                            if spec.project_have_steps:
                                for step in spec.project_steps_ids:
                                    if self.isStepinYear( spec, step) == False:
                                        continue
                                    isFoundProjectsByManager = True
                                    isFoundProjectsByOffice = True

                                    row += 1
                                    sheet.set_row(row, False, False, {'hidden': 1, 'level': 1})
                                    # print('setrow level2 row = ',row)
                                    cur_row_format = row_format
                                    cur_row_format_number = row_format_number
                                    # print('step.estimated_probability_id.name = ' + step.estimated_probability_id.name)
                                    if step.estimated_probability_id.name == '0':
                                        # print('row_format_canceled_project')
                                        cur_row_format = row_format_canceled_project
                                        cur_row_format_number = row_format_number_canceled_project
                                    column = 0
                                    sheet.write_string(row, column, spec.project_office_id.name, cur_row_format)
                                    column += 1
                                    sheet.write_string(row, column, spec.project_manager_id.name, cur_row_format)
                                    column += 1
                                    sheet.write_string(row, column, spec.customer_organization_id.name, cur_row_format)
                                    column += 1
                                    sheet.write_string(row, column, step.essence_project, cur_row_format)
                                    column += 1
                                    sheet.write_string(row, column, (step.code or '') +' | '+ spec.project_id + " | "+step.step_id, cur_row_format)
                                    column += 1
                                    sheet.write_string(row, column, self.get_estimated_probability_name_forecast(step.estimated_probability_id.name), cur_row_format)
                                    column += 1
                                    sheet.write_number(row, column, step.total_amount_of_revenue_with_vat, cur_row_format_number)
                                    column += 1
                                    sheet.write_number(row, column, step.margin_income, cur_row_format_number)
                                    column += 1
                                    sheet.write_number(row, column, step.profitability, cur_row_format_number)
                                    column += 1
                                    sheet.write_string(row, column, step.dogovor_number or '', cur_row_format)
                                    column += 1
                                    sheet.write_string(row, column, step.vat_attribute_id.name, cur_row_format)
                                    column += 1
                                    sheet.write_string(row, column, '', head_format_1)
                                    self.print_row_Values(workbook, sheet, row, column,  self.strYEAR, spec, step)
                            else:
                                if self.isProjectinYear(spec) == False:
                                    continue
                                row += 1
                                isFoundProjectsByManager = True
                                isFoundProjectsByOffice = True
                                sheet.set_row(row, False, False, {'hidden': 1, 'level': 1})
                                # print('setrow level2 row = ', row)
                                cur_row_format = row_format
                                cur_row_format_number = row_format_number
                                # print('spec.estimated_probability_id.name = ' + spec.estimated_probability_id.name)
                                if spec.estimated_probability_id.name == '0':
                                    # print('row_format_canceled_project')
                                    cur_row_format = row_format_canceled_project
                                    cur_row_format_number = row_format_number_canceled_project
                                column = 0
                                sheet.write_string(row, column, spec.project_office_id.name, cur_row_format)
                                column += 1
                                sheet.write_string(row, column, spec.project_manager_id.name, cur_row_format)
                                column += 1
                                sheet.write_string(row, column, spec.customer_organization_id.name, cur_row_format)
                                column += 1
                                sheet.write_string(row, column, spec.essence_project, cur_row_format)
                                column += 1
                                sheet.write_string(row, column, (spec.step_project_number or '')+ ' | ' +(spec.project_id or ''), cur_row_format)
                                column += 1
                                sheet.write_string(row, column, self.get_estimated_probability_name_forecast(spec.estimated_probability_id.name), cur_row_format)
                                column += 1
                                sheet.write_number(row, column, spec.total_amount_of_revenue_with_vat, cur_row_format_number)
                                column += 1
                                sheet.write_number(row, column, spec.margin_income, cur_row_format_number)
                                column += 1
                                sheet.write_number(row, column, spec.profitability, cur_row_format_number)
                                column += 1
                                sheet.write_string(row, column, spec.dogovor_number or '', cur_row_format)
                                column += 1
                                sheet.write_string(row, column, spec.vat_attribute_id.name, cur_row_format)
                                column += 1
                                sheet.write_string(row, column, '', head_format_1)
                                self.print_row_Values(workbook, sheet, row, column,  self.strYEAR, spec, False)

                if isFoundProjectsByManager:
                    row += 1
                    column = 1
                    sheet.write_string(row, column, 'ИТОГО ' + project_manager.name, row_format_manager)
                    sheet.set_row(row, False, False, {'hidden': 1, 'level': 1})
                    formulaProjectOffice = formulaProjectOffice + ',{0}'+str(row + 1)
                    for colFormula in range(2, 12):
                        sheet.write_string(row, colFormula, '', row_format_manager)
                    for colFormula in range(12,302):
                        formula = '=sum({2}{0}:{2}{1})'.format(begRowProjectsByManager + 2,row, xl_col_to_name(colFormula))
                        sheet.write_formula(row, colFormula, formula, row_format_manager)
                    # for col in self.array_col_itogi:
                    #     formula = '={1}{0} + {2}{0}'.format(row+1,xl_col_to_name(col),xl_col_to_name(col+ 1))
                    #     print('formula = ', formula)
                    #     sheet.write_formula(row, col -1, formula, head_format_month_itogo)
                    for col in self.array_col_itogi75:
                        formula = '={1}{0} + {2}{0}'.format(row+1,xl_col_to_name(col+ 1),xl_col_to_name(col+ 2))
                        # print('formula = ', formula)
                        sheet.write_formula(row, col -1, formula, head_format_month_itogo)
                    for col in self.array_col_itogi75NoFormula:
                        formula = '=0'
                        sheet.write_formula(row, col - 1, formula, head_format_month_itogo)

            if isFoundProjectsByOffice:
                row += 1
                column = 0
                # sheet.set_row(row, False, False, {'hidden': 1, 'level': 1})
                # print('setrow level1 row = ', row)
                sheet.write_string(row, column, 'ИТОГО ' + project_office.name, row_format_office)
                formulaProjectOffice = formulaProjectOffice + ')'
                formulaItogo = formulaItogo + ',{0}' + str(row + 1)
                # print('formulaProjectOffice = ',formulaProjectOffice)
                for colFormula in range(1, 12):
                    sheet.write_string(row, colFormula, '', row_format_office)

                for colFormula in range(12, 302):
                    formula = formulaProjectOffice.format(xl_col_to_name(colFormula))
                    # print('formula = ', formula)
                    sheet.write_formula(row, colFormula, formula, row_format_office)

        row += 2
        column = 0
        sheet.write_string(row, column, 'ИТОГО по отчету' , row_format_number_itogo)
        formulaItogo = formulaItogo + ')'
        for colFormula in range(1, 12):
            sheet.write_string(row, colFormula, '', row_format_number_itogo)
        for colFormula in range(12, 302):
            formula = formulaItogo.format(xl_col_to_name(colFormula))
            # print('formula = ', formula)
            sheet.write_formula(row, colFormula, formula, row_format_number_itogo)

    def generate_xlsx_report(self, workbook, data, budgets):
        for budget in budgets:
            self.printworksheet(workbook, budget, 'Прогноз')
