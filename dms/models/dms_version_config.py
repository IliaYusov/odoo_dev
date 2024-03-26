from odoo import fields, models


class DmsVersionConfig(models.Model):
    _name = 'dms.version.config'
    _description = 'DMS Version Config'

    model_id = fields.Many2one('ir.model', string='Model', copy=False)
    model_name = fields.Char(related='model_id.model', string='Model Name', copy=False, readonly=True)
    company_id = fields.Many2one('res.company', string='Company', copy=False)
