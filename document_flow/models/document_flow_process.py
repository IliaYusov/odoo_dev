from odoo import _, models, fields, api, Command
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import test_python_expr, safe_eval
from datetime import datetime, date, timedelta

PROCESS_TYPES = [
    ('review', _('Review')),
    ('agreement', _('Agreement')),
    ('execution', _('Execution')),
    ('complex', _('Complex'))
]

MAPPING_PROCESS_TASK_TYPES = {
    'review': 'sys_df_review',
    'agreement': 'sys_df_agreement',
    'execution': 'sys_df_execution'
}

PROCESS_STATES = [
    ('on_registration', _('On Registration')),
    ('started', _('Started')),
    ('break', _('Break')),
    ('finished', _('Finished')),
    ('skipped', _('Skipped'))
]

TASK_FORM_SEQUENCE = [
    ('all_at_once', _('All At Once')),
    ('sequentially', _('Sequentially')),
    ('mixed', _('Mixed'))
]

TYPE_SEQUENCE = [
    ('together_with_the_previous', _('Together with the previous')),
    ('after_the_previous', _('After the previous'))
]


# TODO: необходима возможность выбора роли, возможно каких-то предопределенных методов
def selection_executor_model():
    return [
        ('res.users', _('User')),
        ('document_flow.role_executor', _('Role'))
    ]


# TODO: подумать над необходимостью решений (точно deprecated), документов в этом списке
def selection_parent_model():
    return [
        ('document_flow.event', _('Event')),
        ('document_flow.event.decision', _('Decision')),
        ('document_flow.action', _('Action')),
        ('document_flow.document', _('Document'))
    ]


def recompute_sequence_executors(model, task_sequence, executors):
    i = 0
    sequence = 0
    for command, line_id, line_vals in executors:
        if command not in (Command.UNLINK, Command.DELETE):
            if line_vals:
                if task_sequence == 'all_at_once':
                    sequence = sequence
                elif task_sequence == 'sequentially':
                    sequence += 1
                elif task_sequence == 'mixed':
                    if line_vals.get('type_sequence', False):
                        sequence = sequence if line_vals.get(
                            'type_sequence') == 'together_with_the_previous' else sequence + 1
                    elif line_id:
                        sequence = sequence if model.browse(
                            line_id).type_sequence == 'together_with_the_previous' else sequence + 1
            elif line_id:
                executors[i][0] = 1
                if task_sequence == 'all_at_once':
                    sequence = sequence
                elif task_sequence == 'sequentially':
                    sequence += 1
                elif task_sequence == 'mixed':
                    sequence = sequence if model.browse(
                        line_id).type_sequence == 'together_with_the_previous' else sequence + 1

            if not line_vals:
                line_vals = dict()
            line_vals['sequence'] = sequence

            executors[i][2] = line_vals
            i += 1


def recompute_sequence_actions(model, actions):
    i = 0
    sequence = 0
    for command, line_id, line_vals in actions:
        if command not in (Command.UNLINK, Command.DELETE):
            if not i == 0:
                if line_vals:
                    if line_vals.get('type_sequence', False):
                        sequence = sequence if line_vals.get(
                            'type_sequence') == 'together_with_the_previous' else sequence + 1
                    elif line_id:
                        sequence = sequence if model.browse(
                            line_id).type_sequence == 'together_with_the_previous' else sequence + 1
                elif line_id:
                    actions[i][0] = 1
                    sequence = sequence if model.browse(
                        line_id).type_sequence == 'together_with_the_previous' else sequence + 1

            if not line_vals:
                line_vals = dict()
            line_vals['sequence'] = sequence

            actions[i][2] = line_vals
            i += 1


