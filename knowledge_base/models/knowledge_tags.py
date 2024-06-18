from odoo import fields, models


class Tags(models.Model):
    _name = 'knowledge.tags'
    _description = 'Knowledge Article Tags'

    name = fields.Char(string='Name', index=True, required=True)
    description = fields.Text(string='Description')
