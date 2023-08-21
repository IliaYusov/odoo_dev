from odoo import _, models, fields, api
from datetime import datetime, date, timedelta


class Event(models.Model):
    _name = 'document_flow.event'
    _description = 'Event'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _order = 'date_start desc, id desc'

    name = fields.Char(string='Name', required=True, copy=True)
    company_ids = fields.Many2many('res.company', string='Companies', required=True,
                                   default=lambda self: self.env.company)
    description = fields.Html(string='Description')
    date_start = fields.Datetime(string='Start Date', required=True, index=True, copy=True)
    date_end = fields.Datetime(string='End Date', index=True, copy=False)
    location = fields.Char(string='Location')

    organizer_id = fields.Many2one('res.users', string='Organizer')
    agreed_id = fields.Many2one('res.users', string='Agreed')
    member_ids = fields.Many2many('res.users', relation='event_user_rel', column1='event_id', column2='user_id',
                                  string='Members')
    management_committee_id = fields.Many2one('document_flow.management_committee', string='Management Committee')
    question_ids = fields.One2many('document_flow.event.question', 'event_id', string='Questions')
    decision_ids = fields.One2many('document_flow.event.decision', 'event_id', string='Decisions', copy=True)
    annex_ids = fields.One2many('document_flow.event.annex', 'event_id', string='Annexes')

    state = fields.Selection([
        ('on_registration', 'On Registration'),
        ('on_approval', 'On Approval'),
        ('approved', 'Approved'),
        ('completed', 'Completed')
    ], required=True, index=True, string='Status', default='on_registration', readonly=True, tracking=True, copy=False)

    attachment_count = fields.Integer(compute='_compute_attachment_count', string='Attachments')
    tasks_count = fields.Integer(compute='_compute_tasks_count', string='Tasks')

    is_process_started = fields.Boolean(compute='_compute_is_process_started')

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        default['name'] = _('Copy_%s') % self.name
        return super(Event, self).copy(default=default)

    @api.onchange('management_committee_id')
    def _onchange_management_committee(self):
        if self.management_committee_id and not self.member_ids:
            self.member_ids = self.management_committee_id.member_ids

    def _compute_attachment_count(self):
        for event in self:
            event.attachment_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', type(event).__name__),
                ('res_id', '=', event.id)
            ])

    def _compute_tasks_count(self):
        for event in self:
            tasks_count = 0
            main_process = self.env['document_flow.process.parent_object'].search([
                ('parent_ref_id', '=', self.id),
                ('parent_ref_type', '=', self._name),
                ('process_id', '!=', False),
                ('process_id.type', '=', 'complex'),
                ('process_id.state', '!=', 'break')
            ]).process_id
            if main_process:
                for process in main_process.child_ids:
                    tasks_count += len(process.sudo().task_ids)
            event.tasks_count = tasks_count

    def _compute_is_process_started(self):
        for event in self:
            event.is_process_started = self.env['document_flow.process.parent_object'].search_count([
                ('parent_ref_type', '=', self._name),
                ('parent_ref_id', '=', event.id),
                ('process_id', '!=', False),
                ('process_id.type', '=', 'complex'),
                ('process_id.state', 'in', ('on_registration', 'started', 'finished'))
            ]) > 0

    def action_send_for_approving(self):
        self.ensure_one()
        all_members = list(self.member_ids | self.management_committee_id.member_ids)
        all_members.extend([executor for executor in self.decision_ids.executor_ids])
        c_ids = set([member.company_id.id for member in all_members])
        complex_process = self.env['document_flow.process'].create({
            'company_ids': [(6, 0, c_ids)],
            'name': _('Agree on a protocol of event "%s"', self.name),
            'type': 'complex',
            'description': self.description
        })

        link = self.env['document_flow.process.parent_object'].create({
            'process_id': complex_process.id,
            'parent_ref': '%s,%s' % (self._name, self.id),
            'parent_ref_id': self.id,
            'parent_ref_type': self._name
        })

        if self.agreed_id:
            process_agreement = self.env['document_flow.process'].create({
                'company_ids': [(6, 0, [self.agreed_id.company_id.id])],
                'name': _('Agree on a protocol of event "%s"', self.name),
                'type': 'agreement',
                'sequence': 0,
                'description': self.description,
                'parent_id': complex_process.id
            })
            process_agreement_executor = self.env['document_flow.process.executor'].create({
                'process_id': process_agreement.id,
                'executor_ref': '%s,%s' % (type(self.agreed_id).__name__, self.agreed_id.id),
                'date_deadline': datetime.now()
            })

            link = self.env['document_flow.process.parent_object'].create({
                'process_id': process_agreement.id,
                'parent_ref': '%s,%s' % (self._name, self.id),
                'parent_ref_id': self.id,
                'parent_ref_type': self._name
            })

        members = list(set(self.member_ids) | set(self.management_committee_id.member_ids))
        c_ids = set([member.company_id.id for member in members])
        process_review = self.env['document_flow.process'].create({
            'company_ids': [(6, 0, c_ids)],
            'name': _('Review a protocol of event "%s"', self.name),
            'type': 'review',
            'sequence': 1,
            'description': self.description,
            'parent_id': complex_process.id
        })
        for executor in members:
            process_review_executor = self.env['document_flow.process.executor'].create({
                'process_id': process_review.id,
                'executor_ref': '%s,%s' % (type(executor).__name__, executor.id),
                'date_deadline': datetime.now()
            })

        link = self.env['document_flow.process.parent_object'].create({
            'process_id': process_review.id,
            'parent_ref': '%s,%s' % (self._name, self.id),
            'parent_ref_id': self.id,
            'parent_ref_type': self._name
        })

        reviews = self.decision_ids.search([
            ('event_id', '=', self.id),
            ('task_type', '=', 'review'),
            ('date_deadline', '!=', False),
            ('executor_ids', '!=', False)
        ])
        if reviews.ids:
            for decision in reviews:
                c_ids = set([executor.company_id.id for executor in decision.executor_ids])
                process_review = self.env['document_flow.process'].create({
                    'company_ids': [(6, 0, c_ids)],
                    'name': _('Review with decision of event "%s"', self.name),
                    'type': 'review',
                    'sequence': 1,
                    'description': decision.name,
                    'parent_id': complex_process.id
                })
                for executor in decision.executor_ids:
                    process_review_executor = self.env['document_flow.process.executor'].create({
                        'process_id': process_review.id,
                        'executor_ref': '%s,%s' % (type(executor).__name__, executor.id),
                        'date_deadline': decision.date_deadline
                    })
                link = self.env['document_flow.process.parent_object'].create({
                    'process_id': process_review.id,
                    'parent_ref': '%s,%s' % (type(decision).__name__, decision.id),
                    'parent_ref_id': decision.id,
                    'parent_ref_type': type(decision).__name__
                })

        executions = self.decision_ids.search([
            "&", "&",
            ('event_id', '=', self.id),
            ('task_type', '=', 'execution'),
            ('date_deadline', '!=', False),
            "|",
            ('executor_ids', '!=', False),
            ('responsible_id', '!=', False)
        ])
        if executions.ids:
            for decision in executions:
                executors = list([executor.company_id.id for executor in decision.executor_ids])
                if decision.responsible_id:
                    executors.append(decision.responsible_id.company_id.id)
                c_ids = set(executors)
                process_execution = self.env['document_flow.process'].create({
                    'company_ids': [(6, 0, c_ids)],
                    'name': _('Execute decision of event "%s"', self.name),
                    'type': 'execution',
                    'sequence': 1,
                    'description': decision.name,
                    'parent_id': complex_process.id
                })
                # TODO: свернуть в 1 запись
                if decision.responsible_id and decision.executor_ids:
                    process_execution.write({
                        'reviewer_ref': '%s,%s' % (
                            type(decision.responsible_id).__name__, decision.responsible_id.id)
                    })
                if decision.executor_ids:
                    for executor in decision.executor_ids:
                        process_execution_executor = self.env['document_flow.process.executor'].create({
                            'process_id': process_execution.id,
                            'executor_ref': '%s,%s' % (type(executor).__name__, executor.id),
                            'date_deadline': decision.date_deadline
                        })
                elif decision.responsible_id:
                    process_execution_executor = self.env['document_flow.process.executor'].create({
                        'process_id': process_execution.id,
                        'executor_ref': '%s,%s' % (
                            type(decision.responsible_id).__name__, decision.responsible_id.id),
                        'date_deadline': decision.date_deadline
                    })
                link = self.env['document_flow.process.parent_object'].create({
                    'process_id': process_execution.id,
                    'parent_ref': '%s,%s' % (type(decision).__name__, decision.id),
                    'parent_ref_id': decision.id,
                    'parent_ref_type': type(decision).__name__
                })
        complex_process.action_start_process()

        self.write({'state': 'on_approval'})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'sticky': False,
                'message': _("The process of agreement a protocol were started"),
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }

    def action_open_attachments(self):
        self.ensure_one()
        return {
            'name': _('Attachments'),
            'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,tree,form',
            'context': "{'default_res_model': '%s','default_res_id': %d}" % (self._name, self.id),
            'help': """
                <p class="o_view_nocontent_smiling_face">%s</p>
                """ % _("Add attachments for this event")
        }

    def action_open_tasks(self):
        self.ensure_one()
        task_ids = []
        main_process = self.env['document_flow.process.parent_object'].search([
            ('parent_ref_id', '=', self.id),
            ('parent_ref_type', '=', self._name),
            ('process_id', '!=', False),
            ('process_id.type', '=', 'complex'),
            ('process_id.state', '!=', 'break')
        ]).process_id
        if main_process:
            for process in main_process.sudo().child_ids:
                if process.task_ids:
                    task_ids.extend(process.task_ids.ids)
        return {
            'name': _('Tasks'),
            'domain': [
                ('id', 'in', task_ids)
            ],
            'res_model': 'task.task',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form'
        }


