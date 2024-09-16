from odoo import api, fields, models


class PlannedCashFlow(models.Model):
    _inherit = 'project_budget.planned_cash_flow'

    def _get_default_forecast_probability_id(self):
        return self.env['project_budget.forecast.probability'].search([], limit=1)

    forecast_probability_id = fields.Many2one('project_budget.forecast.probability', string='Forecast Probability',
                                              default=_get_default_forecast_probability_id, required=True)

    # TODO: костыль для обратной совместимости, удалить после миграции на новое поле прогнозной вероятности
    @api.onchange('forecast_probability_id')
    def _onchange_forecast_probability_id(self):
        for rec in self:
            if rec.forecast_probability_id.sequence == 1:
                rec.forecast = 'from_project'
            elif rec.forecast_probability_id.sequence == 2:
                rec.forecast = 'commitment'
            elif rec.forecast_probability_id.sequence == 3:
                rec.forecast = 'reserve'
            else:
                rec.forecast = 'potential'