class Process(models.Model):
    _name = 'document_flow.process'
    _description = 'Process'

    @api.model
    def _selection_executor_model(self):
        return selection_executor_model()

    @api.model
    def _selection_parent_model(self):
        return selection_parent_model()

    # @api.model_create_multi
    # def create(self, vals_list):
    #     result = super(Process, self).create(vals_list)
    #     self.env['document_flow.process.parent_object'].create({
    #         'process_id': result.id,
    #         'parent_ref': '%s,%s' % (self.env.context.get('active_model'), self.env.context.get('active_id')),
    #         'parent_ref_id': self.env.context.get('active_id'),
    #         'parent_ref_type': self.env.context.get('active_model')
    #     })
    #     return result

    code = fields.Char(string='Code', required=True, readonly=True, default=lambda self: _('New'))
    name = fields.Char(string='Name', required=True, copy=True)
    description = fields.Html(string='Description', copy=True)
    type = fields.Selection(PROCESS_TYPES, required=True, default='review', index=True, string='Type')
    state = fields.Selection(PROCESS_STATES, required=True, default='on_registration', string='State')
    company_ids = fields.Many2many('res.company', string='Companies', required=True,
                                   default=lambda self: self.env.company)
    template_id = fields.Many2one('document_flow.process.template', string='Template')
    parent_id = fields.Many2one('document_flow.process', string='Parent Process', ondelete='cascade', index=True)
    executor_ids = fields.One2many('document_flow.process.executor', 'process_id', string='Executors')

    date_start = fields.Datetime(string='Date Start')
    date_end = fields.Datetime(string='Date End')
    date_deadline = fields.Datetime(string='Date Deadline')

    reviewer_ref = fields.Reference(string='Reviewer', selection='_selection_executor_model', store=True)
    reviewer_ref_id = fields.Integer(string='Reviewer Id', index=True)
    reviewer_ref_type = fields.Char(string='Reviewer Type', index=True)

    controller_ref = fields.Reference(string='Controller', selection='_selection_executor_model', store=True)
    controller_ref_id = fields.Integer(string="Controller Id", index=True)
    controller_ref_type = fields.Char(string="Controller Type", index=True)

    child_ids = fields.One2many('document_flow.process', 'parent_id', string='Processes')
    task_ids = fields.One2many('task.task', string='Tasks', compute='_compute_task_ids', context={'active_test': False})
    active_task_ids = fields.One2many('task.task', string='Tasks', compute='_compute_active_task_ids')

    task_sequence = fields.Selection(TASK_FORM_SEQUENCE, required=True, default='all_at_once',
                                     string='Task Form Sequence')
    sequence = fields.Integer(string='Sequence', default=0)
    visible_sequence = fields.Integer(string='Sequence', compute='_compute_sequence')
    start_condition = fields.Text(string='Compute Condition',
                                  help='Conditions that will be checked before process will be started.')

    parent_obj_ref = fields.Reference(string='Parent Object', selection='_selection_parent_model',
                                      compute='_compute_parent_obj', readonly=True)
    task_history_ids = fields.One2many('document_flow.task.history', string='Task History',
                                       compute='_compute_task_history_ids')

    @api.constrains('start_condition')
    def _check_start_condition(self):
        for process in self.filtered('start_condition'):
            msg = test_python_expr(expr=process.start_condition.strip(), mode='exec')
            if msg:
                raise ValidationError(msg)

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_('Error! You cannot create a recursive hierarchy of process.'))

    @api.model
    def create(self, vals_list):
        if vals_list.get('code', _('New')) == _('New'):
            vals_list['code'] = self.env['ir.sequence'].next_by_code('document_flow.process') or _('New')
        res = super(Process, self).create(vals_list)
        return res

    def write(self, vals):
        res = super(Process, self).write(vals)
        return res

    def unlink(self):
        self.task_ids.unlink()
        return super(Process, self).unlink()

    def _compute_parent_obj(self):
        for process in self:
            process.parent_obj_ref = self.env['document_flow.process.parent_object'].search([
                ('process_id', '=', process.id)
            ], limit=1).parent_ref

    @api.onchange('sequence')
    def _compute_sequence(self):
        for process in self:
            process.visible_sequence = process.sequence

    @api.depends('reviewer_ref_type', 'reviewer_ref_id')
    def _compute_reviewer_ref(self):
        for process in self:
            if process.reviewer_ref_type and process.reviewer_ref_type in self.env:
                process.reviewer_ref = '%s,%d' % (process.reviewer_ref_type, process.reviewer_ref_id or 0)
            else:
                process.reviewer_ref = False

    @api.depends('controller_ref_type', 'controller_ref_id')
    def _compute_controller_ref(self):
        for process in self:
            if process.controller_ref_type and process.controller_ref_type in self.env:
                process.controller_ref = '%s,%d' % (process.controller_ref_type, process.controller_ref_id or 0)
            else:
                process.controller_ref = False

    def _compute_task_ids(self):
        for process in self:
            process.task_ids = self.env['task.task'].with_context(active_test=False).search([
                ('parent_ref_type', '=', process._name),
                ('parent_ref_id', 'in', process._get_subprocess_ids_by_process_id().get(process.id, []) if process.type == 'complex' else [process.id])
            ]).ids or False

    def _compute_active_task_ids(self):
        for process in self:
            process.active_task_ids = process.task_ids.filtered(lambda task: task.active)

    def _compute_task_history_ids(self):
        for process in self:
            process.task_history_ids = self.env['document_flow.task.history'].search([
                ('process_id', 'in', process._get_subprocess_ids_by_process_id().get(process.id, []) if process.type == 'complex' else [process.id])
            ]).ids or False

    def _put_task_to_history(self, task):
        return self.env['document_flow.task.history'].create({
            'process_id': self.id,
            'task_id': task.id
        })

    def _get_mainprocess_id_by_process_id(self):
        if not self:
            return {}

        res = dict.fromkeys(self._ids, [])
        if all(self._ids):
            self.env.cr.execute(
                """
                WITH RECURSIVE parents AS
                (
                    SELECT id, NULL :: INTEGER AS parent_id, id AS main_parent_id
                    FROM document_flow_process
                    WHERE parent_id is null 
                    UNION
                    SELECT child.id, child.parent_id, coalesce(p.main_parent_id, child.parent_id) AS main_parent_id
                    FROM document_flow_process child
                    INNER JOIN parents p ON p.id = child.parent_id
                )
                SELECT id, main_parent_id
                FROM parents
                WHERE id IN %(process_ids)s
                """,
                {
                    "process_ids": tuple(self.ids)
                }
            )
            res.update(dict(self.env.cr.fetchall()))
        else:
            res.update({
                process.id: process._get_mainprocess_recursively().ids
                for process in self
            })
        return res

    def _get_mainprocess_recursively(self):
        parent = self.parent_id
        if not parent:
            return self.env['document_flow.process']
        return parent._get_subprocesses_recursively()

    def _get_subprocess_ids_by_process_id(self):
        if not self:
            return {}

        res = dict.fromkeys(self._ids, [])
        if all(self._ids):
            self.env.cr.execute(
                """
                WITH RECURSIVE process_tree
                AS
                (
                    SELECT id, id as complex_process_id
                    FROM document_flow_process
                    WHERE id IN %(process_ids)s
                    UNION
                    SELECT pr.id, tree.complex_process_id
                    FROM document_flow_process pr
                    JOIN process_tree tree ON tree.id = pr.parent_id
                )
                SELECT complex_process_id, ARRAY_AGG(id)
                FROM process_tree
                WHERE id != complex_process_id
                GROUP BY complex_process_id
                """,
                {
                    "process_ids": tuple(self.ids)
                }
            )
            res.update(dict(self.env.cr.fetchall()))
        else:
            res.update({
                process.id: process._get_subprocess_recursively().ids
                for process in self
            })
        return res

    def _get_subprocess_recursively(self):
        children = self.child_ids
        if not children:
            return self.env['document_flow.process']
        return children + children._get_subprocesses_recursively()

    def action_start_process(self):
        self._start()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'sticky': False,
                'message': _("Tasks were created for the following user(s)"),
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }

    def _start(self):
        self.ensure_one()
        res = False
        if self.state == 'on_registration':
            if self.type == 'complex':
                res = self.start_complex_process()
            else:
                if self._check_start_condition():
                    if self.type == 'review':
                        self.start_review_process()
                    elif self.type == 'agreement':
                        self.start_agreement_process()
                    elif self.type == 'execution':
                        self.start_execution_process()
                    res = True
            if res:
                self.write({'state': 'started', 'date_start': fields.Datetime.now()})
            else:
                self.write({'state': 'skipped'})
            return res

    def start_review_process(self):
        if self.executor_ids:
            for executor in self.executor_ids:
                executor.fill_date_deadline()
                executor.create_task_for_executor()

    # TODO: разобраться с reviewer, нужен ли и какой процесс
    def start_agreement_process(self):
        if self.executor_ids:
            min_sequence = min(self.executor_ids, key=lambda pr: pr.sequence).sequence or 0
            for executor in self.executor_ids.filtered(lambda ex: ex.sequence == min_sequence):
                executor.fill_date_deadline()
                executor.create_task_for_executor()

    def start_execution_process(self):
        if self.executor_ids:
            min_sequence = min(self.executor_ids, key=lambda pr: pr.sequence).sequence or 0
            for executor in self.executor_ids.filtered(lambda ex: ex.sequence == min_sequence):
                executor.fill_date_deadline()
                executor.create_task_for_executor()

    def start_complex_process(self):
        next_sequence = min(self.child_ids, key=lambda pr: pr.sequence).sequence or 0
        while next_sequence != -1:
            processes = self.child_ids.filtered(lambda pr: pr.sequence == next_sequence).sorted(lambda pr: pr.id)
            started = False
            for process in processes:
                res = process._start()
                if res:
                    started = True
                    next_sequence = -1
            if not started:
                next_sequence = self.child_ids.filtered(lambda pr: pr.sequence > next_sequence).sorted(
                    lambda pr: pr.sequence)[0].sequence or -1
        return next_sequence == -1

    def _check_start_condition(self):
        if not self.start_condition:
            return True
        else:
            result = dict()
            safe_eval(self.start_condition.strip(), dict(record=self), result, mode="exec", nocopy=True)
            can_start = result.get('result', True)
            return can_start

    def break_execution(self):
        date_break = fields.Datetime.now()
        for process in self:
            process._break_execution(date_break)

    def _break_execution(self, date_break):
        for task in self.active_task_ids.filtered(lambda t: not t.is_closed):
            task.write({'active': False, 'execution_result': _('Task was canceled by the initiator.')})
        for process in self.child_ids.filtered(lambda pr: pr.state == 'started'):
            process._break_execution(date_break)
        self.write({'state': 'break', 'date_end': date_break})

    def resume_from_last_stage(self):
        processes = self.child_ids.filtered(lambda pr: pr.state == 'break') if self.type == 'complex' else [self]
        for process in processes:
            for decline_task in process.active_task_ids.filtered(lambda t: t.stage_id.result_type == 'error'):
                task = self.env['task.task'].browse(decline_task.id).copy()
                process._put_task_to_history(task)
                decline_task.write({'active': False})
            for task in process.task_ids.filtered(lambda t: not t.active and t.stage_id.result_type != 'error'):
                task.write({'active': True, 'execution_result': False})
            process.write({'state': 'started', 'date_end': False})
            if process.parent_id:
                process.parent_id.write({'state': 'started', 'date_end': False})

    def process_task_result(self, date_closed, result_type='ok', feedback=False):
        if result_type == 'ok':
            open_tasks = self.active_task_ids.filtered(lambda t: not t.is_closed)
            if len(open_tasks) - 1 == 0:
                next_executors = self.executor_ids.filtered(lambda ex: ex.sequence > self.sequence).sorted(
                    lambda pr: pr.sequence and pr.id)
                next_sequence = False if not any(next_executors) else next_executors[0].sequence
                if next_sequence:
                    next_executors = self.executor_ids.filtered(lambda ex: ex.sequence == next_sequence)
                    if any(next_executors):
                        for executor in next_executors:
                            executor.fill_date_deadline()
                            executor.create_task_for_executor()
                else:
                    self.write({'state': 'finished', 'date_end': date_closed})
                    if self.parent_id:
                        current_processes = self.parent_id.child_ids.filtered(
                            lambda pr: pr.sequence == self.sequence and pr.state != 'finished')
                        if len(current_processes) == 0:
                            current_sequence = self.sequence
                            started = False
                            while not started:
                                next_childs = self.parent_id.child_ids.filtered(lambda pr: pr.sequence > current_sequence).sorted(
                                    lambda pr: pr.sequence and pr.id)
                                next_sequence = False if not any(next_childs) else next_childs[0].sequence
                                if not next_sequence:
                                    self.parent_id.process_task_result(date_closed, result_type, feedback)
                                    started = True
                                else:
                                    next_processes = self.parent_id.child_ids.filtered(lambda pr: pr.sequence == next_sequence)
                                    if any(next_processes):
                                        for process in next_processes:
                                            res = process._start()
                                            if res:
                                                started = True
                                    else:
                                        self.parent_id.process_task_result(date_closed, result_type, feedback)

                    # TODO: дичайший костыль, либо статус сделать вычисляемым, либо сделать метод по обработке в родителе
                    if self.parent_obj_ref and type(self.parent_obj_ref).__name__ == 'document_flow.event':
                        self.parent_obj_ref.write({'state': 'approved'})
        elif result_type == 'error':
            self.write({'state': 'break', 'date_end': date_closed})
            if self.parent_id:
                self.parent_id.process_task_result(date_closed, result_type, feedback)
            if feedback and self.parent_obj_ref:
                self.parent_obj_ref.write({'state': 'on_registration'})
                self.parent_obj_ref.message_post(
                    body=feedback,
                    message_type='comment',
                    subtype_xmlid='mail.mt_note')


