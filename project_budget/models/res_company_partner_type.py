from odoo import fields, models


class ResCompanyPartnerType(models.Model):
    _name = 'res.company.partner.type'
    _order = 'sequence'
    _description = 'Company Partner Type'

    sequence = fields.Integer(string='Sequence')
    active = fields.Boolean(string='Active', default=True)
    name = fields.Char(string='Type', required=True, translate=True)
