from odoo import api, fields, models


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    active = fields.Boolean(copy=False, default=True, index=True)
    version = fields.Integer('Version', readonly=True)

    current_version_id = fields.Many2one('ir.attachment', string='Current Version', ondelete='cascade')
    version_ids = fields.One2many('ir.attachment', compute='_compute_version_ids', inverse_name='current_version_id',
                                  string='Previous Versions', context={'active_test': False})

    @api.depends('version')
    def _compute_version_ids(self):
        for attachment in self:
            attachment.version_ids = self.env['ir.attachment'].with_context(active_test=False).search([
                ('current_version_id', '=', attachment.id)
            ])

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for vals in vals_list:
            if not self._context.get('without_document'):
                for record in records.filtered(lambda r: not r.res_field):
                    record.sudo()._create_document(dict(vals, res_model=record.res_model, res_id=record.res_id))
        return records

    def write(self, vals):
        if not self.env.context.get('without_document'):
            self.filtered(lambda a: not (vals.get('res_field') or a.res_field)).sudo()._create_document(vals)
        res = super().write(vals)
        return res

    def _create_document(self, vals):
        if vals.get('res_model') == 'dms.document' and vals.get('res_id'):
            document = self.env['dms.document'].browse(vals['res_id'])
            if document.exists() and not document.attachment_id:
                document.attachment_id = self[0].id
            return False

        res_model = vals.get('res_model')
        res_id = vals.get('res_id')
        model = self.env.get(res_model)
        if model is not None and res_id and issubclass(type(model), self.pool['dms.document.mixin']):
            vals_list = [
                model.browse(res_id)._get_document_vals(attachment)
                for attachment in self
                if not attachment.res_field
            ]
            vals_list = [vals for vals in vals_list if vals]
            self.env['dms.document'].create(vals_list)
            return True
        return False
