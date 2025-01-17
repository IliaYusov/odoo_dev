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
                'overdue': project.overdue,
            } for project in self.env['project.budget.project.overdue.report'].search([('overdue', '!=', False)], limit=3)
        ]

        overdue_in_7_day_projects = [
            {
                'id': project.id,
                'project_id': project.project_id.id,
                'step_id': project.step_id.id,
                'step_name': project.step_id.essence_project,
                'name': project.name,
                'customer': project.customer_id.name,
                'key_account_manager': project.key_account_manager_id.name,
                'overdue': project.overdue_in_7_days
            } for project in self.env['project.budget.project.overdue.report'].search([('overdue_in_7_days', '!=', False)], limit=3)
        ]

        result = {
            'overdue_projects': overdue_projects,
            'overdue_in_7_days_projects': overdue_in_7_day_projects,
        }

        return result
