from odoo import _, models
from docx.shared import Pt, Mm
from docx.enum.text import WD_BREAK
from htmldocx import HtmlToDocx

import pytz


class TestReport(models.AbstractModel):
    _name = 'report.project_budget.test_report'
    _description = 'project_budget.test_report'
    _inherit = "report.report_docx.abstract"
