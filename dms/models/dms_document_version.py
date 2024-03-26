from odoo import fields, models


class DmsDocumentVersion(models.Model):
    _name = 'dms.document.version'
    _description = 'DMS Document Version'
    _order = 'version desc'

    document_id = fields.Many2one('dms.document', string='Document', ondelete='cascade', required=True)
    version = fields.Integer('Version', readonly=True, required=True)
    attachment_id = fields.Many2one('ir.attachment', string='Attachment File', invisible=True, ondelete='cascade')
    author_id = fields.Many2one(related='attachment_id.create_uid', readonly=True)
    creation_date = fields.Datetime(related='attachment_id.create_date', readonly=True)
    name = fields.Char(related='attachment_id.name', readonly=True)
    description = fields.Text(related='attachment_id.description', readonly=True)
    file_size = fields.Integer(related='attachment_id.file_size', readonly=True)
    company_id = fields.Many2one(related='attachment_id.company_id', readonly=True)
