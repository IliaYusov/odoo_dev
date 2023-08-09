from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
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


# todo: необходима возможность выбора роли, возможно каких-то предопределенных методов
def selection_executor_model():
    return [('res.users', _('User'))]


def selection_parent_model():
    return [
        ('document_flow.event', _('Event')),
        ('document_flow.event.decision', _('Decision'))
    ]


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
    # user_state = fields.Char(string='User State', compute='_compute_user_state')
    company_ids = fields.Many2many('res.company', string='Companies', required=True,
                                   default=lambda self: self.env.company)
    # company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    template_id = fields.Many2one('document_flow.process.template', string='Template',
                                  domain="[('type', '=', type)]")
    parent_id = fields.Many2one('document_flow.process', string='Parent Process', ondelete='cascade', index=True)
    executor_ids = fields.One2many('document_flow.process.executor', 'process_id', string='Executors')

    date_start = fields.Datetime(string='Date Start', default=fields.Datetime.now())
    date_end = fields.Datetime(string='Date End')
    date_deadline = fields.Datetime(string='Date Deadline')

    reviewer_ref = fields.Reference(string='Reviewer', selection='_selection_executor_model', store=True)
    reviewer_ref_id = fields.Integer(string='Reviewer Id', index=True)
    reviewer_ref_type = fields.Char(string='Reviewer Type', index=True)

    controller_ref = fields.Reference(string='Controller', selection='_selection_executor_model', store=True)
    controller_ref_id = fields.Integer(string="Controller Id", index=True)
    controller_ref_type = fields.Char(string="Controller Type", index=True)

    child_ids = fields.One2many('document_flow.process', 'parent_id', string='Processes')
    task_ids = fields.One2many('task.task', 'parent_ref_id', string='Tasks',
                               domain=lambda self: [('parent_ref_type', '=', 'document_flow.process'),
                                                    ('parent_id', '=', False)])

    task_sequence = fields.Selection(TASK_FORM_SEQUENCE, required=True, default='all_at_once',
                                     string='Task Form Sequence')
    sequence = fields.Integer(string='Sequence', default=0)
    visible_sequence = fields.Integer(string='Sequence', compute='_compute_sequence')

    parent_obj_ref = fields.Reference(string='Parent Object', selection='_selection_parent_model',
                                      compute='_compute_parent_obj', readonly=True)

    @api.model
    def create(self, vals_list):
        if vals_list.get('code', _('New')) == _('New'):
            vals_list['code'] = self.env['ir.sequence'].next_by_code('document_flow.process') or _('New')
        res = super(Process, self).create(vals_list)
        return res

    def write(self, vals):
        res = super(Process, self).write(vals)
        self._recompute_sequence_executors()
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
                process.reviewer_ref = '%s,%s' % (process.reviewer_ref_type, process.reviewer_ref_id or 0)
            else:
                process.reviewer_ref = False

    @api.depends('controller_ref_type', 'controller_ref_id')
    def _compute_controller_ref(self):
        for process in self:
            if process.controller_ref_type and process.controller_ref_type in self.env:
                process.controller_ref = '%s,%s' % (process.controller_ref_type, process.controller_ref_id or 0)
            else:
                process.controller_ref = False

    @api.onchange('template_id')
    def _onchange_template(self):
        if self.template_id and not self.executor_ids:
            self.name = self.template_id.name
            self.description = self.template_id.description
            self.type = self.template_id.type
            self.reviewer_ref = self.template_id.reviewer_ref
            self.date_deadline = fields.Datetime.now() + timedelta(self.template_id.deadline)

            for executor in self.template_id.executor_ids:
                self.env['document_flow.process.executor'].create({
                    'process_id': self.id,
                    'executor_ref': '%s,%s' % (type(executor.executor_ref).__name__, executor.executor_ref.id),
                    'date_deadline': fields.Datetime.now() + timedelta(executor.deadline)
                })

    def _recompute_sequence_executors(self):
        prevSeq = 0
        for executor in self.executor_ids:
            if self.task_sequence == 'all_at_once':
                executor.sequence = prevSeq
            elif self.task_sequence == 'sequentially':
                executor.sequence = prevSeq
                prevSeq += 1
            elif self.task_sequence == 'mixed':
                if executor.type_sequence == 'together_with_the_previous':
                    executor.sequence = prevSeq
                elif executor.type_sequence == 'after_the_previous':
                    executor.sequence = prevSeq + 1
                prevSeq = executor.sequence

    def action_start_process(self):
        if self.state == 'on_registration':
            if self.type == 'complex':
                self.start_complex_process()
            elif self.type == 'review':
                self.start_review_process()
            elif self.type == 'agreement':
                self.start_agreement_process()
            elif self.type == 'execution':
                self.start_execution_process()
            self.write({'state': 'started'})
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

    def start_review_process(self):
        if self.executor_ids:
            for executor in self.executor_ids:
                task = self.env['task.task'].create({
                    'company_id': executor.executor_ref.company_id.id,
                    'name': self.name,
                    'type_id': self.env['task.type'].search([
                        ('code', '=', MAPPING_PROCESS_TASK_TYPES.get(self.type))
                    ], limit=1).id,
                    'description': self.description,
                    'parent_ref': '%s,%s' % (self._name, self.id),
                    'parent_ref_type': self._name,
                    'parent_ref_id': self.id,
                    'date_deadline': executor.date_deadline,
                    'user_id': executor.executor_ref.id
                })

    # TODO: разобраться с reviewer, нужен ли и какой процесс
    def start_agreement_process(self):
        if self.executor_ids:
            for executor in self.executor_ids:
                task = self.env['task.task'].create({
                    'company_id': executor.executor_ref.company_id.id,
                    'name': self.name,
                    'type_id': self.env['task.type'].search([
                        ('code', '=', MAPPING_PROCESS_TASK_TYPES.get(self.type))
                    ], limit=1).id,
                    'description': self.description,
                    'parent_ref': '%s,%s' % (self._name, self.id),
                    'parent_ref_type': self._name,
                    'parent_ref_id': self.id,
                    'date_deadline': executor.date_deadline,
                    'user_id': executor.executor_ref.id
                })

    def start_execution_process(self):
        if self.executor_ids:
            for executor in self.executor_ids:
                task = self.env['task.task'].create({
                    'company_id': executor.executor_ref.company_id.id,
                    'name': self.name,
                    'type_id': self.env['task.type'].search([
                        ('code', '=', MAPPING_PROCESS_TASK_TYPES.get(self.type))
                    ], limit=1).id,
                    'description': self.description,
                    'parent_ref': '%s,%s' % (self._name, self.id),
                    'parent_ref_type': self._name,
                    'parent_ref_id': self.id,
                    'date_deadline': executor.date_deadline,
                    'user_id': executor.executor_ref.id
                })

    def start_complex_process(self):
        min_sequence = self.child_ids.search([
            ('parent_id', '=', self.id)
        ], order='sequence, id', limit=1).sequence or 0
        for process in self.child_ids.search([
            ('parent_id', '=', self.id),
            ('sequence', '=', min_sequence)
        ], order='id'):
            process.action_start_process()

    def process_task_result(self, date_closed, result_type='ok', feedback=False):
        if result_type == 'ok':
            if self.parent_id:
                next_sequence = self.parent_id.child_ids.search([
                    ('parent_id', '=', self.parent_id.id),
                    ('sequence', '>', self.sequence)
                ], order='sequence, id', limit=1).sequence or False
                if not next_sequence:
                    if not self.parent_id.child_ids.search([
                        ('id', '!=', self.id),
                        ('parent_id', '=', self.parent_id.id),
                        ('sequence', '=', self.sequence),
                        ('state', '!=', 'finished')
                    ]):
                        self.parent_id.write({'state': 'finished', 'date_end': date_closed})
                else:
                    for process in self.child_ids.search([
                        ('parent_id', '=', self.parent_id.id),
                        ('sequence', '=', next_sequence)
                    ], order='id'):
                        process.action_start_process()
            self.write({'state': 'finished', 'date_end': date_closed})
        elif result_type == 'error':
            self.write({'state': 'break', 'date_end': date_closed})
            if self.parent_id:
                self.parent_id.write({'state': 'break', 'date_end': date_closed})
            if feedback and self.parent_obj_ref:
                self.parent_obj_ref.write({'state': 'on_registration'})
                self.parent_obj_ref.message_post(
                    body=feedback,
                    message_type='comment',
                    subtype_xmlid='mail.mt_note')