class EventQuestion(models.Model):
    _name = 'document_flow.event.question'
    _description = 'Event Question'

    name = fields.Html(string='Agenda', required=True)
    time_start = fields.Float(string="From")
    time_end = fields.Float(string="To")
    event_id = fields.Many2one('document_flow.event', string='Event', ondelete='cascade', index=True, required=True)
    speaker_ids = fields.Many2many('res.users', relation='event_question_user_rel', column1='question_id',
                                   column2='speaker_id', string='Speakers')


class EventDecision(models.Model):
    _name = 'document_flow.event.decision'
    _description = 'Event Decision'
    _order = 'num, id'

    num = fields.Integer(string='№', required=True, copy=True, default=1)
    visible_num = fields.Integer(string='№', compute='_compute_num')
    name = fields.Html(string='Decided', required=True, copy=True)
    event_id = fields.Many2one('document_flow.event', string='Event', ondelete='cascade', index=True, required=True)
    task_type = fields.Selection([
        ('review', 'Review'),
        ('execution', 'Execution')
    ], required=True, default='review', string='Type')
    responsible_id = fields.Many2one('res.users', string='Responsible')
    executor_ids = fields.Many2many('res.users', relation='event_decision_user_rel', column1='decision_id',
                                    column2='executor_id', string='Executors')
    date_deadline = fields.Date(string='Deadline', index=True)
    process_id = fields.Many2one('document_flow.process', string='Process', compute='_compute_process_id')
    date_execution = fields.Datetime(string='Execution Date', related='process_id.date_end', readonly=True)

    deadline_type = fields.Selection([
        ('to_date', 'To Date'),
        ('after_decision', 'After Decision')
    ], required=True, default='to_date', string='Deadline Type')
    number_days = fields.Integer(string='Within')
    after_decision_id = fields.Many2one('document_flow.event.decision', string='After Decision',
                                        domain="[('id', 'in', parent.decision_ids), ('id', '!=', id),"
                                               "('date_deadline', '!=', False)]")

    repeat_interval = fields.Selection([
        ('week', 'Weeks'),
        ('month', 'Months'),
        ('quarter', 'Quarter'),
        ('year', 'Years'),
    ], required=False, string='Repeat Interval')

    def name_get(self):
        decisions = []
        for decision in self:
            name = '%s %s' % (decision.num, decision.name.striptags())
            decisions.append((decision.id, name))
        return decisions

    @api.onchange('num')
    def _compute_num(self):
        for decision in self:
            decision.visible_num = decision.num

    @api.depends('process_id')
    def _compute_process_id(self):
        for decision in self:
            decision.process_id = self.env['document_flow.process.parent_object'].sudo().search([
                ('parent_ref_type', '=', self._name),
                ('parent_ref_id', '=', decision.id),
                ('process_id', '!=', False),
                ('process_id.state', '!=', 'break')
            ], limit=1).process_id

    @api.onchange('deadline_type', 'after_decision_id', 'number_days')
    def onchange_date_deadline(self):
        if self.deadline_type == 'to_date':
            self.after_decision_id = False
            self.number_days = False
        elif self.deadline_type == 'after_decision' and self.number_days:
            self.date_deadline = self._get_decision_date_deadline(self.after_decision_id) + timedelta(
                days=self.number_days)

    def _get_decision_date_deadline(self, decision):
        if decision.deadline_type == 'to_date':
            return decision.date_deadline
        elif decision.deadline_type == 'after_decision' and decision.prev_decision_id:
            return self._get_decision_date_deadline(decision.prev_decision_id) + timedelta(
                days=decision.number_days)
        else:
            return decision.date_deadline

    def unlink(self):
        self.mapped('process_id').unlink()
        return super(EventDecision, self).unlink()


class EventAnnex(models.Model):
    _name = 'document_flow.event.annex'
    _description = 'Event Annex'
    _order = 'num, id'

    num = fields.Integer(string='№', required=True, default=1)
    visible_num = fields.Integer(string='№', compute='_compute_num')
    name = fields.Html(string='Name', required=True)
    event_id = fields.Many2one('document_flow.event', string='Event', ondelete='cascade', index=True, required=True)

    @api.onchange('num')
    def _compute_num(self):
        for annex in self:
            annex.visible_num = annex.num