class ProcessExecutor(models.Model):
    _name = 'document_flow.process.executor'
    _description = 'Process Executor'
    _order = 'sequence, id'

    @api.model
    def _selection_executor_model(self):
        return selection_executor_model()

    process_id = fields.Many2one('document_flow.process', string='Process', ondelete='cascade', index=True,
                                 required=True)
    num = fields.Integer(string='№', required=True, default=0)
    executor_ref = fields.Reference(string='Executor', selection='_selection_executor_model', required=True, store=True)
    executor_ref_id = fields.Integer(string='Executor Id', index=True, copy=False)
    executor_ref_type = fields.Char(string='Executor Type', index=True, copy=False)
    date_deadline = fields.Date(string='Deadline')
    period = fields.Integer(string='Period')
    sequence = fields.Integer(string='Sequence', required=True, default=0)
    type_sequence = fields.Selection(TYPE_SEQUENCE, required=True, default='together_with_the_previous',
                                     string='Sequence')

    @api.depends('executor_ref_type', 'executor_ref_id')
    def _compute_executor_ref(self):
        for executor in self:
            if executor.executor_ref_type and executor.executor_ref_type in self.env:
                executor.executor_ref = '%s,%s' % (executor.executor_ref_type, executor.executor_ref_id or 0)
            else:
                executor.executor_ref = False

    # @api.depends('period')
    # def _compute_date_deadline(self):
    #     today = fields.Date.today()
    #     for executor in self:
    #         if not executor.date_deadline:
    #             executor.date_deadline = today + timedelta(executor.period)

    def fill_date_deadline(self):
        if not self.date_deadline:
            self.date_deadline = fields.Datetime.now() + timedelta(self.period)

    def create_task_for_executor(self):
        task_data = dict(
            author_id=self.create_uid.id,
            company_id=self.executor_ref.company_id.id,
            name=self.process_id.name,
            type_id=self.env['task.type'].search([
                ('code', '=', MAPPING_PROCESS_TASK_TYPES.get(self.process_id.type))
            ], limit=1).id,
            description=self.process_id.description,
            parent_ref='%s,%s' % (type(self.process_id).__name__, self.process_id.id),
            parent_ref_type=type(self.process_id).__name__,
            parent_ref_id=self.process_id.id,
            date_deadline=self.date_deadline
        )
        if type(self.executor_ref).__name__ == 'res.users':
            task_data['user_id'] = self.executor_ref.id
        else:
            task_data['role_executor_id'] = self.executor_ref.id
        res = self.env['task.task'].create(task_data)
        self.process_id._put_task_to_history(res)
        return res