class ProcessExecutor(models.Model):
    _name = 'document_flow.process.executor'
    _description = 'Process Executor'
    _order = 'num, id'

    @api.model
    def _selection_executor_model(self):
        return selection_executor_model()

    process_id = fields.Many2one('document_flow.process', string='Process', ondelete='cascade', index=True,
                                 required=True)
    num = fields.Integer(string='№', required=True, default=0)
    executor_ref = fields.Reference(string='Executor', selection='_selection_executor_model', required=True, store=True)
    executor_ref_id = fields.Integer(string='Executor Id', index=True, copy=False)
    executor_ref_type = fields.Char(string='Executor Type', index=True, copy=False)
    date_deadline = fields.Date(string='Deadline', required=True)
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


class ProcessTemplate(models.Model):
    _name = 'document_flow.process.template'
    _description = 'Process Template'

    @api.model
    def _selection_executor_model(self):
        return selection_executor_model()

    name = fields.Char(string='Name', required=True)
    description = fields.Html(string='Description')
    type = fields.Selection(PROCESS_TYPES, required=True, default='review', index=True, string='Type')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    executor_ids = fields.One2many('document_flow.process.template.executor', 'template_id', string='Executors')

    reviewer_ref = fields.Reference(string='Reviewer', selection='_selection_executor_model', store=True)
    reviewer_ref_id = fields.Integer(string='Reviewer Id', index=True, copy=False)
    reviewer_ref_type = fields.Char(string='Reviewer Type', index=True, copy=False)
    deadline = fields.Integer(string='Deadline')

    parent_id = fields.Many2one('document_flow.process.template', string='Parent Template', ondelete='cascade',
                                index=True)
    child_ids = fields.One2many('document_flow.process.template', 'parent_id', string='Processes')
    task_sequence = fields.Selection(TASK_FORM_SEQUENCE, required=True, default='all_at_once',
                                     string='Task Form Sequence')
    sequence = fields.Integer(string='Sequence', default=0)
    visible_sequence = fields.Integer(string='Sequence', compute='_compute_sequence')

    def write(self, vals):
        res = super(ProcessTemplate, self).write(vals)
        # self._recompute_sequence_executors()
        return res

    @api.depends('reviewer_ref_type', 'reviewer_ref_id')
    def _compute_executor_ref(self):
        for template in self:
            if template.reviewer_ref_type and template.reviewer_ref_type in self.env:
                template.reviewer_ref = '%s,%s' % (template.reviewer_ref_type, template.reviewer_ref_id or 0)
            else:
                template.reviewer_ref = False

    @api.onchange('sequence')
    def _compute_sequence(self):
        for process in self:
            process.visible_sequence = process.sequence


class ProcessTemplateExecutor(models.Model):
    _name = 'document_flow.process.template.executor'
    _description = 'Process Template Executor'

    @api.model
    def _selection_executor_model(self):
        return selection_executor_model()

    template_id = fields.Many2one('document_flow.process.template', string='Template', ondelete='cascade', index=True,
                                  required=True)
    num = fields.Integer(string='№', required=True, default=0)
    executor_ref = fields.Reference(string='Executor', selection='_selection_executor_model', store=True)
    executor_ref_id = fields.Integer(string='Executor Id', index=True, copy=False)
    executor_ref_type = fields.Char(string='Executor Type', index=True, copy=False)
    deadline = fields.Integer(string='Deadline')

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
