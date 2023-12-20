from odoo import _, models, fields, api
from datetime import datetime, date, timedelta


class Event(models.Model):
    _name = 'document_flow.event'
    _description = 'Event'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _order = 'date_start desc, id desc'

    name = fields.Char(string='Name', copy=True, required=True, tracking=True)
    company_ids = fields.Many2many('res.company', string='Companies', required=True,
                                   default=lambda self: self.env.company)
    description = fields.Html(string='Description')
    date_start = fields.Datetime(string='Start Date', copy=True, index=True, required=True,
                                 default=fields.Date.context_today)
    date_end = fields.Datetime(string='End Date', copy=True, index=True)
    location = fields.Char(string='Location', copy=False)

    organizer_id = fields.Many2one('res.users', string='Organizer', copy=False, required=True,
                                   default=lambda self: self.env.user,
                                   domain="['|', ('company_id', '=', False), ('company_id', 'in', company_ids)]")
    agreed_id = fields.Many2one('res.users', string='Agreed', copy=False,
                                domain="['|', ('company_id', '=', False), ('company_id', 'in', company_ids)]")
    member_ids = fields.Many2many('res.users', relation='event_user_rel', column1='event_id', column2='user_id',
                                  string='Members', copy=True,
                                  domain="['|', ('company_id', '=', False), ('company_id', 'in', company_ids)]")
    management_committee_id = fields.Many2one('document_flow.management_committee', string='Management Committee')
    question_ids = fields.One2many('document_flow.event.question', 'event_id', string='Questions')
    decision_ids = fields.One2many('document_flow.event.decision', 'event_id', string='Decisions', copy=True)
    annex_ids = fields.One2many('document_flow.event.annex', 'event_id', string='Annexes')

    state = fields.Selection([
        ('on_registration', 'On Registration'),
        ('on_approval', 'On Approval'),
        ('approved', 'Approved'),
        ('completed', 'Completed')
    ], string='Status', copy=False, index=True, tracking=True, required=True, readonly=True, default='on_registration')

    attachment_count = fields.Integer(compute='_compute_attachment_count', string='Attachments')
    tasks_count = fields.Integer(compute='_compute_tasks_count', string='Tasks')

    process_id = fields.Many2one('document_flow.process', string='Process', compute='_compute_process_id')
    process_state = fields.Selection(string='State', related='process_id.state', readonly=True)

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        default['name'] = _('Copy_%s') % self.name
        return super(Event, self).copy(default=default)

    @api.onchange('management_committee_id')
    def _onchange_management_committee(self):
        if self.management_committee_id:
            self.member_ids = self.member_ids | self.management_committee_id.member_ids

    def _compute_attachment_count(self):
        for event in self:
            event.attachment_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', type(event).__name__),
                ('res_id', '=', event.id)
            ])

    def _compute_process_id(self):
        for event in self:
            event.process_id = self.env['document_flow.processing'].search([
                ('parent_ref', '=', '%s,%d' % (type(event).__name__, event.id))
            ]).process_ids[-1:]

    def action_send_for_approving(self):
        self.ensure_one()

        processing = self.env['document_flow.processing'].search([
            ('parent_ref', '=', '%s,%d' % (self._name, self.id))
        ])
        if not processing:
            self._archive_previous_decisions()

            processing = self.env['document_flow.processing'].create({
                'parent_ref': '%s,%d' % (self._name, self.id),
                'parent_ref_type': self._name,
                'parent_ref_id': self.id
            })

            if self.agreed_id:
                action_agreement = self.env['document_flow.action'].create({
                    'name': _('Agree on a protocol of event'),
                    'type': 'agreement',
                    'sequence': 0,
                    'description': self.description,
                    'parent_ref_type': type(processing).__name__,
                    'parent_ref_id': processing.id,
                    'type_sequence': 'together_with_the_previous'
                })
                self.env['document_flow.action.executor'].create({
                    'action_id': action_agreement.id,
                    'executor_ref': '%s,%s' % (type(self.agreed_id).__name__, self.agreed_id.id),
                    'date_deadline': datetime.now()
                })

            action_review = self.env['document_flow.action'].create({
                'name': _('Review a protocol of event'),
                'type': 'review',
                'sequence': 1,
                'description': self.description,
                'parent_ref_type': type(processing).__name__,
                'parent_ref_id': processing.id,
                'type_sequence': 'after_the_previous'
            })
            members = list(set(self.member_ids) | set(self.management_committee_id.member_ids))
            for executor in members:
                self.env['document_flow.action.executor'].create({
                    'action_id': action_review.id,
                    'executor_ref': '%s,%s' % (type(executor).__name__, executor.id),
                    'period': 1
                })

            action_complex_execution = self.env['document_flow.action'].create({
                'name': _('Execution decisions of event'),
                'type': 'complex',
                'sequence': 1,
                'description': self.description,
                'parent_ref_type': type(processing).__name__,
                'parent_ref_id': processing.id,
                'type_sequence': 'together_with_the_previous'
            })

            reviews = self.decision_ids.filtered(lambda d: d.task_type == 'review' and d.date_deadline and d.executor_ids)
            if any(reviews):
                for decision in reviews:
                    action_review = self.env['document_flow.action'].create({
                        'name': _('Review with decision of event "%s"', self.name),
                        'type': 'review',
                        'task_sequence': 'one_for_all',
                        'sequence': 0,
                        'description': decision.name,
                        'parent_id': action_complex_execution.id
                    })
                    for executor in decision.executor_ids:
                        self.env['document_flow.action.executor'].create({
                            'action_id': action_review.id,
                            'executor_ref': '%s,%s' % (type(executor).__name__, executor.id),
                            'date_deadline': decision.date_deadline
                        })
                    decision.write({'action_id': action_review.id})

            executions = self.decision_ids.filtered(
                lambda d: d.task_type == 'execution' and d.date_deadline and (d.executor_ids or d.responsible_id))
            if any(executions):
                for decision in executions:
                    executors = list([executor.company_id.id for executor in decision.executor_ids])
                    if decision.responsible_id:
                        executors.append(decision.responsible_id.company_id.id)
                    action_execution_data = dict(
                        name=_('Execute decision of event "%s"', self.name),
                        type='execution',
                        task_sequence='one_for_all',
                        sequence=0,
                        description=decision.name,
                        parent_id=action_complex_execution.id
                    )
                    if decision.responsible_id and decision.executor_ids:
                        action_execution_data['controller_ref'] = '%s,%d' % (
                            type(decision.responsible_id).__name__, decision.responsible_id.id)
                    action_execution = self.env['document_flow.action'].create(action_execution_data)
                    if decision.executor_ids:
                        for executor in decision.executor_ids:
                            self.env['document_flow.action.executor'].create({
                                'action_id': action_execution.id,
                                'executor_ref': '%s,%s' % (type(executor).__name__, executor.id),
                                'date_deadline': decision.date_deadline
                            })
                    elif decision.responsible_id:
                        self.env['document_flow.action.executor'].create({
                            'action_id': action_execution.id,
                            'executor_ref': '%s,%s' % (
                                type(decision.responsible_id).__name__, decision.responsible_id.id),
                            'date_deadline': decision.date_deadline
                        })
                    decision.write({'action_id': action_execution.id})
            self.env.cr.commit()
            processing.action_start_processing()
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

    def _archive_previous_decisions(self):
        if self.management_committee_id:
            events = self.env['document_flow.event'].sudo().search([
                ('id', '!=', self.id),
                ('management_committee_id', '=', self.management_committee_id.id)
            ])
            tasks = events.filtered(lambda e: e.process_id).process_id.active_task_ids.filtered(lambda t: not t.is_closed)
            for task in tasks:
                task.sudo().write({'active': False})

    def action_renumber_decisions(self):
        for event in self:
            num = 1
            for decision in event.decision_ids:
                decision.num = num
                num += 1

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

    def action_open_processing(self):
        self.ensure_one()
        processing = self.env['document_flow.processing'].search([
            ('parent_ref', '=', '%s,%d' % (self._name, self.id))
        ])
        return {
            'view_mode': 'form',
            'res_model': 'document_flow.processing',
            'type': 'ir.actions.act_window',
            'res_id': processing.id,
            'context': {
                'default_parent_ref': '%s,%d' % (self._name, self.id),
                'default_parent_ref_type': self._name,
                'default_parent_ref_id': self.id
            }
        }


