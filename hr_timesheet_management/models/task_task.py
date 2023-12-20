from odoo import models, fields, api, _


class Task(models.Model):
    _inherit = 'task.task'

    analytic_account_id = fields.Many2one(
        'account.analytic.account', compute='_compute_analytic_account_id',
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", ondelete='set null',
        readonly=False, store=True,
        help="""Analytic account to which this task and its timesheets are linked.
             Track the costs and revenues of your task by setting its analytic account on your related documents.
             By default, the analytic account of the project is set. However, it can be changed on each task individually if necessary.""")
    project_analytic_account_id = fields.Many2one('account.analytic.account', string='Project Analytic Account',
                                                  compute='_compute_project_analytic_account_id')
    planned_hours = fields.Float(string='Planned Hours', tracking=True)
    subtask_planned_hours = fields.Float(string='Sub-tasks Planned Hours', compute='_compute_subtask_planned_hours',
                                         help="""Sum of the hours allocated for all the sub-tasks (and their own sub-tasks) linked to this task.
                                              Usually less than or equal to the allocated hours of this task.""")
    effective_hours = fields.Float(string='Hours Spent', compute='_compute_effective_hours', compute_sudo=True,
                                   store=True)
    total_hours_spent = fields.Float(string='Total Hours', compute='_compute_total_hours_spent', store=True,
                                     help='Time spent on this task and its sub-tasks (and their own sub-tasks).')
    subtask_effective_hours = fields.Float(string='Sub-tasks Hours Spent', compute='_compute_subtask_effective_hours',
                                           recursive=True, store=True,
                                           help='Time spent on the sub-tasks (and their own sub-tasks) of this task.')
    timesheet_ids = fields.One2many('account.analytic.line', 'task_id', string='Timesheets')

    def _get_task_analytic_account_id(self):
        self.ensure_one()
        return self.analytic_account_id or self.project_analytic_account_id

    @api.depends('parent_ref')
    def _compute_analytic_account_id(self):
        for task in self:
            if not task.parent_ref or task.parent_ref_type != 'project_budget.projects'\
                    or task.project_analytic_account_id == task.parent_ref.analytic_account_id:
                continue
            task.analytic_account_id = task.parent_ref.analytic_account_id

    @api.depends('parent_ref')
    def _compute_project_analytic_account_id(self):
        for task in self:
            if not task.parent_ref or task.parent_ref_type != 'project_budget.projects'\
                    or task.project_analytic_account_id == task.parent_ref.analytic_account_id:
                continue
            task.project_analytic_account_id = task.parent_ref.analytic_account_id

    @api.depends('child_ids.planned_hours')
    def _compute_subtask_planned_hours(self):
        for task in self:
            task.subtask_planned_hours = sum(child_task.planned_hours + child_task.subtask_planned_hours for child_task in task.child_ids)

    @api.depends('timesheet_ids.unit_amount')
    def _compute_effective_hours(self):
        if not any(self._ids):
            for task in self:
                task.effective_hours = sum(task.timesheet_ids.mapped('unit_amount'))
            return
        timesheet_read_group = self.env['account.analytic.line'].read_group([('task_id', 'in', self.ids)],
                                                                            ['unit_amount', 'task_id'], ['task_id'])
        timesheets_per_task = {res['task_id'][0]: res['unit_amount'] for res in timesheet_read_group}
        for task in self:
            task.effective_hours = timesheets_per_task.get(task.id, 0.0)

    @api.depends('effective_hours', 'subtask_effective_hours')
    def _compute_total_hours_spent(self):
        for task in self:
            task.total_hours_spent = task.effective_hours + task.subtask_effective_hours

    @api.depends('child_ids.effective_hours', 'child_ids.subtask_effective_hours')
    def _compute_subtask_effective_hours(self):
        for task in self.with_context(active_test=False):
            task.subtask_effective_hours = sum(
                child_task.effective_hours + child_task.subtask_effective_hours for child_task in task.child_ids)
