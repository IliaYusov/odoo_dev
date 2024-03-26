from odoo import fields, models


class Workflow(models.Model):
    _inherit = 'workflow.workflow'

    contract_type_id = fields.Many2one('contract.type', string='Contract Type', copy=True, ondelete='set null')
    contract_kind_id = fields.Many2one('contract.kind', string='Contract Kind', copy=True, ondelete='set null')
