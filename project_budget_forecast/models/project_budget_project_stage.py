from odoo import fields, models


class ProjectStage(models.Model):
    _inherit = 'project_budget.project.stage'

    forecast_probability_ids = fields.One2many('project_budget.project.stage.forecast.probability', 'stage_id',
                                               string='Forecast Probabilities')


class ProjectStageForecastProbability(models.Model):
    _name = 'project_budget.project.stage.forecast.probability'
    _description = 'Project Stage Forecast Probability'

    stage_id = fields.Many2one('project_budget.project.stage', string='Stage')
    sale_figure_id = fields.Many2one('project_budget.sale.figure', string='Sale Figure', required=True)
    forecast_probability_id = fields.Many2one('project_budget.forecast.probability', string='Forecast Probability',
                                              required=True)
