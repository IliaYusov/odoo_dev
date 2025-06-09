from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.addons.project_budget.models.project_budget_flow_mixin import FlowMixin


class PlannedCashFlow(models.Model):
    _inherit = 'project_budget.planned_cash_flow'

    # NOTE: смысла в поле нет, необходимо для проекта по дашбордам, коллеги построили на нем аналитику, не удалять!!!
    date_actual = fields.Datetime(related='projects_id.date_actual', readonly=True)

    # NOTE: временное поле, удалить во время перехода на целевую архитектуру модуля бюджетирования
    budget_item_id = fields.Many2one('account.budget.item', string='Budget Item', copy=True,
                                     domain="[('direction', '=', 'income'), ('child_ids', '=', False), ('company_ids', 'in', company_id)]")
    account_type_id = fields.Many2one('res.partner.bank.type', string='Account Type', copy=True)


class FactCashFlow(models.Model):
    _inherit = 'project_budget.fact_cash_flow'

    planned_cash_flow_id = fields.Many2one('project_budget.planned_cash_flow', string='Planned Cash Flow',
                                           index=True, copy=False, store=True,
                                           domain="[('projects_id', '=', projects_id), ('currency_id', '=', currency_id), ('distribution_cash_ids', '=', False)]")
    acceptance_ids = fields.Many2many(
        'project_budget.fact_acceptance_flow',
        relation='project_budget_fact_cash_acceptance_rel',
        string="Acceptance facts",
        compute='_compute_default_acceptance_ids',
        store=True,
        readonly=False,
    )
    # ------------------------------------------------------
    # CONSTRAINS
    # ------------------------------------------------------

    @api.constrains('planned_cash_flow_id')
    def _check_one_plan_for_one_fact(self):
        for rec in self:
            if not rec.env.context.get('form_fix_budget'):
                if self.env['project_budget.fact_cash_flow'].search_count([
                    ('planned_cash_flow_id', '=', rec.planned_cash_flow_id.id), ('planned_cash_flow_id', '!=', False)
                ], limit=2) > 1:
                    raise_text = _("Cash forecast {0} is assigned to several facts")
                    raise_text = raise_text.format(rec.planned_cash_flow_id.flow_id)
                    raise ValidationError(raise_text)

    # ------------------------------------------------------
    # COMPUTE METHODS
    # ------------------------------------------------------

    @api.onchange("planned_cash_flow_id")
    def _compute_default_acceptance_ids(self):
        for row in self:
            row.acceptance_ids = row.planned_cash_flow_id.acceptance_ids.distribution_acceptance_ids.fact_acceptance_flow_id

    # ------------------------------------------------------
    # CRUD
    # ------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        records = super(FactCashFlow, self).create(vals_list)
        if not self.env.context.get('form_fix_budget'):
            for rec in records:
                if rec['planned_cash_flow_id']:
                    self.env['project_budget.distribution_cash'].create({
                        'fact_cash_flow_id': rec.id,
                        'planned_cash_flow_id': rec.planned_cash_flow_id.id,
                        'amount': rec.amount,
                    })
        return records

    def write(self, vals):
        if not self.env.context.get('form_fix_budget'):
            if vals.get('planned_cash_flow_id'):
                distribution = self.env['project_budget.distribution_cash'].search([
                    ('planned_cash_flow_id', '=', vals['planned_cash_flow_id'])
                ], limit=1)

                if distribution:
                    distribution.amount = vals.get('amount', 0)
                else:
                    self.env['project_budget.distribution_cash'].search([
                        ('fact_cash_flow_id', '=', self.id)
                    ]).unlink()
                    self.env['project_budget.distribution_cash'].create({
                        'fact_cash_flow_id': self.id,
                        'planned_cash_flow_id': vals['planned_cash_flow_id'],
                        'amount': vals.get('amount', self.amount)
                    })
            elif 'amount' in vals and self.planned_cash_flow_id:
                distribution = self.env['project_budget.distribution_cash'].search([
                    ('fact_cash_flow_id', '=', self.id)
                ], limit=1)
                if distribution:
                    distribution.amount = vals['amount']
            elif 'planned_cash_flow_id' in vals and not vals['planned_cash_flow_id']:
                self.env['project_budget.distribution_cash'].search([
                    ('fact_cash_flow_id', '=', self.id)
                ]).unlink()
        res = super(FactCashFlow, self).write(vals)
        return res

    # ------------------------------------------------------
    # FLOW MIXIN
    # ------------------------------------------------------

    def action_copy_flow(self):
        FlowMixin.action_copy_flow(self, {'distribution_cash_ids': None, 'planned_cash_flow_id': False})
