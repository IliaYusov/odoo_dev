from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class FactAcceptanceFlow(models.Model):
    _inherit = 'project_budget.fact_acceptance_flow'

    planned_acceptance_flow_id = fields.Many2one('project_budget.planned_acceptance_flow', index=True, copy=True,
                                                 store=True, string='planned_acceptance_flow',
                                                 domain='[("projects_id", "=", projects_id), ("distribution_acceptance_ids", "=", False)]')
    company_id = fields.Many2one(related='projects_id.company_id', readonly=True, store=True)

    # ------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------

    def action_copy_fact_acceptance(self):
        self.ensure_one()
        if self.projects_id.budget_state == 'fixed':  # сделка в зафиксированном бюджете
            raise_text = _("This project is in fixed budget. Copy deny")
            raise (ValidationError(raise_text))
        self.env['project_budget.fact_acceptance_flow'].browse(self.id).copy({
            'id': '-',
            'distribution_acceptance_ids': None,
            'planned_acceptance_flow_id': False,
        })

    # ------------------------------------------------------
    # CONSTRAINS
    # ------------------------------------------------------

    @api.constrains('planned_acceptance_flow_id')
    def _check_one_plan_for_one_fact(self):
        if not self.env.context.get('form_fix_budget'):
            if self.env['project_budget.fact_acceptance_flow'].search_count([
                ('planned_acceptance_flow_id', '=', self.planned_acceptance_flow_id.id), ('planned_acceptance_flow_id', '!=', False)
            ], limit=2) > 1:
                raise_text = _("Acceptance forecast {0} is assigned to several facts")
                raise_text = raise_text.format(self.planned_acceptance_flow_id.acceptance_id)
                raise ValidationError(raise_text)

    # ------------------------------------------------------
    # CRUD
    # ------------------------------------------------------

    def write(self, vals):
        if not self.env.context.get('form_fix_budget'):
            if 'planned_acceptance_flow_id' in vals:
                if vals['planned_acceptance_flow_id']:
                    self.env['project_budget.distribution_acceptance'].sudo().create({
                        'fact_acceptance_flow_id': self.id,
                        'planned_acceptance_flow_id': vals['planned_acceptance_flow_id'],
                        'sum_cash_without_vat': self.sum_cash_without_vat,
                        'sum_cash': self.sum_cash,
                    })
                else:
                    self.env['project_budget.distribution_acceptance'].sudo().search([
                        ('fact_acceptance_flow_id', '=', self.id)
                    ]).unlink()
        fact = super().write(vals)
        return fact

    def create(self, vals_list):
        facts = super().create(vals_list)
        if not self.env.context.get('form_fix_budget'):
            for fact in facts:
                if fact['planned_acceptance_flow_id']:
                    self.env['project_budget.distribution_acceptance'].sudo().create({
                        'fact_acceptance_flow_id': fact.id,
                        'planned_acceptance_flow_id': fact.planned_acceptance_flow_id.id,
                        'sum_cash_without_vat': fact.sum_cash_without_vat,
                        'sum_cash': fact.sum_cash,
                    })
        else:
            for fact in facts:
                if fact.planned_acceptance_flow_id:
                    new_plan = self.env['project_budget.planned_acceptance_flow'].search([
                        ('acceptance_id', '=', fact.planned_acceptance_flow_id.acceptance_id),
                        ('projects_id.commercial_budget_id', '=', fact.projects_id.commercial_budget_id.id),
                    ], limit=1)
                    fact.planned_acceptance_flow_id = new_plan
        return facts