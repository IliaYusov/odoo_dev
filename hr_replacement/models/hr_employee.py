from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    replacement_employee_ids = fields.One2many('hr.employee.replacement', 'replaceable_employee_id',
                                               string='Replacement Employees', check_company=True,
                                               context={'search_default_actual_replacements': 1})
    replaceable_employee_ids = fields.One2many('hr.employee.replacement', 'replacement_employee_id',
                                               string='Replaceable Employees', check_company=True,
                                               context={'search_default_actual_replacements': 1})