class ProcessTemplate(models.Model):
    _name = 'document_flow.process.template'
    _description = 'Process Template'
    _check_company_auto = True

    @api.model
    def _selection_executor_model(self):
        return selection_executor_model()

    name = fields.Char(string='Name', required=True)
    description = fields.Html(string='Description')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    document_type_id = fields.Many2one('document_flow.document.type', string='Document Type')

    action_ids = fields.One2many('document_flow.action', 'parent_ref_id', string='Actions',
                                 domain=lambda self: [('parent_ref_type', '=', self._name)])

    process_ids = fields.One2many('document_flow.process', 'template_id', string='Processes')
    process_count = fields.Integer(compute='_compute_process_count')
    active = fields.Boolean(default=True, index=True)

    @api.model
    def create(self, vals_list):
        if any(vals_list.get('action_ids', [])):
            recompute_sequence_actions(self.env['document_flow.action'], vals_list.get('action_ids'))
        res = super(ProcessTemplate, self).create(vals_list)
        return res

    def write(self, vals):
        if any(vals.get('action_ids', [])):
            recompute_sequence_actions(self.env['document_flow.action'], vals.get('action_ids'))
        res = super(ProcessTemplate, self).write(vals)
        return res

    @api.depends('process_ids')
    def _compute_process_count(self):
        for template in self:
            template.process_count = len(template.process_ids)

    @api.onchange('sequence')
    def _compute_sequence(self):
        for process in self:
            process.visible_sequence = process.sequence


