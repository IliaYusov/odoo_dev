from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import test_python_expr

ACTIVITY_TYPE = [
    ('task', _('Task')),
    ('sub_flow', _('Sub-flow')),
    ('srv_action', _('Server Action')),
    ('win_action', _('Window Action')),
    ('python_code', _('Python Code'))
]

JOIN_MODE = [
    ('XOR', 'Xor'),
    ('AND', 'And')
]

DEFAULT_PYTHON_CODE = """# Available variables:
#  - env: Odoo Environment on which the action is triggered
#  - model: Odoo Model of the record on which the action is triggered; is a void recordset
#  - record: record on which the action is triggered; may be void
#  - records: recordset of all records on which the action is triggered in multi-mode; may be void
#  - time, datetime, dateutil, timezone: useful Python libraries
#  - float_compare: Odoo function to compare floats based on specific precisions
#  - log: log(message, level='info'): logging function to record debug information in ir.logging table
#  - UserError: Warning Exception to use with raise
#  - Command: x2Many commands namespace
# To return an action, assign: action = {...}\n\n\n\n"""


class WorkflowActivity(models.Model):
    _name = 'workflow.activity'
    _description = 'Workflow Activity'
    _order = 'sequence'

    workflow_id = fields.Many2one('workflow.workflow', string='Workflow', copy=True, index=True, ondelete='cascade',
                                  required=True)
    model_id = fields.Many2one(related='workflow_id.model_id', readonly=True)
    company_id = fields.Many2one(related='workflow_id.company_id', readonly=True)

    name = fields.Char(string='Name', copy=True, required=True)
    active = fields.Boolean(copy=False, default=True, index=True)
    sequence = fields.Integer(copy=True, default=0, index=True)
    visible_sequence = fields.Integer(string='№', compute='_compute_sequence')
    description = fields.Html(string='Description', copy=False)
    type = fields.Selection(ACTIVITY_TYPE, string='Activity Type', copy=True, default='task')
    join_mode = fields.Selection(JOIN_MODE, string='Join Mode', copy=True, default='XOR', required=True)
    flow_start = fields.Boolean(string='Flow Start', copy=True, default=False)
    flow_stop = fields.Boolean(string='Flow Stop', copy=True, default=False)

    code = fields.Text(string='Python Code', copy=True, default=DEFAULT_PYTHON_CODE)
    server_action_id = fields.Many2one('ir.actions.server', string='Server Action', copy=True)
    window_act_id = fields.Many2one('ir.actions.act_window', string='Window Action', copy=True)
    sub_flow_id = fields.Many2one('workflow.workflow', string='Sub-flow', copy=True,
                                  domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    task_type_id = fields.Many2one('task.type', string='Task Type', copy=True)
    period_days = fields.Integer(string='Days', copy=True, default=1)
    period_hours = fields.Float(string='Hours', copy=True, default=0)
    user_ids = fields.Many2many('res.users', relation='workflow_activity_user_rel', column1='activity_id',
                                column2='user_id', string='Assignees', copy=True, context={'active_test': False},
                                domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    group_executors_id = fields.Many2one('workflow.group.executors', string='Group Executors', copy=True,
                                         domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    auto_substitution_id = fields.Many2one('workflow.auto.substitution', string='Auto-substitution', copy=True)

    in_transition_ids = fields.One2many('workflow.transition', 'activity_to_id', string='Incoming Transitions',
                                        copy=False)
    out_transition_ids = fields.One2many('workflow.transition', 'activity_from_id', string='Outgoing Transitions',
                                         copy=False)

    _sql_constraints = [
        ('activity_name_uniq',
         'UNIQUE (workflow_id, name)',
         'Activity name must be uniq for workflow')
    ]

    @api.constrains('code')
    def _verify_condition(self):
        for activity in self.filtered('code'):
            msg = test_python_expr(expr=activity.code.strip(), mode='exec')
            if msg:
                raise ValidationError(msg)

    @api.depends('sequence')
    def _compute_sequence(self):
        for activity in self:
            activity.visible_sequence = activity.sequence
