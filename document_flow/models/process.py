import json


from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, date, timedelta
from lxml import etree

ACTION_TYPES = [
    ('review', _('Review')),
    ('agreement', _('Agreement')),
    ('execution', _('Execution'))
]

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
        ('document_flow.event.decision', _('Decision')),
        ('document_flow.action', _('Action')),
        ('document_flow.document', _('Document'))
    ]


def recompute_sequence_executors(processes):
    for process in processes:
        prevSeq = 0
        for executor in process.executor_ids:
            if process.task_sequence == 'all_at_once':
                executor.sequence = prevSeq
            elif process.task_sequence == 'sequentially':
                executor.sequence = prevSeq
                prevSeq += 1
            elif process.task_sequence == 'mixed':
                if executor.type_sequence == 'together_with_the_previous':
                    executor.sequence = prevSeq
                elif executor.type_sequence == 'after_the_previous':
                    executor.sequence = prevSeq + 1
                prevSeq = executor.sequence


class Process(models.Model):
    _name = 'document_flow.process'
    _description = 'Process'
    _order = 'tree_id'

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

    tree_id = fields.Char(string='TreeId', compute='_compute_tree_id', store=True, readonly=False)
    branch_depth = fields.Integer(string='BranchDepth', compute='_compute_branch_depth')

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
    task_ids = fields.One2many('task.task', 'parent_ref_id', string='Tasks',
                               domain=lambda self: [('parent_ref_type', '=', 'document_flow.process'),
                                                    ('parent_id', '=', False)])

    task_sequence = fields.Selection(TASK_FORM_SEQUENCE, required=True, default='all_at_once',
                                     string='Task Form Sequence')
    sequence = fields.Integer(string='Sequence', default=0)
    visible_sequence = fields.Integer(string='Sequence', compute='_compute_sequence')

    parent_obj_ref = fields.Reference(string='Parent Object', selection='_selection_parent_model',
                                      compute='_compute_parent_obj', readonly=True)

    # bokeh_chart = fields.Text(
    #     string='Bokeh Chart',
    #     compute='_compute_bokeh_chart',
    # )
    #
    # def _compute_bokeh_chart(self):
    #     for process in self:
    #         tasks = []
    #         if process.type == 'complex':
    #             for simple_process in process.child_ids:
    #                 if process.date_start:
    #                     if simple_process.date_start:
    #                         tasks.extend(self.env['task.task'].search([
    #                             ('parent_ref_type', '=', type(simple_process).__name__),
    #                             ('parent_ref_id', '=', simple_process.id)
    #                         ]))
    #         else:
    #             if process.date_start:
    #                 tasks.extend(self.env['task.task'].search([
    #                     ('parent_ref_type', '=', type(process).__name__),
    #                     ('parent_ref_id', '=', process.id)
    #                 ]))
    #         date_processes = [pr.date_start + timedelta(hours=1) for pr in process.child_ids if pr.date_start]
    #         date_tasks = [task.date_closed + timedelta(hours=1) for task in tasks if task.date_closed]
    #         # Design your bokeh figure:
    #         p = figure(width=350, height=250, y_axis_type='datetime', x_range=(-0.1, 1.5))
    #         p.toolbar_location = None
    #         p.toolbar.logo = None
    #         p.toolbar.active_drag = None
    #         p.toolbar.active_scroll = None
    #         p.toolbar.active_tap = None
    #         p.xgrid.grid_line_color = None
    #         p.ygrid.grid_line_color = None
    #         p.axis.visible = False
    #         line = p.line([0, 0], [process.date_start, max(task.date_closed + timedelta(hours=2) for task in tasks if task.date_closed)],
    #                       color='green', line_width=3)
    #         # line = p.line([0, 0], [0, -5], line_width=3)
    #         print(date_processes)
    #         print(date_tasks)
    #         circles = p.circle([0] * len(date_processes), date_processes, size=20, color="green", alpha=0.5)
    #         circles = p.circle([0] * len(date_tasks), date_tasks, size=10, color="navy", alpha=0.5)
    #         source = ColumnDataSource(data=dict(height=[0.1] * len(date_tasks),
    #                                             weight=date_tasks,
    #                                             names=[task.date_closed.strftime('%d.%m.%Y %H:%M:%S') + '\n' + 'Executed ' + task.actual_executor_id.name for task in tasks if task.date_closed]))
    #         labels = LabelSet(x='height', y='weight', text='names', x_offset=5, y_offset=5, source=source)
    #
    #         # labels = LabelSet(x=1, y=date_tasks[0], text='Test', x_offset=5, y_offset=5)
    #         p.add_layout(labels)
    #         # circle = p.circle([0, 0, 0, 0, 0], [-1, -2, -3, -4, -5], size=20, color="navy", alpha=0.5)
    #         # (...)
    #         # fill the record field with both markup and the script of a chart.
    #         script, div = components(p, wrap_script=False)
    #         process.bokeh_chart = json.dumps({"div": div, "script": script})

    @api.model
    def create(self, vals_list):
        if vals_list.get('code', _('New')) == _('New'):
            vals_list['code'] = self.env['ir.sequence'].next_by_code('document_flow.process') or _('New')
        res = super(Process, self).create(vals_list)
        return res

    def write(self, vals):
        res = super(Process, self).write(vals)
        recompute_sequence_executors(self)
        return res

    def unlink(self):
        self.task_ids.unlink()
        return super(Process, self).unlink()

    def _compute_parent_obj(self):
        for process in self:
            process.parent_obj_ref = self.env['document_flow.process.parent_object'].search([
                ('process_id', '=', process.id)
            ], limit=1).parent_ref

    def _compute_tree_id(self):
        for process in self:
            if process.parent_id:
                if process.parent_id.tree_id:
                    print(process, process.parent_id, process.parent_id.tree_id, str(process.id).zfill(6))
                    process.tree_id = process.parent_id.tree_id + str(process.id).zfill(6)
                else:
                    tree_id = ''
                    parent = self.env['document_flow.process'].search([('id', '=', process.parent_id.id)], limit=1)
                    while parent:
                        tree_id = str(parent.id).zfill(6) + tree_id
                        parent = self.env['document_flow.process'].search([('id', '=', parent.parent_id.id)], limit=1)
                    process.tree_id = tree_id + str(process.id).zfill(6)
            else:
                process.tree_id = str(process.id).zfill(6)

    def _compute_branch_depth(self):
        for process in self:
            if process.parent_id:
                process.branch_depth = process.parent_id.branch_depth + 1
            else:
                process.branch_depth = 0

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
            self.fill_process_by_template()

    def fill_process_by_template(self):
        if self.template_id:
            self.name = self.template_id.name
            self.description = self.template_id.description
            self.type = self.template_id.type
            self.date_deadline = fields.Datetime.now() + timedelta(self.template_id.period)
            self.task_sequence = self.template_id.task_sequence
            self.sequence = self.template_id.sequence

            for executor in self.template_id.executor_ids:
                self.env['document_flow.process.executor'].create({
                    'process_id': self.id,
                    'sequence': self.template_id.sequence,
                    'type_sequence': self.template_id.type_sequence,
                    'executor_ref': '%s,%s' % (type(executor.executor_ref).__name__, executor.executor_ref.id),
                    'period': executor.period
                })

            for process in self.template_id.child_ids:
                simple_process = self.env['document_flow.process'].create({
                    'name': process.name,
                    'description': process.description,
                    'type': process.type,
                    'parent_id': self.id,
                    'task_sequence': process.task_sequence,
                    'sequence': process.sequence,
                    'reviewer_ref': process.reviewer_ref
                })
                for executor in process.executor_ids:
                    self.env['document_flow.process.executor'].create({
                        'process_id': simple_process.id,
                        'sequence': executor.sequence,
                        'type_sequence': executor.type_sequence,
                        'executor_ref': '%s,%s' % (type(executor.executor_ref).__name__, executor.executor_ref.id),
                        'period': executor.period
                    })

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
            self.write({'state': 'started', 'date_start': fields.Datetime.now()})
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

    def line_0(self):
        pass

    def line_1(self):
        pass

    def line_2(self):
        pass

    def line_3(self):
        pass

    def line_4(self):
        pass

    def line_5(self):
        pass

    def action_expand(self):
        open_list = self.env.context['open_list']
        expanded_list = self.env.context['expanded_list']
        print('begin', open_list, expanded_list)
        if self.id in open_list:
            open_list.remove(self.id)
            if self.id in expanded_list:
                expanded_list.remove(self.id)
            self.expanded = False
            remove_list = [child.id for child in self.child_ids]
            while remove_list:
                new_remove_list = []
                for child_id in remove_list:
                    if child_id in open_list:
                        new_remove_list.extend(child.id for child in self.env['document_flow.process'].search([('id', '=', child_id)]).child_ids)
                        open_list.remove(child_id)
                remove_list = new_remove_list
        else:
            open_list.append(self.id)
            if self.id not in expanded_list:
                expanded_list.append(self.id)
            self.expanded = True
            add_list = [child.id for child in self.child_ids]
            while add_list:
                new_add_list = []
                for child_id in add_list:
                    if child_id not in open_list and self.env['document_flow.process'].search([('id', '=', child_id)]).expanded:
                        new_add_list.extend(child.id for child in self.env['document_flow.process'].search([('id', '=', child_id)]).child_ids)
                        if self.env['document_flow.process'].search([('id', '=', child_id)]).expanded:
                            open_list.append(child_id)
                add_list = new_add_list
        print('end', open_list, expanded_list)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Processes',
            'res_model': 'document_flow.process',
            'view_type': 'tree',
            'view_mode': 'tree,form',
            'limit': 150,
            'domain': f"['|',('parent_id', '=', False),('parent_id.id', 'in', {open_list})]",
            'context': {'open_list': open_list, 'expanded_list': expanded_list},
            'target': 'main',
        }

    def start_review_process(self):
        if self.executor_ids:
            for executor in self.executor_ids:
                executor.fill_date_deadline()
                executor.create_task_for_executor()

    # TODO: разобраться с reviewer, нужен ли и какой процесс
    def start_agreement_process(self):
        if self.executor_ids:
            min_sequence = self.executor_ids.search([
                ('process_id', '=', self.id)
            ], order='sequence, id', limit=1).sequence or 0
            for executor in self.executor_ids.search([
                ('process_id', '=', self.id),
                ('sequence', '=', min_sequence)
            ], order='id'):
                executor.fill_date_deadline()
                executor.create_task_for_executor()

    def start_execution_process(self):
        if self.executor_ids:
            min_sequence = self.executor_ids.search([
                ('process_id', '=', self.id)
            ], order='sequence, id', limit=1).sequence or 0
            for executor in self.executor_ids.search([
                ('process_id', '=', self.id),
                ('sequence', '=', min_sequence)
            ], order='id'):
                executor.fill_date_deadline()
                executor.create_task_for_executor()

    def start_complex_process(self):
        min_sequence = self.child_ids.search([
            ('parent_id', '=', self.id)
        ], order='sequence, id', limit=1).sequence or 0
        [process.action_start_process() for process in self.child_ids.search([
            ('parent_id', '=', self.id),
            ('sequence', '=', min_sequence)
        ], order='id')]

    def process_task_result(self, date_closed, result_type='ok', feedback=False):
        if result_type == 'ok':
            if not self.parent_id:
                next_sequence = self.executor_ids.search([
                    ('process_id', '=', self.id),
                    ('sequence', '>', self.sequence)
                ], order='sequence, id', limit=1).sequence or False
                if not next_sequence:
                    self.write({'state': 'finished', 'date_end': date_closed})
                else:
                    for executor in self.executor_ids.search([
                        ('process_id', '=', self.id),
                        ('sequence', '=', next_sequence)
                    ], order='id'):
                        executor.fill_date_deadline()
                        executor.create_task_for_executor()
            else:
                task_count = 1
                if self.type == 'review':
                    task_count = self.env['task.task'].search_count([
                        ('parent_ref_type', '=', self._name),
                        ('parent_ref_id', '=', self.id),
                        ('is_closed', '=', False)
                    ])
                if task_count - 1 == 0:
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
                        [process.action_start_process() for process in self.child_ids.search([
                            ('parent_id', '=', self.parent_id.id),
                            ('sequence', '=', next_sequence)
                        ], order='id')]
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

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        expanded_list = self.env.context.get('expanded_list') or []
        res = super().get_view(view_id, view_type, **options)
        if view_type == 'tree':
            doc = etree.XML(res['arch'])
            button_right = doc.xpath("//button[@icon='fa-chevron-right']")
            button_down = doc.xpath("//button[@icon='fa-chevron-down']")
            attrs_right = '{' + f'"invisible": ["|", ["child_ids", "=", []], ["id", "in", {expanded_list}]]' + '}'
            attrs_down = '{' + f'"invisible": ["|", ["child_ids", "=", []], ["id", "not in", {expanded_list}]]' + '}'
            button_right[0].set('modifiers', attrs_right)
            button_down[0].set('modifiers', attrs_down)
            for n in range(6):
                line = doc.xpath(f"//button[@name='line_{n}']")
                line_attrs = '{' + f'"invisible": ["|", "&", ["child_ids", "=", []], ["id", "in", {expanded_list}], ["branch_depth", "<=", {n}]]' + '}'
                line[0].set('modifiers', line_attrs)
            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res


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
        return self.env['task.task'].create({
            'author_id': self.create_uid.id,
            'company_id': self.executor_ref.company_id.id,
            'name': self.process_id.name,
            'type_id': self.env['task.type'].search([
                ('code', '=', MAPPING_PROCESS_TASK_TYPES.get(self.process_id.type))
            ], limit=1).id,
            'description': self.process_id.description,
            'parent_ref': '%s,%s' % (type(self.process_id).__name__, self.process_id.id),
            'parent_ref_type': type(self.process_id).__name__,
            'parent_ref_id': self.process_id.id,
            'date_deadline': self.date_deadline,
            'user_id': self.executor_ref.id
        })


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

    action_ids = fields.One2many('document_flow.action', 'parent_ref_id', string='Actions',
                                 domain=lambda self: [('parent_ref_type', '=', self._name)])

    process_ids = fields.One2many('document_flow.process', 'template_id', string='Processes')
    process_count = fields.Integer(compute='_compute_process_count')

    def write(self, vals):
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

    @api.model
    def _selection_parent_model(self):
        return [
            ('document_flow.process.template', _('Process Template')),
            ('document_flow.document', _('Document'))
        ]

    @api.model
    def _selection_executor_model(self):
        return selection_executor_model()

    name = fields.Char(string='Name', required=True)
    type = fields.Selection(ACTION_TYPES, required=True, default='review', index=True, string='Type')
    parent_ref = fields.Reference(string='Parent', ondelete='restrict', selection="_selection_parent_model")
    parent_ref_type = fields.Char(string="Parent Type", index=True)
    parent_ref_id = fields.Integer(string="Parent Id", index=True)
    executor_ids = fields.One2many('document_flow.action.executor', 'action_id', string='Executors')

    reviewer_ref = fields.Reference(string='Reviewer', selection='_selection_executor_model', store=True)
    reviewer_ref_id = fields.Integer(string='Reviewer Id', index=True, copy=False)
    reviewer_ref_type = fields.Char(string='Reviewer Type', index=True, copy=False)
    period = fields.Integer(string='Period')

    task_sequence = fields.Selection(TASK_FORM_SEQUENCE, required=True, default='all_at_once',
                                     string='Task Form Sequence')
    sequence = fields.Integer(string='Sequence', default=0)
    visible_sequence = fields.Integer(string='Sequence', compute='_compute_sequence')

    process_id = fields.Many2one('document_flow.process', string='Process', compute='_compute_process_id')

    def write(self, vals):
        res = super(Action, self).write(vals)
        recompute_sequence_executors(self)
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

    def _compute_process_id(self):
        for action in self:
            action.process_id = self.env['document_flow.process.parent_object'].search([
                ('parent_ref_type', '=', self._name),
                ('parent_ref_id', '=', action.id)
            ])


class ActionExecutor(models.Model):
    _name = 'document_flow.action.executor'
    _description = 'Action Executor'
    _order = 'num, id'

    @api.model
    def _selection_executor_model(self):
        return selection_executor_model()

    action_id = fields.Many2one('document_flow.action', string='Action', ondelete='cascade', index=True,
                                required=True)
    num = fields.Integer(string='№', required=True, default=0)
    executor_ref = fields.Reference(string='Executor', selection='_selection_executor_model', store=True)
    executor_ref_id = fields.Integer(string='Executor Id', index=True, copy=False)
    executor_ref_type = fields.Char(string='Executor Type', index=True, copy=False)
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
