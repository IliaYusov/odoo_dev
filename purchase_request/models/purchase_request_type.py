from odoo import fields, models


class RequestType(models.Model):
    _name = 'purchase.request.type'
    _description = 'Request Type'

    name = fields.Char(string='Name', copy=True, required=True)
