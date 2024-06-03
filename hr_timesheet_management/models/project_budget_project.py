from odoo import api, fields, models, _


class Project(models.Model):
    _inherit = 'project_budget.projects'

    analytic_account_id = fields.Many2one('account.analytic.account', copy=False, domain="""[
        '|', ('company_id', '=', False), ('company_id', '=', company_id)],
        ('partner_id', '=?', partner_id)""")

    timesheet_ids = fields.One2many('account.analytic.line', 'project_id', string='Timesheets')
    total_hours_spent = fields.Float(compute='_compute_total_hours_spent', string='Hours')

    @api.depends('timesheet_ids')
    def _compute_total_hours_spent(self):
        timesheet_read_group = self.env['account.analytic.line'].\
            read_group([('project_id', 'in', self.ids)], ['unit_amount', 'project_id'], ['project_id'])
        timesheets_per_project = {res['project_id'][0]: res['unit_amount'] for res in timesheet_read_group}
        for project in self:
            project.total_hours_spent = timesheets_per_project.get(project.id, 0.0)

    @api.model_create_multi
    def create(self, vals_list):
        defaults = self.default_get(['analytic_account_id', 'commercial_budget_id'])
        for vals in vals_list:
            analytic_account_id = vals.get('analytic_account_id', defaults.get('analytic_account_id'))
            if not analytic_account_id and vals.get('commercial_budget_id') == defaults.get('commercial_budget_id'):
                analytic_account = self._create_analytic_account_from_values(vals)
                vals['analytic_account_id'] = analytic_account.id
        return super().create(vals_list)

    # def write(self, values):
    #     if not values.get('analytic_account_id'):
    #         [project._create_analytic_account() for project in
    #          self.filtered(lambda pr: not pr.analytic_account_id and pr.budget_state == 'work')]
    #     return super(Project, self).write(values)

    @api.model
    def _init_data_analytic_account(self):
        self.search([('analytic_account_id', '=', False), ('budget_state', '=', 'work')])._create_analytic_account()

    @api.model
    def _create_analytic_account_from_values(self, values):
        company = self.env['res.company'].browse(values.get('company_id')) if values.get(
            'company_id') else self.env.company
        org = self.env['res.partner'].browse(
            values.get('partner_id')) if values.get('company_id') else False
        # TODO: Подумать над необходимостью sudo
        analytic_account = self.env['account.analytic.account'].sudo().create({
            'name': values.get('essence_project', _('Unknown Analytic Account')),
            'company_id': company.id,
            'partner_id': org.id if org else False,
            'plan_id': company.analytic_plan_id.id,
        })
        return analytic_account

    def _create_analytic_account(self):
        for project in self:
            # TODO: Подумать над необходимостью sudo
            analytic_account = self.env['account.analytic.account'].sudo().create({
                'name': project.essence_project,
                'company_id': project.company_id.id,
                'partner_id': project.partner_id.id,
                'plan_id': project.company_id.analytic_plan_id.id,
                'active': True
            })
            project.with_context(form_fix_budget=True).write({'analytic_account_id': analytic_account.id})
