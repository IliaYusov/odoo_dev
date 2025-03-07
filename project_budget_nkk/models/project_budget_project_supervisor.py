from odoo import models, fields


class ProjectSupervisor(models.Model):
    _name = 'project_budget.project_supervisor'
    _description = "project_supervisor"
    name = fields.Char(string="project_supervisor name", required=True, translate=True)
    code = fields.Char(string="project_supervisor code", required=True)
    descr = fields.Char(string="project_supervisor description", translate=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='user id',  required=True,)
    avatar_128 = fields.Image(related='user_id.avatar_128', readonly=True)
    project_supervisor_access_ids = fields.One2many(
            comodel_name='project_budget.project_supervisor_access',
            inverse_name='project_supervisor_id',
            string="project_supervisor_access",
            copy=True, auto_join=True)


class ProjectSupervisorAccess(models.Model):
    _name = 'project_budget.project_supervisor_access'
    _description = "project_supervisor_access"
    project_supervisor_id = fields.Many2one('project_budget.project_supervisor', string='project supervisor id',
                                            required=True, )
    user_id = fields.Many2one('res.users', string='user id',  required=True,)
    can_approve_project = fields.Boolean(string="Can approve project as supervisor", default=False)
    descr = fields.Char(string="project supervisor access description", translate=True)
