from odoo import models
from datetime import date, timedelta
import xlsxwriter
from xlsxwriter.utility import xl_col_to_name
import logging


class ReportWeekToWeekExcel(models.AbstractModel):
    _name = 'report.project_budget.report_week_to_week_excel'
    _description = 'project_budget.report_week_to_week_excel'
    _inherit = 'report.report_xlsx.abstract'

    section_names = ['contracting', 'cash', 'acceptance', 'margin_income',]
    probability_names = ['fact', 'commitment', 'reserve', 'potential', 'lead', 'cancelled']
    quarter_names = ['Q1', 'Q2', 'Q3', 'Q4', 'YEAR']

    section_titles = {
        'contracting': 'Контрактование,\n руб. с НДС',
        'cash': 'ПДС,\n руб. с НДС',
        'acceptance': 'Выручка,\n руб. без НДС',
        'margin_income': 'МАРЖА 1,\n руб. без НДС',
    }

    def data_to_dict(self, data, quarter, year):
        projects = {}

        for section_name in self.section_names:
            for probability_name in self.probability_names:
                projects.setdefault(section_name, {}).setdefault(probability_name, 0)

        for p in data:
            if (p['date'].month-1)//3 == quarter and p['date'].year == year:
                if p['probability'] == 'from_project' or not p['probability']:
                    if p['stage_id'][1] in ('Исполнение, 100%', 'Выполнено'):
                        prob = 'fact'
                    elif p['stage_id'][1] == 'Обязательство, 75%':
                        prob = 'commitment'
                    elif p['stage_id'][1] == 'Резерв, 50%':
                        prob = 'reserve'
                    elif p['stage_id'][1] == 'Возможность, 30%':
                        prob = 'potential'
                    elif p['stage_id'][1] == 'Потенциал, 10%':
                        prob = 'lead'
                    elif p['stage_id'][1] == 'Отменен':
                        prob = 'cancelled'
                else:
                    prob = p['probability']

                project_id = str(p['project_id'][1]) + (('|' + str(p['step_id'][1])) if p['step_id'] else '')

                projects[p['type']][prob] += round(p['amount'])

                if p['type'] == 'acceptance' and p['probability'] != 'fact':
                    projects['margin_income'][prob] += round(p['amount'] * p['profitability'] / 100)

        return projects

    def find_difference(self, old_data, new_data, year):
        res = []

        for quarter in range(4):

            res_dict = {}
            for section_name in self.section_names:
                for probability_name in self.probability_names:
                    res_dict.setdefault(section_name, {}).setdefault(probability_name, 0)

            old_dict = self.data_to_dict(old_data, quarter, year)
            new_dict = self.data_to_dict(new_data, quarter, year)
            if new_dict and not old_dict:
                res.append(new_dict)
            elif old_dict and not new_dict:
                for type in self.section_names:
                    for probability in self.probability_names:
                        res_dict[type][probability] = -old_dict[type][probability]
                res.append(res_dict)
            else:
                has_changed = False
                for type in self.section_names:
                    for probability in self.probability_names:
                        res_dict[type][probability] = new_dict[type][probability] - old_dict[type][probability]
                        if res_dict[type][probability] != 0:
                            has_changed = True
                if has_changed:
                    res.append(res_dict)
                else:
                    res.append(False)
        return res

    def data_to_set(self, data):
        projects_set = set()
        for p in data:
            project_id = str(p.project_id.project_id) + '|' + ((str(p.step_id.project_id)) if p.step_id else '')
            projects_set.add(
                project_id + ',' + p.stage_id.code + ',' + p.type + ',' + p.probability + ',' + p.date.strftime(
                    "%d/%m/%y") + ',' + str(round(p.amount))
            )
        return projects_set

    def printworksheet(self, workbook, budget, past_budget, namesheet, year):

        line_format = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "num_format": '#,##0',
        })

        line_format_grey = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "num_format": '#,##0',
            'fg_color': '#E7E6E6',
        })

        line_format_left = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'align': 'left',
            'valign': 'vcenter',
            "num_format": '#,##0',
        })

        row = 2
        col = 3
        sheet = workbook.add_worksheet(namesheet)
        sheet.set_zoom(70)
        sheet.set_column(0, col - 1, 17)
        sheet.set_column(col, 5 * len(self.probability_names) + col - 1, 14)
        sheet.freeze_panes(2, col)
        sheet.hide_zero()
        sheet.autofilter(1, 0, 1, 2)

        sheet.merge_range(0, 0, 0, 2, past_budget.date_actual.strftime("%d/%m/%y") + ' -> ' + date.today().strftime("%d/%m/%y"), line_format)

        for quarter_n in range(5):
            if quarter_n % 2:
                format = line_format
            else:
                format = line_format_grey
            sheet.merge_range(0, col + quarter_n * len(self.probability_names), 0, col + len(self.probability_names) + quarter_n * len(self.probability_names) - 1, self.quarter_names[quarter_n], format)
            for probability_n in range(len(self.probability_names)):
                sheet.write_string(1,  col + quarter_n * len(self.probability_names) + probability_n, self.probability_names[probability_n], format)

        data = self.env['project_budget.financial_data_report'].search([('commercial_budget_id', '=', budget.id)])
        past_data = self.env['project_budget.financial_data_report'].search([('commercial_budget_id', '=', past_budget.id)])
        data_set = self.data_to_set(data)
        past_data_set = self.data_to_set(past_data)
        changed_projects = past_data_set ^ data_set
        changed_ids = list(set((i.split(',')[0]) for i in changed_projects))


        prj_ids = []
        stp_ids = []
        for changed_id in changed_ids:

            prj_id, stp_id = changed_id.split('|')
            prj_ids.append(prj_id)
            stp_ids.append((stp_id))

        old_dict = self.env['project_budget.financial_data_report'].search_read([
            ('date', '>=', date(year,1,1)),
            ('date', '<=', date(year, 12, 31)),
            ('commercial_budget_id', '=', past_budget.id),
            ('project_id.project_id', 'in', prj_ids),
            '|', ('step_id.project_id', 'in', stp_ids),
            ('step_id', '=', False),
        ])
        new_dict = self.env['project_budget.financial_data_report'].search_read([
            ('date', '>=', date(year, 1, 1)),
            ('date', '<=', date(year, 12, 31)),
            ('commercial_budget_id', '=', budget.id),
            ('project_id.project_id', 'in', prj_ids),
            '|', ('step_id.project_id', 'in', stp_ids),
            ('step_id', '=', False),
        ])

        print(changed_ids)

        for changed_id in changed_ids:

            prj_id, stp_id = changed_id.split('|')

            old_data = [x for x in old_dict if prj_id in x['project_id'][1]]
            new_data = [x for x in new_dict if prj_id in x['project_id'][1]]

            if old_data:
                company = old_data[0]['company_id'][1]
                office = old_data[0]['project_office_id'][1]
            elif new_data:
                company = new_data[0]['company_id'][1]
                office = new_data[0]['project_office_id'][1]
            else:
                company = ''
                office = ''

            if new_data and not old_data and new_data[0]['stage_id'][1] not in ('Отменен', 'Потенциал'):
                sheet.write_string(row, 0, company, line_format_left)
                sheet.write_string(row, 1, office, line_format_left)
                sheet.write_string(row, 2, 'NEW', line_format)
                for quarter_n in range(5):
                    sheet.merge_range(row, col + quarter_n * len(self.probability_names), row, col + (1 + quarter_n) * len(self.probability_names)- 1, prj_id + ('|' + stp_id if stp_id else ''), line_format)
            elif old_data and not new_data:
                sheet.write_string(row, 0, company, line_format_left)
                sheet.write_string(row, 1, office, line_format_left)
                sheet.write_string(row, 2, 'REMOVED', line_format)
                for quarter_n in range(5):
                    sheet.merge_range(row, col + quarter_n * len(self.probability_names), row, col + (1 + quarter_n) * len(self.probability_names)- 1, prj_id + ('|' + stp_id if stp_id else ''), line_format)
            elif new_data and old_data and not (new_data[0]['stage_id'][1] in ('Отменен', 'Потенциал') and old_data[0]['stage_id'][1] in ('Отменен', 'Потенциал')):
                sheet.write_string(row, 0, company, line_format_left)
                sheet.write_string(row, 1, office, line_format_left)
                sheet.write_string(row, 2, 'CHANGED', line_format)
                for quarter_n in range(5):
                    sheet.merge_range(row, col + quarter_n * len(self.probability_names), row, col + (1 + quarter_n) * len(self.probability_names)- 1, prj_id + ('|' + stp_id if stp_id else ''), line_format)
            else:
                continue

            row += 1

            for section in self.section_names:
                sheet.write_string(row + self.section_names.index(section), 0, company, line_format_left)
                sheet.write_string(row + self.section_names.index(section), 1, office, line_format_left)
                sheet.write_string(row + self.section_names.index(section), 2, self.section_titles[section], line_format)

            difference = self.find_difference(old_data, new_data, year)

            for quarter_n in range(4):
                if quarter_n % 2:
                    format = line_format
                else:
                    format = line_format_grey
                for section_n in range(len(self.section_names)):
                    for probability_n in range(len(self.probability_names)):
                        if difference[quarter_n]:
                            sheet.write_number(
                                row + section_n,
                                col + probability_n + quarter_n * len(self.probability_names),
                                difference[quarter_n][self.section_names[section_n]][self.probability_names[probability_n]],
                                format
                            )
                        else:
                            sheet.write_number(
                                row + section_n,
                                col + probability_n + quarter_n * len(self.probability_names),
                                0,
                                format
                            )
                        sheet.write_formula(
                            row + section_n,
                            col + 4 * len(self.probability_names) + probability_n,
                            '=sum({1}{0},{2}{0},{3}{0},{4}{0})'.format(
                                row + section_n + 1,
                                xl_col_to_name(col + probability_n),
                                xl_col_to_name(col + 1 * len(self.probability_names) + probability_n),
                                xl_col_to_name(col + 2 * len(self.probability_names) + probability_n),
                                xl_col_to_name(col + 3 * len(self.probability_names) + probability_n),
                            ),
                            line_format_grey
                        )

            row += 4

    def generate_xlsx_report(self, workbook, data, budgets):

        year = data['year']

        budget = self.env['project_budget.commercial_budget'].search([('id', '=', data['commercial_budget_id'])])
        past_budget = self.env['project_budget.commercial_budget'].search([('id', '=', data['past_commercial_budget_id'])])
        self.printworksheet(workbook, budget, past_budget, 'week to week', year)
