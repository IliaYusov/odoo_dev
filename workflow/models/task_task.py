from odoo import api, fields, models


class Task(models.Model):
    _inherit = 'task.task'

    activity_id = fields.Many2one('workflow.process.activity', string='Activity', copy=False)
    group_executors_id = fields.Many2one('workflow.group.executors', string='Group', copy=False, tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super(Task, self).create(vals_list)
        for record in records:
            if record.group_executors_id and not record.user_ids:
                record._send_message_notify('task.mail_template_task_assigned_notify',
                                            record.group_executors_id.member_ids)
        return records

    def write(self, values):
        res = super(Task, self).write(values)
        for task in self.filtered(lambda t: t.activity_id and t.is_closed and t.date_closed):
            task.activity_id.process_task_result({
                'result': task.stage_id.processing_result,
                'feedback': task.execution_result,
                'timestamp': task.date_closed,
                'attachment_ids': task.execution_result_attachment_ids.ids
            })
        return res
