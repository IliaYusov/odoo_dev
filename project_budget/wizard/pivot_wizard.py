from odoo import api, models, fields, _

class pivot_wizard(models.TransientModel):
    _name = 'project_budget.pivot_wizard'
    _description = 'Pivot Wizard'

    @api.model
    def get_view(self, view_id=None, view_type='pivot', **options):
        res = super(pivot_wizard, self).get_view(view_id=view_id, view_type=view_type, **options)
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
                        'end_presale_project_month': step.end_presale_project_month,
                    })
            else:
                self.create({
                    'name': project.project_id,
                    'project_id': project.id,
                    'step_id': False,
                    'total_amount_of_revenue': project.total_amount_of_revenue,
                    'end_presale_project_month': project.end_presale_project_month,
                })
        return res

    name = fields.Char(string="Project_ID | Step ID",)
    project_id = fields.Many2one('project_budget.projects')
    step_id = fields.Many2one('project_budget.project_steps')
    company_id = fields.Many2one('res.company', related='project_id.company_id', store=True)
    project_office_id = fields.Many2one('project_budget.project_office', related='project_id.project_office_id', store=True)
    total_amount_of_revenue = fields.Monetary(string='total amount of revenue')
    end_presale_project_month = fields.Date(string='project presale end month')
    currency_id = fields.Many2one('res.currency', related='project_id.currency_id')