class EventQuestion(models.Model):
    _name = 'document_flow.event.question'
    _description = 'Event Question'

    name = fields.Html(string='Agenda', required=True)
    time_start = fields.Float(string="From")
    time_end = fields.Float(string="To")
    event_id = fields.Many2one('document_flow.event', string='Event', ondelete='cascade', index=True, required=True)
    speaker_ids = fields.Many2many('res.users', relation='event_question_user_rel', column1='question_id',
                                   column2='speaker_id', string='Speakers',
                                   domain="['|', ('company_id', '=', False), ('company_id', 'in', parent.company_ids)]")


class EventDecision(models.Model):
    _name = 'document_flow.event.decision'
    _description = 'Event Decision'
    _order = 'num, id'

    num = fields.Integer(string='№', copy=True, required=True, default=1)
    visible_num = fields.Integer(string='№', compute='_compute_num', copy=False)
    name = fields.Html(string='Decided', required=True, copy=True)
    event_id = fields.Many2one('document_flow.event', string='Event', ondelete='cascade', index=True, required=True)
    task_type = fields.Selection([
        ('review', 'Review'),
        ('execution', 'Execution')
    ], required=True, default='review', string='Type')
    responsible_id = fields.Many2one('res.users', string='Responsible',
                                     domain="['|', ('company_id', '=', False), ('company_id', 'in', parent.company_ids)]")
    executor_ids = fields.Many2many('res.users', relation='event_decision_user_rel', column1='decision_id',
                                    column2='executor_id', string='Executors',
                                    domain="['|', ('company_id', '=', False), ('company_id', 'in', parent.company_ids)]")
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

    action_id = fields.Many2one('document_flow.action', string='Action', copy=False)

    def name_get(self):
        decisions = []
        for decision in self:
            name = '%s %s' % (decision.num, decision.name.striptags())
            decisions.append((decision.id, name))
        return decisions

    @api.depends('num')
    def _compute_num(self):
        for decision in self:
            decision.visible_num = decision.num

    @api.depends('process_id')
    def _compute_process_id(self):
        for decision in self:
            decision.process_id = False

    @api.onchange('deadline_type', 'after_decision_id', 'number_days')
    def onchange_date_deadline(self):
        if self.deadline_type == 'to_date':
            self.after_decision_id = False
            self.number_days = False
        elif self.deadline_type == 'after_decision' and self.number_days:
            self.date_deadline = self._get_decision_date_deadline(self.after_decision_id) + timedelta(
                days=self.number_days)

    @api.onchange('name')
    def _onchange_name(self):
        for decision in self:
            if decision.action_id:
                decision.action_id.write({'description': decision.name})
                if decision.action_id.process_id:
                    decision.action_id.process_id.write({'description': decision.name})

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

    @api.depends('num')
    def _compute_num(self):
        for annex in self:
            annex.visible_num = annex.num
