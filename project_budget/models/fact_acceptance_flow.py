from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import pytz
from datetime import timedelta

class fact_acceptance_flow(models.Model):

    def get_project_steps_list(self):
        domain = [('id', '=', 0)]
        project_steps = self.env['project_budget.project_steps'].search([('projects_id.id', '=', self.env.projects_id.id)])
        project_steps_list = []
        for each in project_steps:
            project_steps_list.append(each.id)
        if project_steps_list:
            domain = [('id', 'in', project_steps_list)]
            return domain
        return domain

    _name = 'project_budget.fact_acceptance_flow'
    _description = "fact acceptance flow"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    projects_id = fields.Many2one('project_budget.projects', string='projects_id', index=True,ondelete='cascade', auto_join=True,readonly=True)
    project_have_steps = fields.Boolean(string="project have steps", related='projects_id.project_have_steps',
                                        readonly=True)
    project_steps_id = fields.Many2one('project_budget.project_steps', string='project_steps_id', index=True,ondelete='cascade',
                                       )
    date_cash = fields.Date(string="date_cash" , required=True, copy=True)
    currency_id = fields.Many2one('res.currency', string='Account Currency', compute='_compute_reference')
    sum_cash_without_vat = fields.Monetary(string="fact sum_cash_without_vat", required=True, copy=True)
    sum_cash = fields.Monetary(string="fact sum_cash", required=True, copy=True, compute='_compute_sum')
    budget_state = fields.Selection(related='projects_id.budget_state', readonly=True, store=True)
    approve_state = fields.Selection(related='projects_id.approve_state', readonly=True, store=True)

    doc_cash = fields.Char(string="doc_cash", copy=True) #20230403 Вавилова Ирина сказла убрать из формы...

    distribution_acceptance_ids = fields.One2many(
        comodel_name='project_budget.distribution_acceptance',
        inverse_name='fact_acceptance_flow_id',
        string="distribution acceptance fact by plan", auto_join=True,copy=True)

    distribution_sum_with_vat = fields.Monetary(string="distribution sum with vat", compute='_compute_distribution_sum')
    distribution_sum_without_vat = fields.Monetary(string="distribution sum without vat", compute='_compute_distribution_sum')
    distribution_sum_without_vat_ostatok = fields.Monetary(string="distribution_sum_without_vat_ostatok", compute='_compute_distribution_sum')
    distribution_sum_with_vat_ostatok = fields.Monetary(string="distribution_sum_with_vat_ostatok", compute='_compute_distribution_sum')

    margin = fields.Monetary(string='margin', compute='_compute_margin')
    margin_manual_input = fields.Boolean(string='manual input of margin')

    @ api.depends('projects_id.currency_id')
    def _compute_reference(self):
        for row in self:
            row.currency_id = row.projects_id.currency_id
    @api.depends("sum_cash_without_vat","project_steps_id.vat_attribute_id","projects_id.vat_attribute_id")
    def _compute_sum(self):
        for row in self:
            if row.project_steps_id:
                row.sum_cash = row.sum_cash_without_vat * (1+row.project_steps_id.vat_attribute_id.percent / 100)
            else:
                row.sum_cash = row.sum_cash_without_vat * (1 + row.projects_id.vat_attribute_id.percent / 100)

    @api.onchange("distribution_acceptance_ids")
    def _compute_distribution_sum(self):
        for row in self:
            row.distribution_sum_with_vat = row.distribution_sum_without_vat = 0
            row.distribution_sum_with_vat_ostatok = row.distribution_sum_without_vat_ostatok = 0
            for distribution_acceptance in row.distribution_acceptance_ids:
                row.distribution_sum_with_vat += distribution_acceptance.sum_cash
                row.distribution_sum_without_vat += distribution_acceptance.sum_cash_without_vat
            row.distribution_sum_with_vat_ostatok =row.sum_cash - row.distribution_sum_with_vat
            row.distribution_sum_without_vat_ostatok = row.sum_cash_without_vat - row.distribution_sum_without_vat

    @api.onchange("sum_cash_without_vat")
    def _compute_margin(self):
        for row in self:
            if row.project_have_steps:
                row.margin = row.sum_cash_without_vat * self.env['project_budget.project_steps'].search(
                    [('id', '=', row.project_steps_id)]).profitability / 100
            else:
                print(row.projects_id)
                row.margin = row.sum_cash_without_vat * self.env['project_budget.projects'].search(
                    [('id', '=', row.projects_id)]).profitability / 100
