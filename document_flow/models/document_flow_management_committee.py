from odoo import models, fields


class ManagementCommittee(models.Model):
    _name = 'document_flow.management_committee'
    _description = 'Management Committee'

    name = fields.Char(string='Name', required=True)
    member_ids = fields.Many2many('res.users', relation='management_committee_user_rel',
                                  column1='management_committee_id', column2='member_id', string='Members')
