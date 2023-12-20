from odoo import api, fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.model
    def default_get(self, field_list):
        result = super(AccountAnalyticLine, self).default_get(field_list)
        if not self.env.context.get('default_employee_id') and 'employee_id' in field_list and result.get('user_id'):
            result['employee_id'] = self.env['hr.employee'].search([
                ('user_id', '=', result['user_id']),
                ('company_id', '=', result.get('company_id', self.env.company.id))
            ], limit=1).id
        return result

    def _domain_employee_id(self):
        domain = [
            '|', ('company_id', '=', False), ('company_id', 'in', self.env.context.get('allowed_company_ids', []))]
        if not self.user_has_groups('hr_timesheet_management.group_hr_timesheet_manager'):
            domain.append(('user_id', '=', self.env.user.id))
        return domain

    task_id = fields.Many2one('task.task', string='Task', index='btree_not_null',
                              readonly=False, store=True,
                              domain="[('parent_ref_type', '=', 'project_budget.projects')]")
    project_id = fields.Many2one('project_budget.projects', string='Project', compute='_compute_project_id',
                                 domain="[('budget_state', '=', 'work')]", index=True, store=True)
    user_id = fields.Many2one('res.users', compute='_compute_user_id', store=True, readonly=False)
    employee_id = fields.Many2one('hr.employee', string='Employee', check_company=True, context={'active_test': False},
                                  domain=_domain_employee_id)
    manager_id = fields.Many2one('hr.employee', string='Manager', related='employee_id.parent_id', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals.update(self._timesheet_preprocess(vals))
            if not vals.get('name'):
                vals['name'] = '/'

        records = super(AccountAnalyticLine, self).create(vals_list)
        return records

    def write(self, values):
        values = self._timesheet_preprocess(values)
        if 'name' in values and not values.get('name'):
            values['name'] = '/'
        result = super(AccountAnalyticLine, self).write(values)
        return result

    @api.depends('task_id', 'task_id.parent_ref')
    def _compute_project_id(self):
        for line in self:
            if not line.task_id.parent_ref or line.task_id.parent_ref_type != 'project_budget.projects'\
                    or line.project_id == line.task_id.parent_ref:
                continue
            line.project_id = line.task_id.parent_ref

    @api.depends('employee_id')
    def _compute_user_id(self):
        for line in self:
            line.user_id = line.employee_id.user_id if line.employee_id else self._default_user()

    def _timesheet_preprocess(self, vals):
        task = self.env['task.task'].browse(vals.get('task_id', False))
        if task and not vals.get('account_id'):
            task_analytic_account_id = task._get_task_analytic_account_id()
            vals['account_id'] = task_analytic_account_id.id
            vals['company_id'] = task_analytic_account_id.company_id.id or task.company_id.id
        return vals

    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)
