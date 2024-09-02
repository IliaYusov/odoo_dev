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
