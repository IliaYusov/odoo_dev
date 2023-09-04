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

    def printworksheet(self,workbook, tenders):
        global is_report_for_management
        print('printworksheet is_report_for_management',is_report_for_management)
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
            'font_name': 'Times New Roman'
        })
        row_format_text_offer = workbook.add_format({
            'border': 1,
            'font_size': 9,
            'text_wrap': True,
            'font_name': 'Times New Roman'
        })
        row_format_text_offer.set_font_color('red')

        row_format_text_comments = workbook.add_format({
            'border': 1,
            'font_size': 9,
            'text_wrap': True,
            'font_name': 'Times New Roman',
            'fg_color': '#FFFFCC',
        })



        date_format = workbook.add_format({'num_format': 'd mmmm yyyy'})
        row = 0
        column = 0
        sheet.write_string(row, column, 'Дата заполнения',head_format)
        sheet.set_column(column, column, 12.75)
        column += 1
        sheet.write_string(row, column, 'Участник',head_format)
        sheet.set_column(column, column, 17.00)
        column += 1
        sheet.write_string(row, column, '№ торгов',head_format)
        sheet.set_column(column, column, 14.27)
        column += 1
        sheet.write_string(row, column, 'Ссылка',head_format)
        sheet.set_column(column, column, 15.27)
        column += 1
        sheet.write_string(row, column, 'Заказчик',head_format)
        sheet.set_column(column, column, 17.91)
        column += 1
        if is_report_for_management == False:
            sheet.write_string(row, column, 'Контактная информация',head_format)
            sheet.set_column(column, column, 17.18)
            column += 1
        sheet.write_string(row, column, 'Наименование закупки',head_format)
        sheet.set_column(column, column, 14.00)
        column += 1
        sheet.write_string(row, column, 'НМЦК',head_format)
        sheet.set_column(column, column, 17.91)
        column += 1
        sheet.write_string(row, column, 'Предложение Участника',head_format)
        sheet.set_column(column, column, 17.91)
        column += 1
        sheet.write_string(row, column, 'Обеспечение заявки',head_format)
        sheet.set_column(column, column, 17.91)
        column += 1
        sheet.write_string(row, column, 'Обеспечение контракта',head_format)
        sheet.set_column(column, column, 17.91)
        column += 1
        if is_report_for_management == False:
            sheet.write_string(row, column, 'Обеспечение ГО',head_format)
            sheet.set_column(column, column, 17.91)
            column += 1
            sheet.write_string(row, column, 'Лицензии / СРО',head_format)
            sheet.set_column(column, column, 17.91)
            column += 1
        sheet.write_string(row, column, 'РП',head_format)
        sheet.set_column(column, column, 17.91)
        column += 1
        sheet.write_string(row, column, 'Текущий статус',head_format)
        sheet.set_column(column, column, 17.91)
        column += 1
        sheet.write_string(row, column, 'Комментарии',head_format)
        sheet.set_column(column, column, 19.89)
        column += 1
        sheet.write_string(row, column, 'Номер пресейла ОЗ',head_format)
        sheet.set_column(column, column, 12.75)
        column += 1

        for tender in tenders:
            row += 1
            column = 0
            sheet.write_string(row, column, str(tender.date_of_filling_in), row_format_text)
            column += 1
            sheet.write_string(row, column,(tender.participant_id.name or '' ),row_format_text)
            column += 1
            sheet.write_string(row, column, (tender.auction_number or '' ),row_format_text)
            column += 1
            sheet.write_string(row, column,(tender.url_tender.striptags() or '' ),row_format_text)
            column += 1
            sheet.write_string(row, column, (tender.customer_organization_id.name or '' ),row_format_text)
            column += 1
            if is_report_for_management == False:
                sheet.write_string(row, column, (tender.contact_information or '' ),row_format_text)
                column += 1
            sheet.write_string(row, column, (tender.name_of_the_purchase or '' ),row_format_text)
            column += 1
            sum_participants_offer = ''
            sum_initial_maximum_contract_price = ''
            sum_payment_for_the_victory = ''
            sum_securing_the_application = ''
            sum_contract_security = ''
            sum_provision_of_GO = ''
            sum_site_payment = ''
            for tendersum in tender.tender_sums_ids:
                sum_participants_offer += '\n' + tendersum.currency_id.symbol + ' ' +str(tendersum.participants_offer) + (tendersum.participants_offer_descr or '')
                sum_initial_maximum_contract_price +=  '\n' + tendersum.currency_id.symbol + ' ' + str(
                                                    tendersum.initial_maximum_contract_price) + (tendersum.initial_maximum_contract_price_descr or '')
                sum_payment_for_the_victory +=  '\n' + tendersum.currency_id.symbol + ' ' + str(
                                                tendersum.payment_for_the_victory) + (tendersum.payment_for_the_victory_descr or '')
                sum_securing_the_application +=  '\n' + tendersum.currency_id.symbol + ' ' + str(
                                                tendersum.securing_the_application) +  (tendersum.securing_the_application_descr or '')
                sum_contract_security +=  '\n' + tendersum.currency_id.symbol + ' ' + str(
                                                tendersum.contract_security) +  (tendersum.contract_security_descr or '')
                sum_provision_of_GO +=  '\n' + tendersum.currency_id.symbol + ' ' + str(
                                                tendersum.provision_of_GO) +  (tendersum.provision_of_GO_descr or '')
                sum_site_payment +=  '\n' + tendersum.currency_id.symbol + ' ' + str(
                                                tendersum.site_payment) +  (tendersum.site_payment_descr or '')

            if tender.is_need_initial_maximum_contract_price == True:
                sheet.write_string(row, column,sum_initial_maximum_contract_price,row_format_text)
            else : sheet.write_string(row, column,'НЕТ',row_format_text)
            column += 1
            sheet.write_string(row, column, sum_participants_offer,row_format_text_offer)
            column += 1
            if tender.is_need_securing_the_application == True:
                sheet.write_string(row, column,sum_securing_the_application,row_format_text)
            else : sheet.write_string(row, column,'НЕТ',row_format_text)
            column += 1
            if tender.is_need_contract_security == True:
                sheet.write_string(row, column,sum_contract_security,row_format_text)
            else : sheet.write_string(row, column,'НЕТ',row_format_text)
            column += 1
            if is_report_for_management == False:
                if tender.is_need_provision_of_GO == True:
                    sheet.write_string(row, column, sum_provision_of_GO,row_format_text)
                else : sheet.write_string(row, column,'НЕТ',row_format_text)
                column += 1
                if tender.is_need_licenses_SRO == True:
                    sheet.write_string(row, column, (tender.licenses_SRO or ''),row_format_text)
                else : sheet.write_string(row, column,'НЕТ',row_format_text)
                column += 1
            str_responsible = ''
            for responsible in tender.responsible_ids:
                print('responsible = ', responsible.name)
                str_responsible = str_responsible + '\n'+(responsible.name or '')
            print('str_responsible = ',str_responsible)
            sheet.write_string(row, column, str_responsible,row_format_text)
            column += 1
            sheet.write_string(row, column, (tender.current_status.name or ''),row_format_text)
            column += 1
            str_comment = ''
            for comment in tender.tender_comments_ids:
                str_comment  = str_comment + '\n' + str(comment.date_comment) + ' ' + (comment.type_comment_id.name or '') + ' ' + (comment.text_comment or '')
            sheet.write_string(row, column, str_comment,row_format_text_comments)
            column += 1
            sheet.write_string(row, column, (tender.presale_number or ''),row_format_text)



    def generate_xlsx_report(self, workbook, data, lines):
        print('data = ',data)
        date_from = datetime.strptime(data['date_from'], "%d-%m-%Y").date()
        date_to = datetime.strptime(data['date_to'], "%d-%m-%Y").date()
        global is_report_for_management
        is_report_for_management= data['is_report_for_management']
        tenders_list = self.env['project_budget.tenders'].search([('date_of_filling_in', '>=', date_from),('date_of_filling_in', '<=', date_to)], order='date_of_filling_in desc')

        print('is_report_for_management =' , is_report_for_management)
        self.printworksheet(workbook, tenders_list)
