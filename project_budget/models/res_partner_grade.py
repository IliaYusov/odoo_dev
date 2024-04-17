from odoo import fields, models


class ResPartnerGrade(models.Model):
    _name = 'res.partner.grade'
    _order = 'sequence'
    _description = 'Partner Grade'

    sequence = fields.Integer(string='Sequence')
    active = fields.Boolean(string='Active', default=True)
    name = fields.Char(string='Level Name', required=True, translate=True)
