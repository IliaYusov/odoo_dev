from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.account'

    receive_tasks_for_approve_project = fields.Boolean(string='Recieve Tasks For Approve Project As Supervisor',
                                                       default=False)
    isRukovoditel_required_in_project = fields.Boolean(string='Mark Project Manager Required In Project', default=False)
    print_rukovoditel_in_kb = fields.Boolean(string='Printed Project Manager instead KAM in KB Report',
                                             default=False)
    print_name_mc = fields.Char(string='Printed Name For MC Report', copy=False)