class Action(models.Model):
    _name = 'document_flow.action'
    _description = 'Action'
    _order = 'sequence, id'

    @api.model
    def _selection_parent_model(self):
        return [
            ('document_flow.process.template', _('Process Template')),
            ('document_flow.processing', _('Processing'))
        ]

    @api.model
    def _selection_executor_model(self):
        return selection_executor_model()

    name = fields.Char(string='Name', copy=True, required=True)
    type = fields.Selection(PROCESS_TYPES, string='Type', copy=True, index=True, required=True, default='review')
    parent_ref = fields.Reference(string='Parent', selection='_selection_parent_model', ondelete='restrict')
    parent_ref_type = fields.Char(string='Parent Type', index=True)
    parent_ref_id = fields.Integer(string='Parent Id', index=True)
    executor_ids = fields.One2many('document_flow.action.executor', 'action_id', string='Executors', copy=True)

    parent_id = fields.Many2one('document_flow.action', string='Parent Action', ondelete='cascade', index=True)
    child_ids = fields.One2many('document_flow.action', 'parent_id', string='Actions', copy=True)

    reviewer_ref = fields.Reference(string='Reviewer', selection='_selection_executor_model', store=True)
    reviewer_ref_id = fields.Integer(string='Reviewer Id', copy=True, index=True)
    reviewer_ref_type = fields.Char(string='Reviewer Type', copy=True, index=True)
    period = fields.Integer(string='Period', copy=True)

    task_sequence = fields.Selection(TASK_FORM_SEQUENCE, string='Task Form Sequence', copy=True, required=True,
                                     default='all_at_once')
    type_sequence = fields.Selection(TYPE_SEQUENCE, string='Sequence', copy=True, required=True,
                                     default='together_with_the_previous')
    sequence = fields.Integer(string='Sequence', copy=True, default=0)
    visible_sequence = fields.Integer(string='Sequence', compute='_compute_sequence')
    start_condition = fields.Text(string='Compute Condition', copy=True,
                                  help='Conditions that will be checked before action will be started.')

    process_id = fields.Many2one('document_flow.process', string='Process', compute='_compute_process_id')

    @api.model
    def create(self, vals_list):
        if any(vals_list.get('executor_ids', [])):
            recompute_sequence_executors(self.env['document_flow.action.executor'], vals_list.get('task_sequence'),
                                         vals_list.get('executor_ids'))
        res = super(Action, self).create(vals_list)
        return res

    def write(self, vals):
        if vals.get('task_sequence') or any(vals.get('executor_ids', [])):
            task_seq = self.task_sequence if not vals.get('task_sequence', False) else vals.get('task_sequence')
            if not vals.get('executor_ids', False):
                executors = list()
                for executor in self.executor_ids:
                    executors.append(list((1, executor.id, dict())))
                vals['executor_ids'] = executors
            recompute_sequence_executors(self.env['document_flow.action.executor'], task_seq, vals.get('executor_ids'))
        res = super(Action, self).write(vals)
        return res

    @api.constrains('start_condition')
    def _check_start_condition(self):
        for action in self.filtered('start_condition'):
            msg = test_python_expr(expr=action.start_condition.strip(), mode='exec')
            if msg:
                raise ValidationError(msg)

    @api.depends('reviewer_ref_type', 'reviewer_ref_id')
    def _compute_executor_ref(self):
        for template in self:
            if template.reviewer_ref_type and template.reviewer_ref_type in self.env:
                template.reviewer_ref = '%s,%s' % (template.reviewer_ref_type, template.reviewer_ref_id or 0)
            else:
                template.reviewer_ref = False

    @api.depends('sequence')
    def _compute_sequence(self):
        for action in self:
            action.visible_sequence = action.sequence

    def _compute_process_id(self):
        for action in self:
            action.process_id = self.env['document_flow.process.parent_object'].search([
                ('parent_ref_type', '=', self._name),
                ('parent_ref_id', '=', action.id)
            ])


