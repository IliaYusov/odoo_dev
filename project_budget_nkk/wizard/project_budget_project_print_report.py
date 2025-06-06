from odoo import fields, models, _


class ProjectBudgetProjectPrintReport(models.TransientModel):
    _inherit = 'project_budget.projects.report.wizard'

    def _get_available_type_report(self):
        type_report = super(ProjectBudgetProjectPrintReport, self)._get_available_type_report()
        if self.env.user.has_group('project_budget_nkk.project_budget_group_print_report_sa'):
            type_report.append(('pds_weekly_plan_fact_sa', _('PDS weekly plan fact SA')))
        if 'Ландата' in (c.name for c in self.env.companies):
            type_report.append(('contracting_revenue_cash', _('Contracting Revenue Cash')))
            type_report.append(('contracting_revenue_cash_v2', _('Contracting Revenue Cash V2')))
        return type_report

    type_report = fields.Selection(selection=_get_available_type_report)
