from odoo import api, fields, models


class HrEmployeeReplacement(models.Model):
    _inherit = 'hr.employee.replacement'

    kam_function = fields.Boolean(string='Can See KAM Projects', default=False)
    project_manager_function = fields.Boolean(string='Can See Project Manager Projects', default=False)
    project_curator_function = fields.Boolean(string='Can See Project Supervisor Projects', inverse='_disable_can_approve_projects', default=False)
    can_approve_projects = fields.Boolean(string='Can Approve Projects as Supervisor', default=False)

    @api.depends('project_curator_function')
    def _disable_can_approve_projects(self):
        for row in self:
            if not row.project_curator_function:
                row.can_approve_projects = False
