from odoo import fields, models, _

PROJECT_STATES = [
    ('pending', _('Pending')),
    ('won', _('Contracted')),
    ('cancel', _('Canceled'))
]

# TODO: Удалить данный selection
PROJECT_STATUS = [
    ('lead', _('Lead')),
    ('prepare', _('Prepare')),
    ('production', _('Production')),
    ('done', _('Done')),
    ('cancel', _('Canceled'))
]


class ProjectStage(models.Model):
    _name = 'project_budget.project.stage'
    _description = 'Project Stage'
    _order = 'sequence, id'

    active = fields.Boolean('Active', default=True)
    code = fields.Char(string='Code', required=True)
    name = fields.Char(string='Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    fold = fields.Boolean(string='Folded in Kanban', default=False,
                          help='If enabled, this stage will be displayed as folded in the Kanban view of your projects.')
    # TODO: Удалить данное поле
    project_status = fields.Selection(PROJECT_STATUS, string='Project Status', copy=True, default='lead', required=True)
    project_state = fields.Selection(PROJECT_STATES, string='Project State', copy=True, default='pending',
                                     required=True)
    color = fields.Integer(string='Color', default=0)
    required_field_ids = fields.Many2many('ir.model.fields',
                                          relation='project_budget_project_stage_required_fields_rel',
                                          column1='stage_id', column2='field_id', string='Required Fields', copy=False,
                                          domain="[('model', '=', 'project_budget.projects'), ('required', '=', False)]")
    company_ids = fields.Many2many('res.company', relation='project_budget_project_stage_company_rel',
                                   column1='stage_id', column2='company_id', string='Companies',
                                   domain=lambda self: [('id', 'in', self.env.context.get('allowed_company_ids', []))])

    def name_get(self):
        name_array = []
        code_only = self.env.context.get('code_only', False)
        for record in self:
            if code_only:
                name_array.append(tuple([record.id, record.code]))
            else:
                name_array.append(tuple([record.id, record.name]))
        return name_array
