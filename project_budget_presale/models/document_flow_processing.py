from odoo import _, models, fields, api


class Processing(models.Model):
    _inherit = 'document_flow.processing'

    @api.model
    def _selection_parent_model(self):
        types = super(Processing, self)._selection_parent_model()
        types.append(('project_budget.presale', _('Presale')))
        return types
