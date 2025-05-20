from odoo import fields, models, _


class CrmLeadCreateLicenseWizard(models.TransientModel):
    _name = 'crm.lead.create.license'
    _description = 'Create License From Lead'

    product_id = fields.Many2one('product.product', string='Product', domain="[('sale_ok', '=', True)]",
                                 ondelete='restrict', required=True)
    version = fields.Char(string='Version', required=True)
    number_users = fields.Integer(string='Number Users', default=1, required=True)
    number_users_is_unlimited = fields.Boolean(string='Unlimited', default=False)
    date_start = fields.Date(string='Date Start', default=fields.Date.context_today, required=True)
    date_end = fields.Date(string='Date End', default=fields.Date.context_today)
    is_unlimited = fields.Boolean(string='Unlimited', default=False)

    # ------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------

    def action_create_license(self):
        lead_ids = self._get_leads_for_license_create()

        license_ids = self.env['license.license'].create(
            [self._get_license_values(lead) for lead in lead_ids]
        )

        for lead, lic in zip(lead_ids, license_ids):
            lead.message_post(body=_('License %s was created', lic._get_html_link()))
            lic.message_post_with_view(
                'mail.message_origin_link',
                values={'self': lic, 'origin': lead},
                subtype_id=self.env.ref('mail.mt_note').id
            )

        action_vals = {
            'type': 'ir.actions.act_window',
            'res_model': 'license.license',
        }

        if len(license_ids) == 1:
            action_vals.update({
                'view_mode': 'form',
                'res_id': license_ids[0].id
            })
        else:
            action_vals.update({
                'name': _('Licenses'),
                'view_mode': 'list,form',
                'domain': [('id', 'in', license_ids.ids)]
            })
        return action_vals

    # ------------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------------

    def _get_leads_for_license_create(self):
        lead_ids = self.env.context.get('lead_ids', [])
        return self.env['project_budget.projects'].browse(lead_ids)

    def _get_license_values(self, lead):
        return {
            'customer_id': lead.partner_id.id,
            'product_id': self.product_id.id,
            'version': self.version,
            'number_users': self.number_users,
            'number_users_is_unlimited': self.number_users_is_unlimited,
            'date_start': self.date_start,
            'date_end': self.date_end,
            'is_unlimited': self.is_unlimited,
            'opportunity_id': lead.id,
            'company_partner_id': lead.company_partner_id.id,
            'company_id': lead.company_id.id
        }
