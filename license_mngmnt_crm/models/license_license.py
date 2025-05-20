from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class License(models.Model):
    _inherit = 'license.license'

    opportunity_id = fields.Many2one('project_budget.projects', string='Opportunity', copy=True,
                                     depends=['customer_id'],
                                     domain="[('step_status', '=', 'project'), ('budget_state', '=', 'work'), ('partner_id', '=', customer_id), ('company_id', '=', company_id)]",
                                     tracking=True)
    company_partner_id = fields.Many2one('res.company.partner', string='Company Partner',
                                         compute='_compute_opportunity_data',
                                         domain="[('company_id', '=', company_id)]", readonly=False, tracking=True,
                                         store=True)
    contract_number = fields.Char(string='Contract Number', copy=False, tracking=True)

    @api.constrains('opportunity_id', 'company_partner_id')
    def _check_company_partner_id(self):
        for rec in self:
            if rec.opportunity_id and rec.opportunity_id.company_partner_id != rec.company_partner_id:
                raise ValidationError(_('Company partner set in the license must match set in the opportunity.'))

    @api.depends('opportunity_id')
    def _compute_opportunity_data(self):
        for rec in self:
            rec.company_partner_id = rec.opportunity_id.company_partner_id if rec.opportunity_id else False
            rec.contract_number = rec.opportunity_id.dogovor_number
