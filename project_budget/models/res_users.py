from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    project_supervisor_access_ids = fields.One2many(
        comodel_name='project_budget.project_supervisor_access',
        inverse_name='user_id',
        string="project_supervisor_access",
        copy=False, auto_join=True)  # TODO убрать после миграции на кураторов

    supervisor_rule = fields.Many2many(compute='_get_list_supervisor_access_ids', comodel_name='project_budget.project_supervisor')  # TODO убрать после миграции на кураторов

    @ api.depends("project_supervisor_access_ids.user_id","project_supervisor_access_ids.project_supervisor_id","project_supervisor_access_ids.descr")
    def _get_list_supervisor_access_ids(self):  # TODO убрать после миграции на кураторов
        supervisor_access = self.env['project_budget.project_supervisor_access'].search([('user_id.id', '=', self.env.user.id)])
        supervisor_list = []
        if not supervisor_access :
            # supervisors = self.env['project_budget.project_supervisor'].search([])
            # for each in supervisors:
            #     supervisor_list.append(each.id)
            supervisor_list.append(False)
        else :
            for each in supervisor_access:
                supervisor_list.append(each.project_supervisor_id.id)
        for rec in self:
            rec.supervisor_rule = supervisor_list

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
