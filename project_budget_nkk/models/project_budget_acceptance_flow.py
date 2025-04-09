from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class FactAcceptanceFlow(models.Model):
    _inherit = 'project_budget.fact_acceptance_flow'

    planned_acceptance_flow_id = fields.Many2one('project_budget.planned_acceptance_flow', index=True, copy=True,
                                                 store=True, string='planned_acceptance_flow',
                                                 domain='[("projects_id", "=", projects_id), ("distribution_acceptance_ids", "=", False)]')
    company_id = fields.Many2one(related='projects_id.company_id', readonly=True, store=True)
    margin = fields.Monetary(string='Margin', compute='_compute_margin', inverse='_inverse_margin', store=True, copy=True)
    margin_manual_input = fields.Boolean(string='Manual input of margin', default=False, copy=True)

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
    # COMPUTE METHODS
    # ------------------------------------------------------

    @api.depends("sum_cash_without_vat", "step_project_child_id.profitability", "projects_id.profitability", "margin_manual_input")
    @api.onchange("sum_cash_without_vat", "margin_manual_input")
    def _compute_margin(self):
        for row in self:
            if not row.margin_manual_input:
                if row.project_have_steps:
                    row.margin = row.sum_cash_without_vat * row.step_project_child_id.profitability / 100
                else:
                    row.margin = row.sum_cash_without_vat * row.projects_id.profitability / 100

    def _inverse_margin(self):
        pass

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
            if vals.get('planned_acceptance_flow_id'):
                distribution = self.env['project_budget.distribution_acceptance'].search([
                    ('planned_acceptance_flow_id', '=', vals['planned_acceptance_flow_id'])
                ], limit=1)

                if distribution:
                    distribution.sum_cash_without_vat = vals.get('sum_cash_without_vat', 0)
                else:
                    self.env['project_budget.distribution_acceptance'].search([
                        ('fact_acceptance_flow_id', '=', self.id)
                    ]).unlink()
                    self.env['project_budget.distribution_acceptance'].create({
                        'fact_acceptance_flow_id': self.id,
                        'planned_acceptance_flow_id': vals['planned_acceptance_flow_id'],
                        'sum_cash_without_vat': vals.get('sum_cash_without_vat', self.sum_cash_without_vat)
                    })
            elif 'sum_cash_without_vat' in vals and self.planned_acceptance_flow_id:
                distribution = self.env['project_budget.distribution_acceptance'].search([
                    ('fact_acceptance_flow_id', '=', self.id)
                ], limit=1)
                if distribution:
                    distribution.sum_cash_without_vat = vals['sum_cash_without_vat']
            elif 'planned_acceptance_flow_id' in vals and not vals['planned_acceptance_flow_id']:
                self.env['project_budget.distribution_acceptance'].search([
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