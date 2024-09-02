from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    percent_fot = fields.Float(string="FOT percent", default=0)
    is_percent_fot_manual = fields.Boolean(string="Manual FOT percent", default=False)
    different_project_offices_in_steps = fields.Boolean(string='different project offices in steps', default=False)
