from odoo import api, fields, models


class ProjectOffice(models.Model):
    _name = 'project_budget.project_office'
    _description = 'Project Office'

    active = fields.Boolean('Active', copy=False, default=True)
    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Code', required=True)
    descr = fields.Char(string='Description')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency', readonly=True)
    parent_id = fields.Many2one('project_budget.project_office', string='Parent Project Office', copy=True,
                                domain="[('id', '!=', id)]")
    child_ids = fields.One2many('project_budget.project_office', 'parent_id', string='Child Project Offices')
    user_id = fields.Many2one('res.users', string='Office manager')
    avatar_128 = fields.Image(related='user_id.avatar_128', readonly=True)

    project_ids = fields.One2many('project_budget.projects', string='Projects', compute='_compute_project_ids')
    project_count = fields.Integer(compute='_compute_project_count')

    revenue = fields.Float(string='Revenue', compute='_compute_revenue')
    cost = fields.Float(string='Cost', compute='_compute_cost')
    margin = fields.Float(string='Margin', compute='_compute_margin')

    receive_tasks_for_approve_project = fields.Boolean(string="Recieve tasks for approve project as supervisor",
                                                       default=False)
    isRukovoditel_required_in_project = fields.Boolean(string="mark rukovoditel required in prject", default=False)
    print_rukovoditel_in_kb = fields.Boolean(string="Print rukovoditel instead KAM in KB form",
                                                       default=False)
    is_prohibit_selection = fields.Boolean(string="is prohibit selection in projects", default=False)
    report_name = fields.Char(string="name for report")
    report_sort = fields.Integer(string="sorting for report", default=0, required=True)

    def _compute_project_ids(self):
        for rec in self:
            rec.project_ids = self.env['project_budget.projects'].search([
                ('budget_state', '=', 'work'),
                ('project_office_id', '=', rec.id)
            ])

    @api.depends('project_ids')
    def _compute_project_count(self):
        for rec in self:
            rec.project_count = len(rec.project_ids)

    @api.depends('project_ids')
    def _compute_revenue(self):
        for rec in self:
            rec.revenue = round(sum([pr.total_amount_of_revenue for pr in rec.project_ids]), 2) or 0

    @api.depends('project_ids')
    def _compute_cost(self):
        for rec in self:
            rec.cost = round(sum([pr.cost_price for pr in rec.project_ids]), 2) or 0

    @api.depends('project_ids')
    def _compute_margin(self):
        for rec in self:
            rec.margin = round(sum([pr.margin_income for pr in rec.project_ids]), 2) or 0
