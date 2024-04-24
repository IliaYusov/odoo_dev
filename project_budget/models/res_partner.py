from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    project_ids = fields.One2many('project_budget.projects', 'partner_id', string='Projects')
    project_count = fields.Integer(compute='_compute_project_count')

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

    def name_get(self):
        res = []
        for record in self:
            name = '%s%s' % ((record.vat + ' - ') if record.vat else '', record.name)
            res += [(record.id, name)]
        return res
