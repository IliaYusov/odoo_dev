from odoo import models, fields, api
from .document_flow_process import selection_executor_model


class TaskHistory(models.Model):
    _name = 'document_flow.task.history'
    _description = 'Task History'

    @api.model
    def _selection_executor_model(self):
        return selection_executor_model()

    process_id = fields.Many2one('document_flow.process', string='Process', ondelete='restrict', index=True,
                                 required=True)
    task_id = fields.Many2one('task.task', string='Task', ondelete='restrict', index=True, required=True)
    executor_ref = fields.Reference(string='Executor', selection='_selection_executor_model',
                                    compute='_compute_executor_ref', index=True, store=True)
    actual_executor_id = fields.Many2one('res.users', related="task_id.actual_executor_id", string='Actual Executor',
                                         index=True, required=True)
    date_created = fields.Datetime(string='Date Created', related="task_id.create_date", readonly=True, store=True)
    date_closed = fields.Datetime(string='Date Closed', related="task_id.date_closed", readonly=True, store=True)
    comment = fields.Html(string='Comment', related='task_id.execution_result', readonly=True)
    processing_result = fields.Selection(string='Processing Result', related='task_id.stage_id.result_type',
                                         readonly=True)

    @api.depends('task_id')
    def _compute_executor_ref(self):
        for rec in self:
            rec.executor_ref = rec.task_id.role_executor_id if rec.task_id.role_executor_id else rec.task_id.user_id
