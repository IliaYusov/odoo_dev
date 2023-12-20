from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    purchase_request_id = fields.Many2one('purchase.request', string='Purchase Request', copy=False, tracking=True)
    deal_id = fields.Many2one('project_budget.projects', string='Project', copy=False, tracking=True,
                              domain="[('budget_state', '=', 'work')]")
    conversion_percent = fields.Integer(string='Conversion Percent', default=0, store=True)
