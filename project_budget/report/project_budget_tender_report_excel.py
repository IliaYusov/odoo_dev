from odoo import models
from xlsxwriter.utility import xl_col_to_name
from datetime import datetime


# from HTMLParser import HTMLParser
# class MLStripper(HTMLParser):
#     def __init__(self):
#         self.reset()
#         self.fed = []
#     def handle_data(self, d):
#         self.fed.append(d)
#     def get_data(self):
#         return ''.join(self.fed)
#
# def strip_tags(html):
#     s = MLStripper()
#     s.feed(html)
#     return s.get_data()

class report_tender_excel(models.AbstractModel):
    _name = 'report.project_budget.report_tender_xlsx'
    _description = 'project_budget.report_tender_excel'
    _inherit = 'report.report_xlsx.abstract'

    is_report_for_management = False

    def printworksheet(self, workbook, tenders):
        global is_report_for_management
        print('printworksheet is_report_for_management', is_report_for_management)
            # One sheet by partner
        sheet = workbook.add_worksheet('tenders')
        head_format = workbook.add_format({
            'bold': True,
            'italic': True,
            'border': 1,
            'font_name': 'Arial',
            'font_size': 9,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#3265a5',
            'color': '#ffffff'
        })

        row_format_text = workbook.add_format({
            'border': 1,
            'font_size': 9,
            'text_wrap': True,
            'font_name': 'Times New Roman',
            'align': 'center',
            'valign': 'vcenter'
        })

        row_format_text_left = workbook.add_format({
            'border': 1,
            'font_size': 9,
            'text_wrap': True,
            'font_name': 'Times New Roman',
            'align': 'left',
            'valign': 'vcenter'
        })

        row_format_text_offer = workbook.add_format({
            'border': 1,
            'font_size': 9,
            'text_wrap': True,
            'font_name': 'Times New Roman',
            'align': 'center',
            'valign': 'vcenter',
            'font_color': 'red'
        })

        row_format_text_red = workbook.add_format({
            'border': 1,
            'font_size': 9,
            'text_wrap': True,
            'font_name': 'Times New Roman',
            'align': 'center',
            'valign': 'vcenter',
            'font_color': 'red'
        })

        row_format_text_comments = workbook.add_format({
            'border': 1,
            'font_size': 9,
            'text_wrap': True,
            'font_name': 'Times New Roman',
            'fg_color': '#FFFFCC',
        })

        date_format = workbook.add_format({'num_format': 'd mmmm yyyy'})
        sheet.freeze_panes(1, 1)
        row = 0
        column = 0
        sheet.write_string(row, column, 'Дата заполнения', head_format)
        sheet.set_column(column, column, 11.27)
        column += 1
        sheet.write_string(row, column, 'Участник', head_format)
        sheet.set_column(column, column, 15.36)
        column += 1
        sheet.write_string(row, column, '№ торгов', head_format)
        sheet.set_column(column, column, 21.73)
        column += 1
        sheet.write_string(row, column, 'Ссылка', head_format)
        sheet.set_column(column, column, 23.82)
        column += 1
        sheet.write_string(row, column, 'Заказчик', head_format)
        sheet.set_column(column, column, 21.36)
        column += 1
        if is_report_for_management == False:
            sheet.write_string(row, column, 'Контактная информация', head_format)
            sheet.set_column(column, column, 24.36)
            column += 1
        sheet.write_string(row, column, 'Наименование закупки', head_format)
        sheet.set_column(column, column, 26.55)
        column += 1
        sheet.write_string(row, column, 'НМЦК', head_format)
        sheet.set_column(column, column, 17.82)
        column += 1
        sheet.write_string(row, column, 'Предложение Участника', head_format)
        sheet.set_column(column, column, 17.91)
        column += 1
        sheet.write_string(row, column, 'Обеспечение заявки', head_format)
        sheet.set_column(column, column, 16.45)
        column += 1
        sheet.write_string(row, column, 'Обеспечение контракта', head_format)
        sheet.set_column(column, column, 16.45)
        column += 1
        if is_report_for_management == False:
            sheet.write_string(row, column, 'Обеспечение ГО', head_format)
            sheet.set_column(column, column, 16.45)
            column += 1
            sheet.write_string(row, column, 'Лицензии / СРО', head_format)
            sheet.set_column(column, column, 17.91)
            column += 1
        sheet.write_string(row, column, 'РП', head_format)
        sheet.set_column(column, column, 15.36)
        column += 1
        sheet.write_string(row, column, 'Текущий статус', head_format)
        sheet.set_column(column, column, 12.91)
        column += 1
        sheet.write_string(row, column, 'Комментарии', head_format)
        sheet.set_column(column, column, 44.27)
        column += 1
        sheet.write_string(row, column, 'Номер пресейла ОЗ', head_format)
        sheet.set_column(column, column, 31.45)
        column += 1

        for tender in tenders:
            row += 1
            column = 0
            sheet.write_string(row, column, tender.date_of_filling_in.strftime("%d.%m.%Y"), row_format_text)
            column += 1
            sheet.write_string(row, column, (tender.signer_id.name or ''), row_format_text)
            column += 1
            sheet.write_string(row, column, (tender.auction_number or ''), row_format_text)
            column += 1
            if tender.url_tender:
                sheet.write_string(row, column, (tender.url_tender.striptags() or ''), row_format_text)
            else:
                sheet.write_string(row, column, '', row_format_text)
            column += 1
            sheet.write_string(row, column, (tender.partner_id.name or ''), row_format_text)
            column += 1
            if is_report_for_management == False:
                sheet.write_string(row, column, (tender.contact_information or ''), row_format_text)
                column += 1
            sheet.write_string(row, column, (tender.name_of_the_purchase or ''), row_format_text)
            column += 1
            sum_participants_offer = ''
            sum_initial_maximum_contract_price = ''
            sum_payment_for_the_victory = ''
            sum_securing_the_application = ''
            sum_contract_security = ''
            sum_provision_of_GO = ''
            sum_site_payment = ''
            for tendersum in tender.tender_sums_ids:

                sum_participants_offer += monetary_format(tendersum.participants_offer_currency_id.symbol, (tendersum.participants_offer  or 0)) + ' ' + (tendersum.participants_offer_descr or '') + '\n'
                sum_initial_maximum_contract_price += monetary_format(tendersum.initial_maximum_contract_price_currency_id.symbol, (tendersum.initial_maximum_contract_price or 0)) + ' ' + (tendersum.initial_maximum_contract_price_descr or '') + '\n'
                sum_payment_for_the_victory += monetary_format(tendersum.payment_for_the_victory_currency_id.symbol, (tendersum.payment_for_the_victory or 0)) + ' ' + (tendersum.payment_for_the_victory_descr or '') + '\n'
                sum_securing_the_application += monetary_format(tendersum.securing_the_application_currency_id.symbol, (tendersum.securing_the_application or 0)) + ' ' + (tendersum.securing_the_application_descr or '') + '\n'
                sum_contract_security += monetary_format(tendersum.contract_security_currency_id.symbol, (tendersum.contract_security or 0)) + ' ' + (tendersum.contract_security_descr or '') + '\n'
                sum_provision_of_GO += monetary_format(tendersum.provision_of_GO_currency_id.symbol, (tendersum.provision_of_GO or 0)) + ' ' + (tendersum.provision_of_GO_descr or '') + '\n'
                sum_site_payment += monetary_format(tendersum.site_payment_currency_id.symbol, (tendersum.site_payment or 0)) + ' ' + (tendersum.site_payment_descr or '') + '\n'

            if tender.is_need_initial_maximum_contract_price == True:
                sheet.write_string(row, column, sum_initial_maximum_contract_price.strip(), row_format_text)
            else: sheet.write_string(row, column, 'НЕТ', row_format_text)
            column += 1
            sheet.write_string(row, column, sum_participants_offer.strip(), row_format_text_offer)
            column += 1
            if tender.is_need_securing_the_application == True:
                sheet.write_string(row, column, sum_securing_the_application.strip(), row_format_text)
            else: sheet.write_string(row, column, 'НЕТ', row_format_text)
            column += 1
            if tender.is_need_contract_security == True:
                sheet.write_string(row, column, sum_contract_security.strip(), row_format_text)
            else: sheet.write_string(row, column, 'НЕТ', row_format_text)
            column += 1
            if is_report_for_management == False:
                if tender.is_need_provision_of_GO == True:
                    sheet.write_string(row, column, sum_provision_of_GO.strip(), row_format_text)
                else: sheet.write_string(row, column, 'НЕТ', row_format_text)
                column += 1
                if tender.is_need_licenses_SRO == True:
                    sheet.write_string(row, column, (tender.licenses_SRO or ''), row_format_text)
                else: sheet.write_string(row, column, 'НЕТ', row_format_text)
                column += 1
            str_responsible = ''
            for responsible in tender.responsible_ids:
                print('responsible = ', responsible.name)
                str_responsible += (responsible.name or '') + '\n'
            print('str_responsible = ', str_responsible)
            sheet.write_string(row, column, str_responsible.strip(), row_format_text)
            column += 1
            if tender.current_status.highlight:
                sheet.write_string(row, column, (tender.current_status.name or ''), row_format_text_red)
            else:
                sheet.write_string(row, column, (tender.current_status.name or ''), row_format_text)
            column += 1
            str_comment = ''
            for comment in tender.tender_comments_ids:
                str_comment += comment.date_comment.strftime("%d.%m.%Y") + ' ' + (comment.type_comment_id.name or '') + ' ' + (comment.text_comment or '') + '\n'
            sheet.write_string(row, column, str_comment.strip(), row_format_text_comments)
            column += 1
            sheet.write_string(row, column, (tender.presale_number or ''), row_format_text_left)

    def generate_xlsx_report(self, workbook, data, lines):
        print('data = ', data)
        date_from = datetime.strptime(data['date_from'], "%d-%m-%Y").date()
        date_to = datetime.strptime(data['date_to'], "%d-%m-%Y").date()
        global is_report_for_management
        is_report_for_management = data['is_report_for_management']
        tenders_list = self.env['project_budget.tenders'].search([('date_of_filling_in', '>=', date_from), ('date_of_filling_in', '<=', date_to)], order='date_of_filling_in desc')

        print('is_report_for_management =', is_report_for_management)
        self.printworksheet(workbook, tenders_list)


def monetary_format(currency_symbol, amount):
    if currency_symbol:
        if currency_symbol == 'руб':
            return '{:,.2f}'.format(amount).replace(',', ' ') + ' ' + currency_symbol
        elif currency_symbol == 'د.إ':
            return '{:,.2f}'.format(amount).replace(',', ' ') + ' AED'
        else:
            return currency_symbol + ' ' + '{:,.2f}'.format(amount).replace(',', ' ')
    else: return ""
