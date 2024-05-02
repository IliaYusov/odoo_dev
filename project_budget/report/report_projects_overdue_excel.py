from odoo import models
from xlsxwriter.utility import xl_col_to_name

class report_projects_overdue_excel(models.AbstractModel):
    _name = 'report.project_budget.report_projects_overdue_excel'
    _description = 'project_budget.report_projects_overdue_excel'
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
        global project_office_ids
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


        row_format = workbook.add_format({
            'border': 1,
            'font_size': 11,
            'font_name': 'Times New Roman'
            #                'text_wrap' : True,
            #                'align': 'center',
            #                'valign': 'vcenter',
            #                'fg_color': '#3265a5',
        })

        row = 0
        column = 0

        column = 0
        sheet.write_string(row, column, 'Проектный офис', head_format)
        sheet.set_column(column, column, 23)
        column += 1
        sheet.write_string(row, column, 'Вероятность', head_format)
        sheet.set_column(column, column, 23)
        column += 1
        sheet.write_string(row, column, 'Куратор', head_format)
        sheet.set_column(column, column, 23)
        column += 1
        sheet.write_string(row, column, 'КАМ', head_format)
        sheet.set_column(column, column, 23)
        column += 1
        sheet.write_string(row, column, 'Руководитель проекта', head_format)
        sheet.set_column(column, column, 23)
        column += 1
        sheet.write_string(row, column, 'Project_id', head_format)
        sheet.set_column(column, column, 23)
        column += 1
        sheet.write_string(row, column, 'Step_id', head_format)
        sheet.set_column(column, column, 13)
        column += 1
        sheet.write_string(row, column, 'Заказчик', head_format)
        sheet.set_column(column, column, 13)
        column += 1
        sheet.write_string(row, column, 'Наименование сделки', head_format)
        sheet.set_column(column, column, 13)
        column += 1
        sheet.write_string(row, column, 'Поле', head_format)
        sheet.set_column(column, column, 31)
        column += 1
        sheet.write_string(row, column, 'Значение', head_format)
        sheet.set_column(column, column, 18)

        sheet.freeze_panes(1, 1)

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

        cur_budget_projects = self.env['project_budget.projects'].search([('commercial_budget_id', '=', budget.id),('project_office_id', 'in', project_offices.ids)])

        for spec in cur_budget_projects:
            isok = False
            raisetext= ''
            dictvalues={}
            isok, raisetext, dictvalues = spec.check_overdue_date(False)

            if isok == True: continue
            stage_id_code = ""
            step_project_office_name = ''
            if 'step_id' in dictvalues:
                step_id = dictvalues['step_id']
                step_obj = self.env['project_budget.project_steps'].search(
                    [('step_id', '=', step_id),('projects_id','=',spec.id)], limit=1)
                if step_obj:
                    stage_id_code = step_obj.stage_id.code
                    step_project_office_name = step_obj.project_office_id.name
            else:
                stage_id_code = spec.stage_id.code

            if stage_id_code in ('0', '100(done)'): continue

            row += 1
            column = 0

            if step_project_office_name and spec.legal_entity_signing_id.different_project_offices_in_steps:
                sheet.write_string(row, column, step_project_office_name, row_format)
            else:
                sheet.write_string(row, column, spec.project_office_id.name, row_format)

            column += 1
            sheet.write_string(row, column, stage_id_code, row_format)

            column += 1
            sheet.write_string(row, column, (spec.project_supervisor_id.name or ""), row_format)
            column += 1
            sheet.write_string(row, column, (spec.project_manager_id.name or ""), row_format)
            column += 1
            sheet.write_string(row, column, (spec.rukovoditel_project_id.name or ""), row_format)
            column += 1
            sheet.write_string(row, column, spec.project_id, row_format)
            column += 1
            if 'step_id' in dictvalues:
                sheet.write_string(row, column, dictvalues['step_id'], row_format)
            else:
                sheet.write_string(row, column, "", row_format)
            column += 1

            sheet.write_string(row, column, (spec.partner_id.name or '') , row_format)
            column += 1
            sheet.write_string(row, column, (spec.essence_project or ''), row_format)
            column += 1
            if 'end_presale_project_month' in dictvalues:
                sheet.write_string(row, column, 'Дата контрактования', row_format)
                column += 1
                sheet.write_string(row, column, dictvalues['end_presale_project_month'], row_format)

            if 'end_sale_project_month' in dictvalues:
                sheet.write_string(row, column, 'Дата последней отгрузки', row_format)
                column += 1
                sheet.write_string(row, column, dictvalues['end_sale_project_month'], row_format)

            if 'planned_acceptance_flow' in dictvalues:
                sheet.write_string(row, column, 'Плановое актирование', row_format)
                column += 1
                sheet.write_string(row, column, dictvalues['planned_acceptance_flow'], row_format)

            if 'planned_cash_flow' in dictvalues:
                sheet.write_string(row, column, 'ПДС', row_format)
                column += 1
                sheet.write_string(row, column, dictvalues['planned_cash_flow'], row_format)


    def generate_xlsx_report(self, workbook, data, budgets):
        print('report KB')
        print('data = ',data)

        global strYEAR
        strYEAR = str(data['year'])
        global YEARint
        YEARint = int(strYEAR)
        global project_office_ids
        project_office_ids = data['project_office_ids']

        commercial_budget_id = data['commercial_budget_id']
        budget = self.env['project_budget.commercial_budget'].search([('id', '=', commercial_budget_id)])

        print('YEARint=',YEARint)
        print('strYEAR =', strYEAR)

        self.printworksheet(workbook, budget, 'raw_data')