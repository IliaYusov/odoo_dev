from odoo import _, models
import datetime
from html.parser import HTMLParser


class HTMLFilter(HTMLParser):
    text = ""

    def handle_data(self, data):
        self.text += data


class EventProtocol(models.AbstractModel):
    _name = 'report.document_flow.decisions_list'
    _description = 'document_flow.decisions_list'
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, events):
        event = events[0]

        head_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_size': 11,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#FFFF00'
        })
        row_format_not_done = workbook.add_format({
            'border': 1,
            'font_size': 9,
            'text_wrap': True,
            'valign': 'top',
        })
        row_format_done = workbook.add_format({
            'border': 1,
            'font_size': 9,
            'color': '#006100',
            'fg_color': '#C6EFCE',
            'text_wrap': True,
            'valign': 'top',
        })
        row_format_overdue = workbook.add_format({
            'border': 1,
            'font_size': 9,
            'color': '#9C0006',
            'fg_color': '#FFC7CE',
            'text_wrap': True,
            'valign': 'top',
        })

        sheet = workbook.add_worksheet('Tasks')

        sheet.merge_range(0, 0, 0, 3, 'Отчет на ' + datetime.date.strftime(datetime.date.today(), '%d.%m.%Y') + ' по ' + event.name)

        row = 1

        sheet.set_column(0, 0, 15)
        sheet.write_string(row, 0, 'Задача', head_format)
        sheet.set_column(1, 1, 100)
        sheet.write_string(row, 1, 'Описание', head_format)
        sheet.set_column(2, 2, 35)
        sheet.write_string(row, 2, 'Исполнитель', head_format)
        sheet.set_column(3, 3, 25)
        sheet.write_string(row, 3, 'Крайний срок исполнения', head_format)

        sheet.freeze_panes(2, 0)

        main_process = self.env['document_flow.process.parent_object'].search([
            ('parent_ref_id', '=', event.id),
            ('parent_ref_type', '=', event._name),
            ('process_id', '!=', False),
            ('process_id.type', '=', 'complex'),
            ('process_id.state', '!=', 'break')
        ]).process_id

        if main_process:
            for task in main_process.task_ids:
                row += 1

                if task.is_closed:
                    row_format = row_format_done
                elif task.date_deadline < datetime.date.today():
                    row_format = row_format_overdue
                else:
                    row_format = row_format_not_done

                if task.description:
                    f = HTMLFilter()
                    html_descr = (str(task.description)
                                  .replace('<li>', '\n  - <li>')
                                  .replace('</ul>', '</ul>\n\n')
                                  .replace('<ul>', '\n<ul>'))
                    f.feed(html_descr)
                    text = f.text.strip()
                else:
                    text = task.name

                sheet.write_string(row, 0, task.code, row_format)
                sheet.write_string(row, 1, text, row_format)
                sheet.write_string(row, 2, task.user_id.name, row_format)
                sheet.write_string(row, 3, datetime.date.strftime(task.date_deadline, '%d.%m.%Y'), row_format)
                sheet.set_row(row, 14)
