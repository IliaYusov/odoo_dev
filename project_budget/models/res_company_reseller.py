from odoo import api, fields, models, _


class ResCompanySeller(models.Model):
    _name = 'res.company.reseller'
    _description = 'Company Reseller'

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    partner_id = fields.Many2one('res.partner', string='Partner',
                                 domain="['&', ('is_company', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                 ondelete='restrict', required=True)
    partner_grade_id = fields.Many2one('res.partner.grade', string='Partner Level', ondelete='restrict')
    active = fields.Boolean(string='Active', default=True)

    project_ids = fields.Many2one('project_budget.projects', string='Projects', compute='_compute_project_ids')
    project_count = fields.Integer(compute='_compute_project_count')

    def name_get(self):
        res = []
        for record in self:
            name = '%s [%s]' % (record.partner_id.name, record.partner_grade_id.name)
            res += [(record.id, name)]
        return res

    # ------------------------------------------------------
    # COMPUTE METHODS
    # ------------------------------------------------------

    def _compute_project_ids(self):
        for record in self:
            record.project_ids = self.env['project_budget.projects'].search([
                ('parent_id', '!=', False),
                ('legal_entity_signing_id.partner_id', '=', 'record.company_id.partner_id.id')
                # TODO: Код для нового поля, после миграции раскоментировать и удалить строчку выше
                # ('partner_signer_id', '=', record.company_id.partner_id.id)
            ])

    @api.depends('project_ids')
    def _compute_project_count(self):
        for record in self:
            record.project_count = len(record.project_ids)

    # ------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------

    def action_open_project(self):
        self.ensure_one()
        return {
            'name': _('Projects'),
            'domain': [
                ('id', 'in', self.project_ids.ids)
            ],
            'res_model': 'project_budget.projects',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'context': {
                'create': False,
                'edit': False,
                'delete': False
            },
            'help': """
                <p class="o_view_nocontent_smiling_face">%s</p>
                """ % _("No partner projects found.")
        }
