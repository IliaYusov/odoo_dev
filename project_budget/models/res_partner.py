from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    project_ids = fields.One2many('project_budget.projects', 'partner_id', string='Projects')
    project_count = fields.Integer(compute='_compute_project_count')
    percent_fot = fields.Float(string="FOT percent", default=0)
    is_percent_fot_manual = fields.Boolean(string="Manual FOT percent", default=False)
    different_project_offices_in_steps = fields.Boolean(string='different project offices in steps', default=False)

    @api.depends('project_ids')
    def _compute_project_count(self):
        domain = [
            ('budget_state', '=', 'work'),
            ('partner_id', 'in', self.ids)
        ]
        res = self.env['project_budget.projects'].read_group(
            domain=domain, fields=['partner_id'], groupby=['partner_id']
        )
        projects = {x['partner_id'][0]: x['partner_id_count'] for x in res}
        for rec in self:
            rec.project_count = projects.get(rec.id, 0)
