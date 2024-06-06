from odoo import fields, models


class HrEmployeeReplacement(models.Model):
    _inherit = 'hr.employee.replacement'

    kam_function = fields.Boolean(string='Can See KAM Projects', default=False)
    project_manager_function = fields.Boolean(string='Can See Project Manager Projects', default=False)
