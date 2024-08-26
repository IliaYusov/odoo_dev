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

    @api.onchange('replaceable_employee_id')
    def _clear_groups(self):  # обнуляем выбранные группы при смене работника
        for record in self:
            record.replaceable_groups_ids = False

    @api.depends('replaceable_employee_id')
    def _get_allowed_groups(self):  # формируем домен групп из активных у пользователя и принадлежащих модулю
        for record in self:
            group = False
            category = 'project_budget.module_category_services_budget_project'
            user = self.replaceable_employee_id.user_id
            if user:
                group = user.groups_id.ids
            record.allowed_groups = self.env['res.groups'].search([('id', 'in', group), ('category_id', '=', self.env.ref(category).id)])
