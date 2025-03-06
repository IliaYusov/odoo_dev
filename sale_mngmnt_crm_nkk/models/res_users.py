from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    product_category_ids = fields.One2many('product.category', string='Categories',
                                           compute='_compute_product_category_ids')
    product_category_head_ids = fields.One2many('product.category', 'head_id', string='Product Category Head')

    @api.depends('product_category_head_ids.head_id')
    def _compute_product_category_ids(self):
        for rec in self:
            rec.product_category_ids = self.env['product.category'].search([
                ('id', 'child_of', rec.product_category_head_ids.ids)
            ])
