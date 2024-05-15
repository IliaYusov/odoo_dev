from odoo import models
import datetime
from xlsxwriter.utility import xl_col_to_name


class ReportBudgetPlanFactExcel(models.AbstractModel):
    _name = 'report.project_budget.report_budget_plan_fact_excel'
    _description = 'project_budget.report_budget_plan_fact_excel'
    _inherit = 'report.report_xlsx.abstract'

    POTENTIAL = 0.6  # коэффициент суммирования потенциала
    KOEFF_RESERVE = 1.0  # легаси из отчета прогноз и УК, оставлю на случай возврата
    KOEFF_POTENTIAL = 1.0

    section_names = ['contracting', 'cash', 'acceptance', 'margin_income', 'margin3_income',]
    company_section_names = ['contracting', 'cash', 'acceptance', 'margin_income', 'margin3_income', 'ebit', 'net_profit']
    quarter_names = ['Q1', 'Q2', 'Q3', 'Q4',]
    probability_names = ['100', '75', '50', '30', 'plan']
    section_titles = {
        'contracting': 'Контрактование,\n руб. с НДС',
        'cash': 'ПДС,\n руб. с НДС',
        'acceptance': 'Выручка,\n руб. без НДС',
        'margin_income': 'МАРЖА 1,\n руб. без НДС',
        'margin3_income': 'МАРЖА 3,\n руб.',
    }
    company_section_titles = {
        'contracting': 'Контрактование,\n руб. с НДС',
        'cash': 'ПДС,\n руб. с НДС',
        'acceptance': 'Выручка,\n руб. без НДС',
        'margin_income': 'МАРЖА 1,\n руб. без НДС',
        'margin3_income': 'МАРЖА 3,\n руб.',
        'ebit': 'EBIT,\n руб.',
        'net_profit': 'Чистая прибыль,\n руб.',
    }

    def is_step_in_year(self, project, step, year):
        if project:
            if step:
                if step.stage_id.code == '0':  # проверяем последний зафиксированный бюджет в предыдущих годах
                    last_fixed_step = self.env['project_budget.project_steps'].search(
                        [('date_actual', '<', datetime.date(year, 1, 1)),
                         ('budget_state', '=', 'fixed'),
                         ('step_id', '=', step.step_id),
                         ], limit=1, order='date_actual desc')
                    if last_fixed_step and last_fixed_step.stage_id.code == '0':
                        return False

                if (year <= step.end_presale_project_month.year <= year + 2)\
                        or (year <= step.end_sale_project_month.year <= year + 2)\
                        or (step.end_presale_project_month.year <= year and step.end_sale_project_month.year >= year + 2):
                    return True
                for pds in project.planned_cash_flow_ids:
                    if pds.project_steps_id.id == step.id:
                        if year <= pds.date_cash.year <= year + 2:
                            return True
                for pds in project.fact_cash_flow_ids:
                    if pds.project_steps_id.id == step.id:
                        if year <= pds.date_cash.year <= year + 2:
                            return True
                for act in project.planned_acceptance_flow_ids:
                    if act.project_steps_id.id == step.id:
                        if year <= act.date_cash.year <= year + 2:
                            return True
                for act in project.fact_acceptance_flow_ids:
                    if act.project_steps_id.id == step.id:
                        if year <= act.date_cash.year <= year + 2:
                            return True
        return False

    def is_project_in_year(self, project, year):
        if project:
            if project.stage_id.code == '0':  # проверяем последний зафиксированный бюджет в предыдущих годах
                last_fixed_project = self.env['project_budget.projects'].search(
                    [('date_actual', '<', datetime.date(year, 1, 1)),
                     ('budget_state', '=', 'fixed'),
                     ('project_id', '=', project.project_id),
                     ], limit=1, order='date_actual desc')
                if last_fixed_project and last_fixed_project.stage_id.code == '0':
                    return False

            if not project.project_have_steps:
                if (year <= project.end_presale_project_month.year <= year + 2)\
                        or (year <= project.end_sale_project_month.year <= year + 2)\
                        or (project.end_presale_project_month.year <= year and project.end_sale_project_month.year >= year + 2):
                    return True
                for pds in project.planned_cash_flow_ids:
                    if year <= pds.date_cash.year <= year + 2:
                        return True
                for pds in project.fact_cash_flow_ids:
                    if year <= pds.date_cash.year <= year + 2:
                        return True
                for act in project.planned_acceptance_flow_ids:
                    if year <= act.date_cash.year <= year + 2:
                        return True
                for act in project.fact_acceptance_flow_ids:
                    if year <= act.date_cash.year <= year + 2:
                        return True
            else:
                for step in project.project_steps_ids:
                    if self.is_step_in_year(project, step, year):
                        return True
        return False

    def get_quarter_from_month(self, month):
        if month in (1, 2, 3):
            return 'Q1'
        if month in (4, 5, 6):
            return 'Q2'
        if month in (7, 8, 9):
            return 'Q3'
        if month in (10, 11, 12):
            return 'Q4'
        return False

    def get_months_from_quarter(self, quarter_name):
        if quarter_name == 'Q1':
            return 1, 2, 3
        elif quarter_name == 'Q2':
            return 4, 5, 6
        elif quarter_name == 'Q3':
            return 7, 8, 9
        elif quarter_name == 'Q4':
            return 10, 11, 12
        else:
            return False

    def get_sum_fact_pds_project_step_quarter(self, project, step, year, quarter):
        sum_cash = 0
        months = self.get_months_from_quarter(quarter)
        pds_list = project.fact_cash_flow_ids
        for pds in pds_list:
            if step:
                if pds.project_steps_id.id != step.id: 
                    continue
            if pds.date_cash.month in months and pds.date_cash.year == year:
                sum_cash += pds.sum_cash
        return sum_cash

    def get_sum_plan_pds_project_step_quarter(self, project, step, year, quarter):
        sum_cash = {'commitment': 0, 'reserve': 0}
        months = self.get_months_from_quarter(quarter)
        pds_list = project.planned_cash_flow_ids
        for pds in pds_list:
            if step:
                if pds.project_steps_id.id != step.id: 
                    continue
            if pds.date_cash.month in months and pds.date_cash.year == year:
                if step:
                    stage_id_name = step.stage_id.code
                else:
                    stage_id_name = project.stage_id.code

                if pds.forecast == 'from_project':

                    if stage_id_name in ('75', '100', '100(done)'):
                        sum_cash['commitment'] = sum_cash.get('commitment', 0) + pds.sum_cash
                    elif stage_id_name == '50':
                        sum_cash['reserve'] = sum_cash.get('reserve', 0) + pds.sum_cash
                else:
                    if stage_id_name != '0':
                        sum_cash[pds.forecast] = sum_cash.get(pds.forecast, 0) + pds.sum_cash
        return sum_cash

    def get_currency_rate_by_project(self, project):
        project_currency_rates = self.env['project_budget.project_currency_rates']
        return project_currency_rates._get_currency_rate_for_project_in_company_currency(project)

    def get_quarter_revenue_project(self, quarter, project, step, year):

        sum100tmp = 0
        sum75tmp = 0
        sum50tmp = 0
        sum30tmp = 0

        months = self.get_months_from_quarter(quarter)

        if months:
            if not step:
                if project.end_presale_project_month.month in months and project.end_presale_project_month.year == year:
                    currency_rate = self.get_currency_rate_by_project(project)
                    if project.stage_id.code in ('100', '100(done)'):
                        sum100tmp += project.total_amount_of_revenue_with_vat * currency_rate
                    if project.stage_id.code == '75':
                        sum75tmp += project.total_amount_of_revenue_with_vat * currency_rate
                    if project.stage_id.code == '50':
                        sum50tmp += project.total_amount_of_revenue_with_vat * self.KOEFF_RESERVE * currency_rate
                    if project.stage_id.code == '30':
                        sum30tmp += project.total_amount_of_revenue_with_vat * self.KOEFF_POTENTIAL * currency_rate
            else:
                if step.end_presale_project_month.month in months and step.end_presale_project_month.year == year:
                    currency_rate = self.get_currency_rate_by_project(step.projects_id)
                    if step.stage_id.code in ('100', '100(done)'):
                        sum100tmp = step.total_amount_of_revenue_with_vat * currency_rate
                    if step.stage_id.code == '75':
                        sum75tmp = step.total_amount_of_revenue_with_vat * currency_rate
                    if step.stage_id.code == '50':
                        sum50tmp = step.total_amount_of_revenue_with_vat * self.KOEFF_RESERVE * currency_rate
                    if step.stage_id.code == '30':
                        sum30tmp = step.total_amount_of_revenue_with_vat * self.KOEFF_POTENTIAL * currency_rate

        return sum100tmp, sum75tmp, sum50tmp, sum30tmp

    def get_quarter_pds_project(self, quarter, project, step, year):

        sum75tmp = sum50tmp = 0

        sum = {'commitment': 0, 'reserve': 0, 'potential': 0}

        months = self.get_months_from_quarter(quarter)

        sum100tmp = self.get_sum_fact_pds_project_step_quarter(project, step, year, quarter)

        sum = self.get_sum_plan_pds_project_step_quarter(project, step, year, quarter)

        if not project.is_correction_project:
            if sum100tmp >= sum.get('commitment', 0):
                sum100tmp_ostatok = sum100tmp - sum['commitment']
                sum['commitment'] = 0
                sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
            else:
                sum['commitment'] = sum['commitment'] - sum100tmp

        # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плана
        sum_ostatok_pds = {'commitment': 0, 'reserve': 0, 'potential': 0}
        sum_distribution_pds = 0
        for planned_cash_flow in project.planned_cash_flow_ids:
            if step:
                if planned_cash_flow.project_steps_id.id != step.id:
                    continue
            if planned_cash_flow.date_cash.month in months and planned_cash_flow.date_cash.year == year:
                sum_distribution_pds += planned_cash_flow.distribution_sum_without_vat
                stage_id_name = project.stage_id.code
                if step:
                    stage_id_name = step.stage_id.code

                if planned_cash_flow.forecast == 'from_project':
                    if stage_id_name in ('75', '100', '100(done)'):
                        sum_ostatok_pds['commitment'] = sum_ostatok_pds.get('commitment', 0) + planned_cash_flow.distribution_sum_with_vat_ostatok
                    elif stage_id_name == '50':
                        sum_ostatok_pds['reserve'] = sum_ostatok_pds.get('reserve', 0) + planned_cash_flow.distribution_sum_with_vat_ostatok
                else:
                    if stage_id_name != '0':
                        sum_ostatok_pds[planned_cash_flow.forecast] = sum_ostatok_pds.get(planned_cash_flow.forecast, 0) + planned_cash_flow.distribution_sum_with_vat_ostatok

        if sum_distribution_pds != 0:  # если есть распределение, то остаток = остатку распределения
            sum = sum_ostatok_pds
            for key in sum:
                if sum[key] < 0 and not project.is_correction_project:
                    sum[key] = 0

        if sum:
            sum75tmp += sum.get('commitment', 0)
            sum50tmp += sum.get('reserve', 0) * self.KOEFF_RESERVE

        return sum100tmp, sum75tmp, sum50tmp

    def get_sum_fact_acceptance_project_step_quarter(self, project, step, year, quarter):
        sum_cash = 0
        months = self.get_months_from_quarter(quarter)
        acceptance_list = project.fact_acceptance_flow_ids
        if acceptance_list:
            for acceptance in acceptance_list:
                if step:
                    if acceptance.project_steps_id.id != step.id:
                        continue
                if acceptance.date_cash.month in months and acceptance.date_cash.year == year:
                    sum_cash += acceptance.sum_cash_without_vat
        return sum_cash

    def get_sum_fact_margin_project_step_quarter(self, project, step, year, quarter):
        sum_cash = 0
        months = self.get_months_from_quarter(quarter)
        if project.is_parent_project:
            for child_project in project.child_project_ids:
                if child_project.project_have_steps:
                    for child_step in child_project.project_steps_ids:
                        sum_cash += self.get_sum_fact_margin_project_step_quarter(child_project, child_step, year,
                                                                                  quarter) * child_project.margin_rate_for_parent
                else:
                    sum_cash += self.get_sum_fact_margin_project_step_quarter(child_project, False, year, quarter) * child_project.margin_rate_for_parent
            return sum_cash
        acceptance_list = project.fact_acceptance_flow_ids
        if acceptance_list:
            for acceptance in acceptance_list:
                if step:
                    if acceptance.project_steps_id.id != step.id:
                        continue
                if acceptance.date_cash.month in months and acceptance.date_cash.year == year:
                    sum_cash += acceptance.margin
        return sum_cash

    def get_sum_planned_acceptance_project_step_quarter(self, project, step, year, quarter):
        sum_acceptance = {'commitment': 0, 'reserve': 0, 'potential': 0}

        months = self.get_months_from_quarter(quarter)

        acceptance_list = project.planned_acceptance_flow_ids
        if acceptance_list:
            for acceptance in acceptance_list:
                if step:
                    if acceptance.project_steps_id.id != step.id:
                        continue
                if acceptance.date_cash.month in months and acceptance.date_cash.year == year:
                    if step:
                        stage_id_name = step.stage_id.code
                    else:
                        stage_id_name = project.stage_id.code

                    if acceptance.forecast == 'from_project':
                        if stage_id_name in ('75', '100', '100(done)'):
                            sum_acceptance['commitment'] = sum_acceptance.get('commitment', 0) + acceptance.sum_cash_without_vat
                        elif stage_id_name == '50':
                            sum_acceptance['reserve'] = sum_acceptance.get('reserve', 0) + acceptance.sum_cash_without_vat
                    else:
                        if stage_id_name != '0':
                            sum_acceptance[acceptance.forecast] = sum_acceptance.get(acceptance.forecast, 0) + acceptance.sum_cash_without_vat
        return sum_acceptance

    def get_sum_planned_margin_project_step_quater(self, project, step, year, quarter):
        sum_margin = {'commitment': 0, 'reserve': 0, 'potential': 0}

        months = self.get_months_from_quarter(quarter)
        if project.is_parent_project:
            for child_project in project.child_project_ids:
                if child_project.project_have_steps:
                    for child_step in child_project.project_steps_ids:
                        for key in sum_margin:
                            sum_margin[key] += self.get_sum_planned_margin_project_step_quater(
                                child_project, child_step, year, quarter)[key] * child_project.margin_rate_for_parent
                else:
                    for key in sum_margin:
                        sum_margin[key] += self.get_sum_planned_margin_project_step_quater(child_project, False, year, quarter)[key] * child_project.margin_rate_for_parent
            return sum_margin
        acceptance_list = project.planned_acceptance_flow_ids
        if acceptance_list:
            for acceptance in acceptance_list:
                if any(distribution.fact_acceptance_flow_id.margin_manual_input for distribution in
                       acceptance.distribution_acceptance_ids):  # если есть ручная маржа - пропускаем
                    continue
                if step:
                    if acceptance.project_steps_id.id != step.id:
                        continue
                    stage_id_name = step.stage_id.code
                    profitability = step.profitability
                else:
                    stage_id_name = project.stage_id.code
                    profitability = project.profitability
                if acceptance.date_cash.month in months and acceptance.date_cash.year == year:
                    if acceptance.forecast == 'from_project':
                        if stage_id_name in ('75', '100', '100(done)'):
                            sum_margin['commitment'] += acceptance.sum_cash_without_vat * profitability / 100
                        elif stage_id_name == '50':
                            sum_margin['reserve'] += acceptance.sum_cash_without_vat * profitability / 100
                    else:
                        if stage_id_name != '0':
                            sum_margin[acceptance.forecast] += acceptance.sum_cash_without_vat * profitability / 100
        return sum_margin

    def get_margin_forecast_from_distributions(self, planned_acceptance, margin_plan, project, step, margin_rate_for_parent):
        # суммируем доли маржи фактов в соотношении (сумма распределения/суммы факта)
        margin_distribution = 0
        for distribution in planned_acceptance.distribution_acceptance_ids:
            if distribution.fact_acceptance_flow_id.sum_cash_without_vat != 0:
                margin_distribution += distribution.fact_acceptance_flow_id.margin * distribution.sum_cash_without_vat / distribution.fact_acceptance_flow_id.sum_cash_without_vat
        stage_id_name = project.stage_id.code
        if step:
            stage_id_name = step.stage_id.code

        if planned_acceptance.forecast == 'from_project':
            if stage_id_name in ('75', '100', '100(done)'):
                margin_plan['commitment'] -= margin_distribution * margin_rate_for_parent
            elif stage_id_name == '50':
                margin_plan['reserve'] -= margin_distribution * margin_rate_for_parent
        else:
            if stage_id_name != '0':
                margin_plan[planned_acceptance.forecast] -= margin_distribution * margin_rate_for_parent
        return margin_plan

    def get_sum_planned_acceptance_project_step_from_distribution(self, project, step, year, quarter):
        # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плана
        sum_ostatok_acceptance = {'commitment': 0, 'reserve': 0, 'potential': 0}
        sum_distribution_acceptance = 0
        months = self.get_months_from_quarter(quarter)

        for planned_acceptance_flow in project.planned_acceptance_flow_ids:
            if step:
                if planned_acceptance_flow.project_steps_id.id != step.id:
                    continue
            if planned_acceptance_flow.date_cash.month in months and planned_acceptance_flow.date_cash.year == year:
                sum_distribution_acceptance += planned_acceptance_flow.distribution_sum_without_vat

                stage_id_name = project.stage_id.code
                if step:
                    stage_id_name = step.stage_id.code

                if planned_acceptance_flow.forecast == 'from_project':
                    if stage_id_name in ('75', '100', '100(done)'):
                        sum_ostatok_acceptance['commitment'] = sum_ostatok_acceptance.get('commitment',
                                                                                          0) + planned_acceptance_flow.distribution_sum_without_vat_ostatok
                    elif stage_id_name == '50':
                        sum_ostatok_acceptance['reserve'] = sum_ostatok_acceptance.get('reserve',
                                                                                       0) + planned_acceptance_flow.distribution_sum_without_vat_ostatok
                else:
                    if stage_id_name != '0':
                        sum_ostatok_acceptance[planned_acceptance_flow.forecast] = sum_ostatok_acceptance.get(
                            planned_acceptance_flow.forecast,
                            0) + planned_acceptance_flow.distribution_sum_without_vat_ostatok

        if sum_distribution_acceptance:  # если есть распределение, то остаток = остатку распределения
            return sum_ostatok_acceptance
        else:
            return False

    def get_sum_planned_margin_project_step_from_distribution(self, project, step, year, quarter, margin_plan, margin_rate_for_parent):
        # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
        sum_distribution_acceptance = 0
        new_margin_plan = margin_plan.copy()
        months = self.get_months_from_quarter(quarter)

        if project.is_parent_project:
            for child_project in project.child_project_ids:
                if child_project.project_have_steps:
                    for child_step in child_project.project_steps_ids:
                        new_margin_plan = self.get_sum_planned_margin_project_step_from_distribution(
                            child_project, child_step, year, quarter, margin_plan, child_project.margin_rate_for_parent)
                        if new_margin_plan:
                            margin_plan = new_margin_plan
                else:
                    new_margin_plan = self.get_sum_planned_margin_project_step_from_distribution(child_project, False, year, quarter, margin_plan, child_project.margin_rate_for_parent)
                    if new_margin_plan:
                        margin_plan = new_margin_plan

            return margin_plan
        for planned_acceptance_flow in project.planned_acceptance_flow_ids:
            if any(distribution.fact_acceptance_flow_id.margin_manual_input for distribution in
                   planned_acceptance_flow.distribution_acceptance_ids):  # если есть ручная маржа - пропускаем
                continue
            if step:
                if planned_acceptance_flow.project_steps_id.id != step.id:
                    continue
            if planned_acceptance_flow.date_cash.month in months and planned_acceptance_flow.date_cash.year == year:
                sum_distribution_acceptance += planned_acceptance_flow.distribution_sum_without_vat

                new_margin_plan = self.get_margin_forecast_from_distributions(
                    planned_acceptance_flow, new_margin_plan, project, step, margin_rate_for_parent)
        if sum_distribution_acceptance:  # если есть распределение, то остаток = остатку распределения
            return new_margin_plan
        else:
            return False

    def get_quarter_acceptance_project(self, quarter, project, step, year):

        sum75tmp = sum50tmp = margin75tmp = margin50tmp = 0

        margin_rate_for_child = 1
        if project.is_child_project:
            margin_rate_for_child = (1 - project.margin_rate_for_parent)

        sum100tmp = self.get_sum_fact_acceptance_project_step_quarter(project, step, year, quarter)
        margin100tmp = self.get_sum_fact_margin_project_step_quarter(project, step, year, quarter) * margin_rate_for_child

        sum = self.get_sum_planned_acceptance_project_step_quarter(project, step, year, quarter)
        margin_sum = self.get_sum_planned_margin_project_step_quater(project, step, year, quarter)

        margin_plan = {'commitment': 0, 'reserve': 0, 'potential': 0}

        if margin_sum:
            margin_plan = margin_sum.copy()

        if not project.is_correction_project and not project.is_parent_project:

            if sum100tmp >= sum.get('commitment', 0):
                sum100tmp_ostatok = sum100tmp - sum['commitment']
                sum['commitment'] = 0
                sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
            else:
                sum['commitment'] = sum['commitment'] - sum100tmp

            if margin100tmp >= margin_plan['commitment']:  # маржа если нет распределения
                margin100tmp_ostatok = margin100tmp - margin_plan['commitment']
                margin_sum['commitment'] = 0
                margin_sum['reserve'] = max(margin_plan['reserve'] - margin100tmp_ostatok, 0)
            else:
                margin_sum['commitment'] = margin_plan['commitment'] - margin100tmp

        sum_ostatok_acceptance = self.get_sum_planned_acceptance_project_step_from_distribution(project, step, year, quarter)
        new_margin_plan = self.get_sum_planned_margin_project_step_from_distribution(project, step, year, quarter, margin_plan, 1)

        if sum_ostatok_acceptance:
            sum = sum_ostatok_acceptance
        if new_margin_plan:
            margin_sum = new_margin_plan

        for key in sum:
            if not project.is_correction_project:
                sum[key] = max(sum[key], 0)
                margin_sum[key] = max(margin_sum[key], 0)

        if sum:
            sum75tmp += sum.get('commitment', 0)
            margin75tmp += margin_sum.get('commitment', 0) * margin_rate_for_child
            sum50tmp += sum.get('reserve', 0) * self.KOEFF_RESERVE
            margin50tmp += margin_sum.get('reserve', 0) * self.KOEFF_RESERVE * margin_rate_for_child

        return sum100tmp, sum75tmp, sum50tmp, margin100tmp, margin75tmp, margin50tmp

    def get_section_data_from_project(self, spec, step, year, data):

        company = spec.company_id.name
        office = spec.project_office_id.name
        manager = spec.project_manager_id.name

        if step and spec.legal_entity_signing_id.different_project_offices_in_steps:
            office = step.project_office_id.name

        section_data = {}

        for section in self.section_names:
            section_data[section] = {}

        for quarter in self.quarter_names:
            section_data['contracting']['100'], section_data['contracting']['75'], section_data['contracting']['50'], \
            section_data['contracting']['30'] = self.get_quarter_revenue_project(quarter, spec, step, year)
            section_data['cash']['100'], section_data['cash']['75'], section_data['cash'][
                '50'] = self.get_quarter_pds_project(quarter, spec, step, year)
            section_data['acceptance']['100'], section_data['acceptance']['75'], section_data['acceptance'][
                '50'], section_data['margin_income']['100'], section_data['margin_income']['75'], section_data['margin_income'][
                '50'] = self.get_quarter_acceptance_project(quarter, spec, step, year)

            for section in self.section_names:
                for probability in self.probability_names:
                    res = section_data.get(section, {}).get(probability, 0)
                    data.setdefault(company, {}).setdefault(office, {}).setdefault(manager, {}).setdefault(section, {}).setdefault(year, {}).setdefault(quarter, {}).setdefault(probability, 0)
                    data[company][office][manager][section][year][quarter][probability] += res
                    data.setdefault(company, {}).setdefault(office, {}).setdefault(section, {}).setdefault(year, {}).setdefault(quarter, {}).setdefault(probability, 0)
                    data[company][office][section][year][quarter][probability] += res
                    data.setdefault(company, {}).setdefault(section, {}).setdefault(year, {}).setdefault(quarter, {}).setdefault(probability, 0)
                    data[company][section][year][quarter][probability] += res
                    parent_office = spec.project_office_id.parent_id
                    while parent_office:
                        data.setdefault(company, {}).setdefault(parent_office.name, {}).setdefault(section, {}).setdefault(year, {}).setdefault(quarter, {}).setdefault(probability, 0)
                        data[company][parent_office.name][section][year][quarter][probability] += res
                        parent_office = parent_office.parent_id

        return data


    def get_data_from_projects(self, cur_budget_projects, stages, year):
        data = {}

        for spec in cur_budget_projects:
            if spec.vgo == '-':

                if spec.project_have_steps:
                    for step in spec.project_steps_ids:
                        if not (self.is_step_in_year(spec, step, year) and step.stage_id.id in stages.ids):
                            continue

                        data = self.get_section_data_from_project(spec, step, year, data)

                else:
                    if not (self.is_project_in_year(spec, year) and spec.stage_id.id in stages.ids):
                        continue

                    data = self.get_section_data_from_project(spec, False, year, data)

        return data

    def get_plans(self, year, data):

        for company_section in self.company_section_names:
            for company in self.env['res.company'].search([('name', 'in', tuple(data.keys()))]):
                section_plan = self.env['project_budget.budget_plan_supervisor_spec'].search([
                    ('budget_plan_supervisor_id.year', '=', year),
                    ('budget_plan_supervisor_id.company_id', '=', company.id),
                    ('budget_plan_supervisor_id.is_company_plan', '=', True),
                    ('type_row', '=', company_section),
                ])
                data.setdefault(company.name, {}).setdefault(company_section, {}).setdefault(year, {}).setdefault('Q1', {})['plan'] = section_plan.q1_plan
                data.setdefault(company.name, {}).setdefault(company_section, {}).setdefault(year, {}).setdefault('Q2', {})['plan'] = section_plan.q2_plan
                data.setdefault(company.name, {}).setdefault(company_section, {}).setdefault(year, {}).setdefault('Q3', {})['plan'] = section_plan.q3_plan
                data.setdefault(company.name, {}).setdefault(company_section, {}).setdefault(year, {}).setdefault('Q4', {})['plan'] = section_plan.q4_plan
                for office_section in self.section_names:
                    for office in self.env['project_budget.project_office'].search([('name', 'in', tuple(data[company.name].keys()))]):
                        section_plan = self.env['project_budget.budget_plan_supervisor_spec'].search([
                            ('budget_plan_supervisor_id.year', '=', year),
                            ('budget_plan_supervisor_id.project_office_id', '=', office.id),
                            ('type_row', '=', office_section),
                        ])
                        data.setdefault(company.name, {}).setdefault(office.name, {}).setdefault(office_section, {}).setdefault(year, {}).setdefault('Q1', {})['plan'] = section_plan.q1_plan
                        data.setdefault(company.name, {}).setdefault(office.name, {}).setdefault(office_section, {}).setdefault(year, {}).setdefault('Q2', {})['plan'] = section_plan.q2_plan
                        data.setdefault(company.name, {}).setdefault(office.name, {}).setdefault(office_section, {}).setdefault(year, {}).setdefault('Q3', {})['plan'] = section_plan.q3_plan
                        data.setdefault(company.name, {}).setdefault(office.name, {}).setdefault(office_section, {}).setdefault(year, {}).setdefault('Q4', {})['plan'] = section_plan.q4_plan
                        parent_office = office.parent_id
                        while parent_office:
                            data.setdefault(company.name, {}).setdefault(parent_office.name, {}).setdefault(office_section, {}).setdefault(year, {}).setdefault('Q1', {}).setdefault('plan', 0)
                            data[company.name][parent_office.name][office_section][year]['Q1']['plan'] += section_plan.q1_plan
                            data.setdefault(company.name, {}).setdefault(parent_office.name, {}).setdefault(office_section, {}).setdefault(year, {}).setdefault('Q2', {}).setdefault('plan', 0)
                            data[company.name][parent_office.name][office_section][year]['Q2']['plan'] += section_plan.q2_plan
                            data.setdefault(company.name, {}).setdefault(parent_office.name, {}).setdefault(office_section, {}).setdefault(year, {}).setdefault('Q3', {}).setdefault('plan', 0)
                            data[company.name][parent_office.name][office_section][year]['Q3']['plan'] += section_plan.q3_plan
                            data.setdefault(company.name, {}).setdefault(parent_office.name, {}).setdefault(office_section, {}).setdefault(year, {}).setdefault('Q4', {}).setdefault('plan', 0)
                            data[company.name][parent_office.name][office_section][year]['Q4']['plan'] += section_plan.q4_plan
                            parent_office = parent_office.parent_id
                        for manager in self.env['project_budget.project_manager'].search(
                                [('name', 'in', tuple(data[company.name][office.name].keys()))]):
                            section_plan = self.env['project_budget.budget_plan_kam_spec'].search([
                                ('budget_plan_kam_id.year', '=', year),
                                ('budget_plan_kam_id.kam_id', '=', manager.id),
                                ('type_row', '=', office_section),
                            ])
                            data.setdefault(company.name, {}).setdefault(office.name, {}).setdefault(manager.name, {}).setdefault(office_section, {}).setdefault(year, {}).setdefault('Q1', {})['plan'] = section_plan.q1_plan
                            data.setdefault(company.name, {}).setdefault(office.name, {}).setdefault(manager.name, {}).setdefault(office_section, {}).setdefault(year, {}).setdefault('Q2', {})['plan'] = section_plan.q2_plan
                            data.setdefault(company.name, {}).setdefault(office.name, {}).setdefault(manager.name, {}).setdefault(office_section, {}).setdefault(year, {}).setdefault('Q3', {})['plan'] = section_plan.q3_plan
                            data.setdefault(company.name, {}).setdefault(office.name, {}).setdefault(manager.name, {}).setdefault(office_section, {}).setdefault(year, {}).setdefault('Q4', {})['plan'] = section_plan.q4_plan
        return data

    def print_rows(self, sheet, workbook, companies, project_offices, project_managers, year, data):

        office_heading_format = workbook.add_format({
            'bold': True,
            'border': 2,
            'font_size': 14,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '#,##0',
            'fg_color': '#D0CECE'
        })

        company_heading_format = workbook.add_format({
            'bold': True,
            'border': 2,
            'font_size': 15,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '#,##0',
            'fg_color': '#A0A0A0'
        })

        line_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "num_format": '#,##0',
        })

        bold_line_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "num_format": '#,##0',
        })

        bold_border_line_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'right': 2,
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "num_format": '#,##0',
        })

        bluegrey_percent_format = workbook.add_format({
            'border': 1,
            'right': 2,
            'left': 2,
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '0.00%',
            'fg_color': '#D6DCE4'
        })

        bluegrey_bold_percent_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'right': 2,
            'left': 2,
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '0.00%',
            'fg_color': '#D6DCE4'
        })

        grey_line_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '#,##0\ _₽;[Red]-#,##0\ _₽',
            'fg_color': '#E7E6E6'
        })

        grey_percent_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '0.00%',
            'fg_color': '#E7E6E6'
        })

        grey_borders_line_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'right': 2,
            'left': 2,
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '#,##0\ _₽;[Red]-#,##0\ _₽',
            'fg_color': '#E7E6E6'
        })

        bold_heading_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'right': 2,
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'bottom',
            "num_format": '#,##0',
        })

        heading_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'bottom',
            "num_format": '#,##0',
        })

        bluegrey_heading_format = workbook.add_format({
            'border': 1,
            'right': 2,
            'left': 2,
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'bottom',
            'num_format': '#,##0',
            'fg_color': '#D6DCE4'
        })

        grey_heading_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'top': 2,
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'bottom',
            'num_format': '#,##0',
            'fg_color': '#E7E6E6'
        })

        grey_borders_heading_format = workbook.add_format({
            'bold': True,
            'border': 2,
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'bottom',
            'num_format': '#,##0',
            'fg_color': '#E7E6E6'
        })

        row = 0
        column = 0

        sheet.set_row(row, 16)
        sheet.set_row(row + 1, 31)
        sheet.freeze_panes(2, 1)

        sheet.merge_range(row, column, row + 1, column, "Наименование показателя/ период", bold_heading_format)
        quarter_names_list = [f"I кв. {year}", f"II кв. {year}", f"III кв. {year}", f"IV кв. кв. {year}"]
        sheet.set_column(column, column, 16)
        for quarter in quarter_names_list:
            sheet.merge_range(row, column + 1, row, column + 4, quarter, bold_heading_format)
            sheet.write_string(row + 1, column + 1, 'ПЛАН', heading_format)
            sheet.write_string(row + 1, column + 2, 'ФАКТ', heading_format)
            sheet.write_string(row + 1, column + 3, 'ПРОГНОЗ (100%+60%)', heading_format)
            sheet.write_string(row + 1, column + 4, f'% исполнения плана Q{quarter_names_list.index(quarter) + 1}',
                               bluegrey_heading_format)
            sheet.set_column(column + 1, column + 4, 14)
            column += 4
        sheet.merge_range(row, column + 1, row, column + 5, f'ИТОГО {year}', grey_borders_heading_format)
        sheet.write_string(row + 1, column + 1, 'ПЛАН', grey_heading_format)
        sheet.write_string(row + 1, column + 2, 'ФАКТ', grey_heading_format)
        sheet.write_string(row + 1, column + 3, 'ПРОГНОЗ (100%+60%)', grey_heading_format)
        sheet.write_string(row + 1, column + 4, f'% исполнения плана {year}', grey_heading_format)
        sheet.write_string(row + 1, column + 5, 'Разница', grey_borders_heading_format)
        sheet.set_column(column + 1, column + 5, 14)
        row += 2

        for company in companies:

            company_data = data.get(company.name, False)
            if not company_data:
                continue

            print('company =', company.name)

            formula_company = []

            for project_office in project_offices:

                office_data = data[company.name].get(project_office.name, False)
                if not office_data:
                    continue

                print('project_office =', project_office.name)

                for project_manager in project_managers:

                    manager_data = data[company.name][project_office.name].get(project_manager.name, False)
                    if not manager_data:
                        continue

                    print('project_manager =', project_manager.name)

                    sheet.merge_range(row, 0, row, 21, f'{project_manager.name}',
                                      office_heading_format)  # печатаем заголовок КАМ
                    row += 1

                    for section in self.section_names:
                        column = 0
                        sheet.set_row(row, 31)
                        sheet.write_string(row, 0, self.section_titles[section], bold_border_line_format)
                        if 'margin' in section:
                            custom_line_format = bold_line_format
                            bluegrey_custom_percent_format = bluegrey_bold_percent_format
                        else:
                            custom_line_format = line_format
                            bluegrey_custom_percent_format = bluegrey_percent_format
                        for quarter in self.quarter_names:
                            sheet.write_number(row, column + 1, manager_data[section][year][quarter]['plan'],
                                               custom_line_format)
                            sheet.write_number(row, column + 2, manager_data[section][year][quarter]['100'],
                                               custom_line_format)
                            sheet.write_number(row, column + 3, manager_data[section][year][quarter]['75'] +
                                               manager_data[section][year][quarter]['50'] * self.POTENTIAL,
                                               custom_line_format)
                            formula = f'=IFERROR({xl_col_to_name(column + 2)}{row + 1}/{xl_col_to_name(column + 1)}{row + 1}, " ")'
                            sheet.write_formula(row, column + 4, formula, bluegrey_custom_percent_format)
                            column += 4
                        formula = (
                            f'={xl_col_to_name(column - 15)}{row + 1}'
                            f'+{xl_col_to_name(column - 11)}{row + 1}'
                            f'+{xl_col_to_name(column - 7)}{row + 1}'
                            f'+{xl_col_to_name(column - 3)}{row + 1}'
                        )
                        sheet.write_formula(row, column + 1, formula, grey_line_format)
                        formula = (
                            f'={xl_col_to_name(column - 14)}{row + 1}'
                            f'+{xl_col_to_name(column - 10)}{row + 1}'
                            f'+{xl_col_to_name(column - 6)}{row + 1}'
                            f'+{xl_col_to_name(column - 2)}{row + 1}'
                        )
                        sheet.write_formula(row, column + 2, formula, grey_line_format)
                        formula = (
                            f'={xl_col_to_name(column - 13)}{row + 1}'
                            f'+{xl_col_to_name(column - 9)}{row + 1}'
                            f'+{xl_col_to_name(column - 5)}{row + 1}'
                            f'+{xl_col_to_name(column - 1)}{row + 1}'
                            f'+{xl_col_to_name(column - 14)}{row + 1}'
                            f'+{xl_col_to_name(column - 10)}{row + 1}'
                            f'+{xl_col_to_name(column - 6)}{row + 1}'
                            f'+{xl_col_to_name(column - 2)}{row + 1}'
                        )
                        sheet.write_formula(row, column + 3, formula, grey_line_format)
                        formula = f'=IFERROR({xl_col_to_name(column + 2)}{row + 1}/{xl_col_to_name(column + 1)}{row + 1}, " ")'
                        sheet.write_formula(row, column + 4, formula, grey_percent_format)
                        formula = (
                            f'={xl_col_to_name(column + 3)}{row + 1}'
                            f'-{xl_col_to_name(column + 1)}{row + 1}'
                        )
                        sheet.write_formula(row, column + 5, formula, grey_borders_line_format)
                        row += 1

                formula_company.append(row)

                sheet.merge_range(row, 0, row, 21, f'{project_office.name}', office_heading_format)  # печатаем заголовок ПО
                row += 1

                for section in self.section_names:
                    column = 0
                    sheet.set_row(row, 31)
                    sheet.write_string(row, 0, self.section_titles[section], bold_border_line_format)
                    if 'margin' in section:
                        custom_line_format = bold_line_format
                        bluegrey_custom_percent_format = bluegrey_bold_percent_format
                    else:
                        custom_line_format = line_format
                        bluegrey_custom_percent_format = bluegrey_percent_format
                    for quarter in self.quarter_names:
                        sheet.write_number(row, column + 1, office_data[section][year][quarter]['plan'], custom_line_format)
                        sheet.write_number(row, column + 2, office_data[section][year][quarter]['100'], custom_line_format)
                        sheet.write_number(row, column + 3, office_data[section][year][quarter]['75'] + office_data[section][year][quarter]['50'] * self.POTENTIAL, custom_line_format)
                        formula = f'=IFERROR({xl_col_to_name(column + 2)}{row + 1}/{xl_col_to_name(column + 1)}{row + 1}, " ")'
                        sheet.write_formula(row, column + 4, formula, bluegrey_custom_percent_format)
                        column += 4
                    formula = (
                        f'={xl_col_to_name(column - 15)}{row + 1}'
                        f'+{xl_col_to_name(column - 11)}{row + 1}'
                        f'+{xl_col_to_name(column - 7)}{row + 1}'
                        f'+{xl_col_to_name(column - 3)}{row + 1}'
                    )
                    sheet.write_formula(row, column + 1, formula, grey_line_format)
                    formula = (
                        f'={xl_col_to_name(column - 14)}{row + 1}'
                        f'+{xl_col_to_name(column - 10)}{row + 1}'
                        f'+{xl_col_to_name(column - 6)}{row + 1}'
                        f'+{xl_col_to_name(column - 2)}{row + 1}'
                    )
                    sheet.write_formula(row, column + 2, formula, grey_line_format)
                    formula = (
                        f'={xl_col_to_name(column - 13)}{row + 1}'
                        f'+{xl_col_to_name(column - 9)}{row + 1}'
                        f'+{xl_col_to_name(column - 5)}{row + 1}'
                        f'+{xl_col_to_name(column - 1)}{row + 1}'
                        f'+{xl_col_to_name(column - 14)}{row + 1}'
                        f'+{xl_col_to_name(column - 10)}{row + 1}'
                        f'+{xl_col_to_name(column - 6)}{row + 1}'
                        f'+{xl_col_to_name(column - 2)}{row + 1}'
                    )
                    sheet.write_formula(row, column + 3, formula, grey_line_format)
                    formula = f'=IFERROR({xl_col_to_name(column + 2)}{row + 1}/{xl_col_to_name(column + 1)}{row + 1}, " ")'
                    sheet.write_formula(row, column + 4, formula, grey_percent_format)
                    formula = (
                        f'={xl_col_to_name(column + 3)}{row + 1}'
                        f'-{xl_col_to_name(column + 1)}{row + 1}'
                    )
                    sheet.write_formula(row, column + 5, formula, grey_borders_line_format)
                    row += 1

            column = 0

            sheet.merge_range(row, column, row, column + 21, f'ИТОГО {company.name}', company_heading_format)  # печатаем заголовок компании
            row += 1

            for section in self.company_section_names:
                column = 0
                sheet.set_row(row, 31)
                sheet.write_string(row, 0, self.company_section_titles[section], bold_border_line_format)
                if section in ('margin_income', 'margin3_income', 'ebit', 'net_profit'):
                    custom_line_format = bold_line_format
                    bluegrey_custom_percent_format = bluegrey_bold_percent_format
                else:
                    custom_line_format = line_format
                    bluegrey_custom_percent_format = bluegrey_percent_format
                for quarter in self.quarter_names:
                    sheet.write_number(row, column + 1, company_data[section][year][quarter]['plan'],
                                       custom_line_format)
                    if section not in ('ebit', 'net_profit'):
                        formula_fact = '=sum(' + ','.join(xl_col_to_name(column + 2) + str(
                            office_row + self.company_section_names.index(section) + 2) for office_row in
                                                          formula_company) + ')'
                        formula_forecast = '=sum(' + ','.join(xl_col_to_name(column + 3) + str(
                            office_row + self.company_section_names.index(section) + 2) for office_row in
                                                     formula_company) + ')'
                    else:
                        formula_fact = formula_forecast = ''
                    sheet.write_formula(row, column + 2, formula_fact, custom_line_format)
                    sheet.write_formula(row, column + 3, formula_forecast, custom_line_format)
                    formula = f'=IFERROR({xl_col_to_name(column + 2)}{row + 1}/{xl_col_to_name(column + 1)}{row + 1}, " ")'
                    sheet.write_formula(row, column + 4, formula, bluegrey_custom_percent_format)
                    column += 4
                formula = (
                    f'={xl_col_to_name(column - 15)}{row + 1}'
                    f'+{xl_col_to_name(column - 11)}{row + 1}'
                    f'+{xl_col_to_name(column - 7)}{row + 1}'
                    f'+{xl_col_to_name(column - 3)}{row + 1}'
                )
                sheet.write_formula(row, column + 1, formula, grey_line_format)
                formula = (
                    f'={xl_col_to_name(column - 14)}{row + 1}'
                    f'+{xl_col_to_name(column - 10)}{row + 1}'
                    f'+{xl_col_to_name(column - 6)}{row + 1}'
                    f'+{xl_col_to_name(column - 2)}{row + 1}'
                )
                sheet.write_formula(row, column + 2, formula, grey_line_format)
                formula = (
                    f'={xl_col_to_name(column - 13)}{row + 1}'
                    f'+{xl_col_to_name(column - 9)}{row + 1}'
                    f'+{xl_col_to_name(column - 5)}{row + 1}'
                    f'+{xl_col_to_name(column - 1)}{row + 1}'
                    f'+{xl_col_to_name(column - 14)}{row + 1}'
                    f'+{xl_col_to_name(column - 10)}{row + 1}'
                    f'+{xl_col_to_name(column - 6)}{row + 1}'
                    f'+{xl_col_to_name(column - 2)}{row + 1}'
                )
                sheet.write_formula(row, column + 3, formula, grey_line_format)
                formula = f'=IFERROR({xl_col_to_name(column + 2)}{row + 1}/{xl_col_to_name(column + 1)}{row + 1}, " ")'
                sheet.write_formula(row, column + 4, formula, grey_percent_format)
                formula = (
                    f'={xl_col_to_name(column + 3)}{row + 1}'
                    f'-{xl_col_to_name(column + 1)}{row + 1}'
                )
                sheet.write_formula(row, column + 5, formula, grey_borders_line_format)
                row += 1
            row += 1

    def printworksheet(self, workbook, namesheet, budget, stages, year):

        sheet = workbook.add_worksheet(namesheet)
        sheet.set_zoom(70)

        cur_budget_projects = self.env['project_budget.projects'].search([
            ('commercial_budget_id', '=', budget.id), ('stage_id', 'in', stages.ids)
        ])

        project_offices = self.env['project_budget.project_office'].search([('parent_id', '=', False)], order='name')  # для сортировки так делаем + берем сначала только верхние элементы

        companies = self.env['res.company'].search([], order='name').filtered(lambda r: r in project_offices.company_id)

        project_managers = self.env['project_budget.project_manager'].search([], order='name').filtered(lambda r: r in cur_budget_projects.project_manager_id)  # для сортировки так делаем

        data = self.get_plans(year, self.get_data_from_projects(cur_budget_projects, stages, year))

        self.print_rows(sheet, workbook, companies, project_offices, project_managers, year, data)

    def generate_xlsx_report(self, workbook, data, budgets):

        year = data['year']
        commercial_budget_id = data['commercial_budget_id']

        budget = self.env['project_budget.commercial_budget'].search([('id', '=', commercial_budget_id)])
        stages = self.env['project_budget.project.stage'].search([('code', '!=', '10')], order='sequence desc')  # для сортировки так делаем
        self.printworksheet(workbook, 'План-Факт', budget,  stages, year)
        