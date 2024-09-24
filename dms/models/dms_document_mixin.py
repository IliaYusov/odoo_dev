from odoo import api, fields, models, _


class DmsDocumentMixin(models.AbstractModel):
    _name = 'dms.document.mixin'
    _description = 'DMS Document creation mixin'

    directory_id = fields.Many2one('dms.directory', string='Directory', copy=False, ondelete='set null')
    file_ids = fields.One2many('dms.document', 'res_id', string='Files',
                               domain=lambda self: [('res_model', '=', self._name)])
    file_count = fields.Integer(string='Files Count', compute='_compute_file_count', readonly=True)

    # ------------------------------------------------------
    # COMPUTE METHODS
    # ------------------------------------------------------

    @api.depends('file_ids')
    def _compute_file_count(self):
        for document in self:
            document.file_count = len(document.file_ids)

    # ------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------

    def action_open_files(self):
        self.ensure_one()
        action_vals = {
            'name': _('Files'),
            'type': 'ir.actions.act_window',
            'res_model': 'dms.document',
            'view_mode': 'kanban,tree,form',
            'domain': [
                ('res_model', '=', self._name),
                ('res_id', '=', self.id)
            ],
            'context': {
                'default_res_model': self._name,
                'default_res_id': self.id,
                'searchpanel_default_directory_id': self._get_document_directory().id
            },
            'help': """
                <p class="o_view_nocontent_empty_folder">%s</p>
            """ % _("Upload <span class=""fw-normal"">a file or</span> drag <span class=""fw-normal"">it here.</span>")
        }
        return action_vals

    # ------------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------------

    def _get_document_vals(self, attachment):
        self.ensure_one()
        document_vals = {}
        if self._check_create_documents():
            document_vals = {
                'attachment_id': attachment.id,
                'name': attachment.name or self.display_name,
                'directory_id': self._get_document_directory().id,
                'partner_id': self._get_document_partner().id
            }
        return document_vals

    def _get_document_directory(self):
        return self.env['dms.directory']

    def _get_document_partner(self):
        return self.env['res.partner']

    def _check_create_documents(self):
        return bool(self and self._get_document_directory())
