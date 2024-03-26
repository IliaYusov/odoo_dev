from odoo import fields, models


class Project(models.Model):
    _inherit = 'project_budget.projects'

    task_count = fields.Integer(compute='_compute_task_count', string='Tasks')

    def _compute_task_count(self):
        self.task_count = self.env['task.task'].search_count([
            ('parent_id', '=', False),
            ('parent_ref_type', '=', self._name),
            ('parent_ref_id', 'in', self.ids)
        ])
