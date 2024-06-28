from odoo import api, fields, models


class ProjectMember(models.Model):
    _name = 'project_budget.project.member'
    _description = 'Project Member'
    _order = 'id'

    project_id = fields.Many2one('project_budget.projects', string='Project', domain="[('budget_state', '=', 'work')]",
                                 index=True, ondelete='cascade')
    company_id = fields.Many2one(related='project_id.company_id', string='Company', readonly=True)
    can_edit = fields.Boolean(related='project_id.can_edit', readonly=True)
    role_id = fields.Many2one('project_budget.project.role', string='Project Role', ondelete='restrict',
                              required=True)
    role_id_domain = fields.Binary(compute='_compute_role_id_domain')
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                  required=True)

    @api.depends('role_id')
    def _compute_role_id_domain(self):
        for rec in self:
            uniq_roles = self.env['project_budget.project.role'].search([
                ('is_unique', '=', True)
            ])
            roles = rec.project_id.project_member_ids.mapped('role_id').filtered(lambda r: r.id in uniq_roles.ids)
            rec.role_id_domain = [
                ('id', 'not in', roles.ids),
            ]
