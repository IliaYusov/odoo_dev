from odoo import api, fields, models, _


class Document(models.Model):
    _name = 'document_flow.document'
    _inherit = ['document_flow.document', 'dms.document.mixin']

    # ------------------------------------------------------
    # DMS.DOCUMENT.MIXIN
    # ------------------------------------------------------

    # TODO: сделать настройку с дефолтным каталогом в модуле?
    def _get_document_directory(self):
        return self.directory_id or self.env.ref('dms_document_flow.dms_directory_document_directory')

    # ------------------------------------------------------
    # CRUD
    # ------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        records = super(Document, self).create(vals_list)

        [document._create_document_directory() for document in records.filtered(lambda d: not d.directory_id)]

        return records

    def write(self, vals):
        if not vals.get('directory_id'):
            [document._create_document_directory() for document in self.filtered(lambda d: not d.directory_id)]

        res = super(Document, self).write(vals)
        return res

    # ------------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------------

    def _create_document_directory(self):
        for document in self:
            # TODO: сделать настройку с дефолтным каталогом в модуле?
            directory = self.env['dms.directory'].create({
                'name': document.code,
                'parent_id': self.env.ref('dms_document_flow.dms_directory_document_directory').id
            })
            document.write({'directory_id': directory.id})
