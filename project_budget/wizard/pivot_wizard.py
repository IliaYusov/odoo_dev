from odoo import api, models, fields, _

class pivot_wizard(models.TransientModel):
    _name = 'project_budget.pivot_wizard'
    _description = 'Pivot Wizard'

    name = fields.Char(string="Project_ID | Step ID",)
    project_id = fields.Many2one('project_budget.projects')
    step_id = fields.Many2one('project_budget.project_steps')
    company_id = fields.Many2one('res.company', related='project_id.company_id', store=True)
    project_office_id = fields.Many2one('project_budget.project_office', related='project_id.project_office_id', store=True)
    total_amount_of_revenue = fields.Monetary(string='total_amount_of_revenue')
    currency_id = fields.Many2one('res.currency', related='project_id.currency_id')

    def create_fields(self):
        old_model = self.env['project_budget.pivot_wizard'].search([])
        if old_model:
            for spec in old_model:
                spec.unlink()
        for project in self.env['project_budget.projects'].search([('budget_state', '=', 'work')]):
            if project.project_have_steps:
                for step in project.project_steps_ids:
                    self.create({
                        'name': project.project_id + ' | ' + step.step_id,
                        'project_id': project.id,
                        'step_id': step.id,
                        'total_amount_of_revenue': step.total_amount_of_revenue,
                    })
            else:
                self.create({
                    'name': project.project_id,
                    'project_id': project.id,
                    'step_id': False,
                    'total_amount_of_revenue': project.total_amount_of_revenue,
                })
        return {
            'type': 'ir.actions.act_window',
            'name': 'action_pivot_wizard_pivot',
            'view_type': 'pivot',
            'view_mode': 'pivot',
            'res_model': 'project_budget.pivot_wizard',
            'target': 'current',
        }
