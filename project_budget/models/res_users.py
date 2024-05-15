from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'
    # _name = "users_budgets_access"
    _description = "users budgets access"
    project_supervisor_access_ids = fields.One2many(
        comodel_name='project_budget.project_supervisor_access',
        inverse_name='user_id',
        string="project_supervisor_access",
        copy=False, auto_join=True)

    rukovoditel_project_access_ids = fields.One2many(
        comodel_name='project_budget.rukovoditel_project_access',
        inverse_name='user_id',
        string="rukovoditel_project_access",
        copy=False, auto_join=True)



    supervisor_rule = fields.Many2many(compute='_get_list_supervisor_access_ids', comodel_name='project_budget.project_supervisor')
    rukovoditel_project_rule = fields.Many2many(compute='_get_list_rukovoditel_project_access_ids',
                                    comodel_name='project_budget.rukovoditel_project')


    @ api.depends("project_supervisor_access_ids.user_id","project_supervisor_access_ids.project_supervisor_id","project_supervisor_access_ids.descr")
    def _get_list_supervisor_access_ids(self):
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

    @ api.depends("rukovoditel_project_access_ids.rukovoditel_project_id","rukovoditel_project_access_ids.user_id")
    def _get_list_rukovoditel_project_access_ids(self):
        print('_get_list_rukovoditel_project_access_ids')
        rukovoditel_project_access = self.env['project_budget.rukovoditel_project_access'].search([('user_id.id', '=', self.env.user.id)])
        rukovoditel_project_list = []
        if not rukovoditel_project_access :
            # managers = self.env['project_budget.project_manager'].search([])
            # for each in managers:
            #     manager_list.append(each.id)
            print('FALSE')
            rukovoditel_project_list.append(False)
        else :
            for each in rukovoditel_project_access:
                print('each.rukovoditel_project_id.id', each.rukovoditel_project_id.id)
                rukovoditel_project_list.append(each.rukovoditel_project_id.id)
        for rec in self:
            rec.rukovoditel_project_rule = rukovoditel_project_list
