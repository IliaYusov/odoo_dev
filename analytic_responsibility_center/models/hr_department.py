from odoo import fields, models


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    def _get_responsibility_center_id_domain(self):
        return "[('plan_id', 'child_of', %s), '|', ('company_id', '=', False), ('company_id', '=', company_id)]" \
            % self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id

    responsibility_center_id = fields.Many2one('account.analytic.account', string='Responsibility Center', copy=False,
                                               domain=_get_responsibility_center_id_domain, tracking=True)
