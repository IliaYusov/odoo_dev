from odoo import fields, models


class LicenseType(models.Model):
    _name = 'license.type'
    _description = 'License Type'

    name = fields.Char(string='Name', required=True, translate=True, help='Type of the license')
