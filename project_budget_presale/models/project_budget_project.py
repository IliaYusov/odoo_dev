from odoo import models, fields


class Project(models.Model):
    _inherit = 'project_budget.projects'

    presale_count = fields.Integer(compute='_compute_presale_count', string='Presales')

    def _compute_presale_count(self):
        for project in self:
            project.presale_count = self.env['project_budget.presale'].search_count([
                ('project_id', '=', project.id)
            ])
