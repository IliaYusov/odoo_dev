from psycopg2 import sql

from odoo import tools
from odoo import fields, models


class FinancialDataReport(models.Model):
    _name = 'project_budget.financial_data_report'
    _description = 'Financial Data Report'
    _auto = False

    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    project_id = fields.Many2one('project_budget.projects', string='Project', readonly=True)
    stage_id = fields.Many2one('project_budget.project.stage', string='Stage', readonly=True)
    key_account_manager_id = fields.Many2one('hr.employee', string='Key Account Manager', readonly=True)
    project_office_id = fields.Many2one('project_budget.project_office', string='Project Office', readonly=True)
    step_id = fields.Many2one('project_budget.projects', string='Step', readonly=True)
    customer_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    type = fields.Char(string='Type', readonly=True)
    probability = fields.Char(string='Probability', readonly=True)
    name = fields.Text(string='Name', readonly=True)
    date = fields.Date(string='Date', readonly=True)
    amount = fields.Monetary(string='Amount', readonly=True)
    distribution = fields.Monetary(string='Distribution', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)
    profitability = fields.Float(string='Profitability', readonly=True)
    commercial_budget_id = fields.Many2one('project_budget.commercial_budget', string='Commercial Budget', readonly=True)

    def init(self):
        query = """
SELECT
    row_number() OVER () as id,
    company_id,
    project_id,
    stage_id,
    project_office_id,
    key_account_manager_id,
    step_id,
    partner_id AS customer_id,
    name,
    type,
    date,
    amount,
    distribution,
    currency_id,
    probability,
    profitability,
    commercial_budget_id
FROM
(
    SELECT
        p.company_id,
        p.id AS project_id,        
        p.stage_id,
        p.project_office_id,        
        p.key_account_manager_id,
        NULL AS step_id,
        p.partner_id,
        p.essence_project AS name,
        p.end_presale_project_month AS date,
        p.total_amount_of_revenue_with_vat AS amount,
        p.currency_id AS currency_id,
        CASE
            WHEN p.total_amount_of_revenue != 0 THEN ((p.total_amount_of_revenue - p.cost_price) / p.total_amount_of_revenue * 100)
            ELSE 0
        END AS profitability,
        0 AS distribution,
        'contracting' AS type,
        '' AS probability,
        p.commercial_budget_id AS commercial_budget_id
    FROM project_budget_projects p
    INNER JOIN project_budget_project_stage st ON st.id = p.stage_id
    INNER JOIN project_budget_project_office po ON po.id = p.project_office_id
    WHERE step_status = 'project' AND p.project_have_steps = false AND p.total_amount_of_revenue_with_vat != 0 AND p.active = true
    UNION
    SELECT
        ps.company_id,
        p.id AS project_id,        
        ps.stage_id,
        ps.project_office_id,        
        ps.key_account_manager_id,
        ps.id AS step_id,
        ps.partner_id,
        p.essence_project AS name,
        ps.end_presale_project_month AS date,
        ps.total_amount_of_revenue_with_vat AS amount,
        ps.currency_id AS currency_id,
        CASE
            WHEN ps.total_amount_of_revenue != 0 THEN ((ps.total_amount_of_revenue - ps.cost_price) / ps.total_amount_of_revenue * 100)
            ELSE 0
        END AS profitability,
        0 AS distribution,
        'contracting' AS type,
        '' AS probability,
        ps.commercial_budget_id AS commercial_budget_id
    FROM project_budget_projects ps
    INNER JOIN project_budget_projects p ON p.id = ps.step_project_parent_id
    AND p.project_have_steps = true AND ps.step_status = 'step'
    INNER JOIN project_budget_project_stage st ON st.id = ps.stage_id
    WHERE ps.total_amount_of_revenue_with_vat != 0  AND ps.active = true
    UNION
    SELECT
        p.company_id,
        p.id AS project_id,        
        p.stage_id,
        p.project_office_id,        
        p.key_account_manager_id,
        NULL AS step_id,
        p.partner_id,
        p.essence_project AS name,
        pc.date_cash AS date,
        ROUND(pc.sum_cash, c.decimal_places) - ROUND(COALESCE(da.sum_distr_cash, 0), c.decimal_places) AS amount,
        p.currency_id AS currency_id,
        CASE
            WHEN p.total_amount_of_revenue != 0 THEN ((p.total_amount_of_revenue - p.cost_price) / p.total_amount_of_revenue * 100)
            ELSE 0
        END AS profitability,
        dcc.sum_cash AS distribution,
        'cash' AS type,
        pc.forecast AS probability,
        p.commercial_budget_id AS commercial_budget_id
    FROM project_budget_projects p
    INNER JOIN project_budget_project_stage st ON st.id = p.stage_id
    INNER JOIN project_budget_project_office po ON po.id = p.project_office_id
    INNER JOIN project_budget_planned_cash_flow pc ON pc.projects_id = p.id
    LEFT JOIN project_budget_distribution_cash dcc ON dcc.planned_cash_flow_id = pc.id
    INNER JOIN res_currency c ON c.id = p.currency_id	
    LEFT JOIN
    (
        SELECT planned_cash_flow_id, SUM(sum_cash) AS sum_distr_cash
        FROM project_budget_distribution_cash
        GROUP BY planned_cash_flow_id
    ) AS da ON da.planned_cash_flow_id = pc.id
    WHERE step_status = 'project' AND p.project_have_steps = false AND p.active = true
    AND ROUND(pc.sum_cash, c.decimal_places) - ROUND(COALESCE(da.sum_distr_cash, 0), c.decimal_places) != 0
    UNION
    SELECT
        ps.company_id,
        p.id AS project_id,        
        ps.stage_id,
        ps.project_office_id,        
        ps.key_account_manager_id,
        ps.id AS step_id,
        ps.partner_id,
        p.essence_project AS name,
        pc.date_cash AS date,
        ROUND(pc.sum_cash, c.decimal_places) - ROUND(COALESCE(da.sum_distr_cash, 0), c.decimal_places) AS amount,
        ps.currency_id AS currency_id,
        CASE
            WHEN ps.total_amount_of_revenue != 0 THEN ((ps.total_amount_of_revenue - ps.cost_price) / ps.total_amount_of_revenue * 100)
            ELSE 0
        END AS profitability,
        dcc.sum_cash AS distribution,
        'cash' AS type,
        pc.forecast AS probability,
        ps.commercial_budget_id AS commercial_budget_id
    FROM project_budget_projects ps
    INNER JOIN project_budget_projects p ON p.id = ps.step_project_parent_id
    AND p.project_have_steps = true AND ps.step_status = 'step'
    INNER JOIN project_budget_project_stage st ON st.id = ps.stage_id
    INNER JOIN project_budget_planned_cash_flow pc ON pc.step_project_child_id = ps.id
    LEFT JOIN project_budget_distribution_cash dcc ON dcc.planned_cash_flow_id = pc.id
    INNER JOIN res_currency c ON c.id = ps.currency_id	
    LEFT JOIN
    (
        SELECT planned_cash_flow_id, SUM(sum_cash) AS sum_distr_cash
        FROM project_budget_distribution_cash
        GROUP BY planned_cash_flow_id
    ) AS da ON da.planned_cash_flow_id = pc.id
    WHERE ROUND(pc.sum_cash, c.decimal_places) - ROUND(COALESCE(da.sum_distr_cash, 0), c.decimal_places) != 0 AND ps.active = true
    UNION
    SELECT
        p.company_id,
        p.id AS project_id,        
        p.stage_id,
        p.project_office_id,        
        p.key_account_manager_id,
        NULL AS step_id,
        p.partner_id,
        p.essence_project AS name,
        fc.date_cash AS date,
        fc.sum_cash AS amount,
        p.currency_id AS currency_id,
        CASE
            WHEN p.total_amount_of_revenue != 0 THEN ((p.total_amount_of_revenue - p.cost_price) / p.total_amount_of_revenue * 100)
            ELSE 0
        END AS profitability,
        0 AS distribution,
        'cash' AS type,
        'fact' AS probability,
        p.commercial_budget_id AS commercial_budget_id
    FROM project_budget_projects p
    INNER JOIN project_budget_project_stage st ON st.id = p.stage_id
    INNER JOIN project_budget_project_office po ON po.id = p.project_office_id
    INNER JOIN project_budget_fact_cash_flow fc ON fc.projects_id = p.id
    WHERE step_status = 'project' AND p.project_have_steps = false AND p.active = true
    UNION
    SELECT
        ps.company_id,
        p.id AS project_id,        
        ps.stage_id,
        ps.project_office_id,        
        ps.key_account_manager_id,
        ps.id AS step_id,
        ps.partner_id,
        p.essence_project AS name,
        fc.date_cash AS date,
        fc.sum_cash AS amount,
        ps.currency_id AS currency_id,
        CASE
            WHEN ps.total_amount_of_revenue != 0 THEN ((ps.total_amount_of_revenue - ps.cost_price) / ps.total_amount_of_revenue * 100)
            ELSE 0
        END AS profitability,
        0 AS distribution,
        'cash' AS type,
        'fact' AS probability,
        ps.commercial_budget_id AS commercial_budget_id
    FROM project_budget_projects ps
    INNER JOIN project_budget_projects p ON p.id = ps.step_project_parent_id
    AND p.project_have_steps = true AND ps.step_status = 'step'
    INNER JOIN project_budget_project_stage st ON st.id = ps.stage_id
    INNER JOIN project_budget_fact_cash_flow fc ON fc.step_project_child_id = ps.id
    WHERE ps.active = true
    UNION
    SELECT
        p.company_id,
        p.id AS project_id,        
        p.stage_id,
        p.project_office_id,        
        p.key_account_manager_id,
        NULL AS step_id,
        p.partner_id,
        p.essence_project AS name,
        pa.date_cash AS date,
        ROUND(pa.sum_cash_without_vat, c.decimal_places) - ROUND(COALESCE(da.sum_distr_cash, 0), c.decimal_places) AS amount,
        p.currency_id AS currency_id,
        CASE
            WHEN p.total_amount_of_revenue != 0 THEN ((p.total_amount_of_revenue - p.cost_price) / p.total_amount_of_revenue * 100)
            ELSE 0
        END AS profitability,
        dac.sum_cash_without_vat AS distribution,
        'acceptance' AS type,
        pa.forecast AS probability,
        p.commercial_budget_id AS commercial_budget_id
    FROM project_budget_projects p
    INNER JOIN project_budget_project_stage st ON st.id = p.stage_id
    INNER JOIN project_budget_project_office po ON po.id = p.project_office_id
    INNER JOIN project_budget_planned_acceptance_flow pa ON pa.projects_id = p.id
    LEFT JOIN project_budget_distribution_acceptance dac ON dac.planned_acceptance_flow_id = pa.id
    INNER JOIN res_currency c ON c.id = p.currency_id	
    LEFT JOIN
    (
        SELECT planned_acceptance_flow_id, SUM(sum_cash_without_vat) AS sum_distr_cash
        FROM project_budget_distribution_acceptance
        GROUP BY planned_acceptance_flow_id
    ) AS da ON da.planned_acceptance_flow_id = pa.id
    WHERE step_status = 'project' AND p.project_have_steps = false AND p.active = true
    AND ROUND(pa.sum_cash_without_vat, c.decimal_places) - ROUND(COALESCE(da.sum_distr_cash, 0), c.decimal_places) != 0
    UNION
    SELECT
        ps.company_id,
        p.id AS project_id,        
        ps.stage_id,
        ps.project_office_id,        
        ps.key_account_manager_id,
        ps.id AS step_id,
        ps.partner_id,
        p.essence_project AS name,
        pa.date_cash AS date,
        ROUND(pa.sum_cash_without_vat, c.decimal_places) - ROUND(COALESCE(da.sum_distr_cash, 0), c.decimal_places) AS amount,
        ps.currency_id AS currency_id,
        CASE
            WHEN ps.total_amount_of_revenue != 0 THEN ((ps.total_amount_of_revenue - ps.cost_price) / ps.total_amount_of_revenue * 100)
            ELSE 0
        END AS profitability,
        dac.sum_cash_without_vat AS distribution,
        'acceptance' AS type,
        pa.forecast AS probability,
        ps.commercial_budget_id AS commercial_budget_id
    FROM project_budget_projects ps
    INNER JOIN project_budget_projects p ON p.id = ps.step_project_parent_id
    AND p.project_have_steps = true AND ps.step_status = 'step'
    INNER JOIN project_budget_project_stage st ON st.id = ps.stage_id
    INNER JOIN project_budget_planned_acceptance_flow pa ON pa.step_project_child_id = ps.id
    LEFT JOIN project_budget_distribution_acceptance dac ON dac.planned_acceptance_flow_id = pa.id
    INNER JOIN res_currency c ON c.id = ps.currency_id	
    LEFT JOIN
    (
        SELECT planned_acceptance_flow_id, SUM(sum_cash_without_vat) AS sum_distr_cash
        FROM project_budget_distribution_acceptance
        GROUP BY planned_acceptance_flow_id
    ) AS da ON da.planned_acceptance_flow_id = pa.id
    WHERE ROUND(pa.sum_cash_without_vat, c.decimal_places) - ROUND(COALESCE(da.sum_distr_cash, 0), c.decimal_places) != 0 AND ps.active = true
    UNION
    SELECT
        p.company_id,
        p.id AS project_id,        
        p.stage_id,
        p.project_office_id,        
        p.key_account_manager_id,
        NULL AS step_id,
        p.partner_id,
        p.essence_project AS name,
        fa.date_cash AS date,
        fa.sum_cash_without_vat AS amount,
        p.currency_id AS currency_id,
        CASE
            WHEN p.total_amount_of_revenue != 0 THEN ((p.total_amount_of_revenue - p.cost_price) / p.total_amount_of_revenue * 100)
            ELSE 0
        END AS profitability,
        0 AS distribution,
        'acceptance' AS type,
        'fact' AS probability,
        p.commercial_budget_id AS commercial_budget_id
    FROM project_budget_projects p
    INNER JOIN project_budget_project_stage st ON st.id = p.stage_id
    INNER JOIN project_budget_project_office po ON po.id = p.project_office_id
    INNER JOIN project_budget_fact_acceptance_flow fa ON fa.projects_id = p.id
    WHERE step_status = 'project' AND p.project_have_steps = false AND p.active = true
    UNION
    SELECT
        ps.company_id,
        p.id AS project_id,        
        ps.stage_id,
        ps.project_office_id,        
        ps.key_account_manager_id,
        ps.id AS step_id,
        ps.partner_id,
        p.essence_project AS name,
        fa.date_cash AS date,
        fa.sum_cash_without_vat AS amount,
        ps.currency_id AS currency_id,
        CASE
            WHEN ps.total_amount_of_revenue != 0 THEN ((ps.total_amount_of_revenue - ps.cost_price) / ps.total_amount_of_revenue * 100)
            ELSE 0
        END AS profitability,
        0 AS distribution,
        'acceptance' AS type,
        'fact' AS probability,
        ps.commercial_budget_id AS commercial_budget_id
    FROM project_budget_projects ps
    INNER JOIN project_budget_projects p ON p.id = ps.step_project_parent_id
    AND p.project_have_steps = true AND ps.step_status = 'step'
    INNER JOIN project_budget_project_stage st ON st.id = ps.stage_id
    INNER JOIN project_budget_fact_acceptance_flow fa ON fa.step_project_child_id = ps.id
    WHERE ps.active = true
    UNION
    SELECT
        p.company_id,
        p.id AS project_id,        
        p.stage_id,
        p.project_office_id,        
        p.key_account_manager_id,
        NULL AS step_id,
        p.partner_id,
        p.essence_project AS name,
        fa.date_cash AS date,
        CASE
            WHEN fa.margin_manual_input = true THEN fa.margin
            WHEN p.total_amount_of_revenue != 0 THEN (fa.sum_cash_without_vat * (p.total_amount_of_revenue - p.cost_price) / p.total_amount_of_revenue)
            ELSE 0
        END AS amount,
        p.currency_id AS currency_id,
        CASE
            WHEN p.total_amount_of_revenue != 0 THEN ((p.total_amount_of_revenue - p.cost_price) / p.total_amount_of_revenue * 100)
            ELSE 0
        END AS profitability,
        0 AS distribution,
        'margin_income' AS type,
        'fact' AS probability,
        p.commercial_budget_id AS commercial_budget_id
    FROM project_budget_projects p
    INNER JOIN project_budget_project_stage st ON st.id = p.stage_id
    INNER JOIN project_budget_project_office po ON po.id = p.project_office_id
    INNER JOIN project_budget_fact_acceptance_flow fa ON fa.projects_id = p.id
    WHERE step_status = 'project' AND p.project_have_steps = false AND p.active = true
    UNION
    SELECT
        ps.company_id,
        p.id AS project_id,        
        ps.stage_id,
        ps.project_office_id,        
        ps.key_account_manager_id,
        ps.id AS step_id,
        ps.partner_id,
        p.essence_project AS name,
        fa.date_cash AS date,
        CASE
            WHEN fa.margin_manual_input = true THEN fa.margin
            WHEN ps.total_amount_of_revenue != 0 THEN (fa.sum_cash_without_vat * (ps.total_amount_of_revenue - ps.cost_price) / ps.total_amount_of_revenue)
            ELSE 0
        END AS amount,
        ps.currency_id AS currency_id,
        CASE
            WHEN ps.total_amount_of_revenue != 0 THEN ((ps.total_amount_of_revenue - ps.cost_price) / ps.total_amount_of_revenue * 100)
            ELSE 0
        END AS profitability,
        0 AS distribution,
        'margin_income' AS type,
        'fact' AS probability,
        ps.commercial_budget_id AS commercial_budget_id
    FROM project_budget_projects ps
    INNER JOIN project_budget_projects p ON p.id = ps.step_project_parent_id
    AND p.project_have_steps = true AND ps.step_status = 'step'
    INNER JOIN project_budget_project_stage st ON st.id = ps.stage_id
    INNER JOIN project_budget_fact_acceptance_flow fa ON fa.step_project_child_id = ps.id
    WHERE ps.active = true
) p
GROUP BY
    company_id,
    project_id,
    stage_id,
    project_office_id,
    key_account_manager_id,
    step_id,
    partner_id,
    name,
    type,
    date,
    amount,
    currency_id,
    distribution,
    probability,
    profitability,
    commercial_budget_id
"""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            sql.SQL("""CREATE or REPLACE VIEW {} as ({})""").format(
                sql.Identifier(self._table),
                sql.SQL(query)
            ))
