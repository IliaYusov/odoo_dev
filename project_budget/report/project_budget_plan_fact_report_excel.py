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
            for pds in project.planned_step_cash_flow_ids:
                if year <= pds.date_cash.year <= year + 2:
                    return True
            for pds in project.fact_step_cash_flow_ids:
                if year <= pds.date_cash.year <= year + 2:
                    return True
            for act in project.planned_step_acceptance_flow_ids:
                if year <= act.date_cash.year <= year + 2:
                    return True
            for act in project.fact_step_acceptance_flow_ids:
                if year <= act.date_cash.year <= year + 2:
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

    def get_months_from_quarter(self, quarter):
        if quarter == 'Q1':
            return 1, 2, 3
        elif quarter == 'Q2':
            return 4, 5, 6
        elif quarter == 'Q3':
            return 7, 8, 9
        elif quarter == 'Q4':
            return 10, 11, 12
        else:
            return False

    def get_sum_fact_pds_project_quarter(self, project, year, quarter):
        sum_cash = 0
        months = self.get_months_from_quarter(quarter)

        if project.step_status == 'project':
            pds_list = project.fact_cash_flow_ids
        elif project.step_status == 'step':
            pds_list = project.fact_step_cash_flow_ids

        for pds in pds_list:
            if pds.date_cash.month in months and pds.date_cash.year == year:
                sum_cash += pds.sum_cash
        return sum_cash

    def get_sum_plan_pds_project_quarter(self, project, year, quarter):
        sum_cash = {'commitment': 0, 'reserve': 0}
        months = self.get_months_from_quarter(quarter)

        if project.step_status == 'project':
            pds_list = project.planned_cash_flow_ids
        elif project.step_status == 'step':
            pds_list = project.planned_step_cash_flow_ids

        for pds in pds_list:
            if pds.date_cash.month in months and pds.date_cash.year == year:

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

    def get_quarter_revenue_project(self, project, year, quarter):

        sum100tmp = 0
        sum75tmp = 0
        sum50tmp = 0
        sum30tmp = 0

        months = self.get_months_from_quarter(quarter)

        if months:
            if project.end_presale_project_month.month in months and project.end_presale_project_month.year == year:
                if project.stage_id.code in ('100', '100(done)'):
                    sum100tmp += project.amount_total_in_company_currency
                if project.stage_id.code == '75':
                    sum75tmp += project.amount_total_in_company_currency
                if project.stage_id.code == '50':
                    sum50tmp += project.amount_total_in_company_currency * self.KOEFF_RESERVE
                if project.stage_id.code == '30':
                    sum30tmp += project.amount_total_in_company_currency * self.KOEFF_POTENTIAL

        return sum100tmp, sum75tmp, sum50tmp, sum30tmp

    def get_quarter_pds_project(self, project, year, quarter):

        sum75tmp = sum50tmp = 0

        sum = {'commitment': 0, 'reserve': 0, 'potential': 0}

        months = self.get_months_from_quarter(quarter)

        sum100tmp = self.get_sum_fact_pds_project_quarter(project, year, quarter)

        sum = self.get_sum_plan_pds_project_quarter(project, year, quarter)

        if not project.is_correction_project:
            if abs(sum100tmp) >= abs(sum.get('commitment', 0)):
                sum100tmp_ostatok = sum100tmp - sum['commitment']
                sum['commitment'] = 0
                sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
            else:
                sum['commitment'] = sum['commitment'] - sum100tmp

        # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плана
        sum_ostatok_pds = {'commitment': 0, 'reserve': 0, 'potential': 0}
        sum_distribution_pds = 0

        if project.step_status == 'project':
            acceptance_list = project.planned_cash_flow_ids
        elif project.step_status == 'step':
            acceptance_list = project.planned_step_cash_flow_ids

        for planned_cash_flow in acceptance_list:

            if planned_cash_flow.date_cash.month in months and planned_cash_flow.date_cash.year == year:
                sum_distribution_pds += planned_cash_flow.distribution_sum_without_vat
                stage_id_name = project.stage_id.code

                if (planned_cash_flow.distribution_sum_with_vat_ostatok > 0 and planned_cash_flow.sum_cash > 0
                        or planned_cash_flow.distribution_sum_with_vat_ostatok < 0 and planned_cash_flow.sum_cash < 0):  # учитываем отрицательный ПДС для Энсиса
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
            # for key in sum:
            #     if sum[key] < 0 and not project.is_correction_project:
            #         sum[key] = 0

        if sum:
            sum75tmp += sum.get('commitment', 0)
            sum50tmp += sum.get('reserve', 0) * self.KOEFF_RESERVE

        return sum100tmp, sum75tmp, sum50tmp

    def get_sum_fact_acceptance_project_quarter(self, project, year, quarter, without_distributions):
        sum_cash = 0
        months = self.get_months_from_quarter(quarter)

        if project.step_status == 'project':
            acceptance_list = project.fact_acceptance_flow_ids
        elif project.step_status == 'step':
            acceptance_list = project.fact_step_acceptance_flow_ids

        if acceptance_list:
            for acceptance in acceptance_list:
                if acceptance.date_cash.month in months and acceptance.date_cash.year == year:
                    if without_distributions and acceptance.distribution_acceptance_ids:
                        continue
                    sum_cash += acceptance.sum_cash_without_vat
        return sum_cash

    def get_sum_fact_margin_project_quarter(self, project, year, quarter, without_distributions):
        if project.is_parent_project:
            if project.margin_from_children_to_parent:
                sum_cash = self.get_margin_fact(project, year, quarter, without_distributions, 1)
                for child_project in project.child_project_ids:
                    if child_project.project_have_steps:
                        for child_step in child_project.step_project_child_ids:
                            sum_cash += self.get_margin_fact(child_step, year, quarter, without_distributions, child_project.margin_rate_for_parent)
                    else:
                        sum_cash += self.get_margin_fact(child_project, year, quarter, without_distributions, child_project.margin_rate_for_parent)
            else:
                total_percent = 0
                for child_project in project.child_project_ids:
                    total_percent += child_project.margin_rate_for_parent
                sum_cash = self.get_margin_fact(project, year, quarter, without_distributions, (1 - total_percent))
        elif project.is_child_project:
            if project.parent_project_id.margin_from_children_to_parent:
                sum_cash = self.get_margin_fact(project, year, quarter, without_distributions, (1 - project.margin_rate_for_parent))
            else:
                sum_cash = self.get_margin_fact(project, year, quarter, without_distributions, 1)
                if project.parent_project_id.project_have_steps:
                    for parent_step in project.parent_project_id.step_project_child_ids:
                        additional_margin = self.get_margin_fact(parent_step, year, quarter, without_distributions, project.margin_rate_for_parent)
                        sum_cash += additional_margin
                else:
                    additional_margin = self.get_margin_fact(project.parent_project_id, year, quarter, without_distributions, project.margin_rate_for_parent)
                    sum_cash += additional_margin
        else:
            sum_cash = self.get_margin_fact(project, year, quarter, without_distributions, 1)
        return sum_cash

    def get_margin_fact(self, project, year, quarter, without_distributions, multiplier):
        sum_cash = 0
        months = self.get_months_from_quarter(quarter)

        if project.step_status == 'project':
            acceptance_list = project.fact_acceptance_flow_ids
        elif project.step_status == 'step':
            acceptance_list = project.fact_step_acceptance_flow_ids

        if acceptance_list:
            for acceptance in acceptance_list:
                if acceptance.date_cash.month in months and acceptance.date_cash.year == year:
                    if without_distributions and acceptance.distribution_acceptance_ids:
                        continue
                    sum_cash += acceptance.margin * multiplier
        return sum_cash

    def get_sum_planned_acceptance_project_quarter(self, project, year, quarter):
        sum_acceptance = {'commitment': 0, 'reserve': 0, 'potential': 0}

        months = self.get_months_from_quarter(quarter)

        if project.step_status == 'project':
            acceptance_list = project.planned_acceptance_flow_ids
        elif project.step_status == 'step':
            acceptance_list = project.planned_step_acceptance_flow_ids

        if acceptance_list:
            for acceptance in acceptance_list:
                if acceptance.date_cash.month in months and acceptance.date_cash.year == year:

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

    def get_sum_planned_margin_project_quater(self, project, year, quarter):
        if project.is_parent_project:
            if project.margin_from_children_to_parent:
                sum_margin = self.get_margin_plan(project, year, quarter, 1)
                if project.child_project_ids:
                    for child_project in project.child_project_ids:
                        if child_project.project_have_steps:
                            for child_step in child_project.step_project_child_ids:
                                additional_margin = self.get_margin_plan(child_step, year, quarter,
                                                                         child_project.margin_rate_for_parent)
                                for key in sum_margin:
                                    sum_margin[key] += additional_margin[key]
                        else:
                            additional_margin = self.get_margin_plan(child_project, year, quarter, child_project.margin_rate_for_parent)
                            for key in sum_margin:
                                sum_margin[key] += additional_margin[key]
            else:
                total_percent = 0
                for child_project in project.child_project_ids:
                    total_percent += child_project.margin_rate_for_parent
                sum_margin = self.get_margin_plan(project, year, quarter, (1 - total_percent))
        elif project.is_child_project:
            if project.parent_project_id.margin_from_children_to_parent:
                sum_margin = self.get_margin_plan(project, year, quarter, (1 - project.margin_rate_for_parent))
            else:
                sum_margin = self.get_margin_plan(project, year, quarter, 1)
                if project.parent_project_id.project_have_steps:
                    for parent_step in project.parent_project_id.step_project_child_ids:
                        additional_margin = self.get_margin_plan(parent_step, year, quarter,
                                                                 project.margin_rate_for_parent)
                        for key in sum_margin:
                            sum_margin[key] += additional_margin[key]
                else:
                    additional_margin = self.get_margin_plan(project.parent_project_id, year, quarter, project.margin_rate_for_parent)
                    for key in sum_margin:
                        sum_margin[key] += additional_margin[key]
        else:
            sum_margin = self.get_margin_plan(project, year, quarter, 1)
        return sum_margin

    def get_margin_plan(self, project, year, quarter, multiplier):
        sum_margin = {'commitment': 0, 'reserve': 0, 'potential': 0}

        months = self.get_months_from_quarter(quarter)

        if project.step_status == 'project':
            acceptance_list = project.planned_acceptance_flow_ids
        elif project.step_status == 'step':
            acceptance_list = project.planned_step_acceptance_flow_ids

        if acceptance_list:
            for acceptance in acceptance_list:
                if any(distribution.fact_acceptance_flow_id.margin_manual_input for distribution in
                       acceptance.distribution_acceptance_ids):  # если есть ручная маржа - пропускаем
                    continue

                stage_id_name = project.stage_id.code
                profitability = project.profitability

                if acceptance.date_cash.month in months and acceptance.date_cash.year == year:
                    if acceptance.forecast == 'from_project':
                        if stage_id_name in ('75', '100', '100(done)'):
                            sum_margin['commitment'] += acceptance.sum_cash_without_vat * profitability * multiplier / 100
                        elif stage_id_name == '50':
                            sum_margin['reserve'] += acceptance.sum_cash_without_vat * profitability * multiplier/ 100
                    else:
                        if stage_id_name != '0':
                            sum_margin[acceptance.forecast] += acceptance.sum_cash_without_vat * profitability * multiplier/ 100
        return sum_margin

    def get_margin_forecast_from_distributions(self, planned_acceptance, margin_plan, project, multiplier):
        # суммируем доли маржи фактов в соотношении (сумма распределения/суммы факта)
        margin_distribution = 0
        for distribution in planned_acceptance.distribution_acceptance_ids:
            if distribution.fact_acceptance_flow_id.sum_cash_without_vat != 0:
                margin_distribution += distribution.fact_acceptance_flow_id.margin * distribution.sum_cash_without_vat / distribution.fact_acceptance_flow_id.sum_cash_without_vat
        stage_id_name = project.stage_id.code
        if planned_acceptance.forecast == 'from_project':
            if stage_id_name in ('75', '100', '100(done)'):
                margin_plan['commitment'] -= margin_distribution * multiplier
            elif stage_id_name == '50':
                margin_plan['reserve'] -= margin_distribution * multiplier
        else:
            if stage_id_name != '0':
                margin_plan[planned_acceptance.forecast] -= margin_distribution * multiplier
        return margin_plan

    def get_sum_planned_acceptance_project_from_distribution(self, project, year, quarter):
        # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плана
        sum_ostatok_acceptance = {'commitment': 0, 'reserve': 0, 'potential': 0}
        sum_distribution_acceptance = 0
        months = self.get_months_from_quarter(quarter)

        if project.step_status == 'project':
            acceptance_list = project.planned_acceptance_flow_ids
        elif project.step_status == 'step':
            acceptance_list = project.planned_step_acceptance_flow_ids

        for planned_acceptance_flow in acceptance_list:

            if planned_acceptance_flow.date_cash.month in months and planned_acceptance_flow.date_cash.year == year:
                sum_distribution_acceptance += planned_acceptance_flow.distribution_sum_without_vat

                stage_id_name = project.stage_id.code

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

    def get_sum_planned_margin_project_from_distribution(self, project, year, quarter, margin_plan, margin_rate_for_parent):
        if project.is_parent_project:
            if project.margin_from_children_to_parent:
                new_margin_plan = self.get_margin_plan_from_distribution(project, year, quarter, margin_plan, 1)
                if new_margin_plan:
                    margin_plan = new_margin_plan
                for child_project in project.child_project_ids:
                    if child_project.project_have_steps:
                        for child_step in child_project.step_project_child_ids:
                            new_margin_plan = self.get_margin_plan_from_distribution(
                                child_step, year, quarter, margin_plan, child_project.margin_rate_for_parent
                            )
                            if new_margin_plan:
                                margin_plan = new_margin_plan
                    else:
                        new_margin_plan = self.get_margin_plan_from_distribution(
                            child_project, year, quarter, margin_plan, child_project.margin_rate_for_parent
                        )
                        if new_margin_plan:
                            margin_plan = new_margin_plan
            else:
                total_percent = 0
                for child_project in project.child_project_ids:
                    total_percent += child_project.margin_rate_for_parent
                new_margin_plan = self.get_margin_plan_from_distribution(
                    project, year, quarter, margin_plan, (1 - total_percent)
                )
                if new_margin_plan:
                    margin_plan = new_margin_plan
        elif project.is_child_project:
            if project.parent_project_id.margin_from_children_to_parent:
                new_margin_plan = self.get_margin_plan_from_distribution(project, year, quarter, margin_plan, (1 - project.margin_rate_for_parent))
                if new_margin_plan:
                    margin_plan = new_margin_plan
            else:
                new_margin_plan = self.get_margin_plan_from_distribution(project, year, quarter, margin_plan, 1)
                if new_margin_plan:
                    margin_plan = new_margin_plan
                if project.parent_project_id.project_have_steps:
                    for parent_step in project.parent_project_id.step_project_child_ids:
                        new_margin_plan = self.get_margin_plan_from_distribution(parent_step, year,
                                                                                 quarter, margin_plan,
                                                                                 project.margin_rate_for_parent)
                        if new_margin_plan:
                            margin_plan = new_margin_plan
                else:
                    new_margin_plan = self.get_margin_plan_from_distribution(project.parent_project_id, year, quarter, margin_plan, project.margin_rate_for_parent)
                    if new_margin_plan:
                        margin_plan = new_margin_plan
        else:
            new_margin_plan = self.get_margin_plan_from_distribution(project, year, quarter, margin_plan, 1)
            if new_margin_plan:
                margin_plan = new_margin_plan
        return margin_plan

    def get_margin_plan_from_distribution(self, project, year, quarter, margin_plan, multiplier):
        # посмотрим на распределение, по идее все с него надо брать, но пока оставляем 2 ветки: если нет распределения идем по старому: в рамках одного месяца сравниваем суммы факта и плаан
        sum_distribution_acceptance = 0
        new_margin_plan = margin_plan.copy()
        months = self.get_months_from_quarter(quarter)
        if project.step_status == 'project':
            acceptance_list = project.planned_acceptance_flow_ids
        elif project.step_status == 'step':
            acceptance_list = project.planned_step_acceptance_flow_ids

        for planned_acceptance_flow in acceptance_list:
            if any(distribution.fact_acceptance_flow_id.margin_manual_input for distribution in
                   planned_acceptance_flow.distribution_acceptance_ids):  # если есть ручная маржа - пропускаем
                continue

            if planned_acceptance_flow.date_cash.month in months and planned_acceptance_flow.date_cash.year == year:
                sum_distribution_acceptance += planned_acceptance_flow.distribution_sum_without_vat
                new_margin_plan = self.get_margin_forecast_from_distributions(
                    planned_acceptance_flow, new_margin_plan, project, multiplier)
        if sum_distribution_acceptance:  # если есть распределение, то остаток = остатку распределения
            return new_margin_plan
        else:
            return False

    def get_quarter_acceptance_project(self, project, year, quarter):

        sum75tmp = sum50tmp = margin75tmp = margin50tmp = 0

        # margin_rate_for_child = 1
        # if project.parent_project_id:
        #     margin_rate_for_child = (1 - project.margin_rate_for_parent)
        # elif project.step_project_parent_id.parent_project_id:
        #     margin_rate_for_child = (1 - project.step_project_parent_id.margin_rate_for_parent)

        sum100tmp = self.get_sum_fact_acceptance_project_quarter(project, year, quarter, False)
        margin100tmp = self.get_sum_fact_margin_project_quarter(project, year, quarter, False)

        acc_fact_wo_distributions = self.get_sum_fact_acceptance_project_quarter(project, year, quarter, True)
        mrg_fact_wo_distributions = self.get_sum_fact_margin_project_quarter(project, year, quarter, True)

        sum = self.get_sum_planned_acceptance_project_quarter(project, year, quarter)
        margin_sum = self.get_sum_planned_margin_project_quater(project, year, quarter)

        margin_plan = {'commitment': 0, 'reserve': 0, 'potential': 0}

        if margin_sum:
            margin_plan = margin_sum.copy()

        if not project.is_correction_project:

            if acc_fact_wo_distributions >= sum.get('commitment', 0):
                sum100tmp_ostatok = acc_fact_wo_distributions - sum['commitment']
                sum['commitment'] = 0
                sum['reserve'] = max(sum['reserve'] - sum100tmp_ostatok, 0)
            else:
                sum['commitment'] = sum['commitment'] - acc_fact_wo_distributions

            if mrg_fact_wo_distributions >= margin_plan['commitment']:  # маржа если нет распределения
                margin100tmp_ostatok = mrg_fact_wo_distributions - margin_plan['commitment']
                margin_sum['commitment'] = 0
                margin_sum['reserve'] = max(margin_plan['reserve'] - margin100tmp_ostatok, 0)
            else:
                margin_sum['commitment'] = margin_plan['commitment'] - mrg_fact_wo_distributions

        sum_ostatok_acceptance = self.get_sum_planned_acceptance_project_from_distribution(project, year, quarter)
        new_margin_plan = self.get_sum_planned_margin_project_from_distribution(project, year, quarter, margin_sum, 1)

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
            margin75tmp += margin_sum.get('commitment', 0)
            sum50tmp += sum.get('reserve', 0) * self.KOEFF_RESERVE
            margin50tmp += margin_sum.get('reserve', 0) * self.KOEFF_RESERVE

        return sum100tmp, sum75tmp, sum50tmp, margin100tmp, margin75tmp, margin50tmp

    def get_section_data_from_project(self, project, year, data):

        company = project.company_id.name
        center = project.responsibility_center_id.name
        manager = project.key_account_manager_id.name

        section_data = {}

        for section in self.section_names:
            section_data[section] = {}

        for quarter in self.quarter_names:
            section_data['contracting']['100'], section_data['contracting']['75'], section_data['contracting']['50'], \
            section_data['contracting']['30'] = self.get_quarter_revenue_project(project, year, quarter)
            section_data['cash']['100'], section_data['cash']['75'], section_data['cash'][
                '50'] = self.get_quarter_pds_project(project, year, quarter)
            section_data['acceptance']['100'], section_data['acceptance']['75'], section_data['acceptance'][
                '50'], section_data['margin_income']['100'], section_data['margin_income']['75'], section_data['margin_income'][
                '50'] = self.get_quarter_acceptance_project(project, year, quarter)

            for section in self.section_names:
                for probability in self.probability_names:
                    res = section_data.get(section, {}).get(probability, 0)
                    data.setdefault(company, {}).setdefault(manager, {}).setdefault(section, {}).setdefault(year, {}).setdefault(quarter, {}).setdefault(probability, 0)
                    data[company][manager][section][year][quarter][probability] += res
                    data.setdefault(company, {}).setdefault(center, {}).setdefault(section, {}).setdefault(year, {}).setdefault(quarter, {}).setdefault(probability, 0)
                    data[company][center][section][year][quarter][probability] += res
                    data.setdefault(company, {}).setdefault(section, {}).setdefault(year, {}).setdefault(quarter, {}).setdefault(probability, 0)
                    data[company][section][year][quarter][probability] += res
                    parent_center = project.responsibility_center_id.parent_id
                    while parent_center:
                        data.setdefault(company, {}).setdefault(parent_center.name, {}).setdefault(section, {}).setdefault(year, {}).setdefault(quarter, {}).setdefault(probability, 0)
                        data[company][parent_center.name][section][year][quarter][probability] += res
                        parent_center = parent_center.parent_id

        return data


    def get_data_from_projects(self, cur_budget_projects, stages, year):
        data = {}

        for project in cur_budget_projects:
            if project.vgo == '-':

                if not (self.is_project_in_year(project, year) and project.stage_id.id in stages.ids):
                    continue

                data = self.get_section_data_from_project(project, year, data)

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
                data.setdefault(company.name, {}).setdefault(company_section, {}).setdefault(year, {}).setdefault('Q3', {})['plan_6_6'] = section_plan.q3_plan_6_6
                data.setdefault(company.name, {}).setdefault(company_section, {}).setdefault(year, {}).setdefault('Q4', {})['plan_6_6'] = section_plan.q4_plan_6_6
                for center_section in self.section_names:
                    for center in self.env['account.analytic.account'].search([
                        ('name', 'in', tuple(data[company.name].keys())),
                        ('plan_id', '=', self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
                    ]):
                        section_plan = self.env['project_budget.budget_plan_supervisor_spec'].search([
                            ('budget_plan_supervisor_id.year', '=', year),
                            ('budget_plan_supervisor_id.responsibility_center_id', '=', center.id),
                            ('type_row', '=', center_section),
                        ])
                        data.setdefault(company.name, {}).setdefault(center.name, {}).setdefault(center_section, {}).setdefault(year, {}).setdefault('Q1', {})['plan'] = section_plan.q1_plan
                        data.setdefault(company.name, {}).setdefault(center.name, {}).setdefault(center_section, {}).setdefault(year, {}).setdefault('Q2', {})['plan'] = section_plan.q2_plan
                        data.setdefault(company.name, {}).setdefault(center.name, {}).setdefault(center_section, {}).setdefault(year, {}).setdefault('Q3', {})['plan'] = section_plan.q3_plan
                        data.setdefault(company.name, {}).setdefault(center.name, {}).setdefault(center_section, {}).setdefault(year, {}).setdefault('Q4', {})['plan'] = section_plan.q4_plan
                        data.setdefault(company.name, {}).setdefault(center.name, {}).setdefault(center_section, {}).setdefault(year, {}).setdefault('Q3', {})['plan_6_6'] = section_plan.q3_plan_6_6
                        data.setdefault(company.name, {}).setdefault(center.name, {}).setdefault(center_section, {}).setdefault(year, {}).setdefault('Q4', {})['plan_6_6'] = section_plan.q4_plan_6_6
                        parent_center = center.parent_id
                        while parent_center:
                            data.setdefault(company.name, {}).setdefault(parent_center.name, {}).setdefault(center_section, {}).setdefault(year, {}).setdefault('Q1', {}).setdefault('plan', 0)
                            data[company.name][parent_center.name][center_section][year]['Q1']['plan'] += section_plan.q1_plan
                            data.setdefault(company.name, {}).setdefault(parent_center.name, {}).setdefault(center_section, {}).setdefault(year, {}).setdefault('Q2', {}).setdefault('plan', 0)
                            data[company.name][parent_center.name][center_section][year]['Q2']['plan'] += section_plan.q2_plan
                            data.setdefault(company.name, {}).setdefault(parent_center.name, {}).setdefault(center_section, {}).setdefault(year, {}).setdefault('Q3', {}).setdefault('plan', 0)
                            data[company.name][parent_center.name][center_section][year]['Q3']['plan'] += section_plan.q3_plan
                            data.setdefault(company.name, {}).setdefault(parent_center.name, {}).setdefault(center_section, {}).setdefault(year, {}).setdefault('Q4', {}).setdefault('plan', 0)
                            data[company.name][parent_center.name][center_section][year]['Q4']['plan'] += section_plan.q4_plan
                            data.setdefault(company.name, {}).setdefault(parent_center.name, {}).setdefault(center_section, {}).setdefault(year, {}).setdefault('Q3', {}).setdefault('plan_6_6', 0)
                            data[company.name][parent_center.name][center_section][year]['Q3']['plan_6_6'] += section_plan.q3_plan_6_6
                            data.setdefault(company.name, {}).setdefault(parent_center.name, {}).setdefault(center_section, {}).setdefault(year, {}).setdefault('Q4', {}).setdefault('plan_6_6', 0)
                            data[company.name][parent_center.name][center_section][year]['Q4']['plan_6_6'] += section_plan.q4_plan_6_6
                            parent_center = parent_center.parent_id
                    for manager in self.env['hr.employee'].with_context(active_test=False).search(
                            [('name', 'in', tuple(data[company.name].keys())), ('company_id.name', '=', company.name)]):
                        section_plan = self.env['project_budget.budget_plan_kam_spec'].search([
                            ('budget_plan_kam_id.year', '=', year),
                            ('budget_plan_kam_id.key_account_manager_id', '=', manager.id),
                            ('type_row', '=', center_section),
                        ])
                        data.setdefault(company.name, {}).setdefault(manager.name, {}).setdefault(center_section, {}).setdefault(year, {}).setdefault('Q1', {})['plan'] = section_plan.q1_plan
                        data.setdefault(company.name, {}).setdefault(manager.name, {}).setdefault(center_section, {}).setdefault(year, {}).setdefault('Q2', {})['plan'] = section_plan.q2_plan
                        data.setdefault(company.name, {}).setdefault(manager.name, {}).setdefault(center_section, {}).setdefault(year, {}).setdefault('Q3', {})['plan'] = section_plan.q3_plan
                        data.setdefault(company.name, {}).setdefault(manager.name, {}).setdefault(center_section, {}).setdefault(year, {}).setdefault('Q4', {})['plan'] = section_plan.q4_plan
                        data.setdefault(company.name, {}).setdefault(manager.name, {}).setdefault(center_section, {}).setdefault(year, {}).setdefault('Q3', {})['plan_6_6'] = section_plan.q3_plan_6_6
                        data.setdefault(company.name, {}).setdefault(manager.name, {}).setdefault(center_section, {}).setdefault(year, {}).setdefault('Q4', {})['plan_6_6'] = section_plan.q4_plan_6_6
        return data

    def print_rows(self, sheet, workbook, companies, responsibility_centers, key_account_managers, year, data, print_managers):

        center_heading_format = workbook.add_format({
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
        quarter_names_list = [f"I кв. {year}", f"II кв. {year}", f"III кв. {year}", f"IV кв. {year}"]
        sheet.set_column(column, column, 16)
        for quarter in quarter_names_list:
            if quarter_names_list.index(quarter) in (2, 3):  # III и IV кварталы
                sheet.merge_range(row, column + 1, row, column + 5, quarter, bold_heading_format)
                sheet.write_string(row + 1, column + 1, 'ПЛАН', heading_format)
                sheet.write_string(row + 1, column + 2, 'ПЛАН 6+6', heading_format)
                sheet.write_string(row + 1, column + 3, 'ФАКТ', heading_format)
                sheet.write_string(row + 1, column + 4, 'ПРОГНОЗ (100%+60%)', heading_format)
                sheet.write_string(row + 1, column + 5, f'% исполнения плана Q{quarter_names_list.index(quarter) + 1}',
                                   bluegrey_heading_format)
                sheet.set_column(column + 1, column + 5, 14)
                column += 5
            else:
                sheet.merge_range(row, column + 1, row, column + 4, quarter, bold_heading_format)
                sheet.write_string(row + 1, column + 1, 'ПЛАН', heading_format)
                sheet.write_string(row + 1, column + 2, 'ФАКТ', heading_format)
                sheet.write_string(row + 1, column + 3, 'ПРОГНОЗ (100%+60%)', heading_format)
                sheet.write_string(row + 1, column + 4, f'% исполнения плана Q{quarter_names_list.index(quarter) + 1}',
                                   bluegrey_heading_format)
                sheet.set_column(column + 1, column + 4, 14)
                column += 4
        sheet.merge_range(row, column + 1, row, column + 8, f'ИТОГО {year}', grey_borders_heading_format)
        sheet.write_string(row + 1, column + 1, 'ПЛАН', grey_heading_format)
        sheet.write_string(row + 1, column + 2, 'ПЛАН 6+6', grey_heading_format)
        sheet.write_string(row + 1, column + 3, 'ФАКТ', grey_heading_format)
        sheet.write_string(row + 1, column + 4, 'ПРОГНОЗ (100%+60%)', grey_heading_format)
        sheet.write_string(row + 1, column + 5, f'% исполнения плана {year}', grey_heading_format)
        sheet.write_string(row + 1, column + 6, '% исполнения плана 6+6', grey_heading_format)
        sheet.write_string(row + 1, column + 7, f'Разница с планом {year}', grey_borders_heading_format)
        sheet.write_string(row + 1, column + 8, 'Разница с планом 6+6', grey_borders_heading_format)
        sheet.set_column(column + 1, column + 8, 14)
        row += 2

        for company in companies:

            company_data = data.get(company.name, False)
            if not company_data:
                continue

            print('company =', company.name)

            formula_company = []

            if print_managers:  # отключаемая печать менеджеров
                for project_manager in key_account_managers:

                    manager_data = data[company.name].get(project_manager.name, False)
                    if not manager_data:
                        continue

                    print('project_manager =', project_manager.name)

                    sheet.merge_range(row, 0, row, 26, f'{project_manager.name} - {company.name}',
                                      center_heading_format)  # печатаем заголовок КАМ
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
                            if self.quarter_names.index(quarter) in (2, 3):  # III и IV кварталы
                                sheet.write_number(row, column + 1, manager_data[section][year][quarter].get('plan', 0),
                                                   custom_line_format)
                                sheet.write_number(row, column + 2, manager_data[section][year][quarter].get('plan_6_6', 0),
                                                   custom_line_format)
                                sheet.write_number(row, column + 3, manager_data[section][year][quarter]['100'],
                                                   custom_line_format)
                                sheet.write_number(row, column + 4, manager_data[section][year][quarter]['75'] +
                                                   manager_data[section][year][quarter]['50'] * self.POTENTIAL,
                                                   custom_line_format)
                                formula = f'=IFERROR({xl_col_to_name(column + 3)}{row + 1}/{xl_col_to_name(column + 2)}{row + 1}, " ")'
                                sheet.write_formula(row, column + 5, formula, bluegrey_custom_percent_format)
                                column += 5
                            else:
                                sheet.write_number(row, column + 1, manager_data[section][year][quarter].get('plan', 0),
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
                            f'={xl_col_to_name(column - 17)}{row + 1}'
                            f'+{xl_col_to_name(column - 13)}{row + 1}'
                            f'+{xl_col_to_name(column - 9)}{row + 1}'
                            f'+{xl_col_to_name(column - 4)}{row + 1}'
                        )
                        sheet.write_formula(row, column + 1, formula, grey_line_format)  # план

                        formula = (
                            f'={xl_col_to_name(column - 16)}{row + 1}'
                            f'+{xl_col_to_name(column - 12)}{row + 1}'
                            f'+{xl_col_to_name(column - 8)}{row + 1}'
                            f'+{xl_col_to_name(column - 3)}{row + 1}'
                        )
                        sheet.write_formula(row, column + 2, formula, grey_line_format)  # план 6+6

                        formula = (
                            f'={xl_col_to_name(column - 16)}{row + 1}'
                            f'+{xl_col_to_name(column - 12)}{row + 1}'
                            f'+{xl_col_to_name(column - 7)}{row + 1}'
                            f'+{xl_col_to_name(column - 2)}{row + 1}'
                        )
                        sheet.write_formula(row, column + 3, formula, grey_line_format)  # факт

                        formula = (
                            f'={xl_col_to_name(column - 15)}{row + 1}'
                            f'+{xl_col_to_name(column - 11)}{row + 1}'
                            f'+{xl_col_to_name(column - 6)}{row + 1}'
                            f'+{xl_col_to_name(column - 1)}{row + 1}'
                            f'+{xl_col_to_name(column - 16)}{row + 1}'
                            f'+{xl_col_to_name(column - 12)}{row + 1}'
                            f'+{xl_col_to_name(column - 7)}{row + 1}'
                            f'+{xl_col_to_name(column - 2)}{row + 1}'
                        )
                        sheet.write_formula(row, column + 4, formula, grey_line_format)  # прогноз

                        formula = f'=IFERROR({xl_col_to_name(column + 3)}{row + 1}/{xl_col_to_name(column + 1)}{row + 1}, " ")'
                        sheet.write_formula(row, column + 5, formula, grey_percent_format)

                        formula = f'=IFERROR({xl_col_to_name(column + 3)}{row + 1}/{xl_col_to_name(column + 2)}{row + 1}, " ")'
                        sheet.write_formula(row, column + 6, formula, grey_percent_format)

                        formula = (
                            f'={xl_col_to_name(column + 4)}{row + 1}'
                            f'-{xl_col_to_name(column + 1)}{row + 1}'
                        )
                        sheet.write_formula(row, column + 7, formula, grey_borders_line_format)

                        formula = (
                            f'={xl_col_to_name(column + 4)}{row + 1}'
                            f'-{xl_col_to_name(column + 2)}{row + 1}'
                        )
                        sheet.write_formula(row, column + 8, formula, grey_borders_line_format)
                        row += 1

            else:  # отключаемая печать офисов
                for responsibility_center in responsibility_centers:

                    center_data = data[company.name].get(responsibility_center.name, False)
                    if not center_data:
                        continue

                    print('responsibility_center =', responsibility_center.name)

                    formula_company.append(row)

                    sheet.merge_range(row, 0, row, 26, f'{responsibility_center.name}', center_heading_format)  # печатаем заголовок ПО
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
                            if self.quarter_names.index(quarter) in (2, 3):  # III и IV кварталы
                                sheet.write_number(row, column + 1, center_data[section][year][quarter]['plan'], custom_line_format)
                                sheet.write_number(row, column + 2, center_data[section][year][quarter]['plan_6_6'], custom_line_format)
                                sheet.write_number(row, column + 3, center_data[section][year][quarter]['100'], custom_line_format)
                                sheet.write_number(row, column + 4, center_data[section][year][quarter]['75'] + center_data[section][year][quarter]['50'] * self.POTENTIAL, custom_line_format)
                                formula = f'=IFERROR({xl_col_to_name(column + 3)}{row + 1}/{xl_col_to_name(column + 2)}{row + 1}, " ")'
                                sheet.write_formula(row, column + 5, formula, bluegrey_custom_percent_format)
                                column += 5
                            else:
                                sheet.write_number(row, column + 1, center_data[section][year][quarter]['plan'], custom_line_format)
                                sheet.write_number(row, column + 2, center_data[section][year][quarter]['100'], custom_line_format)
                                sheet.write_number(row, column + 3, center_data[section][year][quarter]['75'] + center_data[section][year][quarter]['50'] * self.POTENTIAL, custom_line_format)
                                formula = f'=IFERROR({xl_col_to_name(column + 2)}{row + 1}/{xl_col_to_name(column + 1)}{row + 1}, " ")'
                                sheet.write_formula(row, column + 4, formula, bluegrey_custom_percent_format)
                                column += 4
                        formula = (
                            f'={xl_col_to_name(column - 17)}{row + 1}'
                            f'+{xl_col_to_name(column - 13)}{row + 1}'
                            f'+{xl_col_to_name(column - 9)}{row + 1}'
                            f'+{xl_col_to_name(column - 4)}{row + 1}'
                        )
                        sheet.write_formula(row, column + 1, formula, grey_line_format)  # план

                        formula = (
                            f'={xl_col_to_name(column - 16)}{row + 1}'
                            f'+{xl_col_to_name(column - 12)}{row + 1}'
                            f'+{xl_col_to_name(column - 8)}{row + 1}'
                            f'+{xl_col_to_name(column - 3)}{row + 1}'
                        )
                        sheet.write_formula(row, column + 2, formula, grey_line_format)  # план 6+6

                        formula = (
                            f'={xl_col_to_name(column - 16)}{row + 1}'
                            f'+{xl_col_to_name(column - 12)}{row + 1}'
                            f'+{xl_col_to_name(column - 7)}{row + 1}'
                            f'+{xl_col_to_name(column - 2)}{row + 1}'
                        )
                        sheet.write_formula(row, column + 3, formula, grey_line_format)  # факт

                        formula = (
                            f'={xl_col_to_name(column - 15)}{row + 1}'
                            f'+{xl_col_to_name(column - 11)}{row + 1}'
                            f'+{xl_col_to_name(column - 6)}{row + 1}'
                            f'+{xl_col_to_name(column - 1)}{row + 1}'
                            f'+{xl_col_to_name(column - 16)}{row + 1}'
                            f'+{xl_col_to_name(column - 12)}{row + 1}'
                            f'+{xl_col_to_name(column - 7)}{row + 1}'
                            f'+{xl_col_to_name(column - 2)}{row + 1}'
                        )
                        sheet.write_formula(row, column + 4, formula, grey_line_format)  # прогноз

                        formula = f'=IFERROR({xl_col_to_name(column + 3)}{row + 1}/{xl_col_to_name(column + 1)}{row + 1}, " ")'
                        sheet.write_formula(row, column + 5, formula, grey_percent_format)

                        formula = f'=IFERROR({xl_col_to_name(column + 3)}{row + 1}/{xl_col_to_name(column + 2)}{row + 1}, " ")'
                        sheet.write_formula(row, column + 6, formula, grey_percent_format)

                        formula = (
                            f'={xl_col_to_name(column + 4)}{row + 1}'
                            f'-{xl_col_to_name(column + 1)}{row + 1}'
                        )
                        sheet.write_formula(row, column + 7, formula, grey_borders_line_format)

                        formula = (
                            f'={xl_col_to_name(column + 4)}{row + 1}'
                            f'-{xl_col_to_name(column + 2)}{row + 1}'
                        )
                        sheet.write_formula(row, column + 8, formula, grey_borders_line_format)
                        row += 1
                column = 0

                sheet.merge_range(row, column, row, column + 26, f'ИТОГО {company.name}',
                                  company_heading_format)  # печатаем заголовок компании
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
                        if self.quarter_names.index(quarter) in (2, 3):  # III и IV кварталы
                            sheet.write_number(row, column + 1, company_data[section][year][quarter]['plan'],
                                               custom_line_format)
                            sheet.write_number(row, column + 2, company_data[section][year][quarter]['plan_6_6'],
                                               custom_line_format)
                            formula_fact = formula_forecast = ''
                            if section not in ('ebit', 'net_profit'):
                                formula_fact = '=sum(' + ','.join(xl_col_to_name(column + 3) + str(
                                    center_row + self.company_section_names.index(section) + 2) for center_row in
                                                                  formula_company) + ')'
                                formula_forecast = '=sum(' + ','.join(xl_col_to_name(column + 4) + str(
                                    center_row + self.company_section_names.index(section) + 2) for center_row in
                                                             formula_company) + ')'
                            sheet.write_formula(row, column + 3, formula_fact, custom_line_format)
                            sheet.write_formula(row, column + 4, formula_forecast, custom_line_format)
                            formula = f'=IFERROR({xl_col_to_name(column + 2)}{row + 1}/{xl_col_to_name(column + 1)}{row + 1}, " ")'
                            sheet.write_formula(row, column + 5, formula, bluegrey_custom_percent_format)
                            column += 5
                        else:
                            sheet.write_number(row, column + 1, company_data[section][year][quarter]['plan'],
                                               custom_line_format)
                            formula_fact = formula_forecast = ''
                            if section not in ('ebit', 'net_profit'):
                                formula_fact = '=sum(' + ','.join(xl_col_to_name(column + 2) + str(
                                    center_row + self.company_section_names.index(section) + 2) for center_row in
                                                                  formula_company) + ')'
                                formula_forecast = '=sum(' + ','.join(xl_col_to_name(column + 3) + str(
                                    center_row + self.company_section_names.index(section) + 2) for center_row in
                                                             formula_company) + ')'

                            sheet.write_formula(row, column + 2, formula_fact, custom_line_format)
                            sheet.write_formula(row, column + 3, formula_forecast, custom_line_format)
                            formula = f'=IFERROR({xl_col_to_name(column + 2)}{row + 1}/{xl_col_to_name(column + 1)}{row + 1}, " ")'
                            sheet.write_formula(row, column + 4, formula, bluegrey_custom_percent_format)
                            column += 4
                    formula = (
                        f'={xl_col_to_name(column - 17)}{row + 1}'
                        f'+{xl_col_to_name(column - 13)}{row + 1}'
                        f'+{xl_col_to_name(column - 9)}{row + 1}'
                        f'+{xl_col_to_name(column - 4)}{row + 1}'
                    )
                    sheet.write_formula(row, column + 1, formula, grey_line_format)  # план

                    formula = (
                        f'={xl_col_to_name(column - 16)}{row + 1}'
                        f'+{xl_col_to_name(column - 12)}{row + 1}'
                        f'+{xl_col_to_name(column - 8)}{row + 1}'
                        f'+{xl_col_to_name(column - 3)}{row + 1}'
                    )
                    sheet.write_formula(row, column + 2, formula, grey_line_format)  # план 6+6

                    formula = (
                        f'={xl_col_to_name(column - 16)}{row + 1}'
                        f'+{xl_col_to_name(column - 12)}{row + 1}'
                        f'+{xl_col_to_name(column - 7)}{row + 1}'
                        f'+{xl_col_to_name(column - 2)}{row + 1}'
                    )
                    sheet.write_formula(row, column + 3, formula, grey_line_format)  # факт

                    formula = (
                        f'={xl_col_to_name(column - 15)}{row + 1}'
                        f'+{xl_col_to_name(column - 11)}{row + 1}'
                        f'+{xl_col_to_name(column - 6)}{row + 1}'
                        f'+{xl_col_to_name(column - 1)}{row + 1}'
                        f'+{xl_col_to_name(column - 16)}{row + 1}'
                        f'+{xl_col_to_name(column - 12)}{row + 1}'
                        f'+{xl_col_to_name(column - 7)}{row + 1}'
                        f'+{xl_col_to_name(column - 2)}{row + 1}'
                    )
                    sheet.write_formula(row, column + 4, formula, grey_line_format)  # прогноз

                    formula = f'=IFERROR({xl_col_to_name(column + 3)}{row + 1}/{xl_col_to_name(column + 1)}{row + 1}, " ")'
                    sheet.write_formula(row, column + 5, formula, grey_percent_format)

                    formula = f'=IFERROR({xl_col_to_name(column + 3)}{row + 1}/{xl_col_to_name(column + 2)}{row + 1}, " ")'
                    sheet.write_formula(row, column + 6, formula, grey_percent_format)

                    formula = (
                        f'={xl_col_to_name(column + 4)}{row + 1}'
                        f'-{xl_col_to_name(column + 1)}{row + 1}'
                    )
                    sheet.write_formula(row, column + 7, formula, grey_borders_line_format)

                    formula = (
                        f'={xl_col_to_name(column + 4)}{row + 1}'
                        f'-{xl_col_to_name(column + 2)}{row + 1}'
                    )
                    sheet.write_formula(row, column + 8, formula, grey_borders_line_format)
                    row += 1
                row += 1

    def printworksheet(self, workbook, namesheet, budget, stages, year, print_managers):

        sheet = workbook.add_worksheet(namesheet)
        sheet.set_zoom(70)

        cur_budget_projects = self.env['project_budget.projects'].search([
            ('commercial_budget_id', '=', budget.id),
            ('stage_id', 'in', stages.ids),
            '|', '&', ('step_status', '=', 'step'),
            ('step_project_parent_id.project_have_steps', '=', True),
            '&', ('step_status', '=', 'project'),
            ('project_have_steps', '=', False),
        ], order='project_id')

        responsibility_centers = self.env['account.analytic.account'].search([
            ('parent_id', '=', False),
            ('plan_id', '=', self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
            ], order='name')  # для сортировки так делаем + берем сначала только верхние элементы

        companies = self.env['res.company'].search([], order='name').filtered(lambda r: r in responsibility_centers.company_id)

        key_account_managers = self.env['project_budget.projects'].search([]).key_account_manager_id.sorted('name')
        # key_account_managers = self.env.ref('project_budget.group_project_budget_key_account_manager').users.sorted('name').filtered(lambda r: r in cur_budget_projects.key_account_manager_id.user_id)

        data = self.get_plans(year, self.get_data_from_projects(cur_budget_projects, stages, year))

        self.print_rows(sheet, workbook, companies, responsibility_centers, key_account_managers, year, data, print_managers)

    def generate_xlsx_report(self, workbook, data, budgets):

        year = data['year']
        commercial_budget_id = data['commercial_budget_id']
        print_managers = data['print_managers']

        budget = self.env['project_budget.commercial_budget'].search([('id', '=', commercial_budget_id)])
        stages = self.env['project_budget.project.stage'].search([('code', '!=', '10')], order='sequence desc')  # для сортировки так делаем
        self.printworksheet(workbook, 'План-Факт', budget,  stages, year, False)
        self.printworksheet(workbook, 'План-Факт КАМы', budget, stages, year, True)
