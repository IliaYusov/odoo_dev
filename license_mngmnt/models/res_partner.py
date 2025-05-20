from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    license_count = fields.Integer(compute='_compute_license_count', groups='license_mngmnt.license_group_user')

    # ------------------------------------------------------
    # COMPUTE METHODS
    # ------------------------------------------------------

    def _compute_license_count(self):
        domain = [('customer_id', 'in', self.ids)]
        group_data = self.env['license.license'].read_group(
            domain=domain, fields=['customer_id'], groupby=['customer_id']
        )
        mapped_data = {data['customer_id'][0]: data['customer_id_count'] for data in group_data}
        for rec in self:
            rec.license_count = mapped_data.get(rec.id, 0)

    # ------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------

    def action_open_license(self):
        self.ensure_one()
        action = self.env.ref('license_mngmnt.license_license_action')
        result = action.sudo().read()[0]
        result['domain'] = [
            ('customer_id', '=', self.id)
        ]
        result['context'] = {
            'default_customer_id': self.id
        }
        return result
