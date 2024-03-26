from odoo import api, fields, models, _


def selection_executor_model():
    return [
        ('res.users', _('User')),
        ('workflow.group.executors', _('Group'))
    ]


class ContractType(models.Model):
    _inherit = 'contract.type'

    access_setting_ids = fields.One2many('contract.type.accessibility.setting', 'type_id',
                                         string='Accessibility Settings')


class ContractTypeAccessibilitySetting(models.Model):
    _name = 'contract.type.accessibility.setting'
    _description = 'Contract Type Accessibility Setting'

    @api.model
    def _selection_executor_model(self):
        return selection_executor_model()

    type_id = fields.Many2one('contract.type', string='Contract Type', copy=True, index=True, required=True,
                              ondelete='cascade')
    user_ref = fields.Reference(string='User', selection='_selection_executor_model', copy=True, required=True)
    user_id = fields.Many2one('res.users', string='User', compute='_compute_user_id', store=True)
    group_executors_id = fields.Many2one('workflow.group.executors', string='Group',
                                         compute='_compute_group_executors_id', store=True)

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
