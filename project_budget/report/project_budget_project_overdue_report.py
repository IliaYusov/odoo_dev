from psycopg2 import sql

from odoo import tools
from odoo import fields, models


class ProjectOverdueReport(models.Model):
    _name = 'project.budget.project.overdue.report'
    _description = 'Project Overdue Analysis Report'
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
    step_id = fields.Many2one('project_budget.projects', string='Step', readonly=True)
    customer_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    name = fields.Text(string='Name', readonly=True)
    overdue = fields.Char(string='Overdue Reason', readonly=True)
    overdue_in_7_days = fields.Char(string='Overdue in 7 Days Reason', readonly=True)

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
    step_id,
    partner_id AS customer_id,
    name,
    STRING_AGG(overdue, ', ') AS overdue,
    STRING_AGG(overdue_in_7_days, ', ') AS overdue_in_7_days
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
        NULL AS step_id,
        p.partner_id,
        p.essence_project AS name,	
        CASE
            WHEN end_presale_project_month < CURRENT_DATE THEN 'Дата контрактования'
            WHEN end_sale_project_month < CURRENT_DATE AND p.company_id <> 10 THEN 'Дата последней отгрузки'
        END AS overdue,
        CASE
            WHEN end_presale_project_month >= CURRENT_DATE AND end_presale_project_month < CURRENT_DATE + INTERVAL '7' DAY THEN 'Дата контрактования'
            WHEN end_sale_project_month >= CURRENT_DATE AND end_sale_project_month < CURRENT_DATE + INTERVAL '7' DAY AND p.company_id <> 10 THEN 'Дата последней отгрузки'
        END AS overdue_in_7_days
    FROM project_budget_projects p
    INNER JOIN project_budget_project_stage st ON st.id = p.stage_id AND COALESCE(st.fold, false) = false
    AND st.code <> '100'
    INNER JOIN account_analytic_account po ON po.id = p.responsibility_center_id
    WHERE p.budget_state = 'work' AND p.active = true AND step_status = 'project'
    AND (p.end_presale_project_month < CURRENT_DATE + INTERVAL '7' DAY OR p.end_sale_project_month < CURRENT_DATE + INTERVAL '7' DAY)
    UNION
    SELECT
        p.company_id,
        p.id AS project_id,        
        p.stage_id,
        p.responsibility_center_id,        
        p.key_account_manager_id,
        p.project_manager_id,
        p.project_curator_id,
        --p.project_supervisor_id,
        ps.id AS step_id,
        p.partner_id,
        p.essence_project AS name,	
        CASE
            WHEN ps.end_presale_project_month < CURRENT_DATE THEN 'Дата контрактования'
            WHEN ps.end_sale_project_month < CURRENT_DATE AND p.company_id <> 10 THEN 'Дата последней отгрузки'
        END AS overdue,
        CASE
            WHEN ps.end_presale_project_month >= CURRENT_DATE AND ps.end_presale_project_month < CURRENT_DATE + INTERVAL '7' DAY THEN 'Дата контрактования'
            WHEN ps.end_sale_project_month >= CURRENT_DATE AND ps.end_sale_project_month < CURRENT_DATE + INTERVAL '7' DAY AND p.company_id <> 10 THEN 'Дата последней отгрузки'
        END AS overdue_in_7_days
    FROM project_budget_projects ps
    INNER JOIN project_budget_projects p ON p.id = ps.step_project_parent_id AND p.budget_state = 'work' AND p.active = true
    AND p.project_have_steps = true
    INNER JOIN project_budget_project_stage st ON st.id = ps.stage_id AND COALESCE(st.fold, false) = false
    AND st.code <> '100'
    WHERE ps.end_presale_project_month < CURRENT_DATE + INTERVAL '7' DAY OR ps.end_sale_project_month < CURRENT_DATE + INTERVAL '7' DAY
    UNION
    SELECT
        p.company_id,
        p.id AS project_id,        
        p.stage_id,
        p.responsibility_center_id,        
        p.key_account_manager_id,
        p.project_manager_id,
        p.project_curator_id,
        --p.project_supervisor_id,
        pa.step_project_child_id AS step_id,
        p.partner_id,
        p.essence_project AS name,
        CASE
            WHEN pa.date_cash < CURRENT_DATE THEN 'Плановое актирование'
        END AS overdue,
        CASE
            WHEN pa.date_cash >= CURRENT_DATE AND pa.date_cash < CURRENT_DATE + INTERVAL '7' DAY THEN 'Плановое актирование'
        END AS overdue_in_7_days
    FROM project_budget_planned_acceptance_flow pa
    INNER JOIN project_budget_projects p ON p.id = pa.projects_id AND p.budget_state = 'work' AND p.active = true
    INNER JOIN project_budget_project_stage st ON st.id = p.stage_id AND COALESCE(st.fold, false) = false
    INNER JOIN res_currency c ON c.id = p.currency_id	
    LEFT JOIN
    (
        SELECT planned_acceptance_flow_id, SUM(sum_cash_without_vat) AS sum_distr_cash
        FROM project_budget_distribution_acceptance
        GROUP BY planned_acceptance_flow_id
    ) da ON da.planned_acceptance_flow_id = pa.id
    WHERE pa.date_cash < CURRENT_DATE + INTERVAL '7' DAY
    AND ROUND(pa.sum_cash_without_vat, c.decimal_places) - ROUND(COALESCE(da.sum_distr_cash, 0), c.decimal_places) > 0
    UNION
    SELECT
        p.company_id,
        p.id AS project_id,        
        p.stage_id,
        p.responsibility_center_id,        
        p.key_account_manager_id,
        p.project_manager_id,
        p.project_curator_id,
        --p.project_supervisor_id,
        pc.step_project_child_id AS step_id,
        p.partner_id,
        p.essence_project AS name,
        CASE
            WHEN pc.date_cash < CURRENT_DATE THEN 'ПДС'
        END AS overdue,
        CASE
            WHEN pc.date_cash >= CURRENT_DATE AND pc.date_cash < CURRENT_DATE + INTERVAL '7' DAY THEN 'ПДС'
        END AS overdue_in_7_days
    FROM project_budget_planned_cash_flow pc
    INNER JOIN project_budget_projects p ON p.id = pc.projects_id AND p.budget_state = 'work' AND p.active = true
    INNER JOIN project_budget_project_stage st ON st.id = p.stage_id AND COALESCE(st.fold, false) = false
    INNER JOIN res_currency c ON c.id = p.currency_id
    LEFT JOIN
    (
        SELECT planned_cash_flow_id, SUM(sum_cash) AS sum_distr_cash
        FROM project_budget_distribution_cash
        GROUP BY planned_cash_flow_id
    ) dc ON dc.planned_cash_flow_id = pc.id
    WHERE pc.date_cash < CURRENT_DATE + INTERVAL '7' DAY
    AND ROUND(pc.sum_cash, c.decimal_places) - ROUND(COALESCE(dc.sum_distr_cash, 0), c.decimal_places) > 0
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
    step_id,
    partner_id,
    name
"""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            sql.SQL("""CREATE or REPLACE VIEW {} as ({})""").format(
                sql.Identifier(self._table),
                sql.SQL(query)
            ))
