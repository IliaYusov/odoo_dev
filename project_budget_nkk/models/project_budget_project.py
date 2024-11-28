from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class Project(models.Model):
    _inherit = 'project_budget.projects'

    def toggle_active(self):
        if not self.user_has_groups('project_budget.project_budget_admin'):
            raise_text = _("User should have admin rights")
            raise ValidationError(raise_text)
        return super(Project, self).toggle_active()
