from odoo import api, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def get_user_employee_info(self):
        employees = self.env['hr.employee'].sudo().search_read([
            ('user_id', '=', self.env.user.id),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        employee = employees[0] if employees else False
        if employee:
            all_employee = self.env['hr.employee'].sudo().search([
                ('user_id', '=', self.env.user.id)
            ])
            employee.update({
                'subordinate_ids': all_employee.subordinate_ids.user_id.ids or False,
                'replaceable_ids': all_employee.replaceable_employee_ids.user_id.ids
            })
        return employee
