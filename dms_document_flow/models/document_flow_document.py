from odoo import fields, models


class Document(models.Model):
    _name = 'document_flow.document'
    _inherit = ['document_flow.document', 'dms.document.mixin']

    directory_id = fields.Many2one(related='kind_id.directory_id', readonly=True)
