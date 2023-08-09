from odoo import _, models, fields, api, exceptions


class ProjectTask(models.Model):
    _inherit = 'project_budget.projects'

    @api.model
    def _selection_parent_model(self):
        return [('project_budget.projects', _('Project'))]

    task_count = fields.Integer(compute='_compute_task_count', string='Tasks')

    def _compute_task_count(self):
        self.task_count = self.env['task.task'].search_count([
            ('parent_id', '=', False),
            ('parent_ref_type', '=', self._name),
            ('parent_ref_id', 'in', [pr.id for pr in self])
        ])


class ProjectBudgetTask(models.Model):
    _inherit = 'task.task'

    @api.model
    def _selection_parent_model(self):
        types = super(ProjectBudgetTask, self)._selection_parent_model()
        types.append(('project_budget.projects', _('Project')))
        return types
