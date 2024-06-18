from odoo import api, models


class Project(models.Model):
    _inherit = 'project_budget.projects'

    # ------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------

    @api.model
    def retrieve_dashboard(self):
        self.check_access_rights('read')

        overdue_projects = [
            {
                'id': project.id,
                'project_id': project.project_id.id,
                'step_id': project.step_id.id,
                'step_name': project.step_id.essence_project,
                'name': project.name,
                'customer': project.customer_id.name,
                'key_account_manager': project.key_account_manager_id.name,
                'reason': project.reason
            } for project in self.env['project.budget.project.overdue.report'].search([], limit=3)
        ]

        result = {
            'overdue_projects': overdue_projects,
        }

        return result
