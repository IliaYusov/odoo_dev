from odoo import api, fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    contract_ids = fields.One2many('contract.contract', 'partner_id', string='Contracts')
    contract_count = fields.Integer(compute='_compute_contract_count')

    @api.depends('contract_ids')
    def _compute_contract_count(self):
        domain = [('partner_id', 'in', self.ids)]
        res = self.env['contract.contract'].read_group(
            domain=domain, fields=['partner_id'], groupby=['partner_id']
        )
        contracts = {x['partner_id'][0]: x['partner_id_count'] for x in res}
        for rec in self:
            rec.contract_count = contracts.get(rec.id, 0)

    def action_open_contract(self):
        self.ensure_one()
        action = self.env.ref('contract.action_contract_form')
        result = action.sudo().read()[0]
        result['domain'] = [('partner_id', '=', self.id)]
        result['context'] = {'default_partner_id': self.id}
        return result
