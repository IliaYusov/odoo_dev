from odoo import fields, models, _

PROCESSING_RESULTS = [
    ('accepted', _('Accepted')),
    ('declined', _('Declined'))
]


class TaskStage(models.Model):
    _inherit = 'task.stage'

    processing_result = fields.Selection(PROCESSING_RESULTS, string='Processing Result', copy=True)
