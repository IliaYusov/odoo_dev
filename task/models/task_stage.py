from odoo import models, fields, api, _

DEFAULT_BG_COLOR = 'rgba(120,120,120,1)'

RESULT_TYPES = [
    ('ok', _('Ok')),
    ('error', _('Error'))
]


class TaskStage(models.Model):
    _name = "task.stage"
    _description = "Task Stage"
    _order = "sequence"

    name = fields.Char(required=True, string='Name', translate=True)
    code = fields.Char(required=True, string='Code')

    type_id = fields.Many2one('task.stage.type', string="Stage Type", required=True, index=True, ondelete="restrict")
    task_type_id = fields.Many2one('task.type', string='Task Type', ondelete='cascade', required=True, index=True)
    mail_template_id = fields.Many2one('mail.template', string='Email Template', domain=[('model', '=', 'task.task')],
                                       help='If set, an email will be automatically sent to the customer when the task reaches this stage.')

    active = fields.Boolean(default=True, index=True)
    sequence = fields.Integer(default=5, index=True)

    description = fields.Text()
    bg_color = fields.Char(default=DEFAULT_BG_COLOR, string="Background Color")

    use_custom_colors = fields.Boolean()
    res_bg_color = fields.Char(string="Background Color", compute='_compute_custom_colors', readonly=True)

    route_in_ids = fields.One2many('task.stage.route', 'stage_to_id', string='Incoming Routes')
    route_out_ids = fields.One2many('task.stage.route', 'stage_from_id', string='Outgoing Routes')

    previous_stage_ids = fields.Many2many('task.stage', 'task_stage_prev_stage_ids_rel', string='Previous stages',
                                          column1='stage_id', column2='prev_stage_id',
                                          compute='_compute_previous_stage_ids', store=True)

    closed = fields.Boolean(index=True)
    result_type = fields.Selection(RESULT_TYPES, string='Result Type', default='ok')
    diagram_position = fields.Char(readonly=True)

    _sql_constraints = [
        ('stage_name_uniq',
         'UNIQUE (task_type_id, name)',
         'Stage name must be uniq for task type'),
        ('stage_code_uniq',
         'UNIQUE (task_type_id, code)',
         'Stage code must be uniq for task type')
    ]

    @api.depends('task_type_id', 'task_type_id.stage_ids',
                 'task_type_id.route_ids',
                 'task_type_id.route_ids.stage_from_id',
                 'task_type_id.route_ids.stage_to_id')
    def _compute_previous_stage_ids(self):
        for stage in self:
            route_ids = stage.task_type_id.route_ids.filtered(lambda r: r.stage_to_id == stage)

            stage_ids = route_ids.mapped('stage_from_id')
            stage.previous_stage_ids = stage_ids
            stage.invalidate_recordset()

    @api.depends('bg_color', 'type_id', 'use_custom_colors')
    def _compute_custom_colors(self):
        for rec in self:
            if rec.use_custom_colors:
                rec.res_bg_color = rec.bg_color
            elif rec.type_id:
                rec.res_bg_color = rec.type_id.bg_color
            else:
                rec.res_bg_color = DEFAULT_BG_COLOR
