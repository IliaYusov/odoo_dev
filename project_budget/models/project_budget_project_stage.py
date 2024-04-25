from odoo import fields, models, _

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
    fold = fields.Boolean(string='Folded in Kanban',
                          help='If enabled, this stage will be displayed as folded in the Kanban view of your projects.')
    project_status = fields.Selection(PROJECT_STATUS, string='Project Status', copy=True, default='lead', required=True)
    color = fields.Integer(string='Color', default=0)
    required_field_ids = fields.Many2many('ir.model.fields',
                                          relation='project_budget_project_stage_required_fields_rel',
                                          column1='stage_id', column2='field_id', string='Required Fields', copy=False,
                                          domain="[('model', '=', 'project_budget.projects'), ('required', '=', False)]")

    def name_get(self):
        name_array = []
        code_only = self.env.context.get('code_only', False)
        for record in self:
            if code_only:
                name_array.append(tuple([record.id, record.code]))
            else:
                name_array.append(tuple([record.id, record.name]))
        return name_array
