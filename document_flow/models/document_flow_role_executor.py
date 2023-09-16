from odoo import models, fields


class ExecutingRole(models.Model):
    _name = 'document_flow.role_executor'
    _description = 'Role Executors'

    name = fields.Char(string='Name', required=True, translate=True)
    member_ids = fields.Many2many('res.users', relation='executor_role_user_rel',
                                  column1='executor_role_id', column2='member_id', string='Members')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(default=True, index=True)
