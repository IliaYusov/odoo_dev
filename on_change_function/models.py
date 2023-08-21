# -*- coding: utf-8 -*-

from odoo import models, fields, api


class on_change_function(models.Model):
    # Inhertis the model product.template
    _inherit = 'product.template'
    # Creates two new fields (CostPrice and ShippingCost) in the model product.template
    CostPrice = fields.Float(string='Purchase price',help="""Buy price help example.""")
    ShippingCost = fields.Float(string='Shipping Cost')
    TotalCost = fields.Float(compute='_compute_TotalCost')


    @api.onchange('CostPrice','ShippingCost')
    def on_change_price(self):
        # Calculate the total
        for rec in self:
            rec.standard_price = rec.CostPrice + rec.ShippingCost

        #total = self.CostPrice + self.ShippingCost
        #res = {
        #    'value': {
        #        # This sets the total price on the field standard_price.
        #        'standard_price': total
        #    }
        #}
        # Return the values to update it in the view.
        #return res
