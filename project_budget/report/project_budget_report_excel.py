from odoo import models
from xlsxwriter.utility import xl_col_to_name

class report_budget_excel(models.AbstractModel):
    _name = 'report.project_budget.report_budget_excel'
    _description = 'project_budget.report_budget_excel'
    _inherit = 'report.report_xlsx.abstract'

    YEARint = 2023
    year_end = 2023

    probabitily_list_KB = ['30','50','75']
    probabitily_list_PB = ['100','100(done)']
    probabitily_list_Otmena = ['0']
    array_col_itogi = [12, 13,14,15,16,17,18,19,20,21,22,23,24,252,6,27,28]

    def get_currency_rate_by_project(self,project):
        project_currency_rates = self.env['project_budget.project_currency_rates']
        return project_currency_rates._get_currency_rate_for_project_in_company_currency(project)

    def printworksheet(self,workbook,budget,namesheet,stateproject):
        global YEARint
        global year_end
        global project_office_ids
        print('YEARint=',YEARint)
        report_name = budget.name

        total_amount_of_revenue = ''
        total_margin_income = ''

        start_row_of_project_office = 6

            # One sheet by partner
        sheet = workbook.add_worksheet(namesheet)
        bold = workbook.add_format({'bold': True})
        money_format = workbook.add_format({'num_format': '#,##0.00'})
        head_format = workbook.add_format({
            'bold': True,
            'italic': True,
            'border': 1,
            'font_name': 'Arial',
            'font_size': 11,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#3265a5',
            'color': '#ffffff'
        })

        head_light_format = workbook.add_format({
            'italic': True,
            'border': 1,
            'font_name': 'Arial',
            'font_size': 11,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#3265a5',
            'color': '#ffffff'
        })

        row_format_date_month = workbook.add_format({
            'border': 1,
            'font_size': 11,
            'font_name': 'Times New Roman'
            # 'num_format': 14
            #                'text_wrap' : True,
            #                'align': 'center',
            #                'valign': 'vcenter',
            #                'fg_color': '#3265a5',
        })

        row_format_date_month.set_num_format('mmmm yyyy')
        row_format = workbook.add_format({
            'border': 1,
            'font_size': 11,
            'font_name': 'Times New Roman'
            #                'text_wrap' : True,
            #                'align': 'center',
            #                'valign': 'vcenter',
            #                'fg_color': '#3265a5',
        })
        row_format_number = workbook.add_format({
            'border': 1,
            'font_size': 11,
            'num_format': '#,##0.00',
            'font_name': 'Times New Roman'
        })
        row_format_manager = workbook.add_format({
            'border': 1,
            'font_size': 11,
            "bold": True,
            "fg_color": '#D9D9D9',
            'font_name': 'Times New Roman'
        })
        row_format_manager.set_num_format('#,##0')

        row_format_itogo = workbook.add_format({
            'border': 1,
            'font_size': 11,
            "bold": True,
            "fg_color": '#bfbfbf',
            'font_name': 'Times New Roman'
        })
        row_format_itogo.set_num_format('#,##0.00')

        row_format_itogo_percent = workbook.add_format({
            'border': 1,
            'font_size': 11,
            "bold": True,
            "fg_color": '#bfbfbf',
            'font_name': 'Times New Roman'
        })
        row_format_itogo_percent.set_num_format('0%')

        format_subtotal = workbook.add_format({
            'font_size': 11,
            'bold': True,
            'font_name': 'Times New Roman',
            'num_format': '#,##0.00'
        })

        row_format_office = workbook.add_format({
            'border': 1,
            'font_size': 11,
            "bold": True,
            "fg_color": '#60497a',
            "color": '#ffffff',
            'font_name': 'Times New Roman'
        })
        row_format_office.set_num_format('#,##0.00')


        row_format_office_percent = workbook.add_format({
            'border': 1,
            'font_size': 11,
            "bold": True,
            "fg_color": '#60497a',
            "color": '#ffffff',
            'font_name': 'Times New Roman'
        })
        row_format_office_percent.set_num_format('0%')

        row_format_itog_row = workbook.add_format({
            'border': 1,
            'font_size': 11,
            "bold": True,
            "color": '#244062',
            'font_name': 'Times New Roman'
        })
        row_format_itog_row.set_num_format('#,##0.00')

        row_format_percent_row = workbook.add_format({
            'border': 1,
            'font_size': 11,
            "bold": True,
            "color": '#244062',
            'font_name': 'Times New Roman'
        })
        row_format_percent_row.set_num_format('0%')


        date_format = workbook.add_format({'num_format': 'd mmmm yyyy'})
        row = 0
        sheet.merge_range(row,0,row,5, budget.name, bold)
        row += 1
        sheet.merge_range(row, 0, row, 1,"Состояние бюджета")
        sheet.merge_range(row, 2, row, 4,budget.budget_state, bold)
        row += 1
        sheet.merge_range(row, 0, row, 1, "Дата актуализации бюджета")
        if budget.date_actual:
            sheet.merge_range(row, 2, row, 4, budget.date_actual.strftime("%d/%m/%Y"), bold)
        row += 1
        sheet.merge_range(row, 0, row, 1, "Описание")
        sheet.merge_range(row, 2, row, 6, budget.descr  or "", bold)

        row += 2

        column = 0
        sheet.write_string(row, column, "CRM ID",head_format)
        sheet.set_column(column, column, 14)
        column += 1
        sheet.write_string(row, column, "Проектный офис",head_format)
        sheet.set_column(column, column, 14)
        column += 1
        sheet.write_string(row, column, "Куратор проекта",head_format)
        sheet.set_column(column, column, 20)
        column += 1
        sheet.write_string(row, column, "Руководитель проекта",head_format)
        sheet.set_column(column, column, 15)
        column += 1
        sheet.write_string(row, column, "Заказчик/Организация",head_format)
        sheet.set_column(column, column, 25)
        column += 1
        # sheet.write_string(row, column, "Статус Заказчика",head_format)
        # sheet.set_column(column, column, 14)
        # column += 1
        sheet.write_string(row, column, "Отрасль",head_format)
        sheet.set_column(column, column, 18)
        column += 1
        sheet.write_string(row, column, "Суть проекта",head_format)
        sheet.set_column(column, column, 45)
        column += 1
        sheet.write_string(row, column, "Дата окончания Presale-проекта (квартал)",head_format)
        sheet.set_column(column, column, 15)
        column += 1
        sheet.write_string(row, column, "Дата перехода в Производственный бюджет (МЕСЯЦ)",head_format)
        sheet.set_column(column, column, 15)
        column += 1
        sheet.write_string(row, column, " Дата окончания Sale-проекта (квартал)",head_format)
        sheet.set_column(column, column, 10)
        column += 1
        sheet.write_string(row, column, "Период отгрузки либо оказания услуг Клиенту (МЕСЯЦ)",head_format)
        sheet.set_column(column, column, 10)
        column += 1
        sheet.write_string(row, column, "Признак НДС",head_format)
        sheet.set_column(column, column, 13)
        column += 1
        sheet.write_string(row, column, "Выручка от реализации работ(услуг), руб.", head_light_format)
        sheet.set_column(column, column, 10, None, {'hidden': 1, 'level': 1})
        column += 1
        sheet.write_string(row, column, "Выручка от реализации товара, руб.", head_light_format)
        sheet.set_column(column, column, 10, None, {'hidden': 1, 'level': 1})
        column += 1
        sheet.write_string(row, column, "Общая сумма выручки, руб.", head_format)
        sheet.set_column(column, column, 13)
        column += 1
        sheet.write_string(row, column, "Себестоимость товаров, руб.", head_light_format)
        sheet.set_column(column, column, 10, None, {'hidden': 1, 'level': 1})
        column += 1
        sheet.write_string(row, column, "Работы собственные (ФОТ), руб.", head_light_format)
        sheet.set_column(column, column, 10, None, {'hidden': 1, 'level': 1})
        column += 1
        sheet.write_string(row, column, "Работы сторонние (субподряд), руб.", head_light_format)
        sheet.set_column(column, column, 10, None, {'hidden': 1, 'level': 1})
        column += 1
        sheet.write_string(row, column, "Премии по итогам проекта, руб.", head_light_format)
        sheet.set_column(column, column, 10, None, {'hidden': 1, 'level': 1})
        column += 1
        sheet.write_string(row, column, "Транспортные расходы, руб.", head_light_format)
        sheet.set_column(column, column, 10, None, {'hidden': 1, 'level': 1})
        column += 1
        sheet.write_string(row, column, "Командировочные расходы, руб.", head_light_format)
        sheet.set_column(column, column, 10, None, {'hidden': 1, 'level': 1})
        column += 1
        sheet.write_string(row, column, "Представительские расходы, руб.", head_light_format)
        sheet.set_column(column, column, 10, None, {'hidden': 1, 'level': 1})
        column += 1
        sheet.write_string(row, column, "Налоги на ФОТ и премии, руб.", head_light_format)
        sheet.set_column(column, column, 10, None, {'hidden': 1, 'level': 1})
        column += 1
        sheet.write_string(row, column, "Расходы на гарант. обслуж., руб.", head_light_format)
        sheet.set_column(column, column, 10, None, {'hidden': 1, 'level': 1})
        column += 1
        sheet.write_string(row, column, "РКО прочие руб.", head_light_format)
        sheet.set_column(column, column, 10, None, {'hidden': 1, 'level': 1})
        column += 1
        sheet.write_string(row, column, "Прочие расходы, руб.", head_light_format)
        sheet.set_column(column, column, 10, None, {'hidden': 1, 'level': 1})
        column += 1
        sheet.write_string(row, column, "Себестоимость, руб.",head_format)
        sheet.set_column(column, column, 13)
        column += 1
        sheet.write_string(row, column, "Маржинальный доход, руб.",head_format)
        sheet.set_column(column, column, 13)
        column += 1
        sheet.write_string(row, column, "Рентабельность (доля Sale маржи в выручке)",head_format)
        sheet.set_column(column, column, 10)
        column += 1
        sheet.write_string(row, column, "Оценочная вероятность реализации проекта, %",head_format)
        sheet.set_column(column, column, 10)
        column += 1
        sheet.write_string(row, column, "юрлицо, подписывающее договор от НКК",head_format)
        sheet.set_column(column, column, 15)
        column += 1
        sheet.write_string(row, column, "Тип проекта",head_format)
        sheet.set_column(column, column, 10)
        column += 1
        sheet.write_string(row, column, "Комментарии",head_format)
        sheet.set_column(column, column, 15)
        column += 1
        sheet.write_string(row, column, "Технологическое направление",head_format)
        sheet.set_column(column, column, 15)
        sheet.autofilter(row, 0, row, column)
        sheet.freeze_panes(6, 7)
        probabitily_list = ['']
        if stateproject == 'prepare':
            probabitily_list = self.probabitily_list_KB
        if stateproject == 'production':
            probabitily_list = self.probabitily_list_PB
        if stateproject == 'cancel':
            probabitily_list = self.probabitily_list_Otmena

        # sheet.set_column(14, 17, False, False, {'hidden': 1, 'level': 1})
        # sheet.set_column(20, 29, False, False, {'hidden': 1, 'level': 1})

        if project_office_ids:
            child_project_offices = self.env['project_budget.project_office'].search(
                [('id', 'in', project_office_ids)]).child_ids
            while child_project_offices:  # обходим дочерние офисы
                for child_project_office in child_project_offices:
                    if child_project_office.id not in project_office_ids:
                        project_office_ids.append(child_project_office.id)
                new_child_project_offices = child_project_offices.child_ids
                child_project_offices = new_child_project_offices

            project_offices = self.env['project_budget.project_office'].search([
                ('id','in',project_office_ids)], order='name')  # для сортировки так делаем
        else:
            project_offices = self.env['project_budget.project_office'].search([], order='name')
        key_account_managers = self.env.ref(
            'project_budget.group_project_budget_key_account_manager').users.employee_ids.sorted('name')
        # project_managers = self.env['project_budget.project_manager'].search([], order='name')  # для сортировки так делаем
        stages = self.env['project_budget.project.stage'].search([], order='sequence desc')  # для сортировки так делаем

        isFoundProjectsByOffice = False
        isFoundProjectsByManager = False
        begRowProjectsByoffice = 0

        formulaItogo = '=sum(0'
        for project_office in project_offices:
            isFoundProjectsByOffice = False
            begRowProjectsByoffice = 0
            for key_account_manager in key_account_managers:
                # print('project_manager = ', project_manager.name)
                isFoundProjectsByManager = False

                column = -1

                for stage in stages:
                    # print('estimated_probability.name = ', estimated_probability.name)
                    cur_budget_projects = self.env['project_budget.projects'].search([
                        ('project_office_id', '=', project_office.id),
                        ('commercial_budget_id', '=', budget.id),
                        ('key_account_manager_id', '=', key_account_manager.id),
                        # ('project_manager_id', '=', project_manager.id),
                        ('stage_id', '=', stage.id),
                        '|', '&',('step_status', '=', 'step'),
                        ('step_project_parent_id.project_have_steps', '=', True),
                        ('project_have_steps', '=', False),
                    ], order='project_id')

                    for spec in cur_budget_projects:
                        currency_rate = self.get_currency_rate_by_project(spec)
                        if spec.is_framework == True: continue # 20230718 Алина Козленко сказала не выгружать в принципе рамки
                        if (spec.stage_id.code in probabitily_list) and (
                                (spec.end_presale_project_month.year >= YEARint and spec.end_presale_project_month.year <= year_end)
                                    or (spec.end_sale_project_month.year >= YEARint and spec.end_sale_project_month.year <= year_end)
                                    or (spec.end_presale_project_month.year <= YEARint and spec.end_sale_project_month.year >= year_end)):
                            row += 1
                            isFoundProjectsByManager = True
                            isFoundProjectsByOffice = True
                            if begRowProjectsByoffice == 0:
                                begRowProjectsByoffice = row
                            sheet.set_row(row, False, False, {'hidden': 1, 'level': 1})
                            column = 0
                            if spec.step_status == 'step':
                                sheet.write_string(row, column, (spec.step_project_parent_id.project_id or '') + ' | ' + spec.project_id, row_format)
                            else:
                                sheet.write_string(row, column, spec.project_id, row_format)
                            column += 1
                            sheet.write_string(row, column, spec.project_office_id.name, row_format)
                            column += 1
                            sheet.write_string(row, column, spec.project_supervisor_id.name, row_format)
                            column += 1
                            if spec.project_office_id.print_rukovoditel_in_kb == False:
                                sheet.write_string(row, column, spec.key_account_manager_id.name, row_format)
                            else:
                                sheet.write_string(row, column, spec.project_manager_id.name or '', row_format)
                            column += 1
                            sheet.write_string(row, column, spec.partner_id.name, row_format)
                            column += 1
                            # sheet.write_string(row, column, spec.customer_status_id.name, row_format)
                            # column += 1
                            sheet.write_string(row, column, spec.industry_id.name, row_format)
                            column += 1
                            sheet.write_string(row, column, spec.essence_project  or "", row_format)
                            column += 1
                            sheet.write_string(row, column, spec.end_presale_project_quarter, row_format)
                            column += 1
                            sheet.write_datetime(row, column, spec.end_presale_project_month, row_format_date_month)
                            column += 1
                            sheet.write_string(row, column, spec.end_sale_project_quarter, row_format)
                            column += 1
                            sheet.write_datetime(row, column, spec.end_sale_project_month, row_format_date_month)
                            column += 1
                            sheet.write_string(row, column, spec.vat_attribute_id.name or "", row_format)
                            column += 1
                            sheet.write_number(row, column, spec.revenue_from_the_sale_of_works * currency_rate,row_format_number)
                            column += 1
                            sheet.write_number(row, column, spec.revenue_from_the_sale_of_goods * currency_rate,row_format_number)

                            column += 1
                            # sheet.write_number(row, column, spec.total_amount_of_revenue * currency_rate, row_format_number)
                            formula = '=sum({1}{0}:{2}{0})'.format(row+1,xl_col_to_name(12),xl_col_to_name(13))
                            sheet.write_formula(row, column, formula, row_format_itog_row)

                            column += 1
                            sheet.write_number(row, column, spec.cost_of_goods * currency_rate,row_format_number)
                            column += 1
                            sheet.write_number(row, column, spec.own_works_fot * currency_rate,row_format_number)
                            column += 1
                            sheet.write_number(row, column, spec.third_party_works * currency_rate,row_format_number)
                            column += 1
                            sheet.write_number(row, column, spec.awards_on_results_project * currency_rate,row_format_number)
                            column += 1
                            sheet.write_number(row, column, spec.transportation_expenses * currency_rate,row_format_number)
                            column += 1
                            sheet.write_number(row, column, spec.travel_expenses * currency_rate,row_format_number)
                            column += 1
                            sheet.write_number(row, column, spec.representation_expenses * currency_rate,row_format_number)
                            column += 1
                            sheet.write_number(row, column, spec.taxes_fot_premiums * currency_rate,row_format_number)
                            column += 1
                            sheet.write_number(row, column, spec.warranty_service_costs * currency_rate,row_format_number)
                            column += 1
                            sheet.write_number(row, column, spec.rko_other * currency_rate,row_format_number)
                            column += 1
                            sheet.write_number(row, column, spec.other_expenses * currency_rate,row_format_number)

                            column += 1
                            # sheet.write_number(row, column, spec.cost_price * currency_rate,row_format_number)
                            formula = '=sum({1}{0}:{2}{0})'.format(row + 1, xl_col_to_name(15), xl_col_to_name(25))
                            sheet.write_formula(row, column, formula, row_format_itog_row)

                            column += 1
                            # sheet.write_number(row, column, spec.margin_income * currency_rate,row_format_number)
                            formula = '={1}{0}-{2}{0}'.format(row + 1, xl_col_to_name(14), xl_col_to_name(26))
                            sheet.write_formula(row, column, formula, row_format_itog_row)

                            column += 1
                            # sheet.write(row, column, spec.profitability, row_format_number)
                            formula = '=IFERROR({2}{0}/{1}{0},0)'.format(row + 1, xl_col_to_name(14),
                                                                         xl_col_to_name(27))
                            sheet.write_formula(row, column, formula, row_format_percent_row)

                            column += 1
                            sheet.write(row, column, spec.stage_id.code, row_format_number)
                            column += 1
                            sheet.write(row, column, spec.legal_entity_signing_id.name, row_format)
                            column += 1
                            sheet.write_string(row, column, spec.project_type_id.name or "", row_format)
                            column += 1
                            sheet.write_string(row, column, spec.comments or "", row_format)
                            column += 1
                            sheet.write_string(row, column, spec.technological_direction_id.name, row_format)
            if isFoundProjectsByOffice:

                end_row_of_project_office = row  # считаем строки для промежуточных итогов
                total_amount_of_revenue += f'{xl_col_to_name(14)}{start_row_of_project_office + 1}:{xl_col_to_name(14)}{end_row_of_project_office + 1},'
                total_margin_income += f'{xl_col_to_name(27)}{start_row_of_project_office + 1}:{xl_col_to_name(27)}{end_row_of_project_office + 1},'
                start_row_of_project_office = end_row_of_project_office + 2

                row += 1
                column = 0
                # sheet.set_row(row, False, False, {'hidden': 1, 'level': 1})
                # print('setrow level1 row = ', row)
                # sheet.set_row(row, False, False, {'hidden': 1, 'level': 1})
                sheet.write_string(row, column, 'ИТОГО ' + project_office.name, row_format_office)
                formulaItogo = formulaItogo + ',{0}' + str(row + 1)
                # print('formulaProjectOffice = ',formulaProjectOffice)
                for colFormula in range(1, 34):
                    sheet.write_string(row, colFormula, '', row_format_office)
                for colFormula in range(12, 28):
                    formulaProjectOffice = '=sum({0}{1}:{0}{2})'.format(xl_col_to_name(colFormula),
                                                                        begRowProjectsByoffice + 1, row)
                    sheet.write_formula(row, colFormula, formulaProjectOffice, row_format_office)

                formula = '=IFERROR({2}{0}/{1}{0},0)'.format(row + 1, xl_col_to_name(14),
                                                             xl_col_to_name(27))
                sheet.write_formula(row, 28, formula, row_format_office_percent)

        row+=1
        formulaItogo = formulaItogo + ')'
        sheet.write_string(row, column, 'ИТОГО ',row_format_itogo)
        for colFormula in range(1, 34):
            sheet.write_string(row, colFormula, '', row_format_itogo)
        for colFormula in range(12, 28):
            formula = formulaItogo.format(xl_col_to_name(colFormula))
            # print('formula = ',formula)
            sheet.write_formula(row, colFormula, formula, row_format_itogo)

        if total_amount_of_revenue:  # пишем промежуточные итоги в ячейки
            sheet.write_formula('O4', f'=SUBTOTAL(9,{total_amount_of_revenue.rstrip(",")})', format_subtotal)
        if total_margin_income:
            sheet.write_formula('AB4', f'=SUBTOTAL(9,{total_margin_income.rstrip(",")})', format_subtotal)

    def generate_xlsx_report(self, workbook, data, budgets):
        print('report KB')
        print('data = ',data)

        global YEARint
        YEARint = data['year']
        global year_end
        year_end = data['year_end']
        global project_office_ids
        project_office_ids = data['project_office_ids']

        commercial_budget_id = data['commercial_budget_id']
        budget = self.env['project_budget.commercial_budget'].search([('id', '=', commercial_budget_id)])

        print('YEARint=',YEARint)

        self.printworksheet(workbook, budget, 'КБ', 'prepare')
        self.printworksheet(workbook, budget, 'ПБ', 'production')
        self.printworksheet(workbook, budget, 'Отменен', 'cancel')
