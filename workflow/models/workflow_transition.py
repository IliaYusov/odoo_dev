from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import test_python_expr
from .workflow_activity import DEFAULT_PYTHON_CODE

import logging

_logger = logging.getLogger(__name__)


class WorkflowTransition(models.Model):
    _name = 'workflow.transition'
    _description = 'Workflow Transition'
    _order = 'sequence'

    workflow_id = fields.Many2one('workflow.workflow', string='Workflow', copy=True, index=True, ondelete='cascade',
                                  required=True)
    name = fields.Char(string='Name', copy=True)
    sequence = fields.Integer(copy=True, default=0, index=True, required=True)
    activity_from_id = fields.Many2one('workflow.activity', string='From', copy=True, index=True, ondelete='cascade',
                                       required=True)
    activity_to_id = fields.Many2one('workflow.activity', string='To', copy=True, index=True, ondelete='cascade',
                                     required=True)
    condition = fields.Text(string='Condition', copy=True, default=DEFAULT_PYTHON_CODE,
                            help='Condition to pass thru this transition.')

    _sql_constraints = [
        ('workflow_activity_from_activity_to_uniq',
         'UNIQUE (workflow_id, activity_from_id, activity_to_id)',
         'Such transition already present in this workflow')
    ]

    def name_get(self):
        res = []
        for record in self:
            name = '%s -> %s' % (record.activity_from_id.name, record.activity_to_id.name)
            if record.name:
                name = '%s [%s]' % (name, record.name)

            if self.env.context.get('name_only', False) and record.name:
                name = record.name

            res += [(record.id, name)]
        return res

    @api.constrains('condition')
    def _verify_condition(self):
        for transition in self.filtered('condition'):
            msg = test_python_expr(expr=transition.condition.strip(), mode='exec')
            if msg:
                raise ValidationError(msg)
