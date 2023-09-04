from odoo import _, models, fields, api


class TaskHistory(models.Model):
    _name = 'document_flow.task.history'
    _description = 'Task History'

    process_id = fields.Many2one('document_flow.process', string='Process', ondelete='restrict', index=True,
                                 required=True)
    task_id = fields.Many2one('task.task', string='Task', ondelete='restrict', index=True, required=True)
    executor_id = fields.Many2one('res.users', related="task_id.actual_executor_id", string='Executor', index=True,
                                  required=True)
    date_created = fields.Datetime(string='Date Created', related="task_id.create_date", readonly=True, store=True)
    date_closed = fields.Datetime(string='Date Closed', related="task_id.date_closed", readonly=True, store=True)
    comment = fields.Html(string='Comment', related='task_id.execution_result', readonly=True)
    processing_result = fields.Selection(string='Processing Result', related='task_id.stage_id.result_type',
                                         readonly=True)

