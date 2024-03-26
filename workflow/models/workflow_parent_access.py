from odoo import api, fields, models, _


def selection_executor_model():
    return [
        ('res.users', _('User')),
        ('workflow.group.executors', _('Group'))
    ]


class WorkflowParentAccess(models.Model):
    _name = 'workflow.parent.access'
    _description = 'Parent Access'

    @api.model
    def _selection_executor_model(self):
        return selection_executor_model()

    res_model = fields.Char(string='Resource Model', copy=False, index=True, required=True)
    res_id = fields.Integer(string='Resource ID', copy=False, index=True, required=True)
    user_ref = fields.Reference(string='User', selection='_selection_executor_model', copy=False, required=True)
    user_id = fields.Many2one('res.users', string='User', compute='_compute_user_id', copy=False, store=True)
    group_executors_id = fields.Many2one('workflow.group.executors', string='Group',
                                         compute='_compute_group_executors_id', copy=False, store=True)

    @api.depends('user_ref')
    def _compute_user_id(self):
        for rec in self:
            if type(rec.user_ref).__name__ == 'res.users':
                rec.user_id = rec.user_ref.id
            else:
                rec.user_id = False

    @api.depends('user_ref')
    def _compute_group_executors_id(self):
        for rec in self:
            if type(rec.user_ref).__name__ == 'workflow.group.executors':
                rec.group_executors_id = rec.user_ref.id
            else:
                rec.group_executors_id = False
