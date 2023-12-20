from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    replacement_employee_ids = fields.One2many('hr.employee.replacement', 'replaceable_employee_id',
                                               string='Replacement Employees', check_company=True,
                                               context={'search_default_actual_replacements': True})
    replaceable_employee_ids = fields.One2many('hr.employee.replacement', 'replacement_employee_id',
                                               string='Replaceable Employees', check_company=True,
                                               context={'search_default_actual_replacements': True})

    @api.model
    def get_replaceable_user_ids(self):
        return self.get_replaceable_employee_ids().user_id.ids

    @api.model
    def get_replaceable_employee_ids(self):
        today = fields.Date.today()
        return self.env.user.employee_ids.replaceable_employee_ids.filtered(
            lambda r: r.date_start <= today and (
                    not r.date_end or r.date_end >= today)).replaceable_employee_id
