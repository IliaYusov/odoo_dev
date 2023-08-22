from odoo import models, fields, api


class travel(models.Model):
    _name = 'travel.travel'

    doc_number = fields.Char(string="Document number",required=True)
    doc_date = fields.Date(string="Document date",required=True)
    descr = fields.Char(string="Document description")
    status_id    = fields.Many2one('travel.status', string='Status', required=True, ondelete='restrict')
    warehouse_id = fields.Many2one('stock.location', string='Warehouse to' , company_dependent=True, check_company=True, required=True, ondelete='restrict')
    total_sum = fields.Float(string="Total document summa ", store=True, compute='_compute_total', tracking=5)
    total_count = fields.Float(string="Total product count", store=True, compute='_compute_total', tracking=5)
    travel_line_ids = fields.One2many(
        comodel_name='travel.lines',
        inverse_name='travel_id',
        string="Order Lines",
        copy=True, auto_join=True)

    @api.depends('travel_line_ids', 'travel_line_ids.line_quantity','travel_line_ids.line_price')
    def _compute_total(self):
        """подсчитываем итоговую сумму и количество позиций спецификации"""
        for travel in self:
            travel_lines = travel.travel_line_ids
            travel.total_sum = sum(travel_lines.mapped('line_sum'))
            travel.total_count = len(travel_lines)
