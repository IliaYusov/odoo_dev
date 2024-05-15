from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    replaceable_employee_ids = fields.One2many('hr.employee', string='Replaceable Employees',
                                               compute='_compute_replaceable_employee_ids')

    def _compute_replaceable_employee_ids(self):
        for rec in self:
            domain = [
                ('replacement_employee_id', '=', rec.id),
                ('date_start', '<=', fields.Date.today()),
                '|', ('date_end', '=', False), ('date_end', '>=', fields.Date.today())
            ]
            ctx = self.env.context.copy()
            for key, value in ctx.items():
                if key.endswith('_function'):
                    domain += [(key, '=', value)]
            replacement_ids = self.env['hr.employee.replacement'].search(domain)
            rec.replaceable_employee_ids = replacement_ids.replaceable_employee_id.ids or False
