import logging
from io import BytesIO

from ..tools import docx_template_parse_template
from odoo import models, fields
from odoo.exceptions import AccessError

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
        template = self.env.context.get("template_attachment_id", False)
        objs = self._get_objs_for_report(docids, data)
        file_data = BytesIO()
        if template:
            file = docx_template_parse_template.DocxTemplateParseTemplate(BytesIO(template.raw))
            serialized_object = self.serialize(objs[0], 0, file.undeclared_template_variables, file.get_all_template_variables())
            file.render(serialized_object)
        else:
            file = docx.Document()
            self.generate_docx_report(file, data, objs)
        file.save(file_data)
        file_data.seek(0)
        return file_data.read(), "docx"

    def serialize(self, obj, depth, fields_list, template_fields_set):
        data = {}
        for field in fields_list:
            if field in template_fields_set:
                try:
                    new_obj = obj[field]
                except AccessError:
                    continue
                if isinstance(new_obj, models.Model) and depth > 2:
                    continue
                elif isinstance(new_obj, models.Model):
                    if hasattr(new_obj, '__iter__') and len(new_obj) > 1 :
                        data[field] = [self.serialize(o, depth + 1, o._fields, template_fields_set) for o in new_obj]
                    elif new_obj:
                        data[field] = self.serialize(new_obj, depth + 1, new_obj._fields, template_fields_set)
                    else:
                        continue
                else:
                    data[field] = new_obj
        return data

    def generate_docx_report(self, file, data, objs):
        raise NotImplementedError()
