from odoo import api, fields, models


class Team(models.Model):
    _name = 'helpdesk.team'
    _description = 'Helpdesk Team'

    name = fields.Char('Name')
    team_lead_id = fields.Many2one('res.users', string='Team Leader',
                                   domain=lambda self: [
                                       ('groups_id', 'in', self.env.ref('helpdesk.group_team_leader').id)
                                   ])
    member_ids = fields.Many2many('res.users', string='Members')
