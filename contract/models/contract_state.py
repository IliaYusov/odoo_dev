from odoo import fields, models


class ContractState(models.Model):
    _name = 'contract.state'
    _description = 'Contract State'
    _order = 'sequence, id'

    name = fields.Char(string='Name', copy=True, required=True, translate=True)
    sequence = fields.Integer(default=1)
    hidden = fields.Boolean(string='Hidden', default=False, help='Hide the state for selection.')
    active = fields.Boolean(default=True)
