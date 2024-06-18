from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    license_ids = fields.One2many('license.license', 'customer_id', string='Licenses')
    license_count = fields.Integer(compute='_compute_license_count', groups='license_management.group_license_user')

    @api.depends('license_ids')
    def _compute_license_count(self):
        domain = [('customer_id', 'in', self.ids)]
        res = self.env['license.license'].read_group(
            domain=domain, fields=['customer_id'], groupby=['customer_id']
        )
        licenses = {x['customer_id'][0]: x['customer_id_count'] for x in res}
        for rec in self:
            rec.license_count = licenses.get(rec.id, 0)

    def action_open_license(self):
        self.ensure_one()
        action = self.env.ref('license_management.action_license_licenses')
        result = action.sudo().read()[0]
        result['domain'] = [
            ('customer_id', '=', self.id)
        ]
        result['context'] = {
            'default_customer_id': self.id
        }
        return result
