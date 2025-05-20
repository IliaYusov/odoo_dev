from odoo import models, _


class CrmLead(models.Model):
    _inherit = 'project_budget.projects'

    def action_create_license(self):
        return {
            'name': _('Create License'),
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead.create.license',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
            'context': {
                **self.env.context,
                'lead_ids': self.ids,
                'dialog_size': 'large'
            }
        }
