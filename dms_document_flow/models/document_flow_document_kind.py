from odoo import api, models


class DocumentKind(models.Model):
    _name = 'document_flow.document.kind'
    _inherit = ['document_flow.document.kind', 'dms.document.mixin']

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
        records = super(DocumentKind, self).create(vals_list)

        [kind._create_kind_directory() for kind in records.filtered(lambda k: not k.directory_id)]

        return records

    def write(self, vals):
        if not vals.get('directory_id'):
            [kind._create_kind_directory() for kind in self.filtered(lambda k: not k.directory_id)]

        res = super(DocumentKind, self).write(vals)
        return res

    # ------------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------------

    def _create_kind_directory(self):
        for kind in self:
            # TODO: сделать настройку с дефолтным каталогом в модуле?
            directory = self.env['dms.directory'].create({
                'name': kind.name,
                'parent_id': self.env.ref('dms_document_flow.dms_directory_document_directory').id
            })
            kind.write({'directory_id': directory.id})
