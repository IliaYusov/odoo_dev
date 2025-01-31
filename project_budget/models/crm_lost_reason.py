from odoo import fields, models, _


class CrmLostReason(models.Model):
    _name = 'crm.lost.reason'
    _description = 'Lead Lost Reason'

    name = fields.Char(string='Name', required=True, translate=True)
    active = fields.Boolean(string='Active', default=True)
    lead_count = fields.Integer(string='Lead Count', compute='_compute_lead_count')

    def _compute_lead_count(self):
        lead_data = self.env['project_budget.projects'].with_context(active_test=False)._read_group(
            domain=[('lost_reason_id', 'in', self.ids)],
            fields=['lost_reason_id'],
            groupby=['lost_reason_id']
        )
        mapped_data = dict((data['lost_reason_id'][0], data['lost_reason_id_count']) for data in lead_data)
        for rec in self:
            rec.lead_count = mapped_data.get(rec.id, 0)

    def action_open_lost_opportunities(self):
        return {
            'name': _('Leads'),
            'view_mode': 'tree,form',
            'domain': [
                ('lost_reason_id', 'in', self.ids)
            ],
            'res_model': 'project_budget.projects',
            'type': 'ir.actions.act_window',
            'context': {
                'create': False,
                'active_test': False
            }
        }
