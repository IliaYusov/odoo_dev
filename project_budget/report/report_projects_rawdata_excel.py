from odoo import models
from xlsxwriter.utility import xl_col_to_name

class report_projects_rawdata_excel(models.AbstractModel):
    _name = 'report.project_budget.report_projects_rawdata_excel'
    _description = 'project_budget.report_projects_rawdata_excel'
    _inherit = 'report.report_xlsx.abstract'

    strYEAR = '2023'
    YEARint = int(strYEAR)

    probabitily_list_KB = ['30','50','75']
    probabitily_list_PB = ['100','100(done)']
    probabitily_list_Otmena = ['0']
    array_col_itogi = [12, 13,14,15,16,17,18,19,20,21,22,23,24,252,6,27,28]
    def printworksheet(self,workbook,budget,namesheet):
        global strYEAR
        global YEARint
        print('YEARint=',YEARint)
        print('strYEAR =', strYEAR)
        report_name = budget.name
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
        date_format = workbook.add_format({'num_format': 'd mmmm yyyy'})

        row = 0
        column = 0

        column = 0
        sheet.write_string(row, column, 'Компания', row_format)
        column += 1
        sheet.write_string(row, column, 'project_id', row_format)
        column += 1
        sheet.write_string(row, column, 'На согласовании', row_format)
        column += 1
        sheet.write_string(row, column, 'Статус проекта', row_format)
        column += 1
        sheet.write_string(row, column, 'Номер этапа проекта', row_format)
        column += 1
        sheet.write_string(row, column, 'Есть этапы', row_format)
        column += 1
        sheet.write_string(row, column, 'Рамка', row_format)
        column += 1
        sheet.write_string(row, column, 'Есть изменения', row_format)
        column += 1
        sheet.write_string(row, column, 'ВГО', row_format)
        column += 1
        sheet.write_string(row, column, 'Состояние бюджета', row_format)
        column += 1
        sheet.write_string(row, column, 'Валюта проекта', row_format)
        column += 1
        sheet.write_string(row, column, 'Проектный офис', row_format)
        column += 1
        sheet.write_string(row, column, 'Куратор', row_format)
        column += 1
        sheet.write_string(row, column, 'КАМ', row_format)
        column += 1
        sheet.write_string(row, column, 'Руководитель проекта', row_format)
        column += 1
        sheet.write_string(row, column, 'Отрасль', row_format)
        column += 1
        # sheet.write_string(row, column, 'Статус заказчика', row_format)
        # column += 1
        sheet.write_string(row, column, 'Заказчик/организация', row_format)
        column += 1
        sheet.write_string(row, column, 'Наименование проекта', row_format)
        column += 1
        sheet.write_string(row, column, 'Юрлицо, подписывающее договор от НКК', row_format)
        column += 1
        sheet.write_string(row, column, 'Комментарий к проекту', row_format)
        column += 1
        sheet.write_string(row, column, 'Технологическое направление', row_format)
        column += 1
        sheet.write_string(row, column, 'Тип проекта', row_format)
        column += 1
        sheet.write_string(row, column, 'Номер договора (проекта)', row_format)
        column += 1

        sheet.write_string(row, column, "step_id", row_format)  # step_id)
        column += 1
        sheet.write_string(row, column, "Тип этапа", row_format)  # project_steps_type_id)
        column += 1
        sheet.write_string(row, column, "Валюта", row_format)  # currency_id
        column += 1
        sheet.write_string(row, column, "Наименование (этапа)", row_format)  # essence_project
        column += 1
        sheet.write_string(row, column, "Номер договора (этапа)", row_format)  # dogovor_number
        column += 1
        sheet.write_string(row, column, 'Квартал контрактования', row_format)
        column += 1
        sheet.write_string(row, column, 'Дата контрактования', row_format_date_month)
        column += 1
        sheet.write_string(row, column, 'Квартал последней отгрузки', row_format)
        column += 1
        sheet.write_string(row, column, 'Последняя отгрузка', row_format_date_month)
        column += 1
        sheet.write_string(row, column, 'Признак НДС', row_format)
        column += 1
        sheet.write_string(row, column, 'Сумма выручки', row_format_number)
        column += 1
        sheet.write_string(row, column, "Сумма выручки с НДС", row_format_number)
        column += 1
        sheet.write_string(row, column, "Сумма прогноза актирования без НДС", row_format_number)
        column += 1
        sheet.write_string(row, column, "Сумма прогноза ПДС с НДС", row_format_number)
        column += 1
        sheet.write_string(row, column, "Выручка от реализации работ(услуг)", row_format_number)
        column += 1
        sheet.write_string(row, column, "Выручка от реализации товара", row_format_number)
        column += 1
        sheet.write_string(row, column, "Себестоимость проекта", row_format_number)
        column += 1
        sheet.write_string(row, column, "Себестоимость товаров", row_format_number)
        column += 1
        sheet.write_string(row, column, "Работы собственные (ФОТ)", row_format_number)
        column += 1
        sheet.write_string(row, column, "Работы сторонние (субподряд)", row_format_number)
        column += 1
        sheet.write_string(row, column, "Премии по итогам проекта", row_format_number)
        column += 1
        sheet.write_string(row, column, "Транспортные расходы", row_format_number)
        column += 1
        sheet.write_string(row, column, "Командировочные расходы", row_format_number)
        column += 1
        sheet.write_string(row, column, "Представительские расходы", row_format_number)
        column += 1
        sheet.write_string(row, column, "Налоги на ФОТ и премии", row_format_number)
        column += 1
        sheet.write_string(row, column, "Расходы на гарант. обслуж.", row_format_number)
        column += 1
        sheet.write_string(row, column, "РКО прочие", row_format_number)
        column += 1
        sheet.write_string(row, column, "Прочие расходы", row_format_number)
        column += 1
        sheet.write_string(row, column, "Маржа", row_format_number)
        column += 1
        sheet.write_string(row, column, "Рентабельность", row_format_number)
        column += 1
        sheet.write_string(row, column, "Вероятность", row_format_number)
        column += 1
        sheet.write_string(row, column, "Вероятность проекта", row_format_number)

        cur_budget_projects = self.env['project_budget.projects'].search([('commercial_budget_id', '=', budget.id)])

        for spec in cur_budget_projects:
            if spec.project_have_steps == False:
                if True == True: #spec.end_presale_project_month.year >= YEARint or spec.end_sale_project_month.year >= YEARint:
                    row += 1
                    column = 0
                    sheet.write_string(row, column, spec.company_id.name, row_format)
                    column += 1
                    sheet.write_string(row, column, spec.project_id, row_format)
                    column += 1
                    sheet.write_string(row, column, spec.approve_state, row_format)
                    column += 1
                    sheet.write_string(row, column, spec.specification_state, row_format)
                    column += 1
                    sheet.write_string(row, column, (spec.step_project_number or""), row_format)
                    column += 1
                    sheet.write_string(row, column, (str(spec.project_have_steps) or ""), row_format)
                    column += 1
                    sheet.write_string(row, column, (str(spec.is_framework) or ""), row_format)
                    column += 1
                    sheet.write_string(row, column, (str(spec.was_changes) or ""), row_format)
                    column += 1
                    sheet.write_string(row, column, (str(spec.vgo) or ""), row_format)
                    column += 1
                    sheet.write_string(row, column, spec.budget_state, row_format)
                    column += 1
                    sheet.write_string(row, column, spec.currency_id.name, row_format)
                    column += 1
                    sheet.write_string(row, column, spec.project_office_id.name, row_format)
                    column += 1
                    sheet.write_string(row, column, spec.project_supervisor_id.name, row_format)
                    column += 1
                    sheet.write_string(row, column, spec.project_manager_id.name, row_format)
                    column += 1
                    sheet.write_string(row, column, (spec.rukovoditel_project_id.name or ""), row_format)
                    column += 1
                    sheet.write_string(row, column, spec.industry_id.name, row_format)
                    column += 1
                    # sheet.write_string(row, column, spec.customer_status_id.name, row_format)
                    # column += 1
                    sheet.write_string(row, column, spec.partner_id.name, row_format)
                    column += 1
                    sheet.write_string(row, column, (spec.essence_project or ""), row_format)
                    column += 1
                    sheet.write_string(row, column, spec.legal_entity_signing_id.name, row_format)
                    column += 1
                    sheet.write_string(row, column, (spec.comments or ""), row_format)
                    column += 1
                    sheet.write_string(row, column, spec.technological_direction_id.name, row_format)
                    column += 1
                    sheet.write_string(row, column, spec.project_type_id.name, row_format)
                    column += 1
                    sheet.write_string(row, column, (spec.dogovor_number or ""), row_format)
                    column += 1

                    sheet.write_string(row, column, "", row_format) #step_id)
                    column += 1
                    sheet.write_string(row, column, "", row_format) #project_steps_type_id)
                    column += 1
                    sheet.write_string(row, column, "", row_format) #currency_id
                    column += 1
                    sheet.write_string(row, column, "", row_format) #essence_project
                    column += 1
                    sheet.write_string(row, column, "", row_format) #dogovor_number
                    column += 1
                    sheet.write_string(row, column, spec.end_presale_project_quarter, row_format)
                    column += 1
                    sheet.write_datetime(row, column, spec.end_presale_project_month,row_format_date_month)
                    column += 1
                    sheet.write_string(row, column, spec.end_sale_project_quarter, row_format)
                    column += 1
                    sheet.write_datetime(row, column, spec.end_sale_project_month, row_format_date_month)
                    column += 1
                    sheet.write_string(row, column, (spec.vat_attribute_id.name or ""), row_format)
                    column += 1
                    sheet.write_number(row, column, spec.total_amount_of_revenue, row_format_number)
                    column += 1
                    sheet.write_number(row, column, spec.total_amount_of_revenue_with_vat, row_format_number )
                    column += 1
                    sheet.write_number(row, column, spec.planned_acceptance_flow_sum_without_vat, row_format_number )
                    column += 1
                    sheet.write_number(row, column, spec.planned_cash_flow_sum , row_format_number )
                    column += 1
                    sheet.write_number(row, column, spec.revenue_from_the_sale_of_works, row_format_number )
                    column += 1
                    sheet.write_number(row, column, spec.revenue_from_the_sale_of_goods, row_format_number)
                    column += 1
                    sheet.write_number(row, column, spec.cost_price, row_format_number )
                    column += 1
                    sheet.write_number(row, column, spec.cost_of_goods, row_format_number )
                    column += 1
                    sheet.write_number(row, column, spec.own_works_fot, row_format_number )
                    column += 1
                    sheet.write_number(row, column, spec.third_party_works, row_format_number )
                    column += 1
                    sheet.write_number(row, column, spec.awards_on_results_project, row_format_number )
                    column += 1
                    sheet.write_number(row, column, spec.transportation_expenses, row_format_number )
                    column += 1
                    sheet.write_number(row, column, spec.travel_expenses, row_format_number)
                    column += 1
                    sheet.write_number(row, column, spec.representation_expenses, row_format_number )
                    column += 1
                    sheet.write_number(row, column, spec.taxes_fot_premiums, row_format_number )
                    column += 1
                    sheet.write_number(row, column, spec.warranty_service_costs, row_format_number )
                    column += 1
                    sheet.write_number(row, column, spec.rko_other, row_format_number )
                    column += 1
                    sheet.write_number(row, column, spec.other_expenses, row_format_number )
                    column += 1
                    sheet.write_number(row, column, spec.margin_income, row_format_number )
                    column += 1
                    sheet.write_number(row, column, spec.profitability, row_format_number )
                    column += 1
                    sheet.write_string(row, column, spec.estimated_probability_id.name, row_format_number)
                    column += 1
                    sheet.write_string(row, column, spec.estimated_probability_id.name, row_format_number)

            if spec.project_have_steps == True:
                for step in spec.project_steps_ids:
                    if True == True: #step.end_presale_project_month.year >= YEARint or step.end_sale_project_month.year >= YEARint:
                        row += 1
                        column = 0
                        sheet.write_string(row, column, spec.company_id.name, row_format)
                        column += 1
                        sheet.write_string(row, column, spec.project_id, row_format)
                        column += 1
                        sheet.write_string(row, column, spec.approve_state, row_format)
                        column += 1
                        sheet.write_string(row, column, spec.specification_state, row_format)
                        column += 1
                        sheet.write_string(row, column, (spec.step_project_number or ""), row_format)
                        column += 1
                        sheet.write_string(row, column, (str(spec.project_have_steps) or ""), row_format)
                        column += 1
                        sheet.write_string(row, column, (str(spec.is_framework) or ""), row_format)
                        column += 1
                        sheet.write_string(row, column, (str(spec.was_changes) or ""), row_format)
                        column += 1
                        sheet.write_string(row, column, (str(spec.vgo) or ""), row_format)
                        column += 1
                        sheet.write_string(row, column, spec.budget_state, row_format)
                        column += 1
                        sheet.write_string(row, column, spec.currency_id.name, row_format)
                        column += 1
                        if spec.legal_entity_signing_id.different_project_offices_in_steps and step.project_office_id:
                            sheet.write_string(row, column, step.project_office_id.name, row_format)
                        else:
                            sheet.write_string(row, column, spec.project_office_id.name, row_format)
                        column += 1
                        sheet.write_string(row, column, spec.project_supervisor_id.name, row_format)
                        column += 1
                        sheet.write_string(row, column, spec.project_manager_id.name, row_format)
                        column += 1
                        sheet.write_string(row, column, (spec.rukovoditel_project_id.name or ""), row_format)
                        column += 1
                        sheet.write_string(row, column, spec.industry_id.name, row_format)
                        column += 1
                        # sheet.write_string(row, column, spec.customer_status_id.name, row_format)
                        # column += 1
                        sheet.write_string(row, column, spec.partner_id.name, row_format)
                        column += 1
                        sheet.write_string(row, column, (spec.essence_project or ""), row_format)
                        column += 1
                        sheet.write_string(row, column, spec.legal_entity_signing_id.name, row_format)
                        column += 1
                        sheet.write_string(row, column, (spec.comments or ""), row_format)
                        column += 1
                        sheet.write_string(row, column, spec.technological_direction_id.name, row_format)
                        column += 1
                        sheet.write_string(row, column, spec.project_type_id.name, row_format)
                        column += 1
                        sheet.write_string(row, column, (spec.dogovor_number or ""), row_format)
                        column += 1

                        sheet.write_string(row, column, step.step_id, row_format)  # step_id)
                        column += 1
                        sheet.write_string(row, column, step.project_steps_type_id.name, row_format)  # project_steps_type_id)
                        column += 1
                        sheet.write_string(row, column, step.currency_id.name, row_format)  # currency_id
                        column += 1
                        sheet.write_string(row, column, (step.essence_project or ""), row_format)
                        column += 1
                        sheet.write_string(row, column, (step.dogovor_number or ""), row_format)
                        column += 1
                        sheet.write_string(row, column, step.end_presale_project_quarter, row_format)
                        column += 1
                        sheet.write_datetime(row, column, step.end_presale_project_month, row_format_date_month)
                        column += 1
                        sheet.write_string(row, column, step.end_sale_project_quarter, row_format)
                        column += 1
                        sheet.write_datetime(row, column, step.end_sale_project_month, row_format_date_month)
                        column += 1
                        sheet.write_string(row, column, (step.vat_attribute_id.name or ""), row_format)
                        column += 1
                        sheet.write_number(row, column, step.total_amount_of_revenue, row_format_number)
                        column += 1
                        sheet.write_number(row, column, step.total_amount_of_revenue_with_vat, row_format_number)
                        column += 1
                        sheet.write_number(row, column, step.planned_acceptance_flow_sum_without_vat, row_format_number)
                        column += 1
                        sheet.write_number(row, column, step.planned_cash_flow_sum, row_format_number)
                        column += 1
                        sheet.write_number(row, column, step.revenue_from_the_sale_of_works, row_format_number)
                        column += 1
                        sheet.write_number(row, column, step.revenue_from_the_sale_of_goods, row_format_number)
                        column += 1
                        sheet.write_number(row, column, step.cost_price, row_format_number)
                        column += 1
                        sheet.write_number(row, column, step.cost_of_goods, row_format_number)
                        column += 1
                        sheet.write_number(row, column, step.own_works_fot, row_format_number)
                        column += 1
                        sheet.write_number(row, column, step.third_party_works, row_format_number)
                        column += 1
                        sheet.write_number(row, column, step.awards_on_results_project, row_format_number)
                        column += 1
                        sheet.write_number(row, column, step.transportation_expenses, row_format_number)
                        column += 1
                        sheet.write_number(row, column, step.travel_expenses, row_format_number)
                        column += 1
                        sheet.write_number(row, column, step.representation_expenses, row_format_number)
                        column += 1
                        sheet.write_number(row, column, step.taxes_fot_premiums, row_format_number)
                        column += 1
                        sheet.write_number(row, column, step.warranty_service_costs, row_format_number)
                        column += 1
                        sheet.write_number(row, column, step.rko_other, row_format_number)
                        column += 1
                        sheet.write_number(row, column, step.other_expenses, row_format_number)
                        column += 1
                        sheet.write_number(row, column, step.margin_income, row_format_number)
                        column += 1
                        sheet.write_number(row, column, step.profitability, row_format_number)
                        column += 1
                        sheet.write_string(row, column, step.estimated_probability_id.name, row_format_number)
                        column += 1
                        sheet.write_string(row, column, spec.estimated_probability_id.name, row_format_number)


    def generate_xlsx_report(self, workbook, data, budgets):
        print('report KB')
        print('data = ',data)

        global strYEAR
        strYEAR = str(data['year'])
        global YEARint
        YEARint = int(strYEAR)
        commercial_budget_id = data['commercial_budget_id']
        budget = self.env['project_budget.commercial_budget'].search([('id', '=', commercial_budget_id)])

        print('YEARint=',YEARint)
        print('strYEAR =', strYEAR)

        self.printworksheet(workbook, budget, 'raw_data')