from datetime import datetime
from itertools import groupby

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from ..tools.misc import formatLang, floatRound
from odoo.tools.misc import format_date
from odoo.tools import date_utils

AUTO_CLOSE_FORECAST_MODE = [
    ('no', 'No'),
    ('at_date', 'At Date'),
    ('monthly', 'Monthly'),
    ('quarterly', 'Quarterly'),
    ('yearly', 'Yearly')
]


def compute_year_dates(current_date):
    return {
        'date_from': datetime(year=current_date.year, month=1, day=1).date(),
        'date_to': datetime(year=current_date.year, month=12, day=31).date()
    }


class ProjectBudgetReportSalesForecast(models.AbstractModel):
    _name = 'project.budget.report.sales.forecast'
    _description = 'Project Budget Sales Forecast Report'

    @api.model
    def retrieve_dashboard(self, options):
        self.env['project.budget.financial.indicator'].check_access_rights('read')

        result = {
            'companies': self.env['res.company'].search_read(
                domain=[('id', 'in', self.env.context.get('allowed_company_ids', []))],
                fields=['id', 'name']
            ),
            'contraction': {'fact': 0, 'plan': 0, 'forecast': 0, 'percentage': 0},
            'cash_flow': {'fact': 0, 'plan': 0, 'forecast': 0, 'percentage': 0},
            'gross_revenue': {'fact': 0, 'plan': 0, 'forecast': 0, 'percentage': 0},
            'margin': {'fact': 0, 'plan': 0, 'forecast': 0, 'percentage': 0}
        }

        period_options = options.get('date')

        financial_indicators = self.env['project.budget.financial.indicator'].search([
            ('commercial_budget_id.budget_state', '=', 'work'),
            ('date', '>=', period_options.get('date_from')),
            ('date', '<=', period_options.get('date_to'))
        ])

        planned_indicators = self.env['project_budget.budget_plan_supervisor_spec'].search([
            ('budget_plan_supervisor_id.is_company_plan', '=', False),
            ('budget_plan_supervisor_id.year', '=', period_options.get('string'))
        ])

        kam_planned_indicators = self.env['project_budget.budget_plan_kam_spec'].search([
            ('budget_plan_kam_id.year', '=', period_options.get('string'))
        ])

        actual_managers = dict()

        for i in financial_indicators:
            actual_managers.setdefault(i.project_office_id.id, {})
            actual_managers[i.project_office_id.id].setdefault(i.key_account_manager_id.id, i.key_account_manager_id.name)

        for i in kam_planned_indicators:
            actual_managers.setdefault(i.budget_plan_kam_id.project_office_id.id, {})
            actual_managers[i.budget_plan_kam_id.project_office_id.id].setdefault(
                i.budget_plan_kam_id.key_account_manager_id.id, i.budget_plan_kam_id.key_account_manager_id.name
            )

        offices = self.env['project_budget.project_office'].search_read(
            fields=['id', 'name', 'parent_id', 'company_id']
        )

        for company in result['companies']:
            company['offices'] = list()
            for office in offices:
                if office['company_id'][0] == company['id']:
                    managers = actual_managers.get(office['id'], False)
                    office['managers'] = list()
                    # office['planned_indicators'] = planned_indicators.filtered(
                    #     lambda fi: fi.budget_plan_supervisor_id.project_office_id.id == office['id']
                    # ).ids,
                    if managers:
                        for m_id, name in managers.items():
                            office['managers'].append({
                                'id': m_id,
                                'name': name,
                                # 'financial_indicators': financial_indicators.filtered(
                                #     lambda fi: fi.project_office_id.id == office['id'] and fi.key_account_manager_id.id == m_id
                                # ).ids,
                                # 'planned_indicators': kam_planned_indicators.filtered(
                                #     lambda fi: fi.budget_plan_kam_id.key_account_manager_id.id == m_id
                                # ).ids,
                            })
                    company['offices'].append(office)

        c = self._get_contraction_data(datetime(day=1, month=1, year=2024).date(), datetime(day=31, month=12, year=2024).date(), financial_indicators)
        print(c['fact'], c[13] + c[14] * 0.6 + c[15] * 0.1)

        c = self._get_cash_flow_data(datetime(day=1, month=1, year=2024).date(), datetime(day=31, month=12, year=2024).date(), financial_indicators)
        print(c['fact'], c[13] + c[14] * 0.6)

        c = self._get_gross_revenue_data(datetime(day=1, month=1, year=2024).date(), datetime(day=31, month=12, year=2024).date(), financial_indicators)
        print(c['fact'], c[13] + c[14] * 0.6)

        c = self._get_margin_data(datetime(day=1, month=1, year=2024).date(), datetime(day=31, month=12, year=2024).date(), financial_indicators)
        print(c['fact'], c[13] + c[14] * 0.6)

        self._prepare_contraction_data(result, planned_indicators, kam_planned_indicators, financial_indicators, options)
        self._prepare_cash_flow_data(result, planned_indicators, kam_planned_indicators, financial_indicators, options)
        self._prepare_gross_revenue_data(result, planned_indicators,  kam_planned_indicators, financial_indicators, options)
        self._prepare_margin_data(result, planned_indicators,  kam_planned_indicators, financial_indicators, options)
        return result

    # ------------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------------

    def _get_contraction_data(self, period_start, period_end, financial_indicators):
        result = {}

        fact_data = financial_indicators.filtered(
            lambda fi: fi.type == 'contracting'
                       and fi.stage_id.project_state == 'won'
                       and period_start <= fi.date <= period_end
        )
        result['fact'] = sum(d.amount for d in fact_data)

        forecast_data = financial_indicators.filtered(
            lambda fi: fi.type == 'contracting'
                       and fi.forecast_probability_id
                       and period_start <= fi.date <= period_end
        )

        for i, group in groupby(
            sorted(forecast_data, key=lambda i: i.forecast_probability_id.id), lambda i: i.forecast_probability_id.id
        ):
            result[i] = sum(i.amount for i in group)
        return result

    def _get_cash_flow_data(self, period_start, period_end, financial_indicators, close_mode='monthly'):
        result = {}

        fact_data = financial_indicators.filtered(
            lambda fi: fi.type == 'cash_flow'
                       and not fi.forecast_probability_id
                       and period_start <= fi.date <= period_end
        )
        result['fact'] = sum(d.amount for d in fact_data)

        forecast_data = financial_indicators.filtered(
            lambda fi: fi.type == 'cash_flow'
                       and fi.forecast_probability_id
                       and period_start <= fi.date <= period_end
        )

        closed_forecasts = self._auto_close_forecast_by_fact(fact_data, forecast_data, close_mode)

        for i, group in groupby(
            sorted(forecast_data, key=lambda i: i.forecast_probability_id.id), lambda i: i.forecast_probability_id.id
        ):
            result[i] = sum(
                closed_forecasts.get(i.id, i.amount - i.distribution) for i in group if i.amount - i.distribution > 0
            )
        return result

    def _get_gross_revenue_data(self, period_start, period_end, financial_indicators, close_mode='quarterly'):
        result = {}
        fact_data = financial_indicators.filtered(
            lambda fi: fi.type == 'gross_revenue'
                       and not fi.forecast_probability_id
                       and period_start <= fi.date <= period_end
        )
        result['fact'] = sum(d.amount for d in fact_data)

        forecast_data = financial_indicators.filtered(
            lambda fi: fi.type == 'gross_revenue'
                       and fi.forecast_probability_id
                       and period_start <= fi.date <= period_end
        )

        closed_forecasts = self._auto_close_forecast_by_fact(fact_data, forecast_data, close_mode)

        for i, group in groupby(
            sorted(forecast_data, key=lambda i: i.forecast_probability_id.id), lambda i: i.forecast_probability_id.id
        ):
            result[i] = sum(
                closed_forecasts.get(i.id, i.amount - i.distribution) for i in group if i.amount - i.distribution > 0
            )
        return result

    def _get_margin_data(self, period_start, period_end, financial_indicators, close_mode='quarterly'):
        result = {}
        fact_data = financial_indicators.filtered(
            lambda fi: fi.type == 'margin'
                       and not fi.forecast_probability_id
                       and period_start <= fi.date <= period_end
        )
        result['fact'] = sum(d.amount for d in fact_data)

        fact_gross_revenue_data = financial_indicators.filtered(
            lambda fi: fi.type == 'gross_revenue'
                       and not fi.forecast_probability_id
                       and period_start <= fi.date <= period_end
        )

        forecast_data = financial_indicators.filtered(
            lambda fi: fi.type == 'gross_revenue'
                       and fi.profitability > 0
                       and fi.forecast_probability_id
                       and period_start <= fi.date <= period_end
        )

        closed_forecasts = self._auto_close_forecast_by_fact(fact_gross_revenue_data, forecast_data, close_mode)

        for i, group in groupby(
            sorted(forecast_data, key=lambda i: i.forecast_probability_id.id), lambda i: i.forecast_probability_id.id
        ):
            result[i] = sum(
                closed_forecasts.get(i.id, i.amount - i.distribution) * i.profitability for i in group
                if i.amount - i.distribution > 0
                and not any(distribution.fact_acceptance_flow_id.margin_manual_input for distribution in i.planned_acceptance_flow_id.distribution_acceptance_ids)
            )
        return result

    def _prepare_contraction_data(self, result, planned_indicators, kam_planned_indicators, financial_indicators, options):
        for company in result['companies']:
            company['contraction'] = dict()
            for office in company['offices']:
                office['contraction'] = dict()
                for manager in office['managers']:
                    manager['contraction'] = dict()

        fact_data = financial_indicators.filtered(
            lambda fi: fi.type == 'contracting' and fi.stage_id.project_state == 'won')
        for company in result['companies']:
            company_fact = 0
            for office in company['offices']:
                office_fact = 0
                for manager in office['managers']:
                    for m, group in groupby(
                            sorted(
                                fact_data.filtered(
                                    lambda p: p.project_office_id.id == office['id']
                                              and p.key_account_manager_id.id == manager['id']),
                                key=lambda i: i.key_account_manager_id.id
                            ), lambda fi: fi.key_account_manager_id
                    ):
                        if manager['id'] == m.id:
                            manager_fact = sum(indicator.amount for indicator in group)
                            manager['contraction'].update({
                                'fact': self._build_value_dict(manager_fact, 'monetary', options)
                            })
                            office_fact += manager_fact
                            company_fact += manager_fact
                office['contraction'].update({'fact': self._build_value_dict(office_fact, 'monetary', options)})
            company['contraction'].update({'fact': self._build_value_dict(company_fact, 'monetary', options)})
        companies_fact = sum(d.amount for d in fact_data)
        result['contraction'].update({'fact': self._build_value_dict(companies_fact, 'monetary', options)})

        plan_data = planned_indicators.filtered(lambda p: p.type_row == 'contracting')
        kam_plan_data = kam_planned_indicators.filtered(lambda p: p.type_row == 'contracting')
        use_plan_6_6 = any(d.q3_plan_6_6 or d.q4_plan_6_6 for d in plan_data)
        kam_use_plan_6_6 = any(d.q3_plan_6_6 or d.q4_plan_6_6 for d in kam_plan_data)
        for company in result['companies']:
            company_plan = 0
            for office in company['offices']:
                for o, group in groupby(sorted(plan_data, key=lambda i: i.budget_plan_supervisor_id.project_office_id.id), lambda fi: fi.budget_plan_supervisor_id.project_office_id):
                    if office['id'] == o.id:
                        if use_plan_6_6:
                            office_plan = sum(
                                indicator.q3_plan_6_6 + indicator.q4_plan_6_6 + indicator.q1_fact + indicator.q2_fact
                                for indicator in group
                            )
                        else:
                            office_plan = sum(
                                indicator.q1_plan + indicator.q2_plan + indicator.q3_plan + indicator.q4_plan
                                for indicator in group
                            )
                        company_plan += office_plan
                        office['contraction'].update({
                            'plan': self._build_value_dict(office_plan, 'monetary', options),
                            'to_plan': round((office['contraction']['fact']['no_format'] / office_plan) * 100, 2)
                            if office['contraction'].get('fact') and office_plan > 0 else 0
                        })
                for manager in office['managers']:
                    for m, group in groupby(
                        sorted(
                            kam_plan_data.filtered(lambda p: p.budget_plan_kam_id.project_office_id.id == office['id']),
                            key=lambda i: i.budget_plan_kam_id.key_account_manager_id.id
                        ),
                        lambda fi: fi.budget_plan_kam_id.key_account_manager_id
                    ):
                        if manager['id'] == m.id:
                            if kam_use_plan_6_6:
                                manager_plan = sum(
                                    indicator.q3_plan_6_6 + indicator.q4_plan_6_6 + indicator.q1_fact + indicator.q2_fact
                                    for indicator in group
                                )
                            else:
                                manager_plan = sum(
                                    indicator.q1_plan + indicator.q2_plan + indicator.q3_plan + indicator.q4_plan
                                    for indicator in group
                                )
                            manager['contraction'].update({
                                'plan': self._build_value_dict(manager_plan, 'monetary', options),
                                'to_plan': round((manager['contraction']['fact']['no_format'] / manager_plan) * 100, 2)
                                if manager['contraction'].get('fact') and manager_plan > 0 else 0
                            })
            company['contraction'].update({
                'plan': self._build_value_dict(company_plan, 'monetary', options),
                'to_plan': round((company['contraction']['fact']['no_format'] / company_plan) * 100, 2)
                if company['contraction'].get('fact') and company_plan > 0 else 0
            })
        if use_plan_6_6:
            companies_plan = sum(d.q3_plan_6_6 + d.q4_plan_6_6 + d.q1_fact + d.q2_fact for d in plan_data)
        else:
            companies_plan = sum(d.q1_plan + d.q2_plan + d.q3_plan + d.q4_plan for d in plan_data)
        result['contraction'].update({'plan': self._build_value_dict(companies_plan, 'monetary', options)})

        forecast_data = financial_indicators.filtered(
            lambda fi: fi.type == 'contracting' and fi.forecast_probability_id)
        companies_forecast = sum(d.amount * d.forecast_probability_id.coefficient for d in forecast_data)
        result['contraction'].update({'forecast': self._build_value_dict(companies_forecast, 'monetary', options)})

        result['contraction'].update({
            'percentage': round((companies_fact / companies_plan) * 100, 2)
            if companies_plan > 0 else 0
        })

    def _prepare_cash_flow_data(self, result, planned_indicators, kam_planned_indicators, financial_indicators, options):
        for company in result['companies']:
            company['cash_flow'] = dict()
            for office in company['offices']:
                office['cash_flow'] = dict()
                for manager in office['managers']:
                    manager['cash_flow'] = dict()

        fact_data = financial_indicators.filtered(
            lambda fi: fi.type == 'cash_flow' and not fi.forecast_probability_id)
        for company in result['companies']:
            company_fact = 0
            for office in company['offices']:
                office_fact = 0
                for manager in office['managers']:
                    for m, group in groupby(
                            sorted(
                                fact_data.filtered(lambda p: p.project_office_id.id == office['id']),
                                key=lambda i: i.key_account_manager_id.id
                            ), lambda fi: fi.key_account_manager_id
                    ):
                        if manager['id'] == m.id:
                            manager_fact = sum(indicator.amount for indicator in group)
                            manager['cash_flow'].update({
                                'fact': self._build_value_dict(manager_fact, 'monetary', options)
                            })
                            office_fact += manager_fact
                            company_fact += manager_fact
                office['cash_flow'].update({
                    'fact': self._build_value_dict(office_fact, 'monetary', options)
                })
            company['cash_flow'].update({
                'fact': self._build_value_dict(company_fact, 'monetary', options)
            })
        companies_fact = sum(d.amount for d in fact_data)
        result['cash_flow'].update({'fact': self._build_value_dict(companies_fact, 'monetary', options)})

        plan_data = planned_indicators.filtered(lambda p: p.type_row == 'cash')
        kam_plan_data = kam_planned_indicators.filtered(lambda p: p.type_row == 'cash')
        use_plan_6_6 = any(d.q3_plan_6_6 or d.q4_plan_6_6 for d in plan_data)
        kam_use_plan_6_6 = any(d.q3_plan_6_6 or d.q4_plan_6_6 for d in kam_plan_data)
        for company in result['companies']:
            company_plan = 0
            for office in company['offices']:
                for o, group in groupby(sorted(plan_data, key=lambda i: i.budget_plan_supervisor_id.project_office_id.id), lambda fi: fi.budget_plan_supervisor_id.project_office_id):
                    if office['id'] == o.id:
                        if use_plan_6_6:
                            office_plan = sum(
                                indicator.q3_plan_6_6 + indicator.q4_plan_6_6 + indicator.q1_fact + indicator.q2_fact
                                for indicator in group
                            )
                        else:
                            office_plan = sum(
                                indicator.q1_plan + indicator.q2_plan + indicator.q3_plan + indicator.q4_plan
                                for indicator in group
                            )
                        company_plan += office_plan
                        office['cash_flow'].update({
                            'plan': self._build_value_dict(office_plan, 'monetary', options),
                            'to_plan': round((office['cash_flow']['fact']['no_format'] / office_plan) * 100, 2)
                            if office['cash_flow'].get('fact') and office_plan > 0 else 0
                        })
                for manager in office['managers']:
                    for m, group in groupby(
                        sorted(
                            kam_plan_data.filtered(lambda p: p.budget_plan_kam_id.project_office_id.id == office['id']),
                            key=lambda i: i.budget_plan_kam_id.key_account_manager_id.id
                            ),
                            lambda fi: fi.budget_plan_kam_id.key_account_manager_id
                        ):
                        if manager['id'] == m.id:
                            if kam_use_plan_6_6:
                                manager_plan = sum(
                                    indicator.q3_plan_6_6 + indicator.q4_plan_6_6 + indicator.q1_fact + indicator.q2_fact
                                    for indicator in group
                                )
                            else:
                                manager_plan = sum(
                                    indicator.q1_plan + indicator.q2_plan + indicator.q3_plan + indicator.q4_plan
                                    for indicator in group
                                )
                            manager['cash_flow'].update({
                                'plan': self._build_value_dict(manager_plan, 'monetary', options),
                                'to_plan': round((manager['cash_flow']['fact']['no_format'] / manager_plan) * 100, 2)
                                if manager['cash_flow'].get('fact') and manager_plan > 0 else 0
                            })
            company['cash_flow'].update({
                'plan': self._build_value_dict(company_plan, 'monetary', options),
                'to_plan': round((company['cash_flow']['fact']['no_format'] / company_plan) * 100, 2)
                if company['cash_flow'].get('fact') and company_plan > 0 else 0
            })
        if use_plan_6_6:
            companies_plan = sum(d.q3_plan_6_6 + d.q4_plan_6_6 + d.q1_fact + d.q2_fact for d in plan_data)
        else:
            companies_plan = sum(d.q1_plan + d.q2_plan + d.q3_plan + d.q4_plan for d in plan_data)
        result['cash_flow'].update({'plan': self._build_value_dict(companies_plan, 'monetary', options)})

        forecast_data = financial_indicators.filtered(
            lambda fi: fi.type == 'cash_flow' and fi.forecast_probability_id and (
                        fi.forecast_probability_id.id == 3 or fi.forecast_probability_id.id == 4))
        closed_forecasts = self._auto_close_forecast_by_fact(fact_data, forecast_data, 'monthly')
        companies_forecast = sum(
            closed_forecasts.get(data.id, data.amount - data.distribution) * data.forecast_probability_id.coefficient
            for data in forecast_data.filtered(lambda d: d.amount - d.distribution > 0)
        )
        result['cash_flow'].update({'forecast': self._build_value_dict(companies_forecast, 'monetary', options)})

        result['cash_flow'].update({
            'percentage': round((companies_fact / companies_plan) * 100, 2)
            if companies_plan > 0 else 0
        })

    def _prepare_gross_revenue_data(self, result, planned_indicators,  kam_planned_indicators, financial_indicators, options):
        for company in result['companies']:
            company['gross_revenue'] = dict()
            for office in company['offices']:
                office['gross_revenue'] = dict()
                for manager in office['managers']:
                    manager['gross_revenue'] = dict()

        fact_data = financial_indicators.filtered(
            lambda fi: fi.type == 'gross_revenue' and not fi.forecast_probability_id)
        for company in result['companies']:
            company_fact = 0
            for office in company['offices']:
                office_fact = 0
                for manager in office['managers']:
                    for m, group in groupby(
                            sorted(
                                fact_data.filtered(lambda p: p.project_office_id.id == office['id']),
                                key=lambda i: i.key_account_manager_id.id
                            ), lambda fi: fi.key_account_manager_id
                    ):
                        if manager['id'] == m.id:
                            manager_fact = sum(indicator.amount for indicator in group)
                            manager['gross_revenue'].update({
                                'fact': self._build_value_dict(manager_fact, 'monetary',
                                                               options)
                            })
                            company_fact += manager_fact
                            office_fact += manager_fact
                office['gross_revenue'].update({'fact': self._build_value_dict(office_fact, 'monetary', options)})
            company['gross_revenue'].update({'fact': self._build_value_dict(company_fact, 'monetary', options)})
        companies_fact = sum(d.amount for d in fact_data)
        result['gross_revenue'].update({'fact': self._build_value_dict(companies_fact, 'monetary', options)})

        plan_data = planned_indicators.filtered(lambda p: p.type_row == 'acceptance')
        kam_plan_data = kam_planned_indicators.filtered(lambda p: p.type_row == 'acceptance')
        use_plan_6_6 = any(d.q3_plan_6_6 or d.q4_plan_6_6 for d in plan_data)
        kam_use_plan_6_6 = any(d.q3_plan_6_6 or d.q4_plan_6_6 for d in kam_plan_data)
        for company in result['companies']:
            company_plan = 0
            for office in company['offices']:
                for o, group in groupby(sorted(plan_data, key=lambda i: i.budget_plan_supervisor_id.project_office_id.id), lambda fi: fi.budget_plan_supervisor_id.project_office_id):
                    if office['id'] == o.id:
                        if use_plan_6_6:
                            office_plan = sum(
                                indicator.q3_plan_6_6 + indicator.q4_plan_6_6 + indicator.q1_fact + indicator.q2_fact
                                for indicator in group
                            )
                        else:
                            office_plan = sum(
                                indicator.q1_plan + indicator.q2_plan + indicator.q3_plan + indicator.q4_plan
                                for indicator in group
                            )
                        company_plan += office_plan
                        office['gross_revenue'].update({
                            'plan': self._build_value_dict(office_plan, 'monetary', options),
                            'to_plan': round((office['gross_revenue']['fact']['no_format'] / office_plan) * 100, 2)
                            if office['gross_revenue'].get('fact') and office_plan > 0 else 0
                        })
                for manager in office['managers']:
                    for m, group in groupby(
                        sorted(
                            kam_plan_data.filtered(lambda p: p.budget_plan_kam_id.project_office_id.id == office['id']),
                            key=lambda i: i.budget_plan_kam_id.key_account_manager_id.id
                            ),
                        lambda fi: fi.budget_plan_kam_id.key_account_manager_id
                        ):
                        if manager['id'] == m.id:
                            if kam_use_plan_6_6:
                                manager_plan = sum(
                                    indicator.q3_plan_6_6 + indicator.q4_plan_6_6 + indicator.q1_fact + indicator.q2_fact
                                    for indicator in group
                                )
                            else:
                                manager_plan = sum(
                                    indicator.q1_plan + indicator.q2_plan + indicator.q3_plan + indicator.q4_plan
                                    for indicator in group
                                )
                            manager['gross_revenue'].update({
                                'plan': self._build_value_dict(manager_plan, 'monetary', options),
                                'to_plan': round((manager['gross_revenue']['fact']['no_format'] / manager_plan) * 100, 2)
                                if manager['gross_revenue'].get('fact') and manager_plan > 0 else 0
                            })
            company['gross_revenue'].update({
                'plan': self._build_value_dict(company_plan, 'monetary', options),
                'to_plan': round((company['gross_revenue']['fact']['no_format'] / company_plan) * 100, 2)
                if company['gross_revenue'].get('fact') and company_plan > 0 else 0
            })
        if use_plan_6_6:
            companies_plan = sum(d.q3_plan_6_6 + d.q4_plan_6_6 + d.q1_fact + d.q2_fact for d in plan_data)
        else:
            companies_plan = sum(d.q1_plan + d.q2_plan + d.q3_plan + d.q4_plan for d in plan_data)
        result['gross_revenue'].update({'plan': self._build_value_dict(companies_plan, 'monetary', options)})

        forecast_data = financial_indicators.filtered(
            lambda fi: fi.type == 'gross_revenue' and fi.forecast_probability_id and (
                        fi.forecast_probability_id.id == 3 or fi.forecast_probability_id.id == 4))
        closed_forecasts = self._auto_close_forecast_by_fact(fact_data, forecast_data, 'quarterly')
        companies_forecast = sum(
            closed_forecasts.get(data.id, data.amount - data.distribution) * data.forecast_probability_id.coefficient
            for data in forecast_data.filtered(lambda d: d.amount - d.distribution > 0)
        )
        result['gross_revenue'].update({'forecast': self._build_value_dict(companies_forecast, 'monetary', options)})

        result['gross_revenue'].update({
            'percentage': round((companies_fact / companies_plan) * 100, 2)
            if companies_plan > 0 else 0
        })

    def _prepare_margin_data(self, result, planned_indicators,  kam_planned_indicators, financial_indicators, options):
        for company in result['companies']:
            company['margin'] = dict()
            for office in company['offices']:
                office['margin'] = dict()
                for manager in office['managers']:
                    manager['margin'] = dict()

        fact_data = financial_indicators.filtered(
            lambda fi: fi.type == 'margin' and not fi.forecast_probability_id)
        for company in result['companies']:
            company_fact = 0
            for office in company['offices']:
                office_fact = 0
                for manager in office['managers']:
                    for m, group in groupby(
                        sorted(
                            fact_data.filtered(lambda p: p.project_office_id.id == office['id']),
                            key=lambda i: i.key_account_manager_id.id
                        ), lambda fi: fi.key_account_manager_id
                    ):
                        if manager['id'] == m.id:
                            manager_fact = sum(indicator.amount for indicator in group)
                            manager['margin'].update({
                                'fact': self._build_value_dict(manager_fact, 'monetary', options)
                            })
                            company_fact += manager_fact
                            office_fact += manager_fact
                office['margin'].update({'fact': self._build_value_dict(office_fact, 'monetary', options)})
            company['margin'].update({'fact': self._build_value_dict(company_fact, 'monetary', options)})
        companies_fact = sum(d.amount for d in fact_data)
        result['margin'].update({'fact': self._build_value_dict(companies_fact, 'monetary', options)})

        plan_data = planned_indicators.filtered(lambda p: p.type_row == 'margin_income')
        kam_plan_data = kam_planned_indicators.filtered(lambda p: p.type_row == 'margin_income')
        use_plan_6_6 = any(d.q3_plan_6_6 or d.q4_plan_6_6 for d in plan_data)
        kam_use_plan_6_6 = any(d.q3_plan_6_6 or d.q4_plan_6_6 for d in kam_plan_data)
        for company in result['companies']:
            company_plan = 0
            for office in company['offices']:
                for o, group in groupby(sorted(plan_data, key=lambda i: i.budget_plan_supervisor_id.project_office_id.id), lambda fi: fi.budget_plan_supervisor_id.project_office_id):
                    if office['id'] == o.id:
                        if use_plan_6_6:
                            office_plan = sum(
                                indicator.q3_plan_6_6 + indicator.q4_plan_6_6 + indicator.q1_fact + indicator.q2_fact
                                for indicator in group
                            )
                        else:
                            office_plan = sum(
                                indicator.q1_plan + indicator.q2_plan + indicator.q3_plan + indicator.q4_plan
                                for indicator in group
                            )
                        company_plan += office_plan
                        office['margin'].update({
                            'plan': self._build_value_dict(office_plan, 'monetary', options),
                            'to_plan': round((office['margin']['fact']['no_format'] / office_plan) * 100, 2)
                            if office['margin'].get('fact') and office_plan > 0 else 0
                        })
                for manager in office['managers']:
                    for m, group in groupby(
                        sorted(
                            kam_plan_data.filtered(lambda p: p.budget_plan_kam_id.project_office_id.id == office['id']),
                            key=lambda i: i.budget_plan_kam_id.key_account_manager_id.id
                        ),
                        lambda fi: fi.budget_plan_kam_id.key_account_manager_id
                    ):
                        if manager['id'] == m.id:
                            if kam_use_plan_6_6:
                                manager_plan = sum(
                                    indicator.q3_plan_6_6 + indicator.q4_plan_6_6 + indicator.q1_fact + indicator.q2_fact
                                    for indicator in group
                                )
                            else:
                                manager_plan = sum(
                                    indicator.q1_plan + indicator.q2_plan + indicator.q3_plan + indicator.q4_plan
                                    for indicator in group
                                )
                            manager['margin'].update({
                                'plan': self._build_value_dict(manager_plan, 'monetary', options),
                                'to_plan': round((manager['margin']['fact']['no_format'] / manager_plan) * 100, 2)
                                if manager['margin'].get('fact') and manager_plan > 0 else 0
                            })
            company['margin'].update({
                'plan': self._build_value_dict(company_plan, 'monetary', options),
                'to_plan': round((company['margin']['fact']['no_format'] / company_plan) * 100, 2)
                if company['margin'].get('fact') and company_plan > 0 else 0
            })
        if use_plan_6_6:
            companies_plan = sum(d.q3_plan_6_6 + d.q4_plan_6_6 + d.q1_fact + d.q2_fact for d in plan_data)
        else:
            companies_plan = sum(d.q1_plan + d.q2_plan + d.q3_plan + d.q4_plan for d in plan_data)
        result['margin'].update({'plan': self._build_value_dict(companies_plan, 'monetary', options)})

        # TODO: Добавить распределение в маржу?
        fact_gross_revenue_data = financial_indicators.filtered(
            lambda fi: fi.type == 'gross_revenue' and not fi.forecast_probability_id)

        forecast_data = financial_indicators.filtered(
            lambda fi: fi.type == 'gross_revenue' and fi.profitability > 0 and fi.forecast_probability_id and (
                    fi.forecast_probability_id.id == 3 or fi.forecast_probability_id.id == 4))
        closed_forecasts = self._auto_close_forecast_by_fact(fact_gross_revenue_data, forecast_data, 'quarterly')
        companies_forecast = 0
        for data in forecast_data.filtered(lambda d: d.amount - d.distribution > 0):
            if not any(distribution.fact_acceptance_flow_id.margin_manual_input
                       for distribution in data.planned_acceptance_flow_id.distribution_acceptance_ids):
                companies_forecast += closed_forecasts.get(data.id, data.amount - data.distribution)\
                                      * data.forecast_probability_id.coefficient * data.profitability
        result['margin'].update({'forecast': self._build_value_dict(companies_forecast, 'monetary', options)})

        result['margin'].update({
            'percentage': round((companies_fact / companies_plan) * 100, 2)
            if companies_plan > 0 else 0
        })

    def _auto_close_forecast_by_fact(self, fact_indicators, forecast_indicators, close_mode):

        def _keys_groupby(indicator):
            if close_mode == 'at_date':
                return indicator.project_id.id, indicator.date
            elif close_mode == 'monthly':
                return indicator.project_id.id, indicator.date.month
            elif close_mode == 'quarterly':
                return indicator.project_id.id, date_utils.get_quarter_number(indicator.date)
            else:
                return indicator.project_id.id, indicator.date.year

        def _filter_fact_indicators(indicator):
            if close_mode == 'at_date':
                return indicator.project_id.id == k[0] and indicator.distribution == 0 and indicator.date == k[1]
            elif close_mode == 'monthly':
                return indicator.project_id.id == k[0] and indicator.distribution == 0 \
                    and indicator.date.month == k[1]
            elif close_mode == 'quarterly':
                return indicator.project_id.id == k[0] and indicator.distribution == 0 \
                    and date_utils.get_quarter_number(indicator.date) == k[1]
            else:
                return indicator.project_id.id == k[0] and indicator.distribution == 0 \
                    and indicator.date.year == k[1]

        def _filter_redistribution_indicators(indicator):
            if close_mode == 'at_date':
                return indicator.project_id.id == k[0] and indicator.amount - indicator.distribution < 0 \
                    and indicator.date == k[1]
            elif close_mode == 'monthly':
                return indicator.project_id.id == k[0] and indicator.amount - indicator.distribution < 0 \
                    and indicator.date.month == k[1]
            elif close_mode == 'quarterly':
                return indicator.project_id.id == k[0] and indicator.amount - indicator.distribution < 0 \
                    and date_utils.get_quarter_number(indicator.date) == k[1]
            else:
                return indicator.project_id.id == k[0] and indicator.amount - indicator.distribution < 0 \
                    and indicator.date.year == k[1]

        result = dict()
        if close_mode != 'no':
            for k, group in groupby(
                    sorted(forecast_indicators.filtered(
                        lambda d: d.amount - d.distribution > 0 and not d.project_id.is_correction_project),
                        key=_keys_groupby),
                    key=_keys_groupby):
                fact_amount_by_project = sum(i.amount for i in fact_indicators.filtered(_filter_fact_indicators))
                redistribution_amount_by_project = sum(
                    i.distribution - i.amount for i in forecast_indicators.filtered(_filter_redistribution_indicators)
                    if i.distribution - i.amount <= 0)
                undistributed_amount_by_project = fact_amount_by_project + redistribution_amount_by_project
                if undistributed_amount_by_project > 0:
                    remaining_amount = undistributed_amount_by_project
                    for gr in sorted(group, key=lambda g: g.forecast_probability_id.sequence, reverse=True):
                        amount = gr.amount - gr.distribution
                        if remaining_amount <= 0:
                            break
                        if remaining_amount > amount:
                            remaining_amount = remaining_amount - amount
                            result[gr.id] = 0
                        else:
                            result[gr.id] = amount - remaining_amount
                            remaining_amount = 0
        return result

    # ------------------------------------------------------
    # OPTIONS
    # ------------------------------------------------------

    @api.model
    def get_options(self, previous_options=None):
        options = {}
        self._init_options_period(options, previous_options)
        self._init_options_rounding_unit(options)
        return options

    def _init_options_period(self, options, previous_options=None):
        previous_period_options = (previous_options or {}).get('date', {})
        date = fields.Date.context_today(self) if not previous_period_options.get('period', False) \
            else fields.Date.context_today(self) + relativedelta(years=previous_period_options['period'])
        dates = compute_year_dates(date)
        date_from = dates['date_from']
        date_to = dates['date_to']

        options['date'] = dict(
            period_type='year',
            string=date_to.strftime('%Y'),
            date_from=date_from and fields.Date.to_string(date_from) or False,
            date_to=fields.Date.to_string(date_to),
            period=previous_period_options.get('period', 0)
        )

    def _init_options_rounding_unit(self, options):
        default = 'thousands'
        options['rounding_unit'] = default
        options['rounding_unit_names'] = self._get_rounding_unit_names()

    def _get_rounding_unit_names(self):
        currency_symbol = self.env.company.currency_id.symbol

        return dict(
            decimals=_('.%s') % currency_symbol,
            thousands=_('K%s') % currency_symbol,
            millions=_('M%s') % currency_symbol,
            billions=_('B%s') % currency_symbol
        )

    # ------------------------------------------------------
    # FORMAT METHODS
    # ------------------------------------------------------

    @api.model
    def format_data_values(self, options, data):
        if hasattr(data, 'items'):
            for k, v in data.items():
                if k == 'no_format':
                    data['value'] = self._format_value(options, data['no_format'], currency=data['currency'],
                                                       figure_type=data['figure_type'], digits=data['digits'])
                    data['rounded_value'] = self._round_value(options, data['no_format'], digits=data['digits'])
                if isinstance(v, dict):
                    self.format_data_values(options, v)
                elif isinstance(v, list):
                    for d in v:
                        self.format_data_values(options, d)
        return data

    def _build_value_dict(self, value, figure_type, options=None, currency=False, digits=2):
        if value is None:
            return {}

        options = options or {}
        return {
            'currency': currency,
            'digits': digits,
            'figure_type': figure_type,
            'value': self._format_value(options, value, currency=currency, figure_type=figure_type, digits=digits),
            'rounded_value': self._round_value(options, value, digits=digits),
            'no_format': value
        }

    def _round_value(self, options, value, digits=2):
        return floatRound(value, digits, rounding_method='HALF-UP', rounding_unit=options.get('rounding_unit'))

    def _format_value(self, options, value, currency=None, figure_type=None, digits=2):
        if value is None:
            return ''

        if figure_type == 'none':
            return value

        if isinstance(value, str) or figure_type == 'string':
            return str(value)

        if figure_type == 'monetary':
            digits = (currency or self.env.company.currency_id).decimal_places
            currency = None
        elif figure_type == 'integer':
            currency = None
            digits = 0
        elif figure_type == 'boolean':
            return _('Yes') if bool(value) else _('No')
        elif figure_type in ('date', 'datetime'):
            return format_date(self.env, value)
        else:
            currency = None

        formatted_amount = formatLang(self.env, value, digits, currency_obj=currency,
                                      rounding_method='HALF-UP', rounding_unit=options.get('rounding_unit'))

        if figure_type == 'percentage':
            return f'{formatted_amount}%'

        return formatted_amount
