from odoo import _, models


class EventProtocol(models.AbstractModel):
    _name = 'report.document_flow.decisions_list'
    _description = 'document_flow.decisions_list'
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, events):
        event = events[0]

        sheet = workbook.add_worksheet('Decisions')

        task_ids = []
        main_process = self.env['document_flow.process.parent_object'].search([
            ('parent_ref_id', '=', event.id),
            ('parent_ref_type', '=', event._name),
            ('process_id', '!=', False),
            ('process_id.type', '=', 'complex'),
            ('process_id.state', '!=', 'break')
        ]).process_id
        if main_process:
            for task in main_process.task_ids:
                pass
