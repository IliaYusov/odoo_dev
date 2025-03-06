from odoo import api, fields, models, _


class Project(models.Model):
    _inherit = 'project_budget.projects'

    quotation_count = fields.Integer(compute='_compute_sale_data', string='Quotation Count',
                                     groups='sale_mngmnt.sale_group_user')
    order_ids = fields.One2many('sale.order', 'opportunity_id', string='Orders', copy=False,
                                groups='sale_mngmnt.sale_group_user')

    @api.depends('order_ids')
    def _compute_sale_data(self):
        for rec in self:
            rec.quotation_count = len(rec.order_ids)

    def action_open_quotations(self):
        self.ensure_one()
        action_vals = {
            'name': _('Quotations'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [
                ('opportunity_id', '=', self.id)
            ],
            'context': {
                'default_opportunity_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_salesperson_id': self.key_account_manager_id.id
            },
            'help': """
                <p class="o_view_nocontent_smiling_face">%s</p>
                <p>%s</p>
            """ % (_('Create a new quotation, the first step of a new sale!'),
                   _('Once the quotation is confirmed, it becomes a sales order.'))
        }
        return action_vals
