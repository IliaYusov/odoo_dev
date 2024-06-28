from odoo import fields, models


class ReportExternalData(models.Model):
    _name = 'project_budget.report_external_data'
    _description = 'Report External Data'

    company = fields.Char(string='Company')
    data = fields.Text(string='Data')

    def import_report_external_data(self):
        pass
