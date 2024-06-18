from odoo import fields, models


class OS(models.Model):
    _name = 'license.os'
    _description = 'Operating System'
    _order = 'sequence, id'

    name = fields.Char(string='Name', copy=False, required=True)
    sequence = fields.Integer(default=1)

    _sql_constraints = [
        ('os_name_uniq',
         'UNIQUE (name)',
         'Operating system name must be uniq')
    ]
