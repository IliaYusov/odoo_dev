from odoo import api, models, _


# TODO: странная зависимость модулей получается
class Task(models.Model):
    _inherit = 'task.task'

    @api.model
    def _selection_parent_obj_model(self):
        types = super(Task, self)._selection_parent_obj_model()
        types.append(('contract.contract', _('Contract')))
        return types
