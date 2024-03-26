from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    document_ids = fields.One2many('dms.document', 'partner_id', string='Documents')
    document_count = fields.Integer(compute='_compute_document_count')

    @api.depends('document_ids')
    def _compute_document_count(self):
        domain = [('partner_id', 'in', self.ids)]
        res = self.env['dms.document'].read_group(
            domain=domain, fields=['partner_id'], groupby=['partner_id']
        )
        documents = {x['partner_id'][0]: x['partner_id_count'] for x in res}
        for rec in self:
            rec.document_count = documents.get(rec.id, 0)
