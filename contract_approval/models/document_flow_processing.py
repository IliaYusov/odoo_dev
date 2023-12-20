from odoo import api, models, _


class Processing(models.Model):
    _inherit = 'document_flow.processing'

    @api.model
    def _selection_parent_model(self):
        types = super(Processing, self)._selection_parent_model()
        types.append(('contract.contract', _('Contract')))
        return types
