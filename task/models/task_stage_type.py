from odoo import models, fields
from .task_stage import DEFAULT_BG_COLOR


class TaskStageType(models.Model):
    _name = 'task.stage.type'
    _description = 'Stage Type'

    code = fields.Char(required=True)
    name = fields.Char(required=True, translate=True)

    active = fields.Boolean(index=True, default=True)

    bg_color = fields.Char(string="Background Color", default=DEFAULT_BG_COLOR)
