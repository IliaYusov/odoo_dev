from odoo import fields, models


class ReportExternalData(models.Model):
    _name = 'project_budget.report_external_data'
    _description = 'Report External Data'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', string='Company', required=True)
    report_date = fields.Datetime(string='Report Date', default=fields.datetime.now())
    data = fields.Text(string='Data')
    file = fields.Binary(string='File')
