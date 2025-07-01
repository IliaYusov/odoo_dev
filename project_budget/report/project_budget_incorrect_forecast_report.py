from psycopg2 import sql

from odoo import tools
from odoo import fields, models


class IncorrectForecastReport(models.Model):
    _name = 'project.budget.incorrect.forecast.report'
    _description = 'Incorrect Forecasts Analysis Report'
    _auto = False

    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    project_id = fields.Many2one('project_budget.projects', string='Project', readonly=True)
    stage_id = fields.Many2one('project_budget.project.stage', string='Stage', readonly=True)
    key_account_manager_id = fields.Many2one('hr.employee', string='Key Account Manager', readonly=True)
    project_manager_id = fields.Many2one('hr.employee', string='Project Manager', readonly=True)
    # project_supervisor_id = fields.Many2one('project_budget.project_supervisor', string='Project Supervisor',
    #                                         readonly=True)
    project_curator_id = fields.Many2one('hr.employee', string='Project Curator', readonly=True)
    responsibility_center_id = fields.Many2one('account.analytic.account', string='Project Office', readonly=True)
    customer_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    name = fields.Text(string='Name', readonly=True)
    amount_untaxed = fields.Float(string='Amount untaxed', readonly=True)
    amount_total = fields.Float(string='Amount total', readonly=True)
    planned_acceptance_flow_sum = fields.Float(string='Planned acceptance sum', readonly=True)
    planned_cash_flow_sum = fields.Float(string='Planned cash sum', readonly=True)

    def init(self):
        query = """
SELECT
    row_number() OVER () as id,
    company_id,
    project_id,
    stage_id,
    responsibility_center_id,
    key_account_manager_id,
    project_manager_id,
    project_curator_id,
    --project_supervisor_id,
    partner_id AS customer_id,
    name,
    amount_untaxed,
    amount_total,
    planned_acceptance_flow_sum,
    planned_cash_flow_sum
FROM
(
    SELECT
        p.company_id,
        p.id AS project_id,        
        p.stage_id,
        p.responsibility_center_id,        
        p.key_account_manager_id,
        p.project_manager_id,
        p.project_curator_id,
        --p.project_supervisor_id,
        p.partner_id,
        p.essence_project AS name,
        p.amount_untaxed AS amount_untaxed,
        p.amount_total AS amount_total,
        pa.planned_acceptance_flow_sum AS planned_acceptance_flow_sum,
        pc.planned_cash_flow_sum AS planned_cash_flow_sum
    FROM project_budget_projects p
    INNER JOIN project_budget_project_stage st ON st.id = p.stage_id AND COALESCE(st.fold, false) = false
    INNER JOIN account_analytic_account po ON po.id = p.responsibility_center_id
    LEFT JOIN
    (
        SELECT projects_id, SUM(sum_cash_without_vat) AS planned_acceptance_flow_sum
        FROM project_budget_planned_acceptance_flow
        GROUP BY projects_id
    ) pa ON pa.projects_id = p.id
    LEFT JOIN
    (
        SELECT projects_id, SUM(sum_cash) AS planned_cash_flow_sum
        FROM project_budget_planned_cash_flow
        GROUP BY projects_id
    ) pc ON pc.projects_id = p.id
    WHERE p.budget_state = 'work' AND p.active = true AND step_status = 'project' AND (abs(p.amount_untaxed - pa.planned_acceptance_flow_sum) > 1 OR abs(p.amount_total - pc.planned_cash_flow_sum) > 1)
) p
GROUP BY
    company_id,
    project_id,
    stage_id,
    responsibility_center_id,
    key_account_manager_id,
    project_manager_id,
    project_curator_id,
    --project_supervisor_id,
    partner_id,
    name,
    amount_untaxed,
    amount_total,
    planned_acceptance_flow_sum,
    planned_cash_flow_sum
"""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            sql.SQL("""CREATE or REPLACE VIEW {} as ({})""").format(
                sql.Identifier(self._table),
                sql.SQL(query)
            ))
