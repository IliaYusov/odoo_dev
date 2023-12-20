from odoo import api, fields, models
from ...document_flow.models.document_flow_process import selection_executor_model


class DocumentTypeAccess(models.Model):
    _name = 'contract.access'
    _description = 'Contract Access'

    @api.model
    def _selection_executor_model(self):
        executor_models = dict(selection_executor_model())
        executor_models.pop('document_flow.auto_substitution')
        return list(executor_models.items())

    contract_id = fields.Many2one('contract.contract', string='Contract', index=True, required=True,
                                  copy=True, ondelete='cascade')
    user_ref = fields.Reference(string='User', selection='_selection_executor_model', copy=False, required=True)
    user_id = fields.Many2one('res.users', string='User', compute='_compute_user_id', store=True)
    role_executor_id = fields.Many2one('document_flow.role_executor', string='Group',
                                       compute='_compute_role_executor_id', store=True)

    @api.depends('user_ref')
    def _compute_user_id(self):
        for contract in self:
            if type(contract.user_ref).__name__ == 'res.users':
                contract.user_id = contract.user_ref.id
            else:
                contract.user_id = False

    @api.depends('user_ref')
    def _compute_role_executor_id(self):
        for contract in self:
            if type(contract.user_ref).__name__ == 'document_flow.role_executor':
                contract.role_executor_id = contract.user_ref.id
            else:
                contract.role_executor_id = False
