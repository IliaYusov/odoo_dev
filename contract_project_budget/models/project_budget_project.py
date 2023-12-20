from odoo import api, fields, models


class Project(models.Model):
    _inherit = 'project_budget.projects'

    contract_ids = fields.One2many('contract.contract', 'partner_id', string='Contracts')
    contract_count = fields.Integer(compute='_compute_contract_count')

    @api.depends('contract_ids')
    def _compute_contract_count(self):
        domain = [('project_id', 'in', self.ids)]
        res = self.env['contract.contract'].read_group(
            domain=domain, fields=['project_id'], groupby=['project_id']
        )
        contracts = {x['project_id'][0]: x['project_id_count'] for x in res}
        for rec in self:
            rec.contract_count = contracts.get(rec.id, 0)

    def action_open_contract(self):
        self.ensure_one()
        action = self.env.ref('contract.action_contract_form')
        result = action.sudo().read()[0]
        result['domain'] = [('project_id', '=', self.id)]
        result['context'] = {'default_project_id': self.id,
                             'default_partner_id': self.customer_organization_id.partner_id.id}
        return result
