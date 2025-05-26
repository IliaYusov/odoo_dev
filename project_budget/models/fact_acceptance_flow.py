from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import pytz
from datetime import date


class fact_acceptance_flow(models.Model):
    _rec_name = 'name_to_show'

    _name = 'project_budget.fact_acceptance_flow'
    _description = "fact acceptance flow"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    projects_id = fields.Many2one('project_budget.projects', string='projects_id', index=True, ondelete='cascade',
                                  auto_join=True, readonly=True)
    can_edit = fields.Boolean(related='projects_id.can_edit', readonly=True)
    name_to_show = fields.Char(string='name_to_show', compute='_get_name_to_show')
    project_have_steps = fields.Boolean(related='projects_id.project_have_steps', string='project have steps',
                                        readonly=True)
    step_project_child_id = fields.Many2one('project_budget.projects', string="step-project child id", index=True,
                                            ondelete='cascade')
    date_cash = fields.Date(string="date_cash", required=True, copy=True)
    currency_id = fields.Many2one('res.currency', string='Account Currency', compute='_compute_reference')
    sum_cash_without_vat = fields.Monetary(string="fact sum_cash_without_vat", required=True, copy=True)
    sum_cash = fields.Monetary(string="fact sum_cash", required=True, copy=True, compute='_compute_sum')
    budget_state = fields.Selection(related='projects_id.budget_state', readonly=True, store=True)
    approve_state = fields.Selection(related='projects_id.approve_state', readonly=True, store=True)

    doc_cash = fields.Char(string="doc_cash", copy=True) #20230403 Вавилова Ирина сказла убрать из формы...

    distribution_acceptance_ids = fields.One2many(
        comodel_name='project_budget.distribution_acceptance',
        inverse_name='fact_acceptance_flow_id',
        string="distribution acceptance fact by plan", auto_join=True, copy=False)

    distribution_sum_with_vat = fields.Monetary(string="distribution sum with vat", compute='_compute_distribution_sum')
    distribution_sum_without_vat = fields.Monetary(string="distribution sum without vat", compute='_compute_distribution_sum')
    distribution_sum_without_vat_ostatok = fields.Monetary(string="distribution_sum_without_vat_ostatok", compute='_compute_distribution_sum')
    distribution_sum_with_vat_ostatok = fields.Monetary(string="distribution_sum_with_vat_ostatok", compute='_compute_distribution_sum')

    @ api.depends('projects_id.currency_id')
    def _compute_reference(self):
        for row in self:
            row.currency_id = row.projects_id.currency_id

    @api.depends('date_cash', 'step_project_child_id', 'sum_cash_without_vat')
    def _get_name_to_show(self):
        for prj in self:
            prj.name_to_show = prj.date_cash.strftime("%d/%m/%Y") + _(' | acceptance ') + _(' | sum cash without vat ') + f'{prj.sum_cash_without_vat:_.2f}'
            if prj.project_have_steps:
                prj.name_to_show += _(' | step ') + (prj.step_project_child_id.project_id or '') + _(' | code ') + (prj.step_project_child_id.step_project_number or '') + _(' | essence_project ') + (prj.step_project_child_id.essence_project or '')

    @api.depends("sum_cash_without_vat", "step_project_child_id.tax_id", "projects_id.tax_id")
    def _compute_sum(self):
        for row in self:
            if row.step_project_child_id:
                row.sum_cash = row.sum_cash_without_vat * (1+row.step_project_child_id.tax_id.amount / 100)
            else:
                row.sum_cash = row.sum_cash_without_vat * (1 + row.projects_id.tax_id.amount / 100)

    @api.onchange("distribution_acceptance_ids")
    def _compute_distribution_sum(self):
        for row in self:
            row.distribution_sum_with_vat = row.distribution_sum_without_vat = 0
            row.distribution_sum_with_vat_ostatok = row.distribution_sum_without_vat_ostatok = 0
            for distribution_acceptance in row.distribution_acceptance_ids:
                row.distribution_sum_with_vat += distribution_acceptance.sum_cash
                row.distribution_sum_without_vat += distribution_acceptance.sum_cash_without_vat
            row.distribution_sum_with_vat_ostatok = row.sum_cash - row.distribution_sum_with_vat
            row.distribution_sum_without_vat_ostatok = row.sum_cash_without_vat - row.distribution_sum_without_vat

    def action_copy_fact_acceptance(self):
        self.ensure_one()
        if self.projects_id.budget_state == 'fixed':  # сделка в зафиксированном бюджете
            raise_text = _("This project is in fixed budget. Copy deny")
            raise (ValidationError(raise_text))
        self.env['project_budget.fact_acceptance_flow'].browse(self.id).copy({'id': '-', 'distribution_acceptance_ids': None})
