from odoo import fields, models


class ForecastProbability(models.Model):
    _name = 'project_budget.forecast.probability'
    _description = 'Forecast Probability'
    _order = 'sequence, id'

    active = fields.Boolean('Active', default=True)
    name = fields.Char(string='Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    coefficient = fields.Float(string='Coefficient', default=1.0, required=True)


class SaleFigure(models.Model):
    _name = 'project_budget.sale.figure'
    _description = 'Sale Figure'
    _order = 'sequence, id'

    active = fields.Boolean('Active', default=True)
    name = fields.Char(string='Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
