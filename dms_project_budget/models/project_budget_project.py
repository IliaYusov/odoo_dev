from odoo import api, fields, models, _


class Project(models.Model):
    _name = 'project_budget.projects'
    _inherit = ['project_budget.projects', 'dms.document.mixin']

    @api.model
    def _init_project_document_directory(self):
        self.search([('directory_id', '=', False), ('budget_state', '=', 'work')])._create_project_directory()

    # ------------------------------------------------------
    # DMS.DOCUMENT.MIXIN
    # ------------------------------------------------------

    # TODO: сделать настройку с дефолтным каталогом в модуле?
    def _get_document_directory(self):
        return self.directory_id or self.env.ref('dms_project_budget.dms_directory_project_directory')

    def _get_document_partner(self):
        return self.partner_id

    # ------------------------------------------------------
    # CRUD
    # ------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        # т.к. project_id не сгенерирован перед записью, сначала дергаем метод создания. Мб precompute?
        records = super().create(vals_list)

        [project._create_project_directory() for project in
         records.filtered(lambda pr: not pr.directory_id and pr.budget_state == 'work')]

        return records

    def write(self, vals):
        if not vals.get('directory_id'):
            [project._create_project_directory() for project in
             self.filtered(lambda pr: not pr.directory_id and pr.budget_state == 'work')]

        res = super(Project, self).write(vals)
        if res and vals.get('partner_id'):
            [project._move_documents_to_partner() for project in self]
        return res

    # ------------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------------

    def _create_project_directory(self):
        for project in self:
            # TODO: сделать настройку с дефолтным каталогом в модуле?
            directory = self.env['dms.directory'].create({
                'name': project.project_id,
                'parent_id': self.env.ref('dms_project_budget.dms_directory_project_directory').id
            })
            project.with_context(form_fix_budget=True).write({'directory_id': directory.id})

    def _move_documents_to_partner(self):
        documents = self.env['dms.document'].sudo().search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('partner_id', '!=', self.partner_id.id)
        ])
        if documents:
            documents.write({'partner_id': self.partner_id.id})
