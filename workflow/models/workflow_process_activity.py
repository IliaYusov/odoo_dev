from datetime import datetime, date, time, timedelta
from odoo import api, Command, fields, models, _
from odoo.addons.resource.models.resource import float_to_time
from odoo.exceptions import ValidationError, UserError
from odoo.tools.safe_eval import safe_eval
from .workflow_activity import DEFAULT_PYTHON_CODE

import logging

_logger = logging.getLogger(__name__)

ACTIVITY_STATES = [
    ('in_progress', _('In Progress')),
    ('completed', _('Completed')),
    ('canceled', _('Canceled'))
]


class WorkflowProcessActivity(models.Model):
    _name = 'workflow.process.activity'
    _description = 'Workflow Process Activity'
    _order = 'sequence'

    workflow_process_id = fields.Many2one('workflow.process', string='Workflow Process', copy=True, index=True,
                                          ondelete='cascade', required=True)
    workflow_id = fields.Many2one(related='workflow_process_id.workflow_id', string='Workflow', copy=False,
                                  readonly=True)
    res_ref = fields.Reference(related='workflow_process_id.res_ref', copy=False, readonly=True)
    res_model = fields.Char(related='workflow_process_id.res_model', copy=False, readonly=True)
    res_id = fields.Integer(related='workflow_process_id.res_id', copy=False, readonly=True)
    activity_id = fields.Many2one('workflow.activity', string='Activity', copy=True, index=True, ondelete='restrict')
    activity_name = fields.Char(related='activity_id.name', copy=False, readonly=True)
    type = fields.Selection(related='activity_id.type', string='Type', copy=True, readonly=True)
    flow_start = fields.Boolean(related='activity_id.flow_start', string='Flow Start', copy=False, readonly=True,
                                store=True)
    flow_stop = fields.Boolean(related='activity_id.flow_stop', string='Flow Stop', copy=False, readonly=True,
                               store=True)
    sequence = fields.Integer(copy=True, default=0, index=True)
    active = fields.Boolean(default=True, index=True)
    state = fields.Selection(ACTIVITY_STATES, string='State', copy=False, readonly=True)
    date_start = fields.Datetime(string='Date Start', copy=False, readonly=True)
    date_end = fields.Datetime(string='Date End', copy=False, readonly=True)
    duration = fields.Float(string='Duration', compute='_compute_duration', copy=False)

    @api.depends('date_start', 'date_end')
    def _compute_duration(self):
        for activity in self:
            duration = (activity.date_end - activity.date_start).total_seconds() if activity.date_end else False
            activity.duration = duration / timedelta(hours=1).total_seconds() if duration else False

    def process(self, signal=None):
        self.ensure_one()
        if signal is None:
            signal = {}

        result = True
        if self.flow_start:
            self.write({'state': 'completed'})
            self.workflow_process_id.write({'state': 'in_progress'})
        elif self.flow_stop:
            self.write({'state': 'completed'})
            self.workflow_process_id.write({'state': 'completed'})
        else:
            result = self._execute()

        trigger_activity = []
        if self.state == 'completed' and (not signal.get('result', False) or signal[
                'result'] == 'accepted') and self.activity_id.out_transition_ids:
            for tr in self.activity_id.out_transition_ids:
                check_condition = self._run_python_code(tr.condition, signal)
                if check_condition:
                    process_activity = self.workflow_process_id.activity_ids.filtered(
                        lambda act: act.activity_id.id == tr.activity_to_id.id)[:1]
                    if process_activity:
                        trigger_activity.append(process_activity)

        if trigger_activity:
            for activity in trigger_activity:
                activity.process(signal)
        else:
            if signal.get('result', False) and signal['result'] == 'declined':
                self.workflow_process_id.write({'state': 'break'})

        return result

    def process_task_result(self, signal=None):
        if signal is None:
            signal = {}

        if not signal.get('timestamp', False):
            signal['timestamp'] = fields.Datetime.now()

        self.write({'state': 'completed', 'date_end': signal.get('timestamp')})
        self.process(signal)
        if signal.get('feedback', False):
            self.res_ref.message_post(body=signal.get('feedback'), message_type='comment', subtype_xmlid='mail.mt_note',
                                      attachment_ids=signal.get('attachment_ids', []))

    # ------------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------------

    def _execute(self, signal=None):
        result = True
        if not self.state:
            self.write({'state': 'in_progress', 'date_start': fields.datetime.now()})
            func = getattr(self, '_run_%s' % self.activity_id.type)
            result = func()
            if result:
                if self.activity_id.type == 'task':
                    self._issue_rights(
                        result.user_ids if not result.group_executors_id else result.group_executors_id)
                    self._put_activity_to_history(result)
                else:
                    self.write({'state': 'completed', 'date_end': fields.datetime.now()})
                    self._put_activity_to_history()
                self.workflow_process_id.write({'last_activity_id': self.id})
        return result

    # TODO: как православно передать результат обработки задачи (согласовали/отклонили)? Нужен ли сигнал?
    def _run_python_code(self, expression, signal=None):
        expression = expression.strip()
        if not expression or expression == DEFAULT_PYTHON_CODE.strip() or expression == 'True':
            result = True
        elif expression == 'False':
            result = False
        else:
            locals_dict = {
                'env': self.env,
                'model': self.env[self.workflow_process_id.res_model],
                'record': self.env[self.workflow_process_id.res_model].browse(self.workflow_process_id.res_id),
                'signal': signal,
                'UserError': UserError,
                'datetime': datetime,
                'time': time,
                'date': date,
                'timedelta': timedelta,
                'Command': Command
            }
            try:
                safe_eval(expression, locals_dict, mode='exec', nocopy=True)
                result = locals_dict.get('result', False)
            except Warning as ex:
                raise ex
            except SyntaxError as ex:
                raise UserError(_('Wrong python code defined.\n\nError: %s\nLine: %s, Column: %s\n\n%s' % (
                    ex.args[0], ex.args[1][1], ex.args[1][2], ex.args[1][3])))
        return result

    def _run_task(self):
        period_hours = float_to_time(self.activity_id.period_hours)
        task_data = dict(
            type_id=self.activity_id.task_type_id.id,
            name=self.activity_name,
            description=self.env.context.get('description', False) or self.res_ref.description,
            parent_ref_type=self.workflow_process_id.res_model,
            parent_ref_id=self.workflow_process_id.res_id,
            date_deadline=fields.Datetime.now() + timedelta(days=self.activity_id.period_days, hours=period_hours.hour,
                                                            minutes=period_hours.minute),
            activity_id=self.id
        )
        task_data = {**task_data, **self._compute_task_assignees()}
        user = self._compute_author()
        result = self.env['task.task'].with_user(user).sudo().with_context(mail_notify_author=True).create(task_data)
        return result

    def _compute_task_assignees(self):
        result = {}
        if self.activity_id.type == 'task':
            if self.activity_id.user_ids:
                result['user_ids'] = self.activity_id.user_ids.ids
                result['company_ids'] = [Command.link(c_id) for c_id in
                                         set(user.company_id.id for user in self.activity_id.user_ids)]
            elif self.activity_id.group_executors_id:
                result['group_executors_id'] = self.activity_id.group_executors_id.id
                result['company_ids'] = [Command.link(self.activity_id.group_executors_id.company_id.id)]
            elif self.activity_id.auto_substitution_id:
                executor = self._run_python_code(self.activity_id.auto_substitution_id.expression)
                if not executor:
                    raise ValueError(_("Could not be determined '%s'. Check the route or settings.",
                                       self.activity_id.auto_substitution.name))
                result['user_ids'] = [Command.link(executor.id)]
                result['company_ids'] = [Command.link(executor.company_id.id)]
        return result

    def _compute_author(self):
        result = self.res_ref.create_uid
        if self.res_ref._fields.get('author_id', False):
            if type(self.res_ref.author_id) == 'res.users':
                result = self.res_ref.author_id
            elif type(self.res_ref.author_id) == 'hr.employee':
                result = self.res_ref.author_id.user_id
        return result

    def _put_activity_to_history(self, task=False):
        return self.env['workflow.process.activity.history'].create({
            'activity_id': self.id,
            'task_id': task.id if task else False
        })

    def _issue_rights(self, user_ids):
        new_users = []
        if type(user_ids).__name__ == 'res.users':
            new_users = set(user_ids.ids) - set(self.res_ref.access_ids.user_id.ids)
        elif type(user_ids).__name__ == 'workflow.group.executors':
            new_users = set(user_ids.ids) - set(self.res_ref.access_ids.group_executors_id.ids)

        vals = [{
            'res_model': self.res_model,
            'res_id': self.res_id,
            'user_ref': '%s,%d' % (type(user_ids).__name__, usr)
        } for usr in list(new_users)]

        result = self.env['workflow.parent.access'].create(vals)
        return result
