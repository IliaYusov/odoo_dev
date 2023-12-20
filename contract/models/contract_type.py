from odoo import api, fields, models


class ContractType(models.Model):
    _name = 'contract.type'
    _description = 'Contract Type'

    name = fields.Char(string='Name', required=True, copy=True)
    active = fields.Boolean(default=True)
    properties_definition = fields.PropertiesDefinition('Contract Properties')
