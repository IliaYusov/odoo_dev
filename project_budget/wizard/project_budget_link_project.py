from odoo import api, fields, models, _


class ProjectBudgetLinkProjectWizard(models.TransientModel):
    _name = 'project_budget.link.project.wizard'
    _description = 'Project Wizard: Link Project'

    project_id = fields.Many2one('project_budget.projects', string='Project', ondelete='cascade', readonly=True,
                                 required=True)
    company_id = fields.Many2one(related='project_id.company_id', readonly=True)
    partner_id = fields.Many2one(related='project_id.partner_id', readonly=True)
    company_partner_id = fields.Many2one('res.company.partner', string='Company Partner', check_company=True,
                                         domain="[('company_id', '=', company_id)]", required=True)
    parent_project_id = fields.Many2one('project_budget.projects', string='Parent Project',
                                        depends=['company_partner_id'], ondelete='cascade', required=True)
    parent_project_id_domain = fields.Binary(compute='_compute_parent_project_id_domain')

    # ------------------------------------------------------
    # COMPUTE METHODS
    # ------------------------------------------------------
    
    @api.depends('company_partner_id')
    def _compute_parent_project_id_domain(self):
        for record in self:
            domain = [('id', '=', -1)]
            company = self.env['res.company'].search([
                ('partner_id', '=', record.company_partner_id.partner_id.id)
            ])
            if company:
                domain = [
                    ('company_id', '=', company.id),
                    ('partner_id', '=', record.partner_id.id),
                ]
            record.parent_project_id_domain = domain

    # ------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------

    def action_link_project(self):
        self.ensure_one()

        self.project_id.write({'parent_id': self.parent_project_id})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'title': _('Projects Linked'),
                'message': _("Project was linked to project '%s'") % self.parent_project_id,
                'next': {
                    'type': 'ir.actions.act_window_close'
                }
            }
        }
