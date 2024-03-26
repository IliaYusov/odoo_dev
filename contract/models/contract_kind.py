from odoo import api, fields, models


class ContractKind(models.Model):
    _name = 'contract.kind'
    _description = 'Contract Kind'

    name = fields.Char(string='Name', required=True, copy=True)
    active = fields.Boolean(default=True)
