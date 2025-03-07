from odoo import api, fields, models


class ProjectMember(models.Model):
    _inherit = 'project_budget.project.member'

    employee_id = fields.Many2one(required=False)
    is_external = fields.Boolean(string='Is External', default=False)
    contact_id = fields.Many2one('res.partner', string='Contact',
                                 domain="[('type', '=', 'contact'), ('is_company', '=', False)]")

    _sql_constraints = [
        (
            'check_employee_or_contact_not_null',
            'CHECK(employee_id IS NOT NULL OR contact_id IS NOT NULL)',
            'Field "Employee" or "Contact" must not be empty!'
        )
    ]

    @api.onchange('is_external')
    def _onchange_is_external(self):
        self.employee_id = self.employee_id if not self.is_external else False
        self.contact_id = self.contact_id if self.is_external else False
