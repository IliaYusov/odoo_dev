from odoo import models, fields


# TODO: разобраться с отчетами в основном модуле (КБ, КБ_фин, rawdata)
class TechnologicalDirection(models.Model):
    _name = 'project_budget.technological_direction'
    _description = 'Technological Direction'
    _order = 'sequence, id'

    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer(string='Sequence', default=1)
    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Code', required=True)
    descr = fields.Char(string='Description', translate=True)
    recurring_payments = fields.Boolean(string='Recurring Payments', default=False)
