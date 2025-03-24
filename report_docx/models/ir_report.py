from odoo import api, fields, models


class ReportAction(models.Model):
    _inherit = "ir.actions.report"

    report_type = fields.Selection(
        selection_add=[("docx", "DOCX")], ondelete={"docx": "set default"}
    )
    template_attachment_id = fields.Many2one('ir.attachment', string='Template File')

    @api.model
    def _render_docx(self, report_ref, docids, data):
        report_sudo = self._get_report(report_ref)
        report_model_name = "report.%s" % report_sudo.report_name
        report_model = self.env[report_model_name]
        return (
            report_model.with_context(
                active_model=report_sudo.model,
                template_attachment_id=report_sudo.template_attachment_id
            )
            .sudo(False)
            .create_docx_report(docids, data)
        )

    @api.model
    def _get_report_from_name(self, report_name):
        res = super()._get_report_from_name(report_name)
        if res:
            return res
        report_obj = self.env["ir.actions.report"]
        qwebtypes = ["docx"]
        conditions = [
            ("report_type", "in", qwebtypes),
            ("report_name", "=", report_name),
        ]
        context = self.env["res.users"].context_get()
        return report_obj.with_context(**context).search(conditions, limit=1)
