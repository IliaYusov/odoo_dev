from odoo import models
import datetime
import xlsxwriter
from xlsxwriter.utility import xl_col_to_name
import logging

class ReportBudgetPlanFactExcel(models.AbstractModel):
    _name = 'report.project_budget.report_budget_plan_fact_excel'
    _description = 'project_budget.report_budget_plan_fact_excel'
    _inherit = 'report.report_xlsx.abstract'

    POTENTIAL = 0.6
    YEARint = 2023
    koeff_reserve = float(1)
    year_end = 2023
    def is_step_in_year(self, project, step, year):
        if project:
            if step:
                if step.estimated_probability_id.name == '0':  # проверяем последний зафиксированный бюджет в предыдущих годах
                    last_fixed_step = self.env['project_budget.project_steps'].search(
                        [('date_actual', '<', datetime.date(year,1,1)),
                         ('budget_state', '=', 'fixed'),
                         ('step_id', '=', step.step_id),
                         ], limit=1, order='date_actual desc')
                    if last_fixed_step and last_fixed_step.estimated_probability_id.name == '0':
                        return False

                if (step.end_presale_project_month.year >= year and step.end_presale_project_month.year <= year + 2)\
                        or (step.end_sale_project_month.year >= year and step.end_sale_project_month.year <= year + 2)\
                        or (step.end_presale_project_month.year <= year and step.end_sale_project_month.year >= year + 2):
                    return True
                for pds in project.planned_cash_flow_ids:
                    if pds.project_steps_id.id == step.id:
                        if pds.date_cash.year >= year and pds.date_cash.year <= year + 2 :
                            return True
                for pds in project.fact_cash_flow_ids:
                    if pds.project_steps_id.id == step.id:
                        if pds.date_cash.year >= year and pds.date_cash.year <= year + 2:
                            return True
                for act in project.planned_acceptance_flow_ids:
                    if act.project_steps_id.id == step.id:
                        if act.date_cash.year >= year and act.date_cash.year <= year + 2:
                            return True
                for act in project.fact_acceptance_flow_ids:
                    if act.project_steps_id.id == step.id:
                        if act.date_cash.year >= year and act.date_cash.year <= year + 2:
                            return True
        return False

    def is_project_in_year(self, project, year):
        if project:
            if project.estimated_probability_id.name == '0':  # проверяем последний зафиксированный бюджет в предыдущих годах
                last_fixed_project = self.env['project_budget.projects'].search(
                    [('date_actual', '<', datetime.date(year,1,1)),
                     ('budget_state', '=', 'fixed'),
                     ('project_id', '=', project.project_id),
                     ], limit=1, order='date_actual desc')
                if last_fixed_project and last_fixed_project.estimated_probability_id.name == '0':
                    return False

            if project.project_have_steps == False:
                if (project.end_presale_project_month.year >= year and project.end_presale_project_month.year <= year + 2)\
                        or (project.end_sale_project_month.year >= year and project.end_sale_project_month.year <= year + 2)\
                        or (project.end_presale_project_month.year <= year and project.end_sale_project_month.year >= year + 2):
                    return True
                for pds in project.planned_cash_flow_ids:
                    if pds.date_cash.year >= year and pds.date_cash.year <= year + 2:
                        return True
                for pds in project.fact_cash_flow_ids:
                    if pds.date_cash.year >= year and pds.date_cash.year <= year + 2:
                        return True
                for act in project.planned_acceptance_flow_ids:
                    if act.date_cash.year >= year and act.date_cash.year <= year + 2:
                        return True
                for act in project.fact_acceptance_flow_ids:
                    if act.date_cash.year >= year and act.date_cash.year <= year + 2:
                        return True
            else:
                for step in project.project_steps_ids:
                    if self.is_step_in_year(project, step, year):
                        return True
        return False

    section_names = ['contracting', 'cash', 'acceptance', 'margin_income', 'margin3_income',]
    company_section_names = ['contracting', 'cash', 'acceptance', 'margin_income', 'margin3_income', 'ebit', 'net_profit']
    quarter_names = ['Q1', 'Q2', 'Q3', 'Q4',]
    probability_names = ['100', '75', '50', '30', 'plan']
    section_titles = {
        'contracting': 'Контрактование,\n руб. с НДС',
        'cash': 'ПДС,\n руб. с НДС',
        'acceptance': 'Выручка,\n руб. без НДС',
        'margin_income': 'МАРЖА 1,\n руб. без НДС',
        'margin3_income': 'МАРЖА 3,\n руб.',
    }
    company_section_titles = {
        'contracting': 'Контрактование,\n руб. с НДС',
        'cash': 'ПДС,\n руб. с НДС',
        'acceptance': 'Выручка,\n руб. без НДС',
        'margin_income': 'МАРЖА 1,\n руб. без НДС',
        'margin3_income': 'МАРЖА 3,\n руб.',
        'ebit': 'EBIT,\n руб.',
        'net_profit': 'Чистая прибыль,\n руб.',
    }

    dict_formula = {}

    dict_revenue_margin= {
        1: {'name': 'Валовая Выручка, без НДС', 'color': '#B4C6E7'},
        2: {'name': 'Валовая прибыль (Маржа 1), без НДС', 'color': '#F4FD9F'}
    }

    def get_estimated_probability_name_forecast(self, name):
        office_datault = name
        if name == '0': office_datault = 'Отменен'
        if name == '30': office_datault = 'Идентификация проекта'
        if name == '50': office_datault = 'Подготовка ТКП'
        if name == '75': office_datault = 'Подписание договора'
        if name == '100': office_datault = 'Исполнение'
        if name == '100(done)': office_datault = 'Исполнен/закрыт'
        return office_datault

    def get_quarter_from_month(self,month):
        if month in (1,2,3):
            return 'Q1'
        if month in (4,5,6):
            return 'Q2'
        if month in (7,8,9):
            return 'Q3'
        if month in (10,11,12):
            return 'Q4'
        return False


    def get_months_from_quater(self, quarter_name):
        months = False;
        if quarter_name == 'Q1':
            months=(1,2,3)
        if quarter_name == 'Q2':
            months=(4,5,6)
        if quarter_name == 'Q3':
            months=(7,8,9)
        if quarter_name == 'Q4':
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

    def get_sum_fact_pds_project_step_quarter(self, project, step, year, quarter):
        sum_cash = 0
        months = self.get_months_from_quater(quarter)
        pds_list = project.fact_cash_flow_ids
        for pds in pds_list:
            if step:
                if pds.project_steps_id.id != step.id: continue
            if pds.date_cash.month in months and pds.date_cash.year == year:
                sum_cash += pds.sum_cash
        return sum_cash

    def get_sum_plan_pds_project_step_quarter(self, project, step, year, quarter):
        sum_cash = {'commitment': 0, 'reserve':0}
        months = self.get_months_from_quater(quarter)
        pds_list = project.planned_cash_flow_ids
        for pds in pds_list:
            if step:
                if pds.project_steps_id.id != step.id: continue
            if pds.date_cash.month in months and pds.date_cash.year == year:
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

    def get_quarter_revenue_project(self, quarter, project, step, year):
        global koeff_reserve
        global koeff_potential

        sum100tmp = 0
        sum75tmp = 0
        sum50tmp = 0
        sum30tmp = 0

        months = self.get_months_from_quater(quarter)

        if months:
            if step == False:
                if project.end_presale_project_month.month in months and project.end_presale_project_month.year == year:
                    currency_rate = self.get_currency_rate_by_project(project)
                    if project.estimated_probability_id.name in ('100','100(done)'):
                        sum100tmp += project.total_amount_of_revenue_with_vat * currency_rate
                    if project.estimated_probability_id.name == '75':
                        sum75tmp += project.total_amount_of_revenue_with_vat * currency_rate
                    if project.estimated_probability_id.name == '50':
                        sum50tmp += project.total_amount_of_revenue_with_vat * koeff_reserve*currency_rate
                    if project.estimated_probability_id.name == '30':
                        sum30tmp += project.total_amount_of_revenue_with_vat * koeff_potential * currency_rate
            else:
                if step.end_presale_project_month.month in months and step.end_presale_project_month.year == year:
                    currency_rate = self.get_currency_rate_by_project(step.projects_id)
                    if step.estimated_probability_id.name in ('100','100(done)'):
                        sum100tmp = step.total_amount_of_revenue_with_vat * currency_rate
                    if step.estimated_probability_id.name == '75':
                        sum75tmp = step.total_amount_of_revenue_with_vat * currency_rate
                    if step.estimated_probability_id.name == '50':
                        sum50tmp = step.total_amount_of_revenue_with_vat * koeff_reserve * currency_rate
                    if step.estimated_probability_id.name == '30':
                        sum30tmp = step.total_amount_of_revenue_with_vat * koeff_potential * currency_rate

        return sum100tmp, sum75tmp, sum50tmp, sum30tmp

    def get_quarter_pds_project(self, quarter, project, step, year):
        global koeff_reserve

        sum100tmp = sum75tmp = sum50tmp = 0

        sum = {'commitment': 0, 'reserve': 0, 'potential': 0}

        months = self.get_months_from_quater(quarter)

        sum100tmp = self.get_sum_fact_pds_project_step_quarter(project, step, year, quarter)

        sum = self.get_sum_plan_pds_project_step_quarter(project, step, year, quarter)

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
        for planned_cash_flow in project.planned_cash_flow_ids:
            if step:
                if planned_cash_flow.project_steps_id.id != step.id: continue
            if planned_cash_flow.date_cash.month in months and planned_cash_flow.date_cash.year == year:
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
            sum75tmp += sum.get('commitment', 0)
            sum50tmp += sum.get('reserve', 0) * koeff_reserve

        return sum100tmp, sum75tmp, sum50tmp

    def get_sum_fact_acceptance_project_step_quater(self, project, step, year, quarter):
        sum_cash = 0
        months = self.get_months_from_quater(quarter)
        acceptance_list = project.fact_acceptance_flow_ids
        if acceptance_list:
            for acceptance in acceptance_list:
                if step:
                    if acceptance.project_steps_id.id != step.id: continue
                if acceptance.date_cash.month in months and acceptance.date_cash.year == year:
                    sum_cash += acceptance.sum_cash_without_vat
        return sum_cash

    def get_sum_fact_margin_project_step_quarter(self, project, step, year, quarter):
        sum_cash = 0
        months = self.get_months_from_quater(quarter)
        if project.is_parent_project:
            for child_project in project.child_project_ids:
                if child_project.project_have_steps:
                    for child_step in child_project.project_steps_ids:
                        sum_cash += self.get_sum_fact_margin_project_step_quarter(child_project, child_step, year,
                                                                                  quarter) * child_project.margin_rate_for_parent
                else:
                    sum_cash += self.get_sum_fact_margin_project_step_quarter(child_project, False, year, quarter) * child_project.margin_rate_for_parent
            return sum_cash
        acceptance_list = project.fact_acceptance_flow_ids
        if acceptance_list:
            for acceptance in acceptance_list:
                if step:
                    if acceptance.project_steps_id.id != step.id: continue
                if acceptance.date_cash.month in months and acceptance.date_cash.year == year:
                    sum_cash += acceptance.margin
        return sum_cash

    def get_sum_planned_acceptance_project_step_quater(self, project, step, year, quarter):
        sum_acceptance = {'commitment': 0, 'reserve':0, 'potential': 0}

        months = self.get_months_from_quater(quarter)

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
        return sum_acceptance

    def get_sum_planned_margin_project_step_quater(self, project, step, year, quarter):
        sum_margin = {'commitment': 0, 'reserve': 0, 'potential': 0}

        months = self.get_months_from_quater(quarter)
        if project.is_parent_project:
            for child_project in project.child_project_ids:
                if child_project.project_have_steps:
                    for child_step in child_project.project_steps_ids:
                        for key in sum_margin:
                            sum_margin[key] += self.get_sum_planned_margin_project_step_quater(child_project, child_step, year,
                                                                                  quarter)[key] * child_project.margin_rate_for_parent
                else:
                    for key in sum_margin:
                        sum_margin[key] += self.get_sum_planned_margin_project_step_quater(child_project, False, year, quarter)[key] * child_project.margin_rate_for_parent
            return sum_margin
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
        return sum_margin

    def get_margin_forecast_from_distributions(self, planned_acceptance, margin_plan, project, step, margin_rate_for_parent):
        # суммируем доли маржи фактов в соотношении (сумма распределения/суммы факта)
        margin_distribution = 0
        for distribution in planned_acceptance.distribution_acceptance_ids:
            if distribution.fact_acceptance_flow_id.sum_cash_without_vat != 0:
                margin_distribution += distribution.fact_acceptance_flow_id.margin * distribution.sum_cash_without_vat / distribution.fact_acceptance_flow_id.sum_cash_without_vat
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

    def get_sum_planned_acceptance_project_step_from_distribution(self, project, step, year, quarter):
        # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
        sum_ostatok_acceptance = {'commitment': 0, 'reserve': 0, 'potential': 0}
        sum_distribution_acceptance = 0
        months = self.get_months_from_quater(quarter)

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

        if sum_distribution_acceptance:  # если есть распределение, то остаток = остатку распределения
            return sum_ostatok_acceptance
        else:
            return False

    def get_sum_planned_margin_project_step_from_distribution(self, project, step, year, quarter, margin_plan, margin_rate_for_parent):
        # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
        sum_distribution_acceptance = 0
        new_margin_plan = margin_plan.copy()
        months = self.get_months_from_quater(quarter)

        if project.is_parent_project:
            for child_project in project.child_project_ids:
                if child_project.project_have_steps:
                    for child_step in child_project.project_steps_ids:
                        new_margin_plan =  self.get_sum_planned_margin_project_step_from_distribution(child_project, child_step, year,
                                                                              quarter, margin_plan, child_project.margin_rate_for_parent)
                        if new_margin_plan:
                            margin_plan = new_margin_plan
                else:
                    new_margin_plan = self.get_sum_planned_margin_project_step_from_distribution(child_project, False, year, quarter, margin_plan, child_project.margin_rate_for_parent)
                    if new_margin_plan:
                        margin_plan = new_margin_plan

            return margin_plan
        for planned_acceptance_flow in project.planned_acceptance_flow_ids:
            if step:
                if planned_acceptance_flow.project_steps_id.id != step.id: continue
            if planned_acceptance_flow.date_cash.month in months and planned_acceptance_flow.date_cash.year == year:
                sum_distribution_acceptance += planned_acceptance_flow.distribution_sum_without_vat

                new_margin_plan = self.get_margin_forecast_from_distributions(planned_acceptance_flow, new_margin_plan, project,
                                                                          step, margin_rate_for_parent)
        if sum_distribution_acceptance:  # если есть распределение, то остаток = остатку распределения
            return new_margin_plan
        else:
            return False

    def get_quarter_acceptance_project(self, quarter, project, step, year):

        sum100tmp = sum75tmp = sum50tmp = margin100tmp = margin75tmp = margin50tmp = 0

        if step == False:
            profitability = project.profitability
        else:
            profitability = step.profitability

        margin_rate_for_child = 1
        if project.is_child_project:
            margin_rate_for_child = (1 - project.margin_rate_for_parent)

        sum100tmp = self.get_sum_fact_acceptance_project_step_quater(project, step, year, quarter)
        margin100tmp = self.get_sum_fact_margin_project_step_quarter(project, step, year, quarter) * margin_rate_for_child

        sum = self.get_sum_planned_acceptance_project_step_quater(project, step, year, quarter)
        margin_sum = self.get_sum_planned_margin_project_step_quater(project, step, year, quarter)

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

        sum_ostatok_acceptance = self.get_sum_planned_acceptance_project_step_from_distribution(project, step, year, quarter)
        new_margin_plan = self.get_sum_planned_margin_project_step_from_distribution(project, step, year, quarter, margin_plan, 1)

        if sum_ostatok_acceptance:
            sum = sum_ostatok_acceptance
        if new_margin_plan:
            margin_sum = new_margin_plan

        for key in sum:
            if not project.is_correction_project:
                sum[key] = max(sum[key], 0)
                margin_sum[key] = max(margin_sum[key], 0)

        if sum:
            sum75tmp += sum.get('commitment', 0)
            margin75tmp += margin_sum.get('commitment', 0) * margin_rate_for_child
            sum50tmp += sum.get('reserve', 0) * koeff_reserve
            margin50tmp += margin_sum.get('reserve', 0) * koeff_reserve * margin_rate_for_child

        return sum100tmp, sum75tmp, sum50tmp, margin100tmp, margin75tmp, margin50tmp

    # def get_month_number_rus(self, monthNameRus):
    #     if monthNameRus == 'Январь': return 1
    #     if monthNameRus == 'Февраль': return 2
    #     if monthNameRus == 'Март' : return 3
    #     if monthNameRus == 'Апрель' : return 4
    #     if monthNameRus == 'Май' : return 5
    #     if monthNameRus == 'Июнь' : return 6
    #     if monthNameRus == 'Июль' : return 7
    #     if monthNameRus == 'Август' : return 8
    #     if monthNameRus == 'Сентябрь' : return 9
    #     if monthNameRus == 'Октябрь' : return 10
    #     if monthNameRus == 'Ноябрь' : return 11
    #     if monthNameRus == 'Декабрь' : return 12
    #     return False

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

    # def print_estimated_rows(self, sheet, row, format, format_cross):
    #
    #     for colFormula in range(2, 9):
    #         sheet.write_string(row, colFormula, '', format)
    #
    #     for colFormula in list(range(9, 215)) + list(range(216, 230)) + list(range(231, 245)):
    #         sheet.write_string(row, colFormula, '', format)
    #
    #     for type in plan_shift:  # формулы расчетных планов
    #         start_column = 9
    #         if type in ('revenue', 'pds'):
    #             shift = 0
    #             if type == 'revenue':
    #                 width = 4
    #             elif type == 'pds':
    #                 start_column += 83
    #                 width = 3
    #             for element in range(len(self.quarter_names)):
    #                 if element in [3, 7, 8, 12, 16, 17, 18]:  # учитываем колонки планов
    #                     shift += 1
    #                 formula = '={1}{0}+{2}{0}*$D$1+{3}{0}*$D$2'.format(
    #                     row,
    #                     xl_col_to_name(start_column + shift + element * width),
    #                     xl_col_to_name(start_column + shift + element * width + 1),
    #                     xl_col_to_name(start_column + shift + element * width + 2),
    #                 )
    #                 sheet.merge_range(
    #                     row,
    #                     start_column + shift + element * width,
    #                     row,
    #                     start_column + shift + element * width + 2,
    #                     formula,
    #                     format
    #                 )
    #                 if type == 'revenue':
    #                     sheet.write_string(row, start_column + shift + element * width + 3, '',
    #                                        format_cross)
    #         else:
    #             shift = 0
    #             if type == 'acceptance':
    #                 start_column += 148
    #                 width = 4
    #             elif type == 'margin':
    #                 start_column += 178
    #                 width = 4
    #             for element in range(len(self.quarter_names)):
    #                 if element in [5]:  # учитываем колонки планов
    #                     shift += 1
    #                 formula = '={1}{0}+{2}{0}*$D$1+{3}{0}*$D$2'.format(
    #                     row,
    #                     xl_col_to_name(start_column + shift + element * width),
    #                     xl_col_to_name(start_column + shift + element * width + 1),
    #                     xl_col_to_name(start_column + shift + element * width + 2),
    #                 )
    #                 sheet.merge_range(
    #                     row,
    #                     start_column + shift + element * width,
    #                     row,
    #                     start_column + shift + element * width + 2,
    #                     formula,
    #                     format
    #                 )
    #             if type == 'acceptance':
    #                 sheet.write_string(row, start_column + shift + element * width + 3, '',
    #                                    format_cross)
    #     for type,shifts in plan_shift.items():
    #         formula = '={1}{0}*$D$1+{2}{0}*$D$2'.format(
    #             row,
    #             xl_col_to_name(shifts['NEXT'] + 1),
    #             xl_col_to_name(shifts['NEXT'] + 2),
    #         )
    #         sheet.merge_range(row, shifts['NEXT'] + 1, row, shifts['NEXT'] + 2, formula, format)
    #         formula = '={1}{0}*$D$1+{2}{0}*$D$2'.format(
    #             row,
    #             xl_col_to_name(shifts['AFTER_NEXT'] + 1),
    #             xl_col_to_name(shifts['AFTER_NEXT'] + 2),
    #         )
    #         sheet.merge_range(row, shifts['AFTER_NEXT'] + 1, row, shifts['AFTER_NEXT'] + 2, formula, format)
    #         if type in ('revenue', 'acceptance'):
    #             sheet.write_string(row, shifts['NEXT'] + 3, '', format_cross)
    #             sheet.write_string(row, shifts['AFTER_NEXT'] + 3, '', format_cross)

    def print_row(self, sheet, workbook, companies, project_offices, project_managers, estimated_probabilities, year, budget, row, level):
        global dict_formula

        office_heading_format = workbook.add_format({
            'bold': True,
            'border': 2,
            'font_size': 14,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '#,##0',
            'fg_color': '#D0CECE'
        })

        company_heading_format = workbook.add_format({
            'bold': True,
            'border': 2,
            'font_size': 15,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '#,##0',
            'fg_color': '#A0A0A0'
        })

        line_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "num_format": '#,##0',
        })

        bold_line_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "num_format": '#,##0',
        })

        bold_border_line_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'right': 2,
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "num_format": '#,##0',
        })

        bluegrey_percent_format = workbook.add_format({
            'border': 1,
            'right': 2,
            'left': 2,
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '0.00%',
            'fg_color': '#D6DCE4'
        })

        bluegrey_bold_percent_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'right': 2,
            'left': 2,
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '0.00%',
            'fg_color': '#D6DCE4'
        })

        grey_line_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '#,##0\ _₽;[Red]-#,##0\ _₽',
            'fg_color': '#E7E6E6'
        })

        grey_percent_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '0.00%',
            'fg_color': '#E7E6E6'
        })

        grey_borders_line_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'right': 2,
            'left': 2,
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '#,##0\ _₽;[Red]-#,##0\ _₽',
            'fg_color': '#E7E6E6'
        })

        is_found_projects_by_company = False
        is_found_projects_by_office = False

        cur_budget_projects = self.env['project_budget.projects'].search([
            ('commercial_budget_id', '=', budget.id), ('estimated_probability_id', 'in', estimated_probabilities.ids)
        ])

        cur_project_offices = project_offices
        cur_companies = companies.filtered(lambda r: r in cur_project_offices.company_id)

        for company in cur_companies:
            print('company =', company.name)

            company_data = {}  # инициализируем словарь офисов
            for section in self.company_section_names:
                company_data.setdefault(section, {})
                for quarter in self.quarter_names:
                    company_data[section].setdefault(quarter, {})
                    for probability in self.probability_names:
                        company_data[section][quarter][probability] = 0

            for section in self.company_section_names:  # планы компании
                section_plan = self.env['project_budget.budget_plan_supervisor_spec'].search([
                    ('budget_plan_supervisor_id.year', '=', year),
                    ('budget_plan_supervisor_id.company_id', '=', company.id),
                    ('budget_plan_supervisor_id.is_company_plan', '=', True),
                    ('type_row', '=', section),
                ])

                company_data[section]['Q1']['plan'] = section_plan.q1_plan
                company_data[section]['Q2']['plan'] = section_plan.q2_plan
                company_data[section]['Q3']['plan'] = section_plan.q3_plan
                company_data[section]['Q4']['plan'] = section_plan.q4_plan

            is_found_projects_by_company = False
            formula_company = []

            row0 = row

            for project_office in cur_project_offices.filtered(lambda r: r in (office for office in self.env[
                'project_budget.project_office'].search([('company_id', '=', company.id), ]))):
                print('project_office =', project_office.name, level)

                office_data = {}  # инициализируем словарь офисов
                for section in self.section_names:
                    office_data.setdefault(section, {})
                    for quarter in self.quarter_names:
                        office_data[section].setdefault(quarter, {})
                        for probability in self.probability_names:
                            office_data[section][quarter][probability] = 0

                child_project_offices = self.env['project_budget.project_office'].search(
                    [('parent_id', '=', project_office.id)], order='name')

                row0 = self.print_row(sheet, workbook, companies, child_project_offices, project_managers, estimated_probabilities, year, budget, row, level + 1)

                is_found_projects_by_office = False
                if row0 != row:
                    is_found_projects_by_office = True

                row = row0

                for section in self.section_names:  # планы проектного офиса
                    section_plan = self.env['project_budget.budget_plan_supervisor_spec'].search([
                        ('budget_plan_supervisor_id.year', '=', year),
                        ('budget_plan_supervisor_id.project_office_id', '=', project_office.id),
                        ('type_row', '=', section),
                    ])

                    office_data[section]['Q1']['plan'] = section_plan.q1_plan
                    office_data[section]['Q2']['plan'] = section_plan.q2_plan
                    office_data[section]['Q3']['plan'] = section_plan.q3_plan
                    office_data[section]['Q4']['plan'] = section_plan.q4_plan

                for spec in cur_budget_projects:
                    if spec.id in dict_formula['printed_projects']:
                        continue
                    if not (spec.project_office_id == project_office or (spec.legal_entity_signing_id.different_project_offices_in_steps and spec.project_have_steps)):
                        continue
                    # if spec.estimated_probability_id.name != '0':
                    # if spec.is_framework == True and spec.project_have_steps == False: continue # рамка без этапов - пропускаем
                    if spec.vgo == '-':
                        cur_project_rate = self.get_currency_rate_by_project(spec)

                        if spec.project_have_steps:
                            for step in spec.project_steps_ids:
                                if step.id in dict_formula['printed_steps']:
                                    continue

                                if ((spec.legal_entity_signing_id.different_project_offices_in_steps and step.project_office_id == project_office)
                                        or ((not spec.legal_entity_signing_id.different_project_offices_in_steps or not step.project_office_id) and spec.project_office_id == project_office)):

                                    if self.is_step_in_year(spec, step, year) == False:
                                        continue

                                    is_found_projects_by_company = True
                                    is_found_projects_by_office = True

                                    for quarter in self.quarter_names:

                                        # Контрактование, с НДС
                                        contracting_q_100_tmp = contracting_q_75_tmp = contracting_q_50_tmp = contracting_q_30_tmp = 0

                                        (
                                            contracting_q_100_tmp,
                                            contracting_q_75_tmp,
                                            contracting_q_50_tmp,
                                            contracting_q_30_tmp
                                        ) = self.get_quarter_revenue_project(quarter, spec, step, year)

                                        office_data['contracting'][quarter]['30'] += contracting_q_30_tmp
                                        office_data['contracting'][quarter]['50'] += contracting_q_50_tmp
                                        office_data['contracting'][quarter]['75'] += contracting_q_75_tmp
                                        office_data['contracting'][quarter]['100'] += contracting_q_100_tmp

                                        # Поступление денежных средств, с НДС
                                        cash_q_100_tmp = cash_q_75_tmp = cash_q_50_tmp = 0

                                        (
                                            cash_q_100_tmp,
                                            cash_q_75_tmp,
                                            cash_q_50_tmp
                                        ) = self.get_quarter_pds_project(quarter, spec, step, year)

                                        office_data['cash'][quarter]['50'] += cash_q_50_tmp
                                        office_data['cash'][quarter]['75'] += cash_q_75_tmp
                                        office_data['cash'][quarter]['100'] += cash_q_100_tmp

                                        # Валовая Выручка, без НДС
                                        revenue_q_100_tmp = revenue_q_75_tmp = revenue_q_50_tmp = 0
                                        margin_income_q_100_tmp = margin_income_q_75_tmp = margin_income_q_50_tmp = 0

                                        (
                                            revenue_q_100_tmp,
                                            revenue_q_75_tmp,
                                            revenue_q_50_tmp,
                                            margin_income_q_100_tmp,
                                            margin_income_q_75_tmp,
                                            margin_income_q_50_tmp
                                        ) = self.get_quarter_acceptance_project(quarter, spec, step, year)

                                        office_data['acceptance'][quarter]['50'] += revenue_q_50_tmp
                                        office_data['acceptance'][quarter]['75'] += revenue_q_75_tmp
                                        office_data['acceptance'][quarter]['100'] += revenue_q_100_tmp

                                        office_data['margin_income'][quarter]['50'] += margin_income_q_50_tmp
                                        office_data['margin_income'][quarter]['75'] += margin_income_q_75_tmp
                                        office_data['margin_income'][quarter]['100'] += margin_income_q_100_tmp

                        else:
                            if spec.project_office_id == project_office:
                                if self.is_project_in_year(spec, year) == False:
                                    continue

                                is_found_projects_by_company = True
                                is_found_projects_by_office = True

                                for quarter in self.quarter_names:

                                    # Контрактование, с НДС
                                    contracting_q_100_tmp = contracting_q_75_tmp = contracting_q_50_tmp = contracting_q_30_tmp = 0

                                    (
                                        contracting_q_100_tmp,
                                        contracting_q_75_tmp,
                                        contracting_q_50_tmp,
                                        contracting_q_30_tmp
                                    ) = self.get_quarter_revenue_project(quarter, spec, False, year)

                                    office_data['contracting'][quarter]['30'] += contracting_q_30_tmp
                                    office_data['contracting'][quarter]['50'] += contracting_q_50_tmp
                                    office_data['contracting'][quarter]['75'] += contracting_q_75_tmp
                                    office_data['contracting'][quarter]['100'] += contracting_q_100_tmp

                                    # Поступление денежных средств, с НДС
                                    cash_q_100_tmp = cash_q_75_tmp = cash_q_50_tmp = 0

                                    (
                                        cash_q_100_tmp,
                                        cash_q_75_tmp,
                                        cash_q_50_tmp
                                    ) = self.get_quarter_pds_project(quarter, spec, False, year)

                                    office_data['cash'][quarter]['50'] += cash_q_50_tmp
                                    office_data['cash'][quarter]['75'] += cash_q_75_tmp
                                    office_data['cash'][quarter]['100'] += cash_q_100_tmp

                                    # Валовая Выручка, без НДС
                                    revenue_q_100_tmp = revenue_q_75_tmp = revenue_q_50_tmp = 0
                                    margin_income_q_100_tmp = margin_income_q_75_tmp = margin_income_q_50_tmp = 0

                                    (
                                        revenue_q_100_tmp,
                                        revenue_q_75_tmp,
                                        revenue_q_50_tmp,
                                        margin_income_q_100_tmp,
                                        margin_income_q_75_tmp,
                                        margin_income_q_50_tmp
                                    ) = self.get_quarter_acceptance_project(quarter, spec, False, year)

                                    office_data['acceptance'][quarter]['50'] += revenue_q_50_tmp
                                    office_data['acceptance'][quarter]['75'] += revenue_q_75_tmp
                                    office_data['acceptance'][quarter]['100'] += revenue_q_100_tmp

                                    office_data['margin_income'][quarter]['50'] += margin_income_q_50_tmp
                                    office_data['margin_income'][quarter]['75'] += margin_income_q_75_tmp
                                    office_data['margin_income'][quarter]['100'] += margin_income_q_100_tmp

                if is_found_projects_by_office:

                    if level == 1:
                        
                        formula_company.append(row)

                        sheet.merge_range(row, 0, row, 21, f'{project_office.name}', office_heading_format)  # печатаем заголовок ПО
                        row += 1

                        for section in self.section_names:
                            column = 0
                            sheet.set_row(row, 31)
                            sheet.write_string(row, 0, self.section_titles[section], bold_border_line_format)
                            if 'margin' in section:
                                custom_line_format = bold_line_format
                                bluegrey_custom_percent_format = bluegrey_bold_percent_format
                            else:
                                custom_line_format = line_format
                                bluegrey_custom_percent_format = bluegrey_percent_format
                            for quarter in self.quarter_names:
                                sheet.write_number(row, column + 1, office_data[section][quarter]['plan'], custom_line_format)
                                sheet.write_number(row, column + 2, office_data[section][quarter]['100'], custom_line_format)
                                sheet.write_number(row, column + 3, office_data[section][quarter]['75'] + office_data[section][quarter]['50'] * self.POTENTIAL, custom_line_format)
                                formula = f'=IFERROR({xl_col_to_name(column + 2)}{row + 1}/{xl_col_to_name(column + 1)}{row + 1}, " ")'
                                sheet.write_formula(row, column + 4, formula, bluegrey_custom_percent_format)
                                column += 4
                            formula = (
                                f'={xl_col_to_name(column - 15)}{row + 1}'
                                f'+{xl_col_to_name(column - 11)}{row + 1}'
                                f'+{xl_col_to_name(column - 7)}{row + 1}'
                                f'+{xl_col_to_name(column - 3)}{row + 1}'
                            )
                            sheet.write_formula(row, column + 1, formula, grey_line_format)
                            formula = (
                                f'={xl_col_to_name(column - 14)}{row + 1}'
                                f'+{xl_col_to_name(column - 10)}{row + 1}'
                                f'+{xl_col_to_name(column - 6)}{row + 1}'
                                f'+{xl_col_to_name(column - 2)}{row + 1}'
                            )
                            sheet.write_formula(row, column + 2, formula, grey_line_format)
                            formula = (
                                f'={xl_col_to_name(column - 13)}{row + 1}'
                                f'+{xl_col_to_name(column - 9)}{row + 1}'
                                f'+{xl_col_to_name(column - 5)}{row + 1}'
                                f'+{xl_col_to_name(column - 1)}{row + 1}'
                                f'+{xl_col_to_name(column - 14)}{row + 1}'
                                f'+{xl_col_to_name(column - 10)}{row + 1}'
                                f'+{xl_col_to_name(column - 6)}{row + 1}'
                                f'+{xl_col_to_name(column - 2)}{row + 1}'
                            )
                            sheet.write_formula(row, column + 3, formula, grey_line_format)
                            formula = f'=IFERROR({xl_col_to_name(column + 2)}{row + 1}/{xl_col_to_name(column + 1)}{row + 1}, " ")'
                            sheet.write_formula(row, column + 4, formula, grey_percent_format)
                            formula = (
                                f'={xl_col_to_name(column + 3)}{row + 1}'
                                f'-{xl_col_to_name(column + 1)}{row + 1}'
                            )
                            sheet.write_formula(row, column + 5, formula, grey_borders_line_format)
                            row += 1

                    # if not project_office.parent_id:
                    #     formula_company += ',{0}' + f'{row + 1}'
                    #
                    # str_project_office_id = 'project_office_' + str(int(project_office.parent_id))
                    # if str_project_office_id in dict_formula:
                    #     dict_formula[str_project_office_id] = dict_formula[str_project_office_id] + ',{0}' + str(row+1)
                    # else:
                    #     dict_formula[str_project_office_id] = ',{0}'+str(row+1)
                    #
                    # if not project_office.parent_id:  # корневой офис добавляем сразу
                    #     dict_formula['offices_lines'].add(row+1)
                    # else:  # ищем всех родителей и проверяем есть ли они в выбранных офисах, если нет, добавляем
                    #     parent = project_office.parent_id
                    #     while parent:
                    #         if parent.id in project_office_ids:
                    #             break
                    #         else:
                    #             parent = parent.parent_id
                    #     else:
                    #         dict_formula['offices_lines'].add(row + 1)
                    #
                    # str_project_office_id = 'project_office_' + str(int(project_office.id))
                    #
                    # if str_project_office_id in dict_formula:
                    #     formulaProjectOffice = formulaProjectOffice + dict_formula[str_project_office_id]+')'
                    # else:
                    #     formulaProjectOffice = formulaProjectOffice + ')'
                    #
                    # for colFormula in range(2, 9):
                    #     sheet.write_string(row, colFormula, '', row_format_office)
                    #
                    # for colFormula in list(range(9, 215)) + list(range(216, 230)) + list(range(231, 245)):
                    #     formula = formulaProjectOffice.format(xl_col_to_name(colFormula))
                    #     # print('formula = ', formula)
                    #     sheet.write_formula(row, colFormula, formula, row_format_office)
                    #
                    # for type in plan_shift:  # кресты в планах
                    #     for c in plan_shift[type].values():
                    #         sheet.write_string(row, c, '', row_format_plan_cross)

            if is_found_projects_by_company:
                column = 0

                if level == 1:  # печатаем заголовок компании
                    sheet.merge_range(row, column, row, column + 21, f'ИТОГО {company.name}', company_heading_format)
                    row += 1

                    for section in self.company_section_names:
                        column = 0
                        sheet.set_row(row, 31)
                        sheet.write_string(row, 0, self.company_section_titles[section], bold_border_line_format)
                        if section in ('margin_income', 'margin3_income', 'ebit', 'net_profit'):
                            custom_line_format = bold_line_format
                            bluegrey_custom_percent_format = bluegrey_bold_percent_format
                        else:
                            custom_line_format = line_format
                            bluegrey_custom_percent_format = bluegrey_percent_format
                        for quarter in self.quarter_names:
                            sheet.write_number(row, column + 1, company_data[section][quarter]['plan'],
                                               custom_line_format)
                            if section not in ('ebit', 'net_profit'):
                                formula_fact = '=sum(' + ','.join(xl_col_to_name(column + 2) + str(
                                    office_row + self.company_section_names.index(section) + 2) for office_row in
                                                                  formula_company) + ')'
                                formula_forecast = '=sum(' + ','.join(xl_col_to_name(column + 3) + str(
                                    office_row + self.company_section_names.index(section) + 2) for office_row in
                                                             formula_company) + ')'
                            else:
                                formula_fact = formula_forecast = ''
                            sheet.write_formula(row, column + 2, formula_fact, custom_line_format)
                            sheet.write_formula(row, column + 3, formula_forecast, custom_line_format)
                            formula = f'=IFERROR({xl_col_to_name(column + 2)}{row + 1}/{xl_col_to_name(column + 1)}{row + 1}, " ")'
                            sheet.write_formula(row, column + 4, formula, bluegrey_custom_percent_format)
                            column += 4
                        formula = (
                            f'={xl_col_to_name(column - 15)}{row + 1}'
                            f'+{xl_col_to_name(column - 11)}{row + 1}'
                            f'+{xl_col_to_name(column - 7)}{row + 1}'
                            f'+{xl_col_to_name(column - 3)}{row + 1}'
                        )
                        sheet.write_formula(row, column + 1, formula, grey_line_format)
                        formula = (
                            f'={xl_col_to_name(column - 14)}{row + 1}'
                            f'+{xl_col_to_name(column - 10)}{row + 1}'
                            f'+{xl_col_to_name(column - 6)}{row + 1}'
                            f'+{xl_col_to_name(column - 2)}{row + 1}'
                        )
                        sheet.write_formula(row, column + 2, formula, grey_line_format)
                        formula = (
                            f'={xl_col_to_name(column - 13)}{row + 1}'
                            f'+{xl_col_to_name(column - 9)}{row + 1}'
                            f'+{xl_col_to_name(column - 5)}{row + 1}'
                            f'+{xl_col_to_name(column - 1)}{row + 1}'
                            f'+{xl_col_to_name(column - 14)}{row + 1}'
                            f'+{xl_col_to_name(column - 10)}{row + 1}'
                            f'+{xl_col_to_name(column - 6)}{row + 1}'
                            f'+{xl_col_to_name(column - 2)}{row + 1}'
                        )
                        sheet.write_formula(row, column + 3, formula, grey_line_format)
                        formula = f'=IFERROR({xl_col_to_name(column + 2)}{row + 1}/{xl_col_to_name(column + 1)}{row + 1}, " ")'
                        sheet.write_formula(row, column + 4, formula, grey_percent_format)
                        formula = (
                            f'={xl_col_to_name(column + 3)}{row + 1}'
                            f'-{xl_col_to_name(column + 1)}{row + 1}'
                        )
                        sheet.write_formula(row, column + 5, formula, grey_borders_line_format)
                        row += 1
                    row += 1

                # str_company_id = 'company_' + str(int(company.id))
                #
                # dict_formula['companies_lines'].add(row + 1)
                #
                # formula_company = formula_company + ')'
                #
                # for colFormula in range(2, 9):
                #     sheet.write_string(row, colFormula, '', row_format_number_itogo)
                #
                # for colFormula in list(range(9, 215)) + list(range(216, 230)) + list(range(231, 245)):
                #     formula = formula_company.format(xl_col_to_name(colFormula))
                #     sheet.write_formula(row, colFormula, formula, row_format_number_itogo)
                #
                # for type in plan_shift:  # кресты в планах
                #     for c in plan_shift[type].values():
                #         sheet.write_string(row, c, '', row_format_plan_cross)

        return row

    def printworksheet(self, workbook, budget, namesheet, estimated_probabilities, year):

        report_name = budget.name
        sheet = workbook.add_worksheet(namesheet)
        sheet.set_zoom(70)
        sheet.hide_zero()

        bold_heading_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'right': 2,
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'bottom',
            "num_format": '#,##0',
        })

        heading_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'bottom',
            "num_format": '#,##0',
        })

        bluegrey_heading_format = workbook.add_format({
            'border': 1,
            'right': 2,
            'left': 2,
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'bottom',
            'num_format': '#,##0',
            'fg_color': '#D6DCE4'
        })

        grey_heading_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'top': 2,
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'bottom',
            'num_format': '#,##0',
            'fg_color': '#E7E6E6'
        })

        grey_borders_heading_format = workbook.add_format({
            'bold': True,
            'border': 2,
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'bottom',
            'num_format': '#,##0',
            'fg_color': '#E7E6E6'
        })

        row = 0
        column = 0

        sheet.set_row(row, 16)
        sheet.set_row(row + 1, 31)
        sheet.freeze_panes(2, 1)

        sheet.merge_range(row, column, row + 1, column, "Наименование показателя/ период", bold_heading_format)
        quarter_names_list = [f"I кв. {year}", f"II кв. {year}", f"III кв. {year}", f"IV кв. кв. {year}"]
        sheet.set_column(column, column, 16)
        for quarter in quarter_names_list:
            sheet.merge_range(row, column + 1, row, column + 4, quarter, bold_heading_format)
            sheet.write_string(row + 1, column + 1, 'ПЛАН', heading_format)
            sheet.write_string(row + 1, column + 2, 'ФАКТ', heading_format)
            sheet.write_string(row + 1, column + 3, 'ПРОГНОЗ (100%+60%)', heading_format)
            sheet.write_string(row + 1, column + 4, f'% исполнения плана Q{quarter_names_list.index(quarter) + 1}', bluegrey_heading_format)
            sheet.set_column(column + 1, column + 4, 14)
            column += 4
        sheet.merge_range(row, column + 1, row, column + 5, f'ИТОГО {year}', grey_borders_heading_format)
        sheet.write_string(row + 1, column + 1, 'ПЛАН', grey_heading_format)
        sheet.write_string(row + 1, column + 2, 'ФАКТ', grey_heading_format)
        sheet.write_string(row + 1, column + 3, 'ПРОГНОЗ (100%+60%)', grey_heading_format)
        sheet.write_string(row + 1, column + 4, f'% исполнения плана {year}', grey_heading_format)
        sheet.write_string(row + 1, column + 5, 'Разница', grey_borders_heading_format)
        sheet.set_column(column + 1, column + 5, 14)
        row += 2

        companies = self.env['res.company'].search([], order='name')

        project_offices = self.env['project_budget.project_office'].search([('parent_id', '=', False)], order='name')  # для сортировки так делаем + берем сначала только верхние элементы

        project_managers = self.env['project_budget.project_manager'].search([], order='name')  # для сортировки так делаем

        row = self.print_row(sheet, workbook, companies, project_offices, project_managers, estimated_probabilities, year, budget, row, 1)

        # # ИТОГО
        # row += 1
        # column = 0
        # sheet.write_string(row, column, 'ИТОГО по отчету' , row_format_number_itogo)
        # sheet.write_string(row, column + 1, 'ИТОГО по отчету', row_format_number_itogo)
        # formula_itogo = False
        # formula_plan = False
        # if dict_formula['companies_lines']:
        #     formula_itogo = '=sum(' + ','.join(('{0}' + str(c)) for c in dict_formula['companies_lines']) + ')'
        #     formula_plan = '=sum(,' + ','.join(('{0}' + str(c + 1)) for c in dict_formula['companies_lines']) + ')'  # увеличиваем все номера строк на 1
        #     sheet.set_row(row, False, False, {'hidden': 1, 'level': 0})
        #     sheet.set_row(row + 1, False, False, {'hidden': 1, 'level': 0})
        # elif dict_formula['offices_lines']:
        #     formula_itogo = '=sum(' + ','.join(('{0}' + str(c)) for c in dict_formula['offices_lines']) + ')'
        #     formula_plan = '=sum(' + ','.join(('{0}' + str(c + 1)) for c in dict_formula['offices_lines']) + ')'  # увеличиваем все номера строк на 1
        #     sheet.set_row(row, False, False, {'hidden': 1, 'level': 1})
        #
        # if formula_itogo:
        #     for colFormula in range(2, 9):
        #         sheet.write_string(row, colFormula, '', row_format_number_itogo)
        #     for colFormula in list(range(9, 215)) + list(range(216, 230)) + list(range(231, 245)):
        #         formula = formula_itogo.format(xl_col_to_name(colFormula))
        #         sheet.write_formula(row, colFormula, formula, row_format_number_itogo)
        #
        # # расчетный план по отчету
        # row += 1
        # column = 0
        # sheet.write_string(row, column, 'ИТОГО: Расчетный План по отчету' , row_format_itogo_estimated_plan_left)
        # sheet.write_string(row, column + 1, 'ИТОГО: Расчетный План по отчету', row_format_itogo_estimated_plan_left)
        #
        # self.print_estimated_rows(sheet, row, row_format_itogo_estimated_plan,
        #                           row_format_itogo_estimated_plan_cross)
        #
        # for type in plan_shift:  # кресты в планах
        #     for c in plan_shift[type].values():
        #         if formula_plan:
        #             formula = formula_plan.format(xl_col_to_name(c))
        #             sheet.write_string(row - 1, c, '', row_format_plan_cross)
        #             sheet.write_formula(row, c, formula, row_format_plan)

    def generate_xlsx_report(self, workbook, data, budgets):

        global YEARint
        YEARint = data['year']
        global year_end
        year_end = data['year_end']

        year = data['year']

        global dict_formula
        global koeff_reserve
        global koeff_potential
        global margin_shift
        global plan_shift
        global fact_columns
        global project_office_ids
        koeff_reserve = data['koeff_reserve']
        koeff_potential = data['koeff_potential']
        fact_columns = set()
        project_office_ids=data['project_office_ids']
        commercial_budget_id = data['commercial_budget_id']

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

        dict_formula = {'printed_projects': set(), 'printed_steps': set(), 'companies_lines': set(), 'offices_lines': set()}
        budget = self.env['project_budget.commercial_budget'].search([('id', '=', commercial_budget_id)])
        estimated_probabilities = self.env['project_budget.estimated_probability'].search([('name', 'not in', ('0', '10'))], order='code desc')  # для сортировки так делаем
        self.printworksheet(workbook, budget, 'План-Факт', estimated_probabilities, year)