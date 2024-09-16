import logging

from datetime import datetime, timedelta
from itertools import groupby

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from ..tools.misc import formatLang, floatRound
from odoo.tools.misc import format_date

_logger = logging.getLogger(__name__)


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

        self._prepare_contraction_data(result, planned_indicators, financial_indicators, options)
        self._prepare_cash_flow_data(result, planned_indicators, financial_indicators, options)
        self._prepare_gross_revenue_data(result, planned_indicators, financial_indicators, options)
        self._prepare_margin_data(result, planned_indicators, financial_indicators, options)

        return result

    # ------------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------------

    def _prepare_contraction_data(self, result, planned_indicators, financial_indicators, options):
        for company in result['companies']:
            company['contraction'] = dict()

        fact_data = financial_indicators.filtered(
            lambda fi: fi.type == 'contracting' and fi.stage_id.project_state == 'won')
        for company in result['companies']:
            for c, group in groupby(fact_data, lambda fi: fi.company_id):
                if company['id'] == c.id:
                    company['contraction'].update({
                        'fact': self._build_value_dict(sum(indicator.amount for indicator in group), 'monetary',
                                                       options)
                    })
        companies_fact = sum(d.amount for d in fact_data)
        result['contraction'].update({'fact': self._build_value_dict(companies_fact, 'monetary', options)})

        plan_data = planned_indicators.filtered(lambda p: p.type_row == 'contracting')
        for company in result['companies']:
            for c, group in groupby(plan_data, lambda fi: fi.company_id):
                if company['id'] == c.id:
                    company_plan = sum(
                        indicator.q1_plan + indicator.q2_plan + indicator.q3_plan + indicator.q4_plan
                        for indicator in group
                    )
                    company['contraction'].update({
                        'plan': self._build_value_dict(company_plan, 'monetary', options),
                        'to_plan': round((company['contraction']['fact']['no_format'] / company_plan) * 100, 2)
                        if company['contraction'].get('fact') and company_plan > 0 else 0
                    })
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

    def _prepare_cash_flow_data(self, result, planned_indicators, financial_indicators, options):
        for company in result['companies']:
            company['cash_flow'] = dict()

        fact_data = financial_indicators.filtered(
            lambda fi: fi.type == 'cash_flow' and not fi.forecast_probability_id)
        for company in result['companies']:
            for c, group in groupby(fact_data, lambda fi: fi.company_id):
                if company['id'] == c.id:
                    company['cash_flow'].update({
                        'fact': self._build_value_dict(sum(indicator.amount for indicator in group), 'monetary',
                                                       options)
                    })
        companies_fact = sum(d.amount for d in fact_data)
        result['cash_flow'].update({'fact': self._build_value_dict(companies_fact, 'monetary', options)})

        plan_data = planned_indicators.filtered(lambda p: p.type_row == 'cash')
        for company in result['companies']:
            for c, group in groupby(plan_data, lambda fi: fi.company_id):
                if company['id'] == c.id:
                    company_plan = sum(
                        indicator.q1_plan + indicator.q2_plan + indicator.q3_plan + indicator.q4_plan
                        for indicator in group
                    )
                    company['cash_flow'].update({
                        'plan': self._build_value_dict(company_plan, 'monetary', options),
                        'to_plan': round((company['cash_flow']['fact']['no_format'] / company_plan) * 100, 2)
                        if company['cash_flow'].get('fact') and company_plan > 0 else 0
                    })
        companies_plan = sum(d.q1_plan + d.q2_plan + d.q3_plan + d.q4_plan for d in plan_data)
        result['cash_flow'].update({'plan': self._build_value_dict(companies_plan, 'monetary', options)})

        forecast_data = financial_indicators.filtered(lambda fi: fi.type == 'cash_flow' and fi.forecast_probability_id)
        forecasts_with_fact = self._clear_forecast_data(fact_data, forecast_data)
        companies_forecast = sum(forecasts_with_fact.get(d.id, d.amount) * d.forecast_probability_id.coefficient
                                 for d in forecast_data)
        result['cash_flow'].update({'forecast': self._build_value_dict(companies_forecast, 'monetary', options)})

        result['cash_flow'].update({
            'percentage': round((companies_fact / companies_plan) * 100, 2)
            if companies_plan > 0 else 0
        })

    def _prepare_gross_revenue_data(self, result, planned_indicators, financial_indicators, options):
        for company in result['companies']:
            company['gross_revenue'] = dict()

        fact_data = financial_indicators.filtered(
            lambda fi: fi.type == 'gross_revenue' and not fi.forecast_probability_id)
        for company in result['companies']:
            for c, group in groupby(fact_data, lambda fi: fi.company_id):
                if company['id'] == c.id:
                    company['gross_revenue'].update({
                        'fact': self._build_value_dict(sum(indicator.amount for indicator in group), 'monetary',
                                                       options)
                    })
        companies_fact = sum(d.amount for d in fact_data)
        result['gross_revenue'].update({'fact': self._build_value_dict(companies_fact, 'monetary', options)})

        plan_data = planned_indicators.filtered(lambda p: p.type_row == 'acceptance')
        for company in result['companies']:
            for c, group in groupby(plan_data, lambda fi: fi.company_id):
                if company['id'] == c.id:
                    company_plan = sum(
                        indicator.q1_plan + indicator.q2_plan + indicator.q3_plan + indicator.q4_plan
                        for indicator in group
                    )
                    company['gross_revenue'].update({
                        'plan': self._build_value_dict(company_plan, 'monetary', options),
                        'to_plan': round((company['gross_revenue']['fact']['no_format'] / company_plan) * 100, 2)
                        if company['gross_revenue'].get('fact') and company_plan > 0 else 0
                    })
        companies_plan = sum(d.q1_plan + d.q2_plan + d.q3_plan + d.q4_plan for d in plan_data)
        result['gross_revenue'].update({'plan': self._build_value_dict(companies_plan, 'monetary', options)})

        forecast_data = financial_indicators.filtered(
            lambda fi: fi.type == 'gross_revenue' and fi.forecast_probability_id)
        forecasts_with_fact = self._clear_forecast_data(fact_data, forecast_data)
        companies_forecast = sum(forecasts_with_fact.get(d.id, d.amount) * d.forecast_probability_id.coefficient
                                 for d in forecast_data)
        result['gross_revenue'].update({'forecast': self._build_value_dict(companies_forecast, 'monetary', options)})

        result['gross_revenue'].update({
            'percentage': round((companies_fact / companies_plan) * 100, 2)
            if companies_plan > 0 else 0
        })

    def _prepare_margin_data(self, result, planned_indicators, financial_indicators, options):
        for company in result['companies']:
            company['margin'] = dict()

        fact_data = financial_indicators.filtered(
            lambda fi: fi.type == 'margin' and not fi.forecast_probability_id)
        for company in result['companies']:
            for c, group in groupby(fact_data, lambda fi: fi.company_id):
                if company['id'] == c.id:
                    company['margin'].update({
                        'fact': self._build_value_dict(sum(indicator.amount for indicator in group), 'monetary',
                                                       options)
                    })
        companies_fact = sum(d.amount for d in fact_data)
        result['margin'].update({'fact': self._build_value_dict(companies_fact, 'monetary', options)})

        plan_data = planned_indicators.filtered(lambda p: p.type_row == 'margin_income')
        for company in result['companies']:
            for c, group in groupby(plan_data, lambda fi: fi.company_id):
                if company['id'] == c.id:
                    company_plan = sum(
                        indicator.q1_plan + indicator.q2_plan + indicator.q3_plan + indicator.q4_plan
                        for indicator in group
                    )
                    company['margin'].update({
                        'plan': self._build_value_dict(company_plan, 'monetary', options),
                        'to_plan': round((company['margin']['fact']['no_format'] / company_plan) * 100, 2)
                        if company['margin'].get('fact') and company_plan > 0 else 0
                    })
        companies_plan = sum(d.q1_plan + d.q2_plan + d.q3_plan + d.q4_plan for d in plan_data)
        result['margin'].update({'plan': self._build_value_dict(companies_plan, 'monetary', options)})

        forecast_data = financial_indicators.filtered(
            lambda fi: fi.type == 'gross_revenue' and fi.forecast_probability_id)
        forecasts_with_fact = self._clear_forecast_data(fact_data, forecast_data)
        companies_forecast = sum(forecasts_with_fact.get(d.id, d.amount) * d.forecast_probability_id.coefficient
                                 for d in forecast_data)
        result['margin'].update({'forecast': self._build_value_dict(companies_forecast, 'monetary', options)})

        result['margin'].update({
            'percentage': round((companies_fact / companies_plan) * 100, 2)
            if companies_plan > 0 else 0
        })

    def _clear_forecast_data(self, fact_indicators, forecast_indicators):
        result = dict()
        for project, group in groupby(
                forecast_indicators.filtered(lambda d: not d.distribution and not d.project_id.is_correction_project),
                lambda pr: pr.project_id):
            sum_fact_by_project = sum(
                p.amount for p in fact_indicators.filtered(lambda pr: pr.project_id.id == project.id))
            if sum_fact_by_project > 0:
                _logger.warning('Нашли факт %s у проекта %d. Раскидываем его по прогнозу.', sum_fact_by_project, sr.id)
                remaining_amount = sum_fact_by_project
                for gr in sorted(group, key=lambda g: g.forecast_probability_id.sequence, reverse=True):
                    if remaining_amount <= 0:
                        break
                    if remaining_amount > gr.amount:
                        remaining_amount = remaining_amount - gr.amount
                        result[gr.id] = 0
                    else:
                        result[gr.id] = gr.amount - remaining_amount
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
                    data['rounded_value'] = self._round_value(options, data['no_format'], digits=data['digits']),
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
