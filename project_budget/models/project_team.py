from odoo import _, models, fields, api


class project_team(models.Model):
    _name = 'project_budget.project_team'
    _description = "project budget team"
    _check_company_auto = True

    projects_id = fields.Many2one('project_budget.projects', string='project', index=True, required=True, ondelete='cascade', delegate=True)
    project_id = fields.Char(related='projects_id.project_id', store=True)
    employee_id = fields.Many2one('hr.employee', string='employee', required=True)
    role_id = fields.Many2many('project_budget.project_role', string='role', required=True)
