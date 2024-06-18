from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class License(models.Model):
    _inherit = 'license.license'

    project_id = fields.Many2one('project_budget.projects', string='Project', copy=True, depends=['customer_id'],
                                 domain="[('budget_state', '=', 'work'), ('partner_id', '=', customer_id), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                 tracking=True)
    company_partner_id = fields.Many2one('res.company.partner', string='Company Partner',
                                         compute='_compute_company_partner_id',
                                         domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                         readonly=False, tracking=True, store=True)

    @api.constrains('project_id', 'company_partner_id')
    def _check_company_partner_id(self):
        if self.project_id and self.project_id.company_partner_id != self.company_partner_id:
            raise ValidationError(_("Company partner set in the license must match set in the project."))

    @api.depends('project_id')
    def _compute_company_partner_id(self):
        for rec in self:
            rec.company_partner_id = rec.project_id.company_partner_id if rec.project_id else False
