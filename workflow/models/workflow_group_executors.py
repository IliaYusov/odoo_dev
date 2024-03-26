from odoo import fields, models


class GroupExecutors(models.Model):
    _name = 'workflow.group.executors'
    _description = 'Group Executors'
    _check_company_auto = True

    name = fields.Char(string='Name', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    member_ids = fields.Many2many('res.users', relation='workflow_group_executors_user_rel',
                                  column1='group_executors_id', column2='user_id', string='Members',
                                  domain="['|', ('company_id', '=', False), ('company_ids', 'in', company_id)]")
    active = fields.Boolean(default=True, index=True)
