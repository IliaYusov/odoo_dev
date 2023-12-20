from odoo import models, fields


class Project(models.Model):
    _inherit = 'project_budget.projects'

    purchase_request_count = fields.Integer(compute='_compute_purchase_request_count', string='Purchase Requests')

    def _compute_purchase_request_count(self):
        for project in self:
            project.purchase_request_count = self.env['purchase.request'].search_count([
                ('project_id', '=', project.id)
            ])
