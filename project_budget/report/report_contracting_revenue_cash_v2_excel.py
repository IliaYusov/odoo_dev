from datetime import datetime
from odoo import models
from odoo.tools import date_utils


class ReportContractingRevenueCashV2Excel(models.AbstractModel):
    _name = 'report.project_budget.report_contracting_revenue_cash_v2_excel'
    _description = 'report contracting revenue cash excel'
    _inherit = 'report.report_xlsx.abstract'

    def print_prj(self, workbook, sheet, prj, rvn_plan, rvn_facts, csh_plans, csh_facts, row, col):
        row_format = workbook.add_format({
            'font_size': 10,
        })
        row_format_number = workbook.add_format({
            'font_size': 10,
            'num_format': '#,##0',
        })
        row_format_date = workbook.add_format({
            'font_size': 10,
            'num_format': 'dd.mm.yyyy',
        })

        rvn_plan_date = ''
        rvn_plan_amount = 0
        if rvn_plan:
            rvn_plan_date = rvn_plan.date_cash
            rvn_plan_amount = rvn_plan.sum_cash

        rvn_fact_date = ''
        rvn_fact_amount = 0
        if rvn_facts:
            for fact in rvn_facts:
                rvn_fact_amount += fact.sum_cash
                if rvn_fact_date:
                    rvn_fact_date = max(rvn_fact_date, fact.date_cash)
                else:
                    rvn_fact_date = fact.date_cash

        csh_plan_date = ''
        csh_plan_amount = 0
        if csh_plans:
            for plan in csh_plans:
                csh_plan_amount += plan.sum_cash
                if csh_plan_date:
                    csh_plan_date = max(csh_plan_date, plan.date_cash)
                else:
                    csh_plan_date = plan.date_cash
        if rvn_plan:
            csh_plan_amount = min(rvn_plan_amount, csh_plan_amount) if csh_plan_amount >= 0 else max(rvn_plan_amount, csh_plan_amount) # на случай нескольких актов закрытых одним ПДС

        csh_fact_date = ''
        csh_fact_amount = 0
        if csh_facts:
            for fact in csh_facts:
                csh_fact_amount += fact.sum_cash
                if csh_fact_date:
                    csh_fact_date = max(csh_fact_date, fact.date_cash)
                else:
                    csh_fact_date = fact.date_cash
        if csh_plans:
            csh_fact_amount = min(csh_fact_amount, csh_plan_amount) if csh_plan_amount >=0 else max(csh_fact_amount, csh_plan_amount) # на случай нескольких актов закрытых одним ПДС

        sheet.write(row, col, prj.project_id, row_format)
        col += 1
        sheet.write(row, col, prj.step_project_number or '', row_format)
        col += 1
        sheet.write(row, col, prj.responsibility_center_id.name, row_format)
        col += 1

        if prj.order_ids:
            pn = ', '.join(cat.root_category_id.name if cat.root_category_id else cat.name for cat in prj.order_ids.line_ids.product_category_id)
            sheet.write(row, col, pn, row_format)
        else:
            sheet.write(row, col, '', row_format)
        col += 1

        if prj.order_ids:
            rpn = ', '.join(cat.root_category_id.head_id.name if cat.root_category_id else cat.head_id.name for cat in prj.order_ids.line_ids.product_category_id if (cat.root_category_id.head_id if cat.root_category_id else cat.head_id))
            sheet.write(row, col, rpn, row_format)
        else:
            sheet.write(row, col, '', row_format)
        col += 1

        sheet.write(row, col, prj.key_account_manager_id.name or '', row_format)
        col += 1
        sheet.write(row, col, prj.project_manager_id.name or '', row_format)
        col += 1
        sheet.write(row, col, prj.partner_id.name or '', row_format)
        col += 1
        sheet.write(row, col, prj.company_partner_id.partner_id.name or '', row_format)
        col += 1
        sheet.write(row, col, prj.essence_project or '', row_format)
        col += 1
        sheet.write(row, col, prj.stage_id.name, row_format)
        col += 1
        sheet.write(row, col, prj.profitability, row_format_number)
        col += 1
        sheet.write(row, col, prj.end_presale_project_month, row_format_date)
        col += 1
        sheet.write(row, col, 'Q' + str(date_utils.get_quarter_number(prj.end_presale_project_month)) + ' ' + str(prj.end_presale_project_month.year), row_format)
        col += 1
        sheet.write(row, col, prj.amount_total_in_company_currency, row_format_number)
        col += 1
        sheet.write(row, col, rvn_plan_date, row_format_date)
        col += 1
        sheet.write(row, col, rvn_fact_date, row_format_date)
        col += 1
        sheet.write(row, col, rvn_plan_amount, row_format_number)
        col += 1
        sheet.write(row, col, rvn_fact_amount, row_format_number)
        col += 1
        sheet.write(row, col, rvn_plan_amount - rvn_fact_amount, row_format_number)
        col += 1

        if csh_plans:
            frst_faf = prj.planned_acceptance_flow_ids.sorted('date_cash')[:1]
            frst_fcf = prj.planned_cash_flow_ids.sorted('date_cash')[:1]
        else:
            frst_faf = prj.fact_acceptance_flow_ids.sorted('date_cash')[:1] or prj.planned_acceptance_flow_ids.sorted(
                'date_cash')[:1]
            frst_fcf = prj.fact_cash_flow_ids.sorted('date_cash')[:1]
        res = ''
        if frst_faf and frst_fcf:
            if frst_fcf.date_cash <= frst_faf.date_cash and frst_fcf.sum_cash >= frst_faf.sum_cash * (
                    1 + prj.tax_id.amount / 100):
                res = 'Предоплата 100%'
            elif frst_fcf.date_cash <= frst_faf.date_cash and frst_fcf.sum_cash < frst_faf.sum_cash * (
                    1 + prj.tax_id.amount / 100):
                res = 'Частичная предоплата'
            elif frst_fcf.date_cash > frst_faf.date_cash:
                res = 'Постоплата 100%'

        sheet.write(row, col, res, row_format)
        col += 1
        sheet.write(row, col, csh_plan_date, row_format_date)
        col += 1
        sheet.write(row, col, csh_fact_date, row_format_date)
        col += 1
        sheet.write(row, col, csh_plan_amount, row_format_number)
        col += 1
        sheet.write(row, col, csh_fact_amount, row_format_number)
        col += 1
        sheet.write(row, col, csh_plan_amount - csh_fact_amount, row_format_number)
        col += 1

    def print_worksheets(self, workbook, sheets, date_start, date_end):
        projects = self.env['project_budget.projects'].search([
            ('budget_state', '=', 'work'),
            '|', '&', ('step_status', '=', 'step'),
            ('step_project_parent_id.project_have_steps', '=', True),
            '&', ('step_status', '=', 'project'),
            ('project_have_steps', '=', False),
        ], order='project_id asc')

        row_prj = 0

        for prj in projects:

            if not prj.planned_acceptance_flow_ids and not prj.planned_cash_flow_ids and date_start <= prj.end_presale_project_month <= date_end:
                row_prj += 1
                self.print_prj(workbook, sheets['projects'], prj, False, False, False, False, row_prj, 0, )

            for rvn_plan in prj.planned_acceptance_flow_ids:
                if date_start <= rvn_plan.date_cash <= date_end:
                    row_prj += 1
                    rvn_facts = rvn_plan.distribution_acceptance_ids.fact_acceptance_flow_id
                    csh_plans = prj.planned_cash_flow_ids.filtered(lambda c: rvn_plan in c.acceptance_ids and date_start <= c.date_cash <= date_end)
                    csh_facts = csh_plans.distribution_cash_ids.fact_cash_flow_id
                    self.print_prj(workbook, sheets['projects'], prj, rvn_plan, rvn_facts, csh_plans, csh_facts, row_prj, 0,)

            for rvn_fact in prj.fact_acceptance_flow_ids:
                if not rvn_fact.distribution_acceptance_ids and date_start <= rvn_fact.date_cash <= date_end:
                    row_prj += 1
                    csh_facts = prj.fact_cash_flow_ids.filtered(lambda c: rvn_fact in c.acceptance_ids and date_start <= c.date_cash <= date_end)
                    self.print_prj(workbook, sheets['projects'], prj, False, rvn_fact, False, csh_facts, row_prj, 0,)

            for csh_plan in prj.planned_cash_flow_ids:
                if not csh_plan.acceptance_ids and date_start <= csh_plan.date_cash <= date_end:
                    row_prj += 1
                    cash_facts = csh_plan.distribution_cash_ids.fact_cash_flow_id
                    self.print_prj(workbook, sheets['projects'], prj, False, False, csh_plan, cash_facts, row_prj, 0,)

            for csh_fact in prj.fact_cash_flow_ids:
                if not csh_fact.distribution_cash_ids and not csh_fact.acceptance_ids and date_start <= csh_fact.date_cash <= date_end:
                    row_prj += 1
                    self.print_prj(workbook, sheets['projects'], prj, False, False, False, csh_fact, row_prj, 0,)

        sheets['projects'].add_table(0, 0, row_prj, 25, {
            'columns': [
                {'header': 'ID проекта'},
                {'header': 'Контракт.Номер этапа проекта'},
                {'header': 'Контракт.Центр ответственности'},
                {'header': 'Контракт.ПН'},
                {'header': 'Контракт.Ответственный РПН'},
                {'header': 'Контракт.КАМ'},
                {'header': 'Контракт.Руководитель проекта'},
                {'header': 'Контракт.Заказчик'},
                {'header': 'Контракт.Партнер'},
                {'header': 'Контракт.Наименование'},
                {'header': 'Контракт.Этап'},
                {'header': 'Контракт.Рентабельность'},
                {'header': 'Контракт.Дата контрактования'},
                {'header': 'Контракт.Квартал контрактования'},
                {'header': 'Контракт.Сумма контрактования'},
                {'header': 'ВВ_план.Дата ВВ'},
                {'header': 'ВВ_факт.Дата ВВ'},
                {'header': 'ВВ_план_сумма'},
                {'header': 'ВВ_факт_сумма'},
                {'header': 'ВВ_to go'},
                {'header': 'ПДС_план.Тип оплаты'},
                {'header': 'ПДС_план.Дата ПДС'},
                {'header': 'ПДС_факт.Дата ПДС'},
                {'header': 'ПДС_план_сумма'},
                {'header': 'ПДС_факт_сумма'},
                {'header': 'ПДС_to go'},
            ]
        })

    def generate_xlsx_report(self, workbook, data, budgets):
        date_start = datetime.strptime(data['date_start'], '%Y-%m-%d').date()
        date_end = datetime.strptime(data['date_end'], '%Y-%m-%d').date()

        sheets = {
            'projects': workbook.add_worksheet('Проекты'),
        }

        self.print_worksheets(workbook, sheets, date_start, date_end)
