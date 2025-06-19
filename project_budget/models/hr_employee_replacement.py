from odoo import api, fields, models


class HrEmployeeReplacement(models.Model):
    _inherit = 'hr.employee.replacement'

    kam_function = fields.Boolean(string='Can See KAM Projects', default=False)  # TODO убрать после миграции на кураторов
    project_manager_function = fields.Boolean(string='Can See Project Manager Projects', default=False)  # TODO убрать после миграции на кураторов
    project_curator_function = fields.Boolean(string='Can See Project Supervisor Projects', inverse='_disable_can_approve_projects', default=False)  # TODO убрать после миграции на кураторов
    can_approve_projects = fields.Boolean(string='Can Approve Projects as Supervisor', default=False)  # TODO убрать после миграции на кураторов
    allowed_groups = fields.Many2many('res.groups', compute="_get_allowed_groups")

    @api.depends('project_curator_function')  # TODO убрать после миграции на кураторов
    def _disable_can_approve_projects(self):
        for row in self:
            if not row.project_curator_function:
                row.can_approve_projects = False

    @api.onchange('replaceable_employee_id', 'replacement_employee_id')
    def _clear_groups(self):  # обнуляем выбранные группы при смене работника
        for record in self:
            record.replaceable_groups_ids = False

    @api.depends('replaceable_employee_id', 'replacement_employee_id')
    def _get_allowed_groups(self):  # формируем домен групп из активных у пользователя и принадлежащих модулю
        for record in self:
            groups = False
            # category = 'base.module_category_services_budget_project'
            category = 'base.module_category_hidden'
            replaceable_user = record.replaceable_employee_id.user_id
            replacement_user = record.replacement_employee_id.user_id
            if replaceable_user and replacement_user:
                groups = (
                        record.replaceable_employee_id.user_id.groups_id -
                        (record.replacement_employee_id.user_id.groups_id - record.replacement_employee_id.user_id.delegated_group_ids)
                        + self.replaceable_groups_ids
                ).ids

            record.allowed_groups = self.env['res.groups'].search([('id', 'in', groups), ('category_id', '!=', self.env.ref(category).id)], order='category_id')

    def _update_employees_replacement_status(self):  # запускать утром
        active_replacements = self.env['hr.employee.replacement'].search([('active', '=', True)])
        for replacement in active_replacements:
            if replacement.date_end < fields.Date.today():
                replacement.toggle_active()
        new_active_replacements =  self.env['hr.employee.replacement'].search([('active', '=', True)])
        for replacement in new_active_replacements:
            if replacement.date_start <= fields.Date.today():
                self._add_groups(replacement.replacement_employee_id, replacement.replaceable_groups_ids)

    def _add_groups(self, employee, groups):
        for group in groups:
            if group not in employee.user_id.groups_id:
                group.write({'users': [(4, employee.user_id.id)]})
                employee.user_id.write({'delegated_group_ids': [(4, group.id)]})

    def _remove_groups(self, employee, groups):
        groups_in_other_replacements = self.env['hr.employee.replacement'].search(
            [('replacement_employee_id', '=', employee.id), ('active', '=', True)],
        ).replaceable_groups_ids
        for group in groups:
            if group in employee.user_id.delegated_group_ids and group not in groups_in_other_replacements:
                group.write({'users': [(3, employee.user_id.id)]})
                employee.user_id.write({'delegated_group_ids': [(3, group.id)]})

    def write(self, vals_list):
        old_replacement = {}
        for row in self:
            old_replacement[row.id] = {
                'active': row.active,
                'replacement_employee_id': row.replacement_employee_id,
                'replaceable_groups_ids': row.replaceable_groups_ids,
            }

        res = super().write(vals_list)

        if res:
            for row in self:
                date_is_suitable = row.date_start <= fields.Date.today() and (not row.date_end or fields.Date.today() <= row.date_end)
                if old_replacement[row.id]['active']:
                    self._remove_groups(old_replacement[row.id]['replacement_employee_id'], old_replacement[row.id]['replaceable_groups_ids'])
                if row.active and date_is_suitable:
                    self._add_groups(row.replacement_employee_id, row.replaceable_groups_ids)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        if res:
            for row in res:
                date_is_suitable = row.date_start <= fields.Date.today() and (
                            not row.date_end or fields.Date.today() <= row.date_end)
                if row.active and date_is_suitable:
                    self._add_groups(row.replacement_employee_id, row.replaceable_groups_ids)
        return res

    def unlink(self):
        old_replacement = {}
        for row in self:
            old_replacement[row.id] = {
                'active': row.active,
                'replacement_employee_id': row.replacement_employee_id,
                'replaceable_groups_ids': row.replaceable_groups_ids,
            }
        res = super().unlink()
        if res:
            for replacement in old_replacement.values():
                if replacement['active']:
                    self._remove_groups(replacement['replacement_employee_id'], replacement['replaceable_groups_ids'])
        return res
