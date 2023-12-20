from odoo import api, fields, models


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    active = fields.Boolean(copy=False, default=True, index=True)
    version = fields.Integer('Version', readonly=True)

    current_version_id = fields.Many2one('ir.attachment', string='Current Version', ondelete='cascade')
    version_ids = fields.One2many('ir.attachment', compute='_compute_version_ids', inverse_name='current_version_id',
                                  string='Previous Versions', context={'active_test': False})
    version_count = fields.Integer(string='Version Count', compute='_compute_version_count')

    def _read_group_allowed_fields(self):
        allowed_fields = super()._read_group_allowed_fields()
        allowed_fields.append('version')
        return allowed_fields

    @api.depends('version')
    def _compute_version_ids(self):
        for attachment in self:
            attachment.version_ids = self.env['ir.attachment'].with_context(active_test=False).search([
                ('current_version_id', '=', attachment.id)
            ])

    @api.depends('version_ids')
    def _compute_version_count(self):
        for attachment in self:
            attachment.version_count = len(attachment.version_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model = vals.get('res_model') or self.env.context.get('active_model')
            if self.env['dms.version.config'].search([('model_id', '=', model)]) and not vals.get('version', False):
                vals['version'] = 1

        records = super().create(vals_list)
        return records

    def write(self, vals):
        model = vals.get('res_model') or self.env.context.get('active_model')
        if self.env['dms.version.config'].search([('model_id', '=', model)]):
            copy = self.copy({'active': False, 'current_version_id': self.id})
            self.env.cr.execute(
                "UPDATE ir_attachment SET create_date='%s' WHERE id=%s" %
                (copy.create_date, self.id)
            )
            self.env.cr.execute(
                "UPDATE ir_attachment SET create_date='%s', create_uid=%s WHERE id=%s" %
                (self.create_date, self.create_uid.id, copy.id)
            )
            vals['version'] = self.version + 1
        res = super().write(vals)
        return res
