from odoo import models
import datetime
import calendar
import xlsxwriter
from xlsxwriter.utility import xl_col_to_name


class ReportBudgetForecastExcel(models.AbstractModel):
    _name = 'report.project_budget.report_budget_forecast_v3_excel'
    _description = 'project_budget.report_budget_forecast_v3_excel'
    _inherit = 'report.report_xlsx.abstract'

    START_COLUMN = 10

    indicators = ['contraction', 'cash_flow', 'gross_revenue', 'margin']

    month_rus_name = [
        'Январь',
        'Февраль',
        'Март',
        'Апрель',
        'Май',
        'Июнь',
        'Июль',
        'Август',
        'Сентябрь',
        'Октябрь',
        'Ноябрь',
        'Декабрь',
    ]

    def calculate_periods_dict(self, workbook, year):
        data = [
            {
                'indicator': 'contraction',
                'periods': [],
                'type': 'monthly',
                'year': year,
                'name': 'Контрактование, с НДС',
            },
            {
                'indicator': 'cash_flow',
                'periods': [],
                'type': 'monthly',
                'year': year,
                'name': 'Поступление денежных средств, с НДС',
            },
            {
                'indicator': 'gross_revenue',
                'periods': [],
                'type': 'quarterly',
                'year': year,
                'name': 'Валовая Выручка, без НДС'
            },
            {
                'indicator': 'margin',
                'periods': [],
                'type': 'quarterly',
                'year': year,
                'name': 'Валовая прибыль (Маржа 1), без НДС',
            },
            {
                'type': 'blank',
            },
            {
                'indicator': 'contraction',
                'periods': [],
                'type': 'yearly',
                'year': year + 1,
                'name': 'Контрактование, с НДС',
            },
            {
                'indicator': 'cash_flow',
                'periods': [],
                'type': 'yearly',
                'year': year + 1,
                'name': 'Поступление денежных средств, с НДС',
            },
            {
                'indicator': 'gross_revenue',
                'periods': [],
                'type': 'yearly',
                'year': year + 1,
                'name': 'Валовая Выручка, без НДС',
            },
            {
                'indicator': 'margin',
                'periods': [],
                'type': 'yearly',
                'year': year + 1,
                'name': 'Валовая прибыль (Маржа 1), без НДС',
            },
            {
                'type': 'blank',
            },
            {
                'indicator': 'contraction',
                'periods': [],
                'type': 'yearly',
                'year': year + 2,
                'name': 'Контрактование, с НДС',
            },
            {
                'indicator': 'cash_flow',
                'periods': [],
                'type': 'yearly',
                'year': year + 2,
                'name': 'Поступление денежных средств, с НДС',
            },
            {
                'indicator': 'gross_revenue',
                'periods': [],
                'type': 'yearly',
                'year': year + 2,
                'name': 'Валовая Выручка, без НДС',
            },
            {
                'indicator': 'margin',
                'periods': [],
                'type': 'yearly',
                'year': year + 2,
                'name': 'Валовая прибыль (Маржа 1), без НДС',
            },
        ]

        for section in data:
            if section['type'] == 'monthly':
                for month in range(1, 13):
                    section['periods'].append({
                        'start': datetime.datetime(day=1, month=month, year=section['year']),
                        'end': datetime.datetime(day=calendar.monthrange(year, month)[1], month=month, year=section['year']),
                        'cols': [
                            {
                                'type': 'fact',
                                'amount': 0,
                                'name': 'Факт',
                            },
                            {
                                'type': 'commitment',
                                'amount': 0,
                                'name': 'Обязательство',
                            },
                            {
                                'type': 'reserve',
                                'amount': 0,
                                'name': 'Резерв',
                            },
                            {
                                'type': 'potential',
                                'amount': 0,
                                'name': 'Потенциал',
                            },
                        ],
                        'name': self.month_rus_name[month - 1]
                    })
                    if month == 3:
                        section['periods'].append({
                            'cols': [
                                {
                                    'type': 'plan',
                                    'amount': 0,
                                    'name': 'План Q1',
                                },
                                {
                                    'type': 'fact',
                                    'amount': 0,
                                    'name': 'Факт',
                                },
                                {
                                    'type': 'commitment',
                                    'amount': 0,
                                    'name': 'Обязательство',
                                },
                                {
                                    'type': 'reserve',
                                    'amount': 0,
                                    'name': 'Резерв',
                                },
                                {
                                    'type': 'potential',
                                    'amount': 0,
                                    'name': 'Потенциал',
                                },
                            ],
                            'name': 'Q1 итого'
                        })
                    elif month == 6:
                        section['periods'].append({
                            'cols': [
                                {
                                    'type': 'plan',
                                    'amount': 0,
                                    'name': 'План Q2',
                                },
                                {
                                    'type': 'fact',
                                    'amount': 0,
                                    'name': 'Факт',
                                },
                                {
                                    'type': 'commitment',
                                    'amount': 0,
                                    'name': 'Обязательство',
                                },
                                {
                                    'type': 'reserve',
                                    'amount': 0,
                                    'name': 'Резерв',
                                },
                                {
                                    'type': 'potential',
                                    'amount': 0,
                                    'name': 'Потенциал',
                                },
                            ],
                            'name': 'Q2 итого'
                        })
                        section['periods'].append({
                            'cols': [
                                {
                                    'type': 'plan',
                                    'amount': 0,
                                    'name': 'План HY1',
                                },
                                {
                                    'type': 'fact',
                                    'amount': 0,
                                    'name': 'Факт',
                                },
                                {
                                    'type': 'commitment',
                                    'amount': 0,
                                    'name': 'Обязательство',
                                },
                                {
                                    'type': 'reserve',
                                    'amount': 0,
                                    'name': 'Резерв',
                                },
                                {
                                    'type': 'potential',
                                    'amount': 0,
                                    'name': 'Потенциал',
                                },
                            ],
                            'name': f'HY1 {section["year"]} итого'
                        })
                    elif month == 9:
                        section['periods'].append({
                            'cols': [
                                {
                                    'type': 'plan',
                                    'amount': 0,
                                    'name': 'План Q3',
                                },
                                {
                                    'type': 'plan66',
                                    'amount': 0,
                                    'name': 'План Q3 6+6',
                                },
                                {
                                    'type': 'fact',
                                    'amount': 0,
                                    'name': 'Факт',
                                },
                                {
                                    'type': 'commitment',
                                    'amount': 0,
                                    'name': 'Обязательство',
                                },
                                {
                                    'type': 'reserve',
                                    'amount': 0,
                                    'name': 'Резерв',
                                },
                                {
                                    'type': 'potential',
                                    'amount': 0,
                                    'name': 'Потенциал',
                                },
                            ],
                            'name': 'Q3 итого'
                        })
                    elif month == 12:
                        section['periods'].append({
                            'cols': [
                                {
                                    'type': 'plan',
                                    'amount': 0,
                                    'name': 'План Q4',
                                },
                                {
                                    'type': 'plan66',
                                    'amount': 0,
                                    'name': 'План Q4 6+6',
                                },
                                {
                                    'type': 'fact',
                                    'amount': 0,
                                    'name': 'Факт',
                                },
                                {
                                    'type': 'commitment',
                                    'amount': 0,
                                    'name': 'Обязательство',
                                },
                                {
                                    'type': 'reserve',
                                    'amount': 0,
                                    'name': 'Резерв',
                                },
                                {
                                    'type': 'potential',
                                    'amount': 0,
                                    'name': 'Потенциал',
                                },
                            ],
                            'name': 'Q4 итого'
                        })
                        section['periods'].append({
                            'cols': [
                                {
                                    'type': 'plan',
                                    'amount': 0,
                                    'name': 'План HY2',
                                },
                                {
                                    'type': 'plan66',
                                    'amount': 0,
                                    'name': 'План HY2 6+6',
                                },
                                {
                                    'type': 'fact',
                                    'amount': 0,
                                    'name': 'Факт',
                                },
                                {
                                    'type': 'commitment',
                                    'amount': 0,
                                    'name': 'Обязательство',
                                },
                                {
                                    'type': 'reserve',
                                    'amount': 0,
                                    'name': 'Резерв',
                                },
                                {
                                    'type': 'potential',
                                    'amount': 0,
                                    'name': 'Потенциал',
                                },
                            ],
                            'name': f'HY2 {section["year"]} итого'
                        })
                        section['periods'].append({
                            'cols': [
                                {
                                    'type': 'plan',
                                    'amount': 0,
                                    'name': f'План {section["year"]}',
                                },
                                {
                                    'type': 'plan66',
                                    'amount': 0,
                                    'name': f'План {section["year"]} 6+6',
                                },
                                {
                                    'type': 'fact',
                                    'amount': 0,
                                    'name': 'Факт',
                                },
                                {
                                    'type': 'commitment',
                                    'amount': 0,
                                    'name': 'Обязательство',
                                },
                                {
                                    'type': 'reserve',
                                    'amount': 0,
                                    'name': 'Резерв',
                                },
                                {
                                    'type': 'potential',
                                    'amount': 0,
                                    'name': 'Потенциал',
                                },
                            ],
                            'name': f'{section["year"]} итого'
                        })
            elif section['type'] == 'quarterly':
                section['periods'].append({
                    'start': datetime.datetime(day=1, month=1, year=section['year']),
                    'end': datetime.datetime(day=31, month=3, year=section['year']),
                    'cols': [
                        {
                            'type': 'plan',
                            'amount': 0,
                            'name': 'План Q1',
                        },
                        {
                            'type': 'fact',
                            'amount': 0,
                            'name': 'Факт',
                        },
                        {
                            'type': 'commitment',
                            'amount': 0,
                            'name': 'Обязательство',
                        },
                        {
                            'type': 'reserve',
                            'amount': 0,
                            'name': 'Резерв',
                        },
                        {
                            'type': 'potential',
                            'amount': 0,
                            'name': 'Потенциал',
                        },
                    ],
                    'name': 'Q1'
                })
                section['periods'].append({
                    'start': datetime.datetime(day=1, month=4, year=section['year']),
                    'end': datetime.datetime(day=30, month=6, year=section['year']),
                    'cols': [
                        {
                            'type': 'plan',
                            'amount': 0,
                            'name': 'План Q2',
                        },
                        {
                            'type': 'fact',
                            'amount': 0,
                            'name': 'Факт',
                        },
                        {
                            'type': 'commitment',
                            'amount': 0,
                            'name': 'Обязательство',
                        },
                        {
                            'type': 'reserve',
                            'amount': 0,
                            'name': 'Резерв',
                        },
                        {
                            'type': 'potential',
                            'amount': 0,
                            'name': 'Потенциал',
                        },
                    ],
                    'name': 'Q2'
                })
                section['periods'].append({
                    'cols': [
                        {
                            'type': 'plan',
                            'amount': 0,
                            'name': 'План HY1',
                        },
                        {
                            'type': 'fact',
                            'amount': 0,
                            'name': 'Факт',
                        },
                        {
                            'type': 'commitment',
                            'amount': 0,
                            'name': 'Обязательство',
                        },
                        {
                            'type': 'reserve',
                            'amount': 0,
                            'name': 'Резерв',
                        },
                        {
                            'type': 'potential',
                            'amount': 0,
                            'name': 'Потенциал',
                        },
                    ],
                    'name': f'HY1 {section["year"]} итого'
                })
                section['periods'].append({
                    'start': datetime.datetime(day=1, month=7, year=section['year']),
                    'end': datetime.datetime(day=30, month=9, year=section['year']),
                    'cols': [
                        {
                            'type': 'plan',
                            'amount': 0,
                            'name': 'План Q3',
                        },
                        {
                            'type': 'plan66',
                            'amount': 0,
                            'name': 'План Q3 6+6',
                        },
                        {
                            'type': 'fact',
                            'amount': 0,
                            'name': 'Факт',
                        },
                        {
                            'type': 'commitment',
                            'amount': 0,
                            'name': 'Обязательство',
                        },
                        {
                            'type': 'reserve',
                            'amount': 0,
                            'name': 'Резерв',
                        },
                        {
                            'type': 'potential',
                            'amount': 0,
                            'name': 'Потенциал',
                        },
                    ],
                    'name': 'Q3'
                })
                section['periods'].append({
                    'start': datetime.datetime(day=1, month=10, year=section['year']),
                    'end': datetime.datetime(day=31, month=12, year=section['year']),
                    'cols': [
                        {
                            'type': 'plan',
                            'amount': 0,
                            'name': 'План Q4',
                        },
                        {
                            'type': 'plan66',
                            'amount': 0,
                            'name': 'План Q4 6+6',
                        },
                        {
                            'type': 'fact',
                            'amount': 0,
                            'name': 'Факт',
                        },
                        {
                            'type': 'commitment',
                            'amount': 0,
                            'name': 'Обязательство',
                        },
                        {
                            'type': 'reserve',
                            'amount': 0,
                            'name': 'Резерв',
                        },
                        {
                            'type': 'potential',
                            'amount': 0,
                            'name': 'Потенциал',
                        },
                    ],
                    'name': 'Q4'
                })
                section['periods'].append({
                    'cols': [
                        {
                            'type': 'plan',
                            'amount': 0,
                            'name': 'План HY2',
                        },
                        {
                            'type': 'plan66',
                            'amount': 0,
                            'name': 'План HY2 6+6',
                        },
                        {
                            'type': 'fact',
                            'amount': 0,
                            'name': 'Факт',
                        },
                        {
                            'type': 'commitment',
                            'amount': 0,
                            'name': 'Обязательство',
                        },
                        {
                            'type': 'reserve',
                            'amount': 0,
                            'name': 'Резерв',
                        },
                        {
                            'type': 'potential',
                            'amount': 0,
                            'name': 'Потенциал',
                        },
                    ],
                    'name': f'HY2 {section["year"]} итого'
                })
                section['periods'].append({
                    'cols': [
                        {
                            'type': 'plan',
                            'amount': 0,
                            'name': f'План {section["year"]}',
                        },
                        {
                            'type': 'plan66',
                            'amount': 0,
                            'name': f'План {section["year"]} 6+6',
                        },
                        {
                            'type': 'fact',
                            'amount': 0,
                            'name': 'Факт',
                        },
                        {
                            'type': 'commitment',
                            'amount': 0,
                            'name': 'Обязательство',
                        },
                        {
                            'type': 'reserve',
                            'amount': 0,
                            'name': 'Резерв',
                        },
                        {
                            'type': 'potential',
                            'amount': 0,
                            'name': 'Потенциал',
                        },
                    ],
                    'name': f'{section["year"]} итого'
                })
            elif section['type'] == 'yearly':
                section['periods'].append({
                    'start': datetime.datetime(day=1, month=1, year=section['year']),
                    'end': datetime.datetime(day=31, month=12, year=section['year']),
                    'cols': [
                        {
                            'type': 'plan',
                            'amount': 0,
                            'name': f'План {section["year"]}',
                        },
                        {
                            'type': 'fact',
                            'amount': 0,
                            'name': 'Факт',
                        },
                        {
                            'type': 'commitment',
                            'amount': 0,
                            'name': 'Обязательство',
                        },
                        {
                            'type': 'reserve',
                            'amount': 0,
                            'name': 'Резерв',
                        },
                        {
                            'type': 'potential',
                            'amount': 0,
                            'name': 'Потенциал',
                        },
                    ],
                    'name': f'{section["year"]} итого'
                })
        return data

    def print_worksheet(self, workbook, budget, worksheet_name, year):

        report_name = budget.name
        sheet = workbook.add_worksheet(worksheet_name)
        sheet.set_zoom(85)
        sheet.hide_zero()

        bold = workbook.add_format({'bold': True})
        money_format = workbook.add_format({'num_format': '#,##0'})
        head_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_size': 10,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            'fg_color': '#FFFF00'
        })
        summary_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_size': 12,
            'text_wrap': True,
            'valign': 'vcenter',
            "num_format": '#,##0',
        })
        summary_format_border_top = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'text_wrap': True,
            'valign': 'vcenter',
            "num_format": '#,##0',
            'top': 2,
            'left': 2,
            'right': 2,
        })
        summary_format_border_top_center = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'text_wrap': True,
            'valign': 'vcenter',
            'align': 'center',
            "num_format": '#,##0',
            'top': 2,
            'left': 2,
            'right': 2,
        })
        summary_format_border_bottom = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'text_wrap': True,
            'valign': 'vjustify',
            "num_format": '#,##0',
            'top': 1,
            'bottom': 2,
            'left': 2,
            'right': 2,
        })
        summary_format_percent = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_size': 12,
            'text_wrap': True,
            'valign': 'vcenter',
            "num_format": '0%',
        })
        head_format_1 = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "bold": False,
            "fg_color": '#C6E0B4',
            "font_size": 8,
        })
        row_format_date_month = workbook.add_format({
            'border': 1,
            'font_size': 10,
        })
        row_format_manager = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#D9D9D9',
        })
        row_format_manager.set_num_format('#,##0')
        row_format_office = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#8497B0',
        })
        row_format_office.set_num_format('#,##0')
        row_format_date_month.set_num_format('mmm yyyy')
        row_format = workbook.add_format({
            'border': 1,
            'font_size': 10
        })
        row_format_canceled_project = workbook.add_format({
            'border': 1,
            'font_size': 10
        })
        row_format_canceled_project.set_font_color('red')
        row_format_number = workbook.add_format({
            'border': 1,
            'font_size': 10,
        })
        row_format_number.set_num_format('#,##0')
        row_format_number_canceled_project = workbook.add_format({
            'border': 1,
            'font_size': 10,
        })
        row_format_number_canceled_project.set_num_format('#,##0')
        row_format_number_canceled_project.set_font_color('red')
        row_format_number_itogo = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#A9D08E',

        })
        row_format_number_itogo.set_num_format('#,##0')
        head_format_month_itogo = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "bold": True,
            "fg_color": '#DCE6F1',
            "font_size": 10,
        })
        head_format_month_itogo.set_num_format('#,##0')
        row_format_plan = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#DCE6F1',
            "num_format": '#,##0',
        })
        row_format_diff = workbook.add_format({
            'border': 1,
            'font_size': 12,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "bold": True,
            "fg_color": '#DDD9C4',
            "num_format": '#,##0;[red]-#,##0',
        })
        row_format_itogo_estimated_plan = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#FFFF00',
            "num_format": '#,##0',
            'align': 'center',
        })
        row_format_itogo_estimated_plan_left = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#FFFF00',
            "num_format": '#,##0',
        })
        row_format_itogo_estimated_plan_cross = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#FFFF00',
            "num_format": '#,##0',
            'align': 'center',
            'diag_type': 3,
        })
        row_format_plan_cross = workbook.add_format({
            'border': 1,
            "fg_color": '#DCE6F1',
            'diag_type': 3,
        })
        date_format = workbook.add_format({'num_format': 'd mmmm yyyy'})

        row = 0
        sheet.write_string(row, 0, budget.name, bold)
        row = 2
        column = 0
        # sheet.write_string(row, column, "Прогноз",head_format)
        sheet.write_string(row + 1, column, "Проектный офис", head_format_1)
        sheet.write_string(row + 2, column, "", head_format_1)
        sheet.set_column(column, column, 21.5)
        column += 1
        sheet.merge_range(row - 2, column, row - 1, column, "Расчетный План:", summary_format)
        sheet.write_string(row + 1, column, "КАМ", head_format_1)
        sheet.write_string(row + 2, column, "", head_format_1)
        sheet.set_column(column, column, 19.75)
        column += 1
        sheet.write_string(row - 2, column, "Обязательство", summary_format)
        sheet.write_string(row - 1, column, "Резерв", summary_format)
        sheet.write_string(row + 1, column, "Заказчик", head_format_1)
        sheet.write_string(row + 2, column, "", head_format_1)
        sheet.set_column(column, column, 25)
        column += 1
        sheet.write_number(row - 2, column, 1, summary_format_percent)
        sheet.write_number(row - 1, column, 0.6, summary_format_percent)
        sheet.write_string(row + 1, column, "Наименование Проекта", head_format_1)
        sheet.write_string(row + 2, column, "", head_format_1)
        sheet.set_column(column, column, 12.25)
        column += 1
        # sheet.write_string(row, column, "", head_format)
        sheet.write_string(row + 1, column, "Номер этапа проекта CRM", head_format_1)
        sheet.write_string(row + 2, column, "", head_format_1)
        # sheet.set_column(column, column, 15)
        column += 1
        sheet.write_string(row + 1, column, "Номер этапа проекта AX", head_format_1)
        sheet.write_string(row + 2, column, "", head_format_1)
        # sheet.set_column(column, column, 15)
        column += 1
        # sheet.write_string(row, column, "", head_format)
        sheet.write_string(row + 1, column, "Сумма проекта/этапа, руб.", head_format_1)
        sheet.write_string(row + 2, column, "", head_format_1)
        # sheet.set_column(column, column, 14)
        column += 1
        # sheet.write_string(row, column, "", head_format)
        sheet.write_string(row + 1, column, "Дата контрактования", head_format_1)
        sheet.write_string(row + 2, column, "", head_format_1)
        # sheet.set_column(column, column, 16.88)
        column += 1
        # sheet.write_string(row, column, "", head_format)
        sheet.write_string(row + 1, column, "Прибыльность, экспертно, %", head_format_1)
        sheet.write_string(row + 2, column, "", head_format_1)
        # sheet.set_column(column, column, 9)
        sheet.set_column(4, 9, False, False, {'hidden': 1, 'level': 1})
        column += 1
        # sheet.write_string(row, column, "", head_format)
        sheet.write_string(row + 1, column, "", head_format_1)
        sheet.write_string(row + 2, column, "", head_format_1)
        sheet.set_column(column, column, 2)
        column += 1


        forecast_ids = {
            'commitment': self.env.ref('project_budget_nkk.project_budget_forecast_probability_commitment').id,
            'reserve': self.env.ref('project_budget_nkk.project_budget_forecast_probability_reserve').id,
            'potential': self.env.ref('project_budget_nkk.project_budget_forecast_probability_potential').id,
        }

        data = self.calculate_periods_dict(workbook, year)

        start_col = 10

        for section in data:  # печатаем шапку
            if section['type'] != 'blank':
                for period in section['periods']:
                    sheet.merge_range(row, column, row, column + len(period['cols']) - 1, period['name'], head_format_1)
                    for i, col in enumerate(period['cols']):

                        if col['type'] in ('plan', 'plan66', 'fact'):
                            sheet.merge_range(row + 2, column, row + 1, column, col['name'], head_format_1)
                        else:
                            sheet.write_string(row + 2, column, col['name'], head_format_1)

                        if col['type'] == 'commitment':
                            sheet.merge_range(row + 1, column, row + 1, column + (len(period['cols']) - i - 1), 'Прогноз до конца периода (на дату отчета)', head_format_1)

                        column += 1
                sheet.merge_range(row - 1, start_col, row - 1, column - 1, section['name'], head_format_1)
            else:
                column += 1
            start_col = column

        financial_indicators = self.env['project.budget.financial.indicator'].search([
            ('commercial_budget_id', '=', budget.id),
            ('date', '>=', datetime.datetime(day=1, month=1, year=year)),
            ('date', '<=', datetime.datetime(day=31, month=12, year=year + 2))
        ], order='company_id, project_office_id, key_account_manager_id, stage_id, project_id')

        row += 3

        company_rows = list()
        for company in financial_indicators.company_id:
            office_rows = list()

            current_offices = financial_indicators.project_office_id.filtered(lambda o: o.company_id == company)
            current_offices_wo_parents = current_offices.filtered(lambda o: not o.parent_id)
            all_offices = list()
            all_offices_sorted = list()

            for office in current_offices:  # добавляем все промежуточные родители в список офисов
                office_parent = office.parent_id
                while office_parent:
                    if office_parent not in all_offices:
                        all_offices.append(office_parent)
                    office_parent = office_parent.parent_id
                all_offices.append(office)

            def get_office_ids(o_wo_parents, all_o, all_o_sorted):  # сортируем офисы так, чтобы потомки шли перед родителями
                for o in o_wo_parents:
                    child_offices = o.child_ids
                    if child_offices:
                        all_o_sorted = get_office_ids(child_offices, all_o, all_o_sorted)
                    if o not in all_o_sorted and o in all_o:
                        all_o_sorted.append(o)
                return all_o_sorted

            all_offices_sorted = get_office_ids(current_offices_wo_parents, all_offices, all_offices_sorted)

            for office in all_offices_sorted:
                kam_rows = list()
                for kam in financial_indicators.key_account_manager_id.filtered(lambda k: k.company_id == company):
                    stage_rows = list()
                    kam_is_present = False
                    for stage in financial_indicators.stage_id:
                        stage_start_row = row + 1
                        stage_is_present = False
                        for project in financial_indicators.project_id.filtered(
                            lambda p: p.company_id == company
                                      and p.project_office_id == office
                                      and p.key_account_manager_id == kam
                                      and p.stage_id == stage
                        ):
                            current_indicators = financial_indicators.filtered(lambda ci: ci.project_id == project)
                            if current_indicators:
                                stage_is_present = True
                                kam_is_present = True
                                column = self.START_COLUMN
                                sheet.write_string(row, 0, office.name, head_format_1)
                                sheet.write_string(row, 1, kam.name, head_format_1)
                                sheet.write_string(row, 2, project.project_id, head_format_1)
                                for section in data:
                                    if section['type'] != 'blank':
                                        for period in section['periods']:
                                            if period.get('start', False):
                                                res = {
                                                    'contraction': self.env['project.budget.report.sales.forecast']._get_contraction_data(period['start'].date(), period['end'].date(), current_indicators),
                                                    'cash_flow': self.env['project.budget.report.sales.forecast']._get_cash_flow_data(period['start'].date(), period['end'].date(), current_indicators),
                                                    'gross_revenue': self.env['project.budget.report.sales.forecast']._get_gross_revenue_data(period['start'].date(), period['end'].date(), current_indicators),
                                                    'margin': self.env['project.budget.report.sales.forecast']._get_margin_data(period['start'].date(), period['end'].date(), current_indicators),
                                                }
                                                # print(period['start'].date(), period['end'].date(), project.project_id, contraction)
                                                for col in period['cols']:
                                                    sheet.write_number(row, column, res[section['indicator']].get(forecast_ids.get(col['type'], col['type']), 0))
                                                    column += 1
                                            else:
                                                column += len(period['cols'])
                                    else:
                                        column += 1
                                row += 1
                        if stage_is_present:  # суммируем по вероятностям
                            sheet.write_string(row, 0, kam.name + ' ' + stage.name, head_format_1)
                            column = self.START_COLUMN
                            for section in data:
                                if section['type'] != 'blank':
                                    for period in section['periods']:
                                        for col in period['cols']:
                                            formula = '=sum({0}{1}:{0}{2})'.format(xl_col_to_name(column), stage_start_row, row)
                                            sheet.write_formula(row, column, formula)
                                            column += 1
                                else:
                                    column += 1
                            row += 1
                            stage_rows.append(row)
                    if kam_is_present:  #суммируем по КАМам
                        sheet.write_string(row, 0, kam.name + ' Итого', head_format_1)
                        column = self.START_COLUMN
                        for section in data:
                            if section['type'] != 'blank':
                                for period in section['periods']:
                                    for col in period['cols']:
                                        formula = '=sum(' + ','.join(xl_col_to_name(column) + str(r) for r in stage_rows) + ')'
                                        sheet.write_formula(row, column, formula)
                                        column += 1
                            else:
                                column += 1
                        row += 1
                        kam_rows.append(row)
                # суммируем по ПО
                sheet.write_string(row, 0, office.name + ' Итого', head_format_1)
                column = self.START_COLUMN
                for section in data:
                    if section['type'] != 'blank':
                        for period in section['periods']:
                            for col in period['cols']:
                                formula = '=sum(' + ','.join(
                                    xl_col_to_name(column) + str(r) for r in kam_rows) + ')'
                                sheet.write_formula(row, column, formula)
                                column += 1
                    else:
                        column += 1
                row += 1
                office_rows.append(row)
            # суммируем по компании
            sheet.write_string(row, 0, company.name + ' Итого', head_format_1)
            column = self.START_COLUMN
            for section in data:
                if section['type'] != 'blank':
                    for period in section['periods']:
                        for col in period['cols']:
                            formula = '=sum(' + ','.join(
                                xl_col_to_name(column) + str(r) for r in office_rows) + ')'
                            sheet.write_formula(row, column, formula)
                            column += 1
                else:
                    column += 1
            row += 1
            company_rows.append(row)
        sheet.write_string(row, 0, 'Итого по отчету', head_format_1)
        column = self.START_COLUMN
        for section in data:
            if section['type'] != 'blank':
                for period in section['periods']:
                    for col in period['cols']:
                        formula = '=sum(' + ','.join(
                            xl_col_to_name(column) + str(r) for r in company_rows) + ')'
                        sheet.write_formula(row, column, formula)
                        column += 1
            else:
                column += 1
            row += 1

    def generate_xlsx_report(self, workbook, data, budgets):

        year = data['year']
        commercial_budget_id = data['commercial_budget_id']

        budget = self.env['project_budget.commercial_budget'].search([('id', '=', commercial_budget_id)])

        stages = self.env['project_budget.project.stage'].search([('code', '!=', '10')], order='sequence desc')  # для сортировки так делаем
        self.print_worksheet(workbook, budget, 'Прогноз', year)
