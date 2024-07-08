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
    probability
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
        0 AS distribution,
        'contracting' AS type,
        CASE
            WHEN st.code in ('100', '100(done)') THEN 'fact'
            WHEN st.code = '75' THEN 'commitment'
            WHEN st.code = '50' THEN 'reserve'
            WHEN st.code = '30' THEN 'potential'
        END AS probability
    FROM project_budget_projects p
    INNER JOIN project_budget_project_stage st ON st.id = p.stage_id AND COALESCE(st.fold, false) = false
    AND st.code not in ('0', '10')
    INNER JOIN project_budget_project_office po ON po.id = p.project_office_id
    WHERE p.budget_state = 'work' AND p.active = true AND step_status = 'project' AND p.project_have_steps = false
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
        0 AS distribution,
        'contracting' AS type,
        CASE
            WHEN st.code in ('100', '100(done)') THEN 'fact'
            WHEN st.code = '75' THEN 'commitment'
            WHEN st.code = '50' THEN 'reserve'
            WHEN st.code = '30' THEN 'potential'
        END AS probability
    FROM project_budget_projects ps
    INNER JOIN project_budget_projects p ON p.id = ps.step_project_parent_id AND p.budget_state = 'work' AND p.active = true
    AND p.project_have_steps = true AND ps.step_status = 'step'
    INNER JOIN project_budget_project_stage st ON st.id = ps.stage_id AND COALESCE(st.fold, false) = false
    AND st.code not in ('0', '10')
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
        pc.sum_cash AS amount,
        p.currency_id AS currency_id,
        dc.sum_cash AS distribution,
        'cash' AS type,
        CASE
            WHEN pc.forecast != 'from_project' THEN pc.forecast
            WHEN pc.forecast = 'from_project' AND st.code in ('75', '100') THEN 'commitment'
            WHEN pc.forecast = 'from_project' AND st.code = '50' THEN 'reserve'
            WHEN pc.forecast = 'from_project' AND st.code = '30' THEN 'potential'
        END AS probability
    FROM project_budget_projects p
    INNER JOIN project_budget_project_stage st ON st.id = p.stage_id AND COALESCE(st.fold, false) = false
    AND st.code not in ('0', '10')
    INNER JOIN project_budget_project_office po ON po.id = p.project_office_id
    INNER JOIN project_budget_planned_cash_flow pc ON pc.projects_id = p.id
    INNER JOIN project_budget_distribution_cash dc ON dc.planned_cash_flow_id = pc.id
    WHERE p.budget_state = 'work' AND p.active = true AND step_status = 'project' AND p.project_have_steps = false
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
        pc.sum_cash AS amount,
        ps.currency_id AS currency_id,
        dc.sum_cash AS distribution,
        'cash' AS type,
        CASE
            WHEN pc.forecast != 'from_project' THEN pc.forecast
            WHEN pc.forecast = 'from_project' AND st.code in ('75', '100') THEN 'commitment'
            WHEN pc.forecast = 'from_project' AND st.code = '50' THEN 'reserve'
            WHEN pc.forecast = 'from_project' AND st.code = '30' THEN 'potential'
        END AS probability
    FROM project_budget_projects ps
    INNER JOIN project_budget_projects p ON p.id = ps.step_project_parent_id AND p.budget_state = 'work' AND p.active = true
    AND p.project_have_steps = true AND ps.step_status = 'step'
    INNER JOIN project_budget_project_stage st ON st.id = ps.stage_id AND COALESCE(st.fold, false) = false
    AND st.code not in ('0', '10')
    INNER JOIN project_budget_planned_cash_flow pc ON pc.step_project_child_id = ps.id
    INNER JOIN project_budget_distribution_cash dc ON dc.planned_cash_flow_id = pc.id
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
        0 AS distribution,
        'cash' AS type,
        'fact' AS probability
    FROM project_budget_projects p
    INNER JOIN project_budget_project_stage st ON st.id = p.stage_id AND COALESCE(st.fold, false) = false
    AND st.code not in ('0', '10')
    INNER JOIN project_budget_project_office po ON po.id = p.project_office_id
    INNER JOIN project_budget_fact_cash_flow fc ON fc.projects_id = p.id
    WHERE p.budget_state = 'work' AND p.active = true AND step_status = 'project' AND p.project_have_steps = false
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
        0 AS distribution,
        'cash' AS type,
        'fact' AS probability
    FROM project_budget_projects ps
    INNER JOIN project_budget_projects p ON p.id = ps.step_project_parent_id AND p.budget_state = 'work' AND p.active = true
    AND p.project_have_steps = true AND ps.step_status = 'step'
    INNER JOIN project_budget_project_stage st ON st.id = ps.stage_id AND COALESCE(st.fold, false) = false
    AND st.code not in ('0', '10')
    INNER JOIN project_budget_fact_cash_flow fc ON fc.step_project_child_id = ps.id
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
        pa.sum_cash_without_vat AS amount,
        p.currency_id AS currency_id,
        da.sum_cash_without_vat AS distribution,
        'acceptance' AS type,
        CASE
            WHEN pa.forecast != 'from_project' THEN pa.forecast
            WHEN pa.forecast = 'from_project' AND st.code in ('75', '100') THEN 'commitment'
            WHEN pa.forecast = 'from_project' AND st.code = '50' THEN 'reserve'
            WHEN pa.forecast = 'from_project' AND st.code = '30' THEN 'potential'
        END AS probability
    FROM project_budget_projects p
    INNER JOIN project_budget_project_stage st ON st.id = p.stage_id AND COALESCE(st.fold, false) = false
    AND st.code not in ('0', '10')
    INNER JOIN project_budget_project_office po ON po.id = p.project_office_id
    INNER JOIN project_budget_planned_acceptance_flow pa ON pa.projects_id = p.id
    INNER JOIN project_budget_distribution_acceptance da ON da.planned_acceptance_flow_id = pa.id
    WHERE p.budget_state = 'work' AND p.active = true AND step_status = 'project' AND p.project_have_steps = false
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
        pa.sum_cash_without_vat AS amount,
        ps.currency_id AS currency_id,
        da.sum_cash_without_vat AS distribution,
        'acceptance' AS type,
        CASE
            WHEN pa.forecast != 'from_project' THEN pa.forecast
            WHEN pa.forecast = 'from_project' AND st.code in ('75', '100') THEN 'commitment'
            WHEN pa.forecast = 'from_project' AND st.code = '50' THEN 'reserve'
            WHEN pa.forecast = 'from_project' AND st.code = '30' THEN 'potential'
        END AS probability
    FROM project_budget_projects ps
    INNER JOIN project_budget_projects p ON p.id = ps.step_project_parent_id AND p.budget_state = 'work' AND p.active = true
    AND p.project_have_steps = true AND ps.step_status = 'step'
    INNER JOIN project_budget_project_stage st ON st.id = ps.stage_id AND COALESCE(st.fold, false) = false
    AND st.code not in ('0', '10')
    INNER JOIN project_budget_planned_acceptance_flow pa ON pa.step_project_child_id = ps.id
    INNER JOIN project_budget_distribution_acceptance da ON da.planned_acceptance_flow_id = pa.id
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
        0 AS distribution,
        'acceptance' AS type,
        'fact' AS probability
    FROM project_budget_projects p
    INNER JOIN project_budget_project_stage st ON st.id = p.stage_id AND COALESCE(st.fold, false) = false
    AND st.code not in ('0', '10')
    INNER JOIN project_budget_project_office po ON po.id = p.project_office_id
    INNER JOIN project_budget_fact_acceptance_flow fa ON fa.projects_id = p.id
    WHERE p.budget_state = 'work' AND p.active = true AND step_status = 'project' AND p.project_have_steps = false
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
        0 AS distribution,
        'acceptance' AS type,
        'fact' AS probability
    FROM project_budget_projects ps
    INNER JOIN project_budget_projects p ON p.id = ps.step_project_parent_id AND p.budget_state = 'work' AND p.active = true
    AND p.project_have_steps = true AND ps.step_status = 'step'
    INNER JOIN project_budget_project_stage st ON st.id = ps.stage_id AND COALESCE(st.fold, false) = false
    AND st.code not in ('0', '10')
    INNER JOIN project_budget_fact_acceptance_flow fa ON fa.step_project_child_id = ps.id
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
        fa.margin / 100 AS amount,
        p.currency_id AS currency_id,
        0 AS distribution,
        'margin_income' AS type,
        'fact' AS probability
    FROM project_budget_projects p
    INNER JOIN project_budget_project_stage st ON st.id = p.stage_id AND COALESCE(st.fold, false) = false
    AND st.code not in ('0', '10')
    INNER JOIN project_budget_project_office po ON po.id = p.project_office_id
    INNER JOIN project_budget_fact_acceptance_flow fa ON fa.projects_id = p.id
    WHERE p.budget_state = 'work' AND p.active = true AND step_status = 'project' AND p.project_have_steps = false
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
        fa.margin AS amount,
        ps.currency_id AS currency_id,
        0 AS distribution,
        'margin_income' AS type,
        'fact' AS probability
    FROM project_budget_projects ps
    INNER JOIN project_budget_projects p ON p.id = ps.step_project_parent_id AND p.budget_state = 'work' AND p.active = true
    AND p.project_have_steps = true AND ps.step_status = 'step'
    INNER JOIN project_budget_project_stage st ON st.id = ps.stage_id AND COALESCE(st.fold, false) = false
    AND st.code not in ('0', '10')
    INNER JOIN project_budget_fact_acceptance_flow fa ON fa.step_project_child_id = ps.id
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
        pa.sum_cash_without_vat * p.profitability / 100 AS amount,
        p.currency_id AS currency_id,
        da.sum_cash_without_vat * p.profitability / 100 AS distribution,
        'margin_income' AS type,
        CASE
            WHEN pa.forecast != 'from_project' THEN pa.forecast
            WHEN pa.forecast = 'from_project' AND st.code in ('75', '100') THEN 'commitment'
            WHEN pa.forecast = 'from_project' AND st.code = '50' THEN 'reserve'
            WHEN pa.forecast = 'from_project' AND st.code = '30' THEN 'potential'
        END AS probability
    FROM project_budget_projects p
    INNER JOIN project_budget_project_stage st ON st.id = p.stage_id AND COALESCE(st.fold, false) = false
    AND st.code not in ('0', '10')
    INNER JOIN project_budget_project_office po ON po.id = p.project_office_id
    INNER JOIN project_budget_planned_acceptance_flow pa ON pa.projects_id = p.id
    INNER JOIN project_budget_distribution_acceptance da ON da.planned_acceptance_flow_id = pa.id
    WHERE p.budget_state = 'work' AND p.active = true AND step_status = 'project' AND p.project_have_steps = false
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
        pa.sum_cash_without_vat * ps.profitability / 100 AS amount,
        ps.currency_id AS currency_id,
        da.sum_cash_without_vat * ps.profitability / 100 AS distribution,
        'margin_income' AS type,
        CASE
            WHEN pa.forecast != 'from_project' THEN pa.forecast
            WHEN pa.forecast = 'from_project' AND st.code in ('75', '100') THEN 'commitment'
            WHEN pa.forecast = 'from_project' AND st.code = '50' THEN 'reserve'
            WHEN pa.forecast = 'from_project' AND st.code = '30' THEN 'potential'
        END AS probability
    FROM project_budget_projects ps
    INNER JOIN project_budget_projects p ON p.id = ps.step_project_parent_id AND p.budget_state = 'work' AND p.active = true
    AND p.project_have_steps = true AND ps.step_status = 'step'
    INNER JOIN project_budget_project_stage st ON st.id = ps.stage_id AND COALESCE(st.fold, false) = false
    AND st.code not in ('0', '10')
    INNER JOIN project_budget_planned_acceptance_flow pa ON pa.step_project_child_id = ps.id
    INNER JOIN project_budget_distribution_acceptance da ON da.planned_acceptance_flow_id = pa.id
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
    probability
"""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            sql.SQL("""CREATE or REPLACE VIEW {} as ({})""").format(
                sql.Identifier(self._table),
                sql.SQL(query)
            ))
