from odoo import fields, models


class BudgetPlanSupervisor(models.Model):
    _inherit = 'project_budget.budget_plan_supervisor'

    supervisor_id = fields.Many2one('project_budget.project_supervisor', string='KAMs supervisor', copy=True,
                                    tracking=True, check_company=True)  # TODO убрать после миграции на кураторов
    supervisor_user_id = fields.Many2one(related='supervisor_id.user_id', readonly=True)  # TODO убрать после миграции на кураторов

    # ------------------------------------------------------
    # CORE METHODS OVERRIDES
    # ------------------------------------------------------

    def name_get(self):
        result = dict(super(BudgetPlanSupervisor, self).name_get())
        for rec in self:
            name = result.get(rec.id)
            name += ' ' + rec.supervisor_id.name if rec.supervisor_id else ''
            result[rec.id] = name
        return list(result.items())


class BudgetPlanKam(models.Model):
    _inherit = 'project_budget.budget_plan_kam'

    supervisor_id = fields.Many2one(related = 'plan_supervisor_id.supervisor_id', string='KAMs supervisor')
    supervisor_user_id = fields.Many2one(related='plan_supervisor_id.supervisor_user_id', readonly=True)