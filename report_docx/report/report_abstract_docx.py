import logging
from io import BytesIO

from odoo import models

_logger = logging.getLogger(__name__)

try:
    import docx

except ImportError:
    _logger.debug("Can not import docxwriter`.")


class ReportDocxAbstract(models.AbstractModel):
    _name = "report.report_docx.abstract"
    _description = "Abstract DOCX Report"

    def _get_objs_for_report(self, docids, data):
        if docids:
            ids = docids
        elif data and "context" in data:
            ids = data["context"].get("active_ids", [])
        else:
            ids = self.env.context.get("active_ids", [])
        return self.env[self.env.context.get("active_model")].browse(ids)

    def create_docx_report(self, docids, data):
        objs = self._get_objs_for_report(docids, data)
        file_data = BytesIO()
        file = docx.Document()
        self.generate_docx_report(file, data, objs)
        file.save(file_data)
        file_data.seek(0)
        return file_data.read(), "docx"

    def generate_docx_report(self, file, data, objs):
        raise NotImplementedError()
