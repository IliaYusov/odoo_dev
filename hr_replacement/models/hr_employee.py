from odoo import fields, models, api


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

    def get_group_domain(self, *args):
        domain = []
        for _ in range(len(args) - 1):
            domain.append('|')
        for field, group in args:
            replacement_ids = self.env['hr.employee.replacement'].search([
                ('replacement_employee_id', '=', self.id),
                ('date_start', '<=', fields.Date.today()),
                '|', ('date_end', '=', False), ('date_end', '>=', fields.Date.today()),
                ('replaceable_groups_ids', '=', self.env.ref(group).id)
            ])
            domain.append((field, 'in', replacement_ids.replaceable_employee_id.user_id.ids))
        return domain
