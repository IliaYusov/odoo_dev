from odoo import fields, models


class ResCompanyPartnerGrade(models.Model):
    _name = 'res.company.partner.grade'
    _order = 'sequence'
    _description = 'Company Partner Grade'

    sequence = fields.Integer(string='Sequence')
    active = fields.Boolean(string='Active', default=True)
    name = fields.Char(string='Level Name', required=True, translate=True)
