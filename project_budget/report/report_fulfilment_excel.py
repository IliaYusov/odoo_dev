import logging

from odoo import models
from odoo.tools import date_utils
from datetime import date, datetime, timedelta
from xlsxwriter.utility import xl_col_to_name
from collections import OrderedDict
from itertools import chain

isdebug = False
logger = logging.getLogger("*___forecast_report___*")


class ReportFulfilmentExcel(models.AbstractModel):
    _name = 'report.project_budget.report_fulfilment_excel'
    _description = 'project_budget.report_fulfilment_excel'
    _inherit = 'report.report_xlsx.abstract'

    def print_head(self, workbook, sheet, year):

        head_format = workbook.add_format({
            'bold': True,
            'font_size': 8,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
            'fg_color': '#f2f2f2',
            'border': 1,
        })

        head_schema = {
            'fulfilment':
                (
                    (
                        ('Компания', 1, 0),
                        ('Партнер/Заказчик', 1, 0),
                        ('Отрасль в которой он работает', 1, 0),
                        ('Номер Договора', 1, 0),
                        ('Тип договора услуги, работа или поставка', 1, 0),
                        ('Сумма договора в валюте договора', 1, 0),
                        ('Валюта договора', 1, 0),
                        ('курс', 1, 0),
                        ('Итого РУБЛИ', 1, 0),
                        ('Срок начала контракта', 1, 0),
                        ('Срок окончания контракта', 1, 0),
                        ('Оплачено по контракту в рублях', 1, 0),
                        (f'Сумма ожидаемых поступлений денежных средств в {str(year)} г в RUB', 0, 3),
                        (),
                        (),
                        (),
                        (f'Сумма ожидаемых поступлений денежных средств в {str(year + 1)} г в RUB', 0, 3),
                        (),
                        (),
                        (),
                        (f'Сумма ожидаемых поступлений денежных средств в {str(year + 2)} г в RUB', 0, 3),
                        (),
                        (),
                        (),
                        (f'Сумма ожидаемых поступлений денежных средств в {str(year + 3)} г в RUB', 0, 3),
                        (),
                        (),
                        (),
                        ('Сумма ожидаемых поступлений денежных средств далее в RUB', 1, 0),
                        ('Заактированная сумма в рамках договора ( на эту сумму у нас есть подтверждающие документы)', 1, 0),
                        ('Маржинальность контракта, в %', 1, 0),
                        ('Банковские реквизиты контракта', 1, 0),
                        ('check', 1, 0),
                        ('СТАТУС', 1, 0),
                        ('Залог', 1, 0),
                        ('Комментарии РП', 1, 0),
                        ('ПО', 1, 0),
                        ('Наименование этапа', 1, 0),
                        ('Остаток  поступлений ДС  от Заказчика', 1, 0),
                        ('Незаактированная сумма (нет подтверждающих  документов)', 1, 0),
                        ('Статус проекта', 1, 0),
                        ('Дебиторка/ задолженность', 1, 0),
                        ('Наличие отдельного банк/сч в рамках ГОЗ', 1, 0),
                    ),
                    (
                        (),
                        (),
                        (),
                        (),
                        (),
                        (),
                        (),
                        (),
                        (),
                        (),
                        (),
                        (),
                        ('1 квартал', 0, 0),
                        ('2 квартал', 0, 0),
                        ('3 квартал', 0, 0),
                        ('4 квартал', 0, 0),
                        ('1 квартал', 0, 0),
                        ('2 квартал', 0, 0),
                        ('3 квартал', 0, 0),
                        ('4 квартал', 0, 0),
                        ('1 квартал', 0, 0),
                        ('2 квартал', 0, 0),
                        ('3 квартал', 0, 0),
                        ('4 квартал', 0, 0),
                        ('1 квартал', 0, 0),
                        ('2 квартал', 0, 0),
                        ('3 квартал', 0, 0),
                        ('4 квартал', 0, 0),
                        (),
                        (),
                        (),
                        (),
                        (),
                        (),
                        (),
                        (),
                        (),
                        (),
                        (),
                        (),
                        (),
                        (),
                        (),
                    ),
                ),
        }

        row = 0
        for sr in head_schema['fulfilment']:
            col = 0
            for sc in sr:
                if sc:
                    if sc[1] or sc[2]:
                        sheet.merge_range(row, col, row + sc[1], col + sc[2], sc[0], head_format)
                    else:
                        sheet.write(row, col, sc[0], head_format)
                col += 1
            row += 1
        return row

    def get_data_from_projects(self, projects, year):
        data = OrderedDict()

        for prj in projects:

            if prj.step_status == 'project':
                essence = prj.essence_project or ''
                cash_fact_ids = prj.fact_cash_flow_ids
                cash_plan_ids = prj.planned_cash_flow_ids
                acc_fact_ids = prj.fact_acceptance_flow_ids
            else:
                essence = prj.step_project_parent_id.essence_project + ' ' + prj.essence_project or ''
                cash_fact_ids = prj.fact_step_cash_flow_ids
                cash_plan_ids = prj.planned_step_cash_flow_ids
                acc_fact_ids = prj.fact_step_acceptance_flow_ids

            data[prj.project_id] = {}
            data[prj.project_id]['company'] = prj.company_id.name
            data[prj.project_id]['partner'] = prj.company_partner_id.partner_id.name or prj.partner_id.name
            data[prj.project_id]['dogovor'] = (prj.dogovor_number or 'б.н.') + ' от ' + prj.end_presale_project_month.strftime('%d.%m.%Y')
            data[prj.project_id]['essence'] = essence
            data[prj.project_id]['amount_total'] = prj.amount_total
            data[prj.project_id]['currency_name'] = prj.currency_id.name
            data[prj.project_id]['currency_rate'] = prj.currency_rate
            data[prj.project_id]['amount_total_in_company_currency'] = prj.amount_total_in_company_currency
            data[prj.project_id]['start_date'] = prj.end_presale_project_month
            data[prj.project_id]['end_date'] = prj.end_sale_project_month
            cash_fact_amount = 0
            for cash_fact in cash_fact_ids:
                cash_fact_amount += cash_fact.sum_cash  #TODO
            data[prj.project_id]['cash_fact_amount'] = cash_fact_amount
            cash_plan_y1q1 = 0
            cash_plan_y1q2 = 0
            cash_plan_y1q3 = 0
            cash_plan_y1q4 = 0
            cash_plan_y2q1 = 0
            cash_plan_y2q2 = 0
            cash_plan_y2q3 = 0
            cash_plan_y2q4 = 0
            cash_plan_y3q1 = 0
            cash_plan_y3q2 = 0
            cash_plan_y3q3 = 0
            cash_plan_y3q4 = 0
            cash_plan_y4q1 = 0
            cash_plan_y4q2 = 0
            cash_plan_y4q3 = 0
            cash_plan_y4q4 = 0
            cash_plan_rest = 0
            for cash_plan in cash_plan_ids:
                if cash_plan.date_cash.year == year:  #TODO
                    if cash_plan.date_cash.month in (1, 2, 3):
                        cash_plan_y1q1 += cash_plan.distribution_sum_with_vat_ostatok  #TODO
                    elif cash_plan.date_cash.month in (4, 5, 6):
                        cash_plan_y1q2 += cash_plan.distribution_sum_with_vat_ostatok  #TODO
                    elif cash_plan.date_cash.month in (7, 8, 9):
                        cash_plan_y1q3 += cash_plan.distribution_sum_with_vat_ostatok  #TODO
                    else:
                        cash_plan_y1q4 += cash_plan.distribution_sum_with_vat_ostatok  #TODO
                elif cash_plan.date_cash.year == year + 1:  #TODO
                    if cash_plan.date_cash.month in (1, 2, 3):
                        cash_plan_y2q1 += cash_plan.distribution_sum_with_vat_ostatok  #TODO
                    elif cash_plan.date_cash.month in (4, 5, 6):
                        cash_plan_y2q2 += cash_plan.distribution_sum_with_vat_ostatok  #TODO
                    elif cash_plan.date_cash.month in (7, 8, 9):
                        cash_plan_y2q3 += cash_plan.distribution_sum_with_vat_ostatok  #TODO
                    else:
                        cash_plan_y2q4 += cash_plan.distribution_sum_with_vat_ostatok  #TODO
                elif cash_plan.date_cash.year == year + 2:  #TODO
                    if cash_plan.date_cash.month in (1, 2, 3):
                        cash_plan_y3q1 += cash_plan.distribution_sum_with_vat_ostatok  #TODO
                    elif cash_plan.date_cash.month in (4, 5, 6):
                        cash_plan_y3q2 += cash_plan.distribution_sum_with_vat_ostatok  #TODO
                    elif cash_plan.date_cash.month in (7, 8, 9):
                        cash_plan_y3q3 += cash_plan.distribution_sum_with_vat_ostatok  #TODO
                    else:
                        cash_plan_y3q4 += cash_plan.distribution_sum_with_vat_ostatok  #TODO
                elif cash_plan.date_cash.year == year + 3:  #TODO
                    if cash_plan.date_cash.month in (1, 2, 3):
                        cash_plan_y4q1 += cash_plan.distribution_sum_with_vat_ostatok  #TODO
                    elif cash_plan.date_cash.month in (4, 5, 6):
                        cash_plan_y4q2 += cash_plan.distribution_sum_with_vat_ostatok  #TODO
                    elif cash_plan.date_cash.month in (7, 8, 9):
                        cash_plan_y4q3 += cash_plan.distribution_sum_with_vat_ostatok  #TODO
                    else:
                        cash_plan_y4q4 += cash_plan.distribution_sum_with_vat_ostatok  #TODO
                elif cash_plan.date_cash.year > year + 3:  # TODO
                    cash_plan_rest += cash_plan.distribution_sum_with_vat_ostatok  # TODO
            data[prj.project_id]['cash_plan_amount'] = {
                'y1q1': cash_plan_y1q1,
                'y1q2': cash_plan_y1q2,
                'y1q3': cash_plan_y1q3,
                'y1q4': cash_plan_y1q4,
                'y2q1': cash_plan_y2q1,
                'y2q2': cash_plan_y2q2,
                'y2q3': cash_plan_y2q3,
                'y2q4': cash_plan_y2q4,
                'y3q1': cash_plan_y3q1,
                'y3q2': cash_plan_y3q2,
                'y3q3': cash_plan_y3q3,
                'y3q4': cash_plan_y3q4,
                'y4q1': cash_plan_y4q1,
                'y4q2': cash_plan_y4q2,
                'y4q3': cash_plan_y4q3,
                'y4q4': cash_plan_y4q4,
                'rest': cash_plan_rest,
            }
            acceptance_fact_amount = 0
            for acc_fact in acc_fact_ids:
                acceptance_fact_amount += acc_fact.sum_cash  #TODO
            data[prj.project_id]['acceptance_fact_amount'] = acceptance_fact_amount
            data[prj.project_id]['step_project_number'] = prj.step_project_number or ''

        return data


    def print_vertical_sum_formula(self, sheet, row, col, start_row, end_row, format_name):
        formula = '=sum({0}{1}:{0}{2})'
        result_formula = formula.format(xl_col_to_name(col), start_row, end_row)
        sheet.write_formula(row, col, result_formula, format_name)

    def print_worksheet(self, workbook, sheet, budget, year):

        row_format = workbook.add_format({
            'font_size': 10,
        })
        row_format_number = workbook.add_format({
            'font_size': 10,
            "num_format": '#,##0.00',
        })
        total_format_number = workbook.add_format({
            'font_size': 10,
            'bold': True,
            "num_format": '#,##0.00',
        })
        row_format_number_green = workbook.add_format({
            'font_size': 10,
            "num_format": '#,##0.00',
            'fg_color': '#EBF1DE',
        })
        row_format_date = workbook.add_format({
            'font_size': 10,
            'num_format': 'dd.mm.yyyy',
        })

        sheet.freeze_panes(0, 2)
        row = self.print_head(workbook, sheet, year)

        projects = self.env['project_budget.projects'].search([
            ('commercial_budget_id', '=', budget.id),
            ('step_status', '=', 'project'),
            ('stage_id.code', '=', '100'),
        ], order='project_id asc')

        data = self.get_data_from_projects(projects, year)

        for prj in data.values():
            col = 0
            sheet.write(row, col, prj['company'], row_format)
            col += 1
            sheet.write(row, col, prj['partner'], row_format)
            col += 1
            col += 1
            sheet.write(row, col, prj['dogovor'], row_format)
            col += 1
            sheet.write(row, col, prj['essence'], row_format)
            col += 1
            sheet.write(row, col, prj['amount_total'], row_format_number)
            col += 1
            sheet.write(row, col, prj['currency_name'], row_format)
            col += 1
            sheet.write(row, col, prj['currency_rate'], row_format_number)
            col += 1
            sheet.write(row, col, prj['amount_total_in_company_currency'], row_format_number)
            col += 1
            sheet.write(row, col, prj['start_date'], row_format_date)
            col += 1
            sheet.write(row, col, prj['end_date'], row_format_date)
            col += 1
            sheet.write(row, col, prj['cash_fact_amount'], row_format_number_green)
            col += 1
            sheet.write(row, col, prj['cash_plan_amount']['y1q1'], row_format_number)
            col += 1
            sheet.write(row, col, prj['cash_plan_amount']['y1q2'], row_format_number)
            col += 1
            sheet.write(row, col, prj['cash_plan_amount']['y1q3'], row_format_number)
            col += 1
            sheet.write(row, col, prj['cash_plan_amount']['y1q4'], row_format_number)
            col += 1
            sheet.write(row, col, prj['cash_plan_amount']['y2q1'], row_format_number)
            col += 1
            sheet.write(row, col, prj['cash_plan_amount']['y2q2'], row_format_number)
            col += 1
            sheet.write(row, col, prj['cash_plan_amount']['y2q3'], row_format_number)
            col += 1
            sheet.write(row, col, prj['cash_plan_amount']['y2q4'], row_format_number)
            col += 1
            sheet.write(row, col, prj['cash_plan_amount']['y3q1'], row_format_number)
            col += 1
            sheet.write(row, col, prj['cash_plan_amount']['y3q2'], row_format_number)
            col += 1
            sheet.write(row, col, prj['cash_plan_amount']['y3q3'], row_format_number)
            col += 1
            sheet.write(row, col, prj['cash_plan_amount']['y3q4'], row_format_number)
            col += 1
            sheet.write(row, col, prj['cash_plan_amount']['y4q1'], row_format_number)
            col += 1
            sheet.write(row, col, prj['cash_plan_amount']['y4q2'], row_format_number)
            col += 1
            sheet.write(row, col, prj['cash_plan_amount']['y4q3'], row_format_number)
            col += 1
            sheet.write(row, col, prj['cash_plan_amount']['y4q4'], row_format_number)
            col += 1
            sheet.write(row, col, prj['cash_plan_amount']['rest'], row_format_number)
            col += 1
            sheet.write(row, col, prj['acceptance_fact_amount'], row_format_number_green)
            col += 1
            col += 1
            col += 1
            col += 1
            col += 1
            col += 1
            col += 1
            col += 1
            sheet.write(row, col, prj['step_project_number'], row_format_number)
            col += 1
            formula = '=({1}{0}-{2}{0})'.format(row + 1, xl_col_to_name(8), xl_col_to_name(11))
            sheet.write_formula(row, col, formula, row_format_number)
            col += 1
            formula = '=({1}{0}-{2}{0})'.format(row + 1, xl_col_to_name(8), xl_col_to_name(29))
            sheet.write_formula(row, col, formula, row_format_number)
            col += 1
            col += 1
            formula = '=IF(({2}{0}-{1}{0})<0,0,({2}{0}-{1}{0}))'.format(row + 1, xl_col_to_name(11), xl_col_to_name(29))
            sheet.write_formula(row, col, formula, row_format_number)
            row += 1
        for col in chain((8,),range(11, 30), (38, 39, 41)):
            self.print_vertical_sum_formula(sheet, row, col, 3, row, total_format_number)

    def generate_xlsx_report(self, workbook, data, budgets):
        year = int(data['year'])
        commercial_budget_id = data['commercial_budget_id']
        budget = self.env['project_budget.commercial_budget'].search([('id', '=', commercial_budget_id)])

        sheet = workbook.add_worksheet(datetime.today().strftime('%d.%m.%Y'))

        self.print_worksheet(workbook, sheet, budget, year)
