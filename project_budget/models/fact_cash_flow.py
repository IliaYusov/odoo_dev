from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import pytz
from datetime import date


class fact_cash_flow(models.Model):
    _name = 'project_budget.fact_cash_flow'
    _description = "fact cash flow"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    projects_id = fields.Many2one('project_budget.projects', string='projects_id', index=True, ondelete='cascade',
                                  auto_join=True, readonly=True)
    can_edit = fields.Boolean(related='projects_id.can_edit', readonly=True)
    project_have_steps = fields.Boolean(related='projects_id.project_have_steps', string='project have steps',
                                        readonly=True)
    step_project_child_id = fields.Many2one('project_budget.projects', string="step-project child id", index=True,
                                            ondelete='cascade')
    date_cash = fields.Date(string="date_cash", required=True, copy=True)
    currency_id = fields.Many2one('res.currency', string='Account Currency', compute='_compute_reference')
    sum_cash_without_vat = fields.Monetary(string="fact sum_cash_without_vat", required=True, copy=True, compute='_compute_sum')
    sum_cash = fields.Monetary(string="fact sum_cash", required=True, copy=True)
    doc_cash = fields.Char(string="doc_cash",  copy=True) #20230403 Вавилова Ирина сказла убрать из формы...
    budget_state = fields.Selection(related='projects_id.budget_state', readonly=True, store=True)
    approve_state = fields.Selection(related='projects_id.approve_state', readonly=True, store=True)

    distribution_cash_ids = fields.One2many(
        comodel_name='project_budget.distribution_cash',
        inverse_name='fact_cash_flow_id',
        string="distribution cash fact by plan", auto_join=True, copy=False)

    distribution_sum_with_vat = fields.Monetary(string="distribution sum with vat", compute='_compute_distribution_sum')
    distribution_sum_without_vat = fields.Monetary(string="distribution sum without vat", compute='_compute_distribution_sum')
    distribution_sum_without_vat_ostatok = fields.Monetary(string="distribution_sum_without_vat_ostatok", compute='_compute_distribution_sum')
    distribution_sum_with_vat_ostatok = fields.Monetary(string="distribution_sum_with_vat_ostatok", compute='_compute_distribution_sum')

    @ api.depends('projects_id.currency_id')
    def _compute_reference(self):
        for row in self:
            row.currency_id = row.projects_id.currency_id

    @api.depends("sum_cash","step_project_child_id.tax_id","projects_id.tax_id")
    def _compute_sum(self):
        for row in self:
            if row.step_project_child_id:
                row.sum_cash_without_vat = row.sum_cash/(1+row.step_project_child_id.tax_id.amount / 100)
            else:
                row.sum_cash_without_vat = row.sum_cash / (1 + row.projects_id.tax_id.amount / 100)

    @api.depends("distribution_cash_ids")
    def _compute_distribution_sum(self):
        for row in self:
            row.distribution_sum_with_vat = row.distribution_sum_without_vat = 0
            row.distribution_sum_with_vat_ostatok = row.distribution_sum_without_vat_ostatok = 0
            for distribution_cash in row.distribution_cash_ids:
                row.distribution_sum_with_vat += distribution_cash.sum_cash
                row.distribution_sum_without_vat += distribution_cash.sum_cash_without_vat
            row.distribution_sum_with_vat_ostatok =row.sum_cash - row.distribution_sum_with_vat
            row.distribution_sum_without_vat_ostatok = row.sum_cash_without_vat - row.distribution_sum_without_vat

    def action_copy_fact_cash(self):
        self.ensure_one()
        if self.projects_id.budget_state == 'fixed':  # сделка в зафиксированном бюджете
            raise_text = _("This project is in fixed budget. Copy deny")
            raise (ValidationError(raise_text))
        self.env['project_budget.fact_cash_flow'].browse(self.id).copy({'id': '-', 'distribution_cash_ids': None})
