from odoo import models
from odoo.tools import date_utils
from datetime import date

class ReportBddsRawDataExcel(models.AbstractModel):
    _name = 'report.project_budget.report_bdds_raw_data_excel'
    _description = 'project_budget.report_bdds_raw_data_excel'
    _inherit = 'report.report_xlsx.abstract'

    def print_flow(self, workbook, sheet, flow, start_row, start_column):
        row_format = workbook.add_format({
            'border': 1,
            'font_size': 11,
            'font_name': 'Times New Roman',
            'num_format': '#,##0.00',
        })
        row_format_date = workbook.add_format({
            'border': 1,
            'font_size': 11,
            'font_name': 'Times New Roman',
            'num_format': 'dd.mm.yy',
        })
        row_format_date_month = workbook.add_format({
            'border': 1,
            'font_size': 11,
            'font_name': 'Times New Roman',
            'num_format': 'mmmm yyyy',
        })
        row = start_row
        for flow_item in flow:
            spec = flow_item.step_project_child_id or flow_item.projects_id
            row += 1
            column = start_column
            sheet.write(row, column, spec.company_id.name, row_format)
            column += 1
            sheet.write(row, column, flow_item.projects_id.project_id, row_format)
            column += 1
            if flow_item.step_project_child_id:
                sheet.write(row, column, flow_item.step_project_child_id.project_id, row_format)
            else:
                sheet.write(row, column, '', row_format)
            column += 1
            sheet.write(row, column, spec.approve_state, row_format)
            column += 1
            sheet.write(row, column, spec.project_status, row_format)
            column += 1
            sheet.write(row, column, spec.step_project_number or '', row_format)
            column += 1
            if flow_item.step_project_child_id:
                sheet.write(row, column, "True", row_format)
            else:
                sheet.write(row, column, "False", row_format)
            column += 1
            sheet.write(row, column, spec.budget_state, row_format)
            column += 1
            sheet.write(row, column, flow_item.currency_id.name, row_format)
            column += 1
            sheet.write(row, column, spec.responsibility_center_id.name, row_format)
            column += 1
            sheet.write(row, column, spec.project_supervisor_id.name or '', row_format)
            column += 1
            sheet.write(row, column, spec.key_account_manager_id.name, row_format)
            column += 1
            sheet.write(row, column, (spec.project_manager_id.name or ""), row_format)
            column += 1
            sheet.write(row, column, spec.industry_id.name, row_format)
            column += 1
            sheet.write(row, column, spec.partner_id.name, row_format)
            column += 1
            sheet.write(row, column, spec.essence_project or '', row_format)
            column += 1
            sheet.write(row, column, spec.signer_id.name, row_format)
            column += 1
            sheet.write(row, column, spec.comments or spec.step_project_parent_id.comments or '', row_format)
            column += 1
            sheet.write(row, column, spec.technological_direction_id.name or '', row_format)
            column += 1
            sheet.write(row, column, spec.project_type_id.name or '', row_format)
            column += 1
            sheet.write(row, column, spec.dogovor_number or spec.step_project_parent_id.dogovor_number or '', row_format)
            column += 1
            sheet.write(row, column, 'Q%d %d' % (date_utils.get_quarter_number(spec.end_presale_project_month), spec.end_presale_project_month.year), row_format)
            column += 1
            sheet.write_datetime(row, column, spec.end_presale_project_month, row_format_date_month)
            column += 1
            sheet.write(row, column, 'Q%d %d' % (date_utils.get_quarter_number(spec.end_sale_project_month), spec.end_sale_project_month.year) if spec.end_sale_project_month else '', row_format)
            column += 1
            sheet.write(row, column, spec.end_sale_project_month or '', row_format_date_month)
            column += 1

            if flow_item._fields.get("tax_id"):
                sheet.write(row, column, flow_item.tax_id.name or '', row_format)
            else:
                sheet.write(row, column, spec.tax_id.name or '', row_format)
            column += 1

            sheet.write(row, column, spec.stage_id.code, row_format)
            column += 1

            if flow_item._fields.get("cash_id"):
                sheet.write(row, column, flow_item.cash_id, row_format)  # TODO
            elif flow_item._fields.get("flow_id"):
                sheet.write(row, column, flow_item.flow_id, row_format)
            column += 1

            if flow_item._fields.get("date_cash"):
                sheet.write(row, column, flow_item.date_cash, row_format_date)  # TODO
            elif flow_item._fields.get("date"):
                sheet.write(row, column, flow_item.date, row_format_date)
            column += 1

            if flow_item.budget_item_id.direction == 'income':
                sheet.write(row, column, 'Поступление', row_format)
            elif flow_item.budget_item_id.direction == 'expense':
                sheet.write(row, column, 'Расход', row_format)
            else:
                sheet.write(row, column, '', row_format)
            column += 1

            sheet.write(row, column, flow_item.budget_item_id.name or '', row_format)
            column += 1
            sheet.write(row, column, flow_item.account_type_id.name or '', row_format)
            column += 1

            if flow_item._fields.get("supplier_id"):
                sheet.write(row, column, flow_item.supplier_id.name or '', row_format)
            else:
                sheet.write(row, column, '', row_format)
            column += 1

            if flow_item._fields.get("sum_cash"):
                sheet.write(row, column, flow_item.sum_cash, row_format)  # TODO
            elif flow_item._fields.get("amount_in_company_currency"):
                sheet.write(row, column, flow_item.amount_untaxed_in_company_currency, row_format)
            column += 1
        return row

    def print_worksheet(self, workbook, budget, sheet_name):
        sheet = workbook.add_worksheet(sheet_name)

        row_format_date_month = workbook.add_format({
            'border': 1,
            'font_size': 11,
            'font_name': 'Times New Roman',
            'num_format': 'mmmm yyyy',
        })

        row_format = workbook.add_format({
            'border': 1,
            'font_size': 11,
            'font_name': 'Times New Roman',
            'num_format': '#,##0.00',

        })

        row = 0
        column = 0
        sheet.write_string(row, column, 'Компания', row_format)
        column += 1
        sheet.write_string(row, column, 'project_id', row_format)
        column += 1
        sheet.write_string(row, column, 'step_id', row_format)
        column += 1
        sheet.write_string(row, column, 'Статус согласования', row_format)
        column += 1
        sheet.write_string(row, column, 'Статус проекта', row_format)
        column += 1
        sheet.write_string(row, column, 'Номер этапа проекта из AXAPTA', row_format)
        column += 1
        sheet.write_string(row, column, 'Это этап', row_format)
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
        sheet.write_string(row, column, "Вероятность проекта", row_format)
        column += 1
        sheet.write_string(row, column, "ДДС ID", row_format)
        column += 1
        sheet.write_string(row, column, "Дата ДДС", row_format)
        column += 1
        sheet.write_string(row, column, "Направление ДДС", row_format)
        column += 1
        sheet.write_string(row, column, "Статья ДДС", row_format)
        column += 1
        sheet.write_string(row, column, "Вид счета", row_format)
        column += 1
        sheet.write_string(row, column, "Поставщик", row_format)
        column += 1
        sheet.write_string(row, column, "Сумма ДДС", row_format)

        cur_budget_cashes = self.env['project_budget.planned_cash_flow'].search([
            ('projects_id.commercial_budget_id', '=', budget.id),
        ])

        row = self.print_flow(workbook, sheet, cur_budget_cashes, row, 0)

        cur_budget_costs = self.env['project_budget.planned_cost_flow'].search([
            ('projects_id.commercial_budget_id', '=', budget.id),
        ])

        row = self.print_flow(workbook, sheet, cur_budget_costs, row, 0)

    def generate_xlsx_report(self, workbook, data, budgets):

        commercial_budget_id = data['commercial_budget_id']
        budget = self.env['project_budget.commercial_budget'].search([('id', '=', commercial_budget_id)])
        budget_date = budget.date_actual or date.today()

        self.print_worksheet(workbook, budget, 'bdds_raw_data ' + budget_date.strftime('%d.%m.%y'))