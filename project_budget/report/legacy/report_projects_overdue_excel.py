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
        global responsibility_center_ids
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

        if responsibility_center_ids:
            child_responsibility_centers = self.env['account.analytic.account'].search([
                ('id', 'in', responsibility_center_ids),
                ('plan_id', '=', self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
            ]).child_ids
            while child_responsibility_centers:  # обходим дочерние офисы
                for child_responsibility_center in child_responsibility_centers:
                    if child_responsibility_center.id not in responsibility_center_ids:
                        responsibility_center_ids.append(child_responsibility_center.id)
                new_child_responsibility_centers = child_responsibility_centers.child_ids
                child_responsibility_centers = new_child_responsibility_centers

            responsibility_centers = self.env['account.analytic.account'].search([
                ('id','in',responsibility_center_ids),
                ('plan_id', '=', self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
            ], order='name')  # для сортировки так делаем
        else:
            responsibility_centers = self.env['account.analytic.account'].search([
                ('plan_id', '=', self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
            ], order='name')

        cur_budget_projects = self.env['project_budget.projects'].search([
            ('commercial_budget_id', '=', budget.id),
            ('responsibility_center_id', 'in', responsibility_centers.ids),
            '|', ('step_status', '=', 'step'),
            ('project_have_steps', '=', False),
        ])

        for spec in cur_budget_projects:
            isok = False
            raisetext= ''
            dictvalues={}
            isok, raisetext, dictvalues = spec.check_overdue_date(False)

            if isok == True: continue

            if spec.stage_id.code in ('0', '100(done)'): continue

            row += 1
            column = 0
            sheet.write_string(row, column, spec.responsibility_center_id.name, row_format)

            column += 1
            sheet.write_string(row, column, spec.stage_id.code, row_format)

            column += 1
            sheet.write_string(row, column, (spec.project_supervisor_id.name or ""), row_format)
            column += 1
            sheet.write_string(row, column, (spec.key_account_manager_id.name or ""), row_format)
            column += 1
            sheet.write_string(row, column, (spec.project_manager_id.name or ""), row_format)
            column += 1
            if spec.step_status == 'project':
                sheet.write_string(row, column, spec.project_id, row_format)
                column += 1
                sheet.write_string(row, column, '', row_format)
            elif spec.step_status == 'step':
                sheet.write_string(row, column, spec.step_project_parent_id.project_id, row_format)
                column += 1
                sheet.write_string(row, column, spec.project_id, row_format)
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
        global responsibility_center_ids
        responsibility_center_ids = data['responsibility_center_ids']

        commercial_budget_id = data['commercial_budget_id']
        budget = self.env['project_budget.commercial_budget'].search([('id', '=', commercial_budget_id)])

        print('YEARint=',YEARint)
        print('strYEAR =', strYEAR)

        self.printworksheet(workbook, budget, 'raw_data')