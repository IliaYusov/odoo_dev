from odoo import fields, models


class ComponentCharacteristic(models.Model):
    _name = 'purchase.request.component.characteristic'
    _description = 'Component Characteristic'

    name = fields.Char(string='Name', copy=True, required=True)
