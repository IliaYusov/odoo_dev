from odoo import models
from xlsxwriter.utility import xl_col_to_name

class ReportContractingRevenueCashExcel(models.AbstractModel):
    _name = 'report.project_budget.report_contracting_revenue_cash_excel'
    _description = 'report contracting revenue cash excel'
    _inherit = 'report.report_xlsx.abstract'


    def get_quater_from_month(self, month):
        if month in (1,2,3):
            return 'Q1'
        if month in (4,5,6):
            return 'Q2'
        if month in (7,8,9):
            return 'Q3'
        if month in (10,11,12):
            return 'Q4'
        return False

    def print_head(self, workbook, sheets):

        head_format = workbook.add_format({
            'bold': True,
            'font_size': 10,
        })

        head_schema = {
            'common':
                (
                    'ID проекта',
                    'Номер этапа проекта',
                    'Центр ответственности',
                    'ПН',
                    'Ответственный РПН',
                    'КАМ',
                    'Руководитель проекта',
                    'Заказчик',
                    'Партнер',
                    'Наименование',
                    'Этап',
                    'Рентабельность',
                ),
            'contracting':
                (
                    'Дата контрактования',
                    'Квартал контрактования',
                    'Сумма контрактования',
                    'Комментарий к проекту',
                ),
            'revenue':
                (
                    'Дата ВВ',
                    'Квартал ВВ',
                    'Сумма ВВ',
                    'Тип',
                    'Комментарий к проекту',
                ),
            'cash':
                (
                    'Дата ПДС',
                    'Квартал ПДС',
                    'Сумма ПДС',
                    'Тип',
                    'Тип оплаты',
                    'Комментарий к проекту',
                )
        }

        for sheet_name, sheet in sheets.items():
            row = 0
            col = 0
            for sc in head_schema['common']:
                sheet.write(row, col, sc, head_format)
                col += 1
            if head_schema.get(sheet_name):
                for sc in head_schema[sheet_name]:
                    sheet.write(row, col, sc, head_format)
                    col += 1

    def print_common(self, workbook, sheet, prj, row, col):

        row_format = workbook.add_format({
            'font_size': 10,
        })
        row_format_number = workbook.add_format({
            'font_size': 10,
            'num_format': '#,##0',
        })

        sheet.write(row, col, prj.project_id, row_format)
        col += 1
        sheet.write(row, col, prj.step_project_number or '', row_format)
        col += 1
        sheet.write(row, col, prj.responsibility_center_id.name, row_format)
        col += 1

        if prj.order_ids:
            pn = ', '.join(cat.root_category_id.name if cat.root_category_id else cat.name for cat in prj.order_ids.line_ids.product_category_id)
            sheet.write(row, col, pn, row_format)
        else:
            sheet.write(row, col, '', row_format)
        col += 1

        if prj.order_ids:
            rpn = ', '.join(cat.root_category_id.head_id.name if cat.root_category_id else cat.head_id.name for cat in prj.order_ids.line_ids.product_category_id if (cat.root_category_id.head_id if cat.root_category_id else cat.head_id))
            sheet.write(row, col, rpn, row_format)
        else:
            sheet.write(row, col, '', row_format)
        col += 1

        sheet.write(row, col, prj.key_account_manager_id.name or '', row_format)
        col += 1
        sheet.write(row, col, prj.project_manager_id.name or '', row_format)
        col += 1
        sheet.write(row, col, prj.partner_id.name or '', row_format)
        col += 1
        sheet.write(row, col, prj.company_partner_id.partner_id.name or '', row_format)
        col += 1
        sheet.write(row, col, prj.essence_project or '', row_format)
        col += 1
        sheet.write(row, col, prj.stage_id.name, row_format)
        col += 1
        sheet.write(row, col, prj.profitability, row_format_number)
        col += 1
        return col

    def print_ctg(self, workbook, sheet, prj, row, col):

        row_format = workbook.add_format({
            'font_size': 10,
        })
        row_format_number = workbook.add_format({
            'font_size': 10,
            'num_format': '#,##0',
        })
        row_format_date = workbook.add_format({
            'font_size': 10,
            'num_format': 'dd.mm.yyyy',
        })

        sheet.write(row, col, prj.end_presale_project_month, row_format_date)
        col += 1
        sheet.write(row, col, self.get_quater_from_month(prj.end_presale_project_month.month) + ' ' + str(prj.end_presale_project_month.year), row_format)
        col += 1
        sheet.write(row, col, prj.total_amount_of_revenue_with_vat, row_format_number)
        col += 1
        sheet.write(row, col, prj.comments or '', row_format)

    def print_rvn(self, workbook, sheet, prj, rvn, row, col, rvn_type):
        row_format = workbook.add_format({
            'font_size': 10,
        })
        row_format_number = workbook.add_format({
            'font_size': 10,
            'num_format': '#,##0',
        })
        row_format_date = workbook.add_format({
            'font_size': 10,
            'num_format': 'dd.mm.yyyy',
        })

        sheet.write(row, col, rvn.date_cash, row_format_date)
        col += 1
        sheet.write(row, col, self.get_quater_from_month(rvn.date_cash.month) + ' ' + str(rvn.date_cash.year), row_format)
        col += 1
        sheet.write(row, col, rvn.sum_cash, row_format_number)
        col += 1
        sheet.write(row, col, rvn_type, row_format)
        col += 1
        sheet.write(row, col, prj.comments or '', row_format)

    def print_csh(self, workbook, sheet, prj, csh, row, col, csh_type):
        row_format = workbook.add_format({
            'font_size': 10,
        })
        row_format_number = workbook.add_format({
            'font_size': 10,
            'num_format': '#,##0',
        })
        row_format_date = workbook.add_format({
            'font_size': 10,
            'num_format': 'dd.mm.yyyy',
        })

        sheet.write(row, col, csh.date_cash, row_format_date)
        col += 1
        sheet.write(row, col, self.get_quater_from_month(csh.date_cash.month) + ' ' + str(csh.date_cash.year), row_format)
        col += 1
        sheet.write(row, col, csh.sum_cash, row_format_number)
        col += 1
        sheet.write(row, col, csh_type, row_format)
        col += 1

        frst_faf = prj.fact_acceptance_flow_ids.sorted('date_cash')[:1]
        frst_fcf = prj.fact_cash_flow_ids.sorted('date_cash')[:1]
        res = ''
        if frst_faf and frst_fcf:
            if frst_fcf.date_cash <= frst_faf.date_cash and frst_fcf.sum_cash >= frst_faf.sum_cash * (1 + prj.vat_attribute_id.percent / 100):
                res = 'Предоплата 100%'
            elif frst_fcf.date_cash <= frst_faf.date_cash and frst_fcf.sum_cash < frst_faf.sum_cash * (1 + prj.vat_attribute_id.percent / 100):
                res = 'Частичная предоплата'
            elif frst_fcf.date_cash > frst_faf.date_cash and frst_fcf.sum_cash >= frst_faf.sum_cash * (1 + prj.vat_attribute_id.percent / 100):
                res = 'Постоплата 100%'

        sheet.write(row, col, res, row_format)
        col += 1

        sheet.write(row, col, prj.comments or '', row_format)

    def print_worksheets(self, workbook, sheets, year):

        self.print_head(workbook, sheets)

        projects = self.env['project_budget.projects'].search([
            ('budget_state', '=', 'work'),
            '|', '&', ('step_status', '=', 'step'),
            ('step_project_parent_id.project_have_steps', '=', True),
            '&', ('step_status', '=', 'project'),
            ('project_have_steps', '=', False),
        ], order='project_id asc')

        row_ctg = row_rvn = row_csh = 0

        for prj in projects:
            if prj.end_presale_project_month.year == year:
                row_ctg += 1
                col = self.print_common(workbook, sheets['contracting'], prj, row_ctg, 0)
                self.print_ctg(workbook, sheets['contracting'], prj, row_ctg, col)

            for rvn in prj.planned_acceptance_flow_ids:
                if rvn.date_cash.year == year:
                    row_rvn += 1
                    col = self.print_common(workbook, sheets['revenue'], prj, row_rvn, 0)
                    self.print_rvn(workbook, sheets['revenue'], prj, rvn, row_rvn, col, 'План')
            for rvn in prj.fact_acceptance_flow_ids:
                if rvn.date_cash.year == year:
                    row_rvn += 1
                    col = self.print_common(workbook, sheets['revenue'], prj, row_rvn, 0)
                    self.print_rvn(workbook, sheets['revenue'], prj, rvn, row_rvn, col, 'Факт')


            for csh in prj.planned_cash_flow_ids:
                if csh.date_cash.year == year:
                    row_csh += 1
                    col = self.print_common(workbook, sheets['cash'], prj, row_csh, 0)
                    self.print_csh(workbook, sheets['cash'], prj, csh, row_csh, col, 'План')
            for csh in prj.fact_cash_flow_ids:
                if csh.date_cash.year == year:
                    row_csh += 1
                    col = self.print_common(workbook, sheets['cash'], prj, row_csh, 0)
                    self.print_csh(workbook, sheets['cash'], prj, csh, row_csh, col, 'Факт')


    def generate_xlsx_report(self, workbook, data, budgets):
        year = int(data['year'])

        sheets = {
            'contracting': workbook.add_worksheet('Контракт'),
            'revenue': workbook.add_worksheet('ВВ'),
            'cash': workbook.add_worksheet('ПДС'),
        }

        self.print_worksheets(workbook, sheets, year)
