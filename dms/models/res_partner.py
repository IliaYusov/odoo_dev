from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    file_ids = fields.One2many('dms.document', 'partner_id', string='Files')
    file_count = fields.Integer(compute='_compute_file_count')

    @api.depends('file_ids')
    def _compute_file_count(self):
        domain = [('partner_id', 'in', self.ids)]
        res = self.env['dms.document'].read_group(
            domain=domain, fields=['partner_id'], groupby=['partner_id']
        )
        files = {x['partner_id'][0]: x['partner_id_count'] for x in res}
        for rec in self:
            rec.file_count = files.get(rec.id, 0)
