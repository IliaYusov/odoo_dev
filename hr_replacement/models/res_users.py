from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    def write(self, vals):  # при снятии группы снимаем группу также и в делегациях групп
        res = super().write(vals)
        if res:
            for key, value in vals.items():
                if key.startswith('in_group_') and not value:
                    removed_group_id = int(key.split('_')[-1])
                    replacements = self.env['hr.employee.replacement'].search([
                        ('replaceable_employee_id.user_id', '=', self.id),
                        ('replaceable_groups_ids', '=', removed_group_id),
                    ])
                    for replacement in replacements:
                        new_groups = self.env['res.groups'].search([
                            ('id', 'in', replacement.replaceable_groups_ids.ids),
                            ('id', '!=', removed_group_id),
                        ])
                        replacement.write({'replaceable_groups_ids': new_groups})
        return res
