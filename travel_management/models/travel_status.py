from odoo import models, fields, api


class travel_status(models.Model):
    _name = 'travel.status'

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    descr = fields.Char(string="Description")