class ActionExecutor(models.Model):
    _name = 'document_flow.action.executor'
    _description = 'Action Executor'
    _order = 'sequence, id'

    @api.model
    def _selection_executor_model(self):
        return selection_executor_model()

    action_id = fields.Many2one('document_flow.action', string='Action', ondelete='cascade', index=True,
                                required=True)
    executor_ref = fields.Reference(string='Executor', selection='_selection_executor_model', store=True)
    executor_ref_id = fields.Integer(string='Executor Id', index=True, copy=False)
    executor_ref_type = fields.Char(string='Executor Type', index=True, copy=False)
    period = fields.Integer(string='Period')

    type_sequence = fields.Selection(TYPE_SEQUENCE, string='Sequence', required=True,
                                     default='together_with_the_previous')

    sequence = fields.Integer(string='Sequence', required=True, default=0)
    visible_sequence = fields.Integer(string='Sequence', compute='_compute_sequence')

    @api.depends('sequence')
    def _compute_sequence(self):
        for executor in self:
            executor.visible_sequence = executor.sequence

    @api.depends('executor_ref_type', 'executor_ref_id')
    def _compute_executor_ref(self):
        for executor in self:
            if executor.executor_ref_type and executor.executor_ref_type in self.env:
                executor.executor_ref = '%s,%s' % (executor.executor_ref_type, executor.executor_ref_id or 0)
            else:
                executor.executor_ref = False


class ParentObjectProcess(models.Model):
    _name = 'document_flow.process.parent_object'
    _description = 'Parent Object Process'

    @api.model
    def _selection_parent_model(self):
        return selection_parent_model()

    process_id = fields.Many2one('document_flow.process', string='Process', ondelete='cascade', index=True,
                                 required=True)
    parent_ref = fields.Reference(string='Parent', selection='_selection_parent_model', ondelete='cascade',
                                  required=True)
    parent_ref_id = fields.Integer(string='Parent Id', index=True)
    parent_ref_type = fields.Char(string='Parent Type', index=True)
