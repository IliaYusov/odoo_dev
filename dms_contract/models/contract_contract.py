from odoo import api, fields, models, _


class Contract(models.Model):
    _name = 'contract.contract'
    _inherit = ['contract.contract', 'dms.document.mixin']

    @api.model
    def _init_contract_document_directory(self):
        self.search([('directory_id', '=', False)])._create_contract_directory()

    # ------------------------------------------------------
    # DMS.DOCUMENT.MIXIN
    # ------------------------------------------------------

    # TODO: сделать настройку с дефолтным каталогом в модуле?
    def _get_document_directory(self):
        return self.directory_id or self.env.ref('dms_contract.dms_directory_contract_directory')

    def _get_document_partner(self):
        return self.partner_id

    # ------------------------------------------------------
    # CRUD
    # ------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        [contract._create_contract_directory() for contract in records.filtered(lambda c: not c.directory_id)]

        return records

    def write(self, vals):
        if not vals.get('directory_id'):
            [contract._create_contract_directory() for contract in self.filtered(lambda c: not c.directory_id)]

        res = super(Contract, self).write(vals)
        if res and vals.get('partner_id'):
            [contract._move_files_to_partner() for contract in self]
        return res

    # ------------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------------

    def _create_contract_directory(self):
        for contract in self:
            # TODO: сделать настройку с дефолтным каталогом в модуле?
            directory = self.env['dms.directory'].create({
                'name': contract.code,
                'parent_id': self.env.ref('dms_contract.dms_directory_contract_directory').id
            })
            contract.write({'directory_id': directory.id})

    def _move_files_to_partner(self):
        files = self.env['dms.document'].sudo().search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('partner_id', '!=', self.partner_id.id)
        ])
        if files:
            files.write({'partner_id': self.partner_id.id})
