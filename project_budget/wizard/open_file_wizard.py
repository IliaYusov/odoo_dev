from odoo import models, fields, _
from io import BytesIO
import base64


class OpenFileWizard(models.TransientModel):
    _name = 'project_budget.open_file_wizard'
    _description = 'Open File Wizard'

    company_id = fields.Many2one('res.company', string='Company', required=True)
    data_file = fields.Binary(string='Data file', required=True)

    def import_file_data(self):
        file = BytesIO(base64.b64decode(self.data_file))
        data = self.env['project_budget.report_external_data'].file_to_data(file)
        if data:
            self.env['project_budget.report_external_data'].create({
                'company_id': self.company_id.id,
                'data': data,
                'file': self.data_file,
            })
