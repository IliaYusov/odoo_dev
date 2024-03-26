from odoo import api, fields, models, _

ACTIVITY_HISTORY_STATES = [
    ('in_progress', _('In Progress')),
    ('done', _('Done')),
    ('declined', _('Declined')),
    ('canceled', _('Canceled'))
]

MAPPING_ACTIVITY_HISTORY_STATES = {
    'in_progress': 'in_progress',
    'completed': 'done',
    'canceled': 'canceled'
}


class WorkflowProcessActivity(models.Model):
    _name = 'workflow.process.activity.history'
    _description = 'Workflow Process Activity History'
    _order = 'date_start'

    name = fields.Char(string='Name', compute='_compute_name', readonly=True)
    activity_id = fields.Many2one('workflow.process.activity', string='Activity', ondelete='restrict', readonly=True,
                                  required=True)
    activity_name = fields.Char(related='activity_id.activity_name', readonly=True)
    workflow_id = fields.Many2one(related='activity_id.workflow_id', string='Workflow', readonly=True)
    workflow_process_id = fields.Many2one(related='activity_id.workflow_process_id', string='Workflow Process',
                                          index=True, ondelete='cascade', readonly=True, required=True)
    res_model = fields.Char(related='workflow_process_id.res_model', string='Resource Model', index=True, readonly=True,
                            store=True)
    res_id = fields.Integer(related='workflow_process_id.res_id', string='Resource ID', index=True, readonly=True,
                            store=True)
    date_start = fields.Datetime(related='activity_id.date_start', string='Date Start', readonly=True)
    date_end = fields.Datetime(related='activity_id.date_end', string='Date End', readonly=True)
    duration = fields.Float(related='activity_id.duration', string='Duration', readonly=True)

    task_id = fields.Many2one('task.task', string='Task')
    executors = fields.Char(string='Executors', compute='_compute_executors', store=True)
    actual_executor_id = fields.Many2one('res.users', compute='_compute_executor_id', string='Actual Executor',
                                         index=True, readonly=False, store=True)
    state = fields.Selection(ACTIVITY_HISTORY_STATES, compute='_compute_state')
    comment = fields.Html(related='task_id.execution_result', string='Comment', readonly=True, related_sudo=True)
    attachment_ids = fields.Many2many(related='task_id.execution_result_attachment_ids', readonly=True,
                                      related_sudo=True)

    # ------------------------------------------------------
    # COMPUTE METHODS
    # ------------------------------------------------------

    @api.depends('activity_id', 'task_id')
    def _compute_name(self):
        for rec in self.sudo():
            rec.name = rec.task_id.name if rec.task_id else rec.activity_id.name

    @api.depends('task_id')
    def _compute_executors(self):
        for rec in self.sudo():
            rec.executors = rec.task_id.group_executors_id.name if rec.task_id.group_executors_id else ', '.join(
                rec.task_id.user_ids.mapped('name'))

    @api.depends('task_id', 'task_id.is_closed')
    def _compute_executor_id(self):
        for rec in self.sudo():
            rec.actual_executor_id = rec.task_id.actual_executor_id

    @api.depends('activity_id', 'task_id', 'task_id.active', 'task_id.is_closed')
    def _compute_state(self):
        for rec in self.sudo():
            if not rec.task_id:
                rec.state = MAPPING_ACTIVITY_HISTORY_STATES.get(rec.activity_id.state)
            else:
                if not rec.task_id.active:
                    rec.state = 'canceled'
                elif not rec.task_id.is_closed:
                    rec.state = 'in_progress'
                elif rec.task_id.stage_id.processing_result == 'declined':
                    rec.state = 'declined'
                else:
                    rec.state = 'done'
