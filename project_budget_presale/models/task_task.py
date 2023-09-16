from odoo import _, models, fields, api


class Task(models.Model):
    _inherit = 'task.task'

    @api.model
    def _selection_parent_obj_model(self):
        types = super(Task, self)._selection_parent_obj_model()
        types.append(('project_budget.presale', _('Presale')))
        return types
