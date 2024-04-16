from odoo import _, models
from docx.shared import Pt, Mm
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

import pytz


class TemplateForm(models.AbstractModel):
    _name = 'report.contract.contract.template.form'
    _description = 'contract.contract.template.form'
    _inherit = 'report.report_docx.abstract'
