from odoo import fields, models


class ReportExternalData(models.Model):
    _name = 'project_budget.report_external_data'
    _description = 'Report External Data'
    _check_company_auto = True
    _rec_name = 'report_date'

    company_id = fields.Many2one('res.company', string='Company', required=True)
    report_date = fields.Date(string='Report Date', default=fields.date.today())
    data = fields.Text(string='Data')
    file = fields.Binary(string='File')
