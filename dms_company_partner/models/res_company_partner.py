from odoo import api, fields, models, _


class ResCompanyPartner(models.Model):
    _name = 'res.company.partner'
    _inherit = ['res.company.partner', 'dms.document.mixin']

    directory_id = fields.Many2one('dms.directory', compute='_compute_directory_id')

    # ------------------------------------------------------
    # DMS.DOCUMENT.MIXIN
    # ------------------------------------------------------

    def _get_document_directory(self):
        return self.env.ref('dms_company_partner.dms_directory_company_partner_directory')

    def _get_document_partner(self):
        return self.partner_id

    # ------------------------------------------------------
    # COMPUTE METHODS
    # ------------------------------------------------------

    def _compute_directory_id(self):
        for rec in self:
            rec.directory_id = self.env.ref('dms_company_partner.dms_directory_company_partner_directory')

    # ------------------------------------------------------
    # CRUD
    # ------------------------------------------------------

    def write(self, vals):
        res = super(ResCompanyPartner, self).write(vals)
        if res and vals.get('partner_id'):
            [rec._move_files_to_partner() for rec in self]
        return res

    # ------------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------------

    def _move_files_to_partner(self):
        files = self.env['dms.document'].sudo().search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('partner_id', '!=', self.partner_id.id)
        ])
        if files:
            files.write({'partner_id': self.partner_id.id})
