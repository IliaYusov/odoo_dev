import datetime

from odoo import _, models
from html2text import html2text


class ReportDecisionsList(models.AbstractModel):
    _name = 'report.document_flow.event_decisions_list'
    _description = 'document_flow.event_decisions_list'
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

        sheet = workbook.add_worksheet('Decisions')

        sheet.merge_range(0, 0, 0, 3,
                          'Отчет на ' + datetime.date.strftime(datetime.date.today(), '%d.%m.%Y') + ' по ' + event.name)
        row = 1
        sheet.set_column(0, 0, 15)
        sheet.write_string(row, 0, _('Task'), head_format)
        sheet.set_column(1, 1, 100)
        sheet.write_string(row, 1, _('Description'), head_format)
        sheet.set_column(2, 2, 35)
        sheet.write_string(row, 2, _('Executors'), head_format)
        sheet.set_column(3, 3, 25)
        sheet.write_string(row, 3, _('Deadline'), head_format)
        sheet.set_column(4, 4, 25)
        sheet.write_string(row, 4, _('Comment'), head_format)

        sheet.freeze_panes(2, 0)

        processes = event.process_id.child_ids.filtered(lambda pr: pr.type == 'complex')
        if processes:
            for task in processes[0].active_task_ids:
                row += 1

                if task.is_closed:
                    row_format = row_format_done
                elif task.date_deadline < datetime.date.today():
                    row_format = row_format_overdue
                else:
                    row_format = row_format_not_done

                sheet.write_string(row, 0, task.code, row_format)
                sheet.write_string(row, 1, task.name if not task.description else html2text(task.description),
                                   row_format)
                sheet.write_string(row, 2, ', '.join(task.user_ids.mapped('name')), row_format)
                sheet.write_string(row, 3, task.date_deadline.strftime('%d.%m.%Y'), row_format)
                sheet.write_string(row, 4, html2text(task.execution_result) if task.is_closed else '', row_format)
                sheet.set_row(row, None)

            # sheet.autofit()
