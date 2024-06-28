from odoo import fields, models


class ProjectRole(models.Model):
    _name = 'project_budget.project.role'
    _description = 'Project Role'
    _order = 'sequence, id'

    active = fields.Boolean('Active', default=True)
    name = fields.Char(string='Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    is_required = fields.Boolean(string='Is Required', default=False,
                                 help='If enabled, this role will be required for project.')
    is_unique = fields.Boolean(string='Is Unique', default=False,
                               help='If enabled, this role will be unique for project.')
    company_id = fields.Many2one('res.company', string='Company')
