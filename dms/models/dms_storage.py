import logging

from odoo import api, fields, models, _

SAVE_TYPES = [
    ('attachment', _('Attachment'))
]

_logger = logging.getLogger(__name__)


class DmsStorage(models.Model):
    _name = 'dms.storage'
    _description = 'DMS Storage'

    name = fields.Char(required=True, translate=True)
    save_type = fields.Selection(selection=SAVE_TYPES, default='database', required=True,
                                 help="""The save type is used to determine how a document is saved by the system.
                                 If you change this setting, you can migrate existing documents
                                 manually by triggering the action.""")

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company,
                                 help='If set, directories and documents will only be available for the selected company.')

    is_hidden = fields.Boolean(string='Storage is Hidden', default=False,
                               help='Indicates if directories and documents are hidden by default.')

    root_directory_ids = fields.One2many('dms.directory', 'storage_id', string='Root Directories', copy=False,
                                         domain="[('parent_id', '=', False)]", readonly=False)
    directory_ids = fields.One2many('dms.directory', 'storage_id', string='Directories', copy=False,
                                    readonly=True)
    directory_count = fields.Integer(compute='_compute_directory_count', string='Count Directories')
    document_ids = fields.One2many('dms.document', 'storage_id', string='Documents', copy=False, readonly=True)
    document_count = fields.Integer(compute='_compute_document_count', string='Count Documents')

    @api.depends('directory_ids')
    def _compute_directory_count(self):
        for record in self:
            record.directory_count = len(record.directory_ids)

    @api.depends('document_ids')
    def _compute_document_count(self):
        for record in self:
            record.document_count = len(record.document_ids)
