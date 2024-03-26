from odoo import fields, models


class DmsDocumentRelatedRecord(models.Model):
    _name = 'dms.document.related.record'
    _description = 'DMS Document Related Record'

    document_id = fields.Many2one('dms.document', string='Document', ondelete='cascade', required=True)
    directory_id = fields.Many2one('dms.directory', string='Directory', ondelete='cascade', required=True)
    res_model = fields.Char(string='Resource Model', required=True)
    res_id = fields.Integer(string='Resource ID', required=True)
