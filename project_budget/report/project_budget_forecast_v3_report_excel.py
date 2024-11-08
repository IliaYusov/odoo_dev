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

    def get_sections_dict(self, year):
        data = [
            {
                'indicator': 'contraction',
                'plan_type': 'contracting',
                'periods': [],
                'type': 'monthly',
                'year': year,
                'name': 'Контрактование, с НДС',
            },
            {
                'indicator': 'cash_flow',
                'plan_type': 'cash',
                'periods': [],
                'type': 'monthly',
                'year': year,
                'name': 'Поступление денежных средств, с НДС',
            },
            {
                'indicator': 'gross_revenue',
                'plan_type': 'acceptance',
                'periods': [],
                'type': 'quarterly',
                'year': year,
                'name': 'Валовая Выручка, без НДС',
            },
            {
                'indicator': 'margin',
                'plan_type': 'margin_income',
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
                'plan_type': 'contracting',
                'periods': [],
                'type': 'yearly',
                'year': year + 1,
                'name': 'Контрактование, с НДС',
            },
            {
                'indicator': 'cash_flow',
                'plan_type': 'cash',
                'periods': [],
                'type': 'yearly',
                'year': year + 1,
                'name': 'Поступление денежных средств, с НДС',
            },
            {
                'indicator': 'gross_revenue',
                'plan_type': 'acceptance',
                'periods': [],
                'type': 'yearly',
                'year': year + 1,
                'name': 'Валовая Выручка, без НДС',
            },
            {
                'indicator': 'margin',
                'plan_type': 'margin_income',
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
                'plan_type': 'contracting',
                'periods': [],
                'type': 'yearly',
                'year': year + 2,
                'name': 'Контрактование, с НДС',
            },
            {
                'indicator': 'cash_flow',
                'plan_type': 'cash',
                'periods': [],
                'type': 'yearly',
                'year': year + 2,
                'name': 'Поступление денежных средств, с НДС',
            },
            {
                'indicator': 'gross_revenue',
                'plan_type': 'acceptance',
                'periods': [],
                'type': 'yearly',
                'year': year + 2,
                'name': 'Валовая Выручка, без НДС',
            },
            {
                'indicator': 'margin',
                'plan_type': 'margin_income',
                'periods': [],
                'type': 'yearly',
                'year': year + 2,
                'name': 'Валовая прибыль (Маржа 1), без НДС',
            },
        ]
        return data

    def add_periods_to_sections(self, data):
        for section in data:
            if section['type'] == 'monthly':
                for month in range(1, 13):
                    section['periods'].append({
                        'name': self.month_rus_name[month - 1],
                        'type': 'M' + str(month),
                        'start': datetime.datetime(day=1, month=month, year=section['year']),
                        'end': datetime.datetime(day=calendar.monthrange(section['year'], month)[1], month=month, year=section['year']),
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
                    })
                    if month == 3:
                        section['periods'].append({
                            'name': 'Q1 итого',
                            'type': 'Q1',
                            'cols': [
                                {
                                    'type': 'plan',
                                    'plan_period': 'q1_plan',
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
                        })
                    elif month == 6:
                        section['periods'].append({
                            'name': 'Q2 итого',
                            'type': 'Q2',
                            'cols': [
                                {
                                    'type': 'plan',
                                    'plan_period': 'q2_plan',
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
                        })
                        section['periods'].append({
                            'name': f'HY1 {section["year"]} итого',
                            'type': 'HY1',
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
                        })
                    elif month == 9:
                        section['periods'].append({
                            'name': 'Q3 итого',
                            'type': 'Q3',
                            'cols': [
                                {
                                    'type': 'plan',
                                    'plan_period': 'q3_plan',
                                    'amount': 0,
                                    'name': 'План Q3',
                                },
                                {
                                    'type': 'plan66',
                                    'plan_period': 'q3_plan_6_6',
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
                        })
                    elif month == 12:
                        section['periods'].append({
                            'name': 'Q4 итого',
                            'type': 'Q4',
                            'cols': [
                                {
                                    'type': 'plan',
                                    'plan_period': 'q4_plan',
                                    'amount': 0,
                                    'name': 'План Q4',
                                },
                                {
                                    'type': 'plan66',
                                    'plan_period': 'q4_plan_6_6',
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
                        })
                        section['periods'].append({
                            'name': f'HY2 {section["year"]} итого',
                            'type': 'HY2',
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
                        })
                        section['periods'].append({
                            'name': f'{section["year"]} итого',
                            'type': 'Y',
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
                        })
            elif section['type'] == 'quarterly':
                section['periods'].append({
                    'name': 'Q1',
                    'type': 'Q1',
                    'start': datetime.datetime(day=1, month=1, year=section['year']),
                    'end': datetime.datetime(day=31, month=3, year=section['year']),
                    'cols': [
                        {
                            'type': 'plan',
                            'plan_period': 'q1_plan',
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
                })
                section['periods'].append({
                    'name': 'Q2',
                    'type': 'Q2',
                    'start': datetime.datetime(day=1, month=4, year=section['year']),
                    'end': datetime.datetime(day=30, month=6, year=section['year']),
                    'cols': [
                        {
                            'type': 'plan',
                            'plan_period': 'q2_plan',
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
                })
                section['periods'].append({
                    'name': f'HY1 {section["year"]} итого',
                    'type': 'HY1',
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
                })
                section['periods'].append({
                    'name': 'Q3',
                    'type': 'Q3',
                    'start': datetime.datetime(day=1, month=7, year=section['year']),
                    'end': datetime.datetime(day=30, month=9, year=section['year']),
                    'cols': [
                        {
                            'type': 'plan',
                            'plan_period': 'q3_plan',
                            'amount': 0,
                            'name': 'План Q3',
                        },
                        {
                            'type': 'plan66',
                            'plan_period': 'q3_plan_6_6',
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
                })
                section['periods'].append({
                    'name': 'Q4',
                    'type': 'Q4',
                    'start': datetime.datetime(day=1, month=10, year=section['year']),
                    'end': datetime.datetime(day=31, month=12, year=section['year']),
                    'cols': [
                        {
                            'type': 'plan',
                            'plan_period': 'q4_plan',
                            'amount': 0,
                            'name': 'План Q4',
                        },
                        {
                            'type': 'plan66',
                            'plan_period': 'q4_plan_6_6',
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
                })
                section['periods'].append({
                    'name': f'HY2 {section["year"]} итого',
                    'type': 'HY2',
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
                })
                section['periods'].append({
                    'name': f'{section["year"]} итого',
                    'type': 'Y',
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
                })
            elif section['type'] == 'yearly':
                section['periods'].append({
                    'name': f'{section["year"]} итого',
                    'type': 'Y',
                    'start': datetime.datetime(day=1, month=1, year=section['year']),
                    'end': datetime.datetime(day=31, month=12, year=section['year']),
                    'cols': [
                        {
                            'type': 'plan',
                            'plan_period': 'year_plan',
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
                })
        return data

    def add_start_columns_to_sections(self, data):
        start_column = self.START_COLUMN
        for section in data:
            section['start_column'] = start_column
            if section['type'] == 'blank':
                start_column += 1
            else:
                start_column += sum(len(period['cols']) for period in section['periods'])
        return data

    def add_total_columns_to_cols(self, data):  # добавляем номера колонок для суммирования по Q HY Y
        for section in data:
            code_columns = {}  # собираем словарь с номерами колонок
            column = section['start_column']
            if section['type'] == 'blank':
                column += 1
            else:
                for period in section['periods']:
                    code_columns[period['type']] = {}
                    for col in period['cols']:
                        code_columns[period['type']][col['type']] = column
                        column += 1

            if section['type'] == 'monthly':  # добавляем кортежи с номерами колонок
                for period in section['periods']:
                    if period['type'] == 'Q1':
                        for col in period['cols']:
                            if col['type'] in ('fact', 'commitment', 'reserve', 'potential'):
                                col['total_columns'] = (
                                    code_columns['M1'][col['type']],
                                    code_columns['M2'][col['type']],
                                    code_columns['M3'][col['type']],
                                )
                    elif period['type'] == 'Q2':
                        for col in period['cols']:
                            if col['type'] in ('fact', 'commitment', 'reserve', 'potential'):
                                col['total_columns'] = (
                                    code_columns['M4'][col['type']],
                                    code_columns['M5'][col['type']],
                                    code_columns['M6'][col['type']],
                                )
                    elif period['type'] == 'Q3':
                        for col in period['cols']:
                            if col['type'] in ('fact', 'commitment', 'reserve', 'potential'):
                                col['total_columns'] = (
                                    code_columns['M7'][col['type']],
                                    code_columns['M8'][col['type']],
                                    code_columns['M9'][col['type']],
                                )
                    elif period['type'] == 'Q4':
                        for col in period['cols']:
                            if col['type'] in ('fact', 'commitment', 'reserve', 'potential'):
                                col['total_columns'] = (
                                    code_columns['M10'][col['type']],
                                    code_columns['M11'][col['type']],
                                    code_columns['M12'][col['type']],
                                )
                    elif period['type'] == 'HY1':
                        for col in period['cols']:
                            if col['type'] in ('plan', 'fact', 'commitment', 'reserve', 'potential'):
                                col['total_columns'] = (
                                    code_columns['Q1'][col['type']],
                                    code_columns['Q2'][col['type']],
                                )
                    elif period['type'] == 'HY2':
                        for col in period['cols']:
                            if col['type'] in ('plan', 'plan66', 'fact', 'commitment', 'reserve', 'potential'):
                                col['total_columns'] = (
                                    code_columns['Q3'][col['type']],
                                    code_columns['Q4'][col['type']],
                                )
                    elif period['type'] == 'Y':
                        for col in period['cols']:
                            if col['type'] in ('plan', 'fact', 'commitment', 'reserve', 'potential'):
                                col['total_columns'] = (
                                    code_columns['HY1'][col['type']],
                                    code_columns['HY2'][col['type']],
                                )
                            elif col['type'] == 'plan66':
                                col['total_columns'] = (
                                    code_columns['HY2'][col['type']],
                                )
            elif section['type'] == 'quarterly':
                for period in section['periods']:
                    if period['type'] == 'HY1':
                        for col in period['cols']:
                            if col['type'] in ('plan', 'fact', 'commitment', 'reserve', 'potential'):
                                col['total_columns'] = (
                                    code_columns['Q1'][col['type']],
                                    code_columns['Q2'][col['type']],
                                )
                    elif period['type'] == 'HY2':
                        for col in period['cols']:
                            if col['type'] in ('plan', 'plan66', 'fact', 'commitment', 'reserve', 'potential'):
                                col['total_columns'] = (
                                    code_columns['Q3'][col['type']],
                                    code_columns['Q4'][col['type']],
                                )
                    elif period['type'] == 'Y':
                        for col in period['cols']:
                            if col['type'] in ('plan', 'fact', 'commitment', 'reserve', 'potential'):
                                col['total_columns'] = (
                                    code_columns['HY1'][col['type']],
                                    code_columns['HY2'][col['type']],
                                )
                            elif col['type'] == 'plan66':
                                col['total_columns'] = (
                                    code_columns['HY2'][col['type']],
                                )
        return data

    def add_head_format_to_sections(self, data, workbook):
        head_format_contraction = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "bold" : True,
            "fg_color" : '#FFD966',
            "font_size" : 12,
        })
        head_format_cash_flow = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "bold" : True,
            "fg_color" : '#D096BF',
            "font_size" : 12,
        })
        head_format_gross_revenue = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "bold" : True,
            "fg_color" : '#B4C6E7',
            "font_size" : 12,
        })
        head_format_margin = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "bold" : True,
            "fg_color" : '#F4FD9F',
            "font_size" : 12,
        })

        head_format = {
            'contraction': head_format_contraction,
            'cash_flow': head_format_cash_flow,
            'gross_revenue': head_format_gross_revenue,
            'margin': head_format_margin,
        }
        for section in data:
            if section['type'] != 'blank':
                section['head_format'] = head_format[section['indicator']]
        return data

    def add_format_to_cols(self, data, workbook):
        head_format_plan = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "bold": True,
            "fg_color": '#DCE6F1',
            "font_size": 12,
        })
        head_format_fact = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "bold": True,
            "fg_color": '#C6E0B4',
            "font_size": 8,
        })
        head_format_forecast = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "bold": False,
            "fg_color": '#E2EFDA',
            "font_size": 8,
        })

        column_format_plan = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#DCE6F1',
            "num_format": '#,##0',
        })
        column_format_plan_cross = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#DCE6F1',
            "num_format": '#,##0',
            'diag_type': 3,
        })
        column_format_fact = workbook.add_format({
            "fg_color": '#C6E0B4',
            'border': 1,
            'font_size': 10,
            "num_format": '#,##0',
        })
        column_format_fact_cross = workbook.add_format({
            "fg_color": '#C6E0B4',
            'border': 1,
            'font_size': 10,
            "num_format": '#,##0',
            'diag_type': 3,
        })
        column_format_forecast = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "num_format": '#,##0',
        })
        column_format_forecast_red = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "num_format": '#,##0',
            'font_color': 'red',
        })
        stage_summary_default_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#F2DCDB',
            "num_format": '#,##0',
        })
        kam_summary_default_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#D9D9D9',
            "num_format": '#,##0',
        })
        kam_summary_estimate_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#FDE9D9',
            "num_format": '#,##0',
            'align': 'center',
        })
        kam_summary_estimate_format_cross = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#FDE9D9',
            "num_format": '#,##0',
            'diag_type': 3,
        })
        office_summary_default_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#8DB4E2',
            "num_format": '#,##0',
        })
        office_summary_estimate_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#CCC0DA',
            "num_format": '#,##0',
            'align': 'center',
        })
        office_summary_estimate_format_cross = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#CCC0DA',
            "num_format": '#,##0',
            'diag_type': 3,
        })
        company_summary_default_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#A9D08E',
            "num_format": '#,##0',
        })
        company_summary_estimate_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#FFFF00',
            "num_format": '#,##0',
            'align': 'center',
        })
        company_summary_estimate_format_cross = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#FFFF00',
            "num_format": '#,##0',
            'diag_type': 3,
        })

        head_format = {
            'plan': head_format_plan,
            'plan66': head_format_plan,
            'fact': head_format_fact,
            'commitment': head_format_forecast,
            'reserve': head_format_forecast,
            'potential': head_format_forecast,
        }
        column_format = {
            'plan': column_format_plan_cross,
            'plan66': column_format_plan_cross,
            'fact': column_format_fact_cross,
            'commitment': column_format_forecast,
            'reserve': column_format_forecast,
            'potential': column_format_forecast,
        }
        column_format_cancel = {
            'plan': column_format_plan_cross,
            'plan66': column_format_plan_cross,
            'fact': column_format_fact_cross,
            'commitment': column_format_forecast_red,
            'reserve': column_format_forecast_red,
            'potential': column_format_forecast_red,
        }
        column_format_won = {
            'plan': column_format_plan_cross,
            'plan66': column_format_plan_cross,
            'fact': column_format_fact,
            'commitment': column_format_forecast,
            'reserve': column_format_forecast,
            'potential': column_format_forecast,
        }
        stage_summary_format = {
            'plan': column_format_plan_cross,
            'plan66': column_format_plan_cross,
            'fact': stage_summary_default_format,
            'commitment': stage_summary_default_format,
            'reserve': stage_summary_default_format,
            'potential': stage_summary_default_format,
        }
        kam_summary_format = {
            'plan': column_format_plan_cross,
            'plan66': column_format_plan_cross,
            'fact': kam_summary_default_format,
            'commitment': kam_summary_default_format,
            'reserve': kam_summary_default_format,
            'potential': kam_summary_default_format,
        }
        kam_estimate_format = {
            'plan': column_format_plan,
            'plan66': column_format_plan,
            'fact': kam_summary_estimate_format,
            'commitment': kam_summary_estimate_format,
            'reserve': kam_summary_estimate_format,
            'potential': kam_summary_estimate_format_cross,
        }
        office_summary_format = {
            'plan': column_format_plan_cross,
            'plan66': column_format_plan_cross,
            'fact': office_summary_default_format,
            'commitment': office_summary_default_format,
            'reserve': office_summary_default_format,
            'potential': office_summary_default_format,
        }
        office_estimate_format = {
            'plan': column_format_plan,
            'plan66': column_format_plan,
            'fact': office_summary_estimate_format,
            'commitment': office_summary_estimate_format,
            'reserve': office_summary_estimate_format,
            'potential': office_summary_estimate_format_cross,
        }
        company_summary_format = {
            'plan': column_format_plan_cross,
            'plan66': column_format_plan_cross,
            'fact': company_summary_default_format,
            'commitment': company_summary_default_format,
            'reserve': company_summary_default_format,
            'potential': company_summary_default_format,
        }
        company_estimate_format = {
            'plan': column_format_plan,
            'plan66': column_format_plan,
            'fact': company_summary_estimate_format,
            'commitment': company_summary_estimate_format,
            'reserve': company_summary_estimate_format,
            'potential': company_summary_estimate_format_cross,
        }
        total_summary_format = {
            'plan': column_format_plan_cross,
            'plan66': column_format_plan_cross,
            'fact': company_summary_default_format,
            'commitment': company_summary_default_format,
            'reserve': company_summary_default_format,
            'potential': company_summary_default_format,
        }
        total_estimate_format = {
            'plan': column_format_plan,
            'plan66': column_format_plan,
            'fact': company_summary_estimate_format,
            'commitment': company_summary_estimate_format,
            'reserve': company_summary_estimate_format,
            'potential': company_summary_estimate_format_cross,
        }
        for section in data:
            if section['type'] != 'blank':
                for period in section['periods']:
                    for col in period['cols']:
                        col['head_format'] = head_format[col['type']]
                        col['column_format'] = column_format[col['type']]
                        col['column_format_cancel'] = column_format_cancel[col['type']]
                        col['column_format_won'] = column_format_won[col['type']]
                        col['stage_summary_format'] = stage_summary_format[col['type']]
                        col['kam_summary_format'] = kam_summary_format[col['type']]
                        col['kam_estimate_format'] = kam_estimate_format[col['type']]
                        col['office_summary_format'] = office_summary_format[col['type']]
                        col['office_estimate_format'] = office_estimate_format[col['type']]
                        col['company_summary_format'] = company_summary_format[col['type']]
                        col['company_estimate_format'] = company_estimate_format[col['type']]
                        col['total_summary_format'] = total_summary_format[col['type']]
                        col['total_estimate_format'] = total_estimate_format[col['type']]
        return data

    def print_worksheet(self, workbook, budget, worksheet_name, year):

        report_name = budget.name
        sheet = workbook.add_worksheet(worksheet_name)
        sheet.set_zoom(85)
        sheet.hide_zero()

        bold = workbook.add_format({'bold': True})
        head_format_left_part = workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'align': 'center',
            'valign': 'vcenter',
            "bold": False,
            "fg_color": '#C6E0B4',
            "font_size": 8,
        })
        summary_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_size': 12,
            'text_wrap': True,
            'valign': 'vcenter',
            "num_format": '#,##0',
        })
        summary_format_percent = workbook.add_format({
            'bold': True,
            'border': 1,
            'font_size': 12,
            'text_wrap': True,
            'valign': 'vcenter',
            "num_format": '0%',
        })
        row_format_left_part = workbook.add_format({
            'border': 1,
            'font_size': 10,
        })
        row_format_left_part_red = workbook.add_format({
            'border': 1,
            'font_size': 10,
            'font_color': 'red',
        })
        stage_summary_default_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#F2DCDB',
            "num_format": '#,##0',
        })
        kam_summary_default_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#D9D9D9',
            "num_format": '#,##0',
        })
        kam_summary_estimate_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#FDE9D9',
            "num_format": '#,##0',
        })
        office_summary_default_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#8DB4E2',
            "num_format": '#,##0',
        })
        office_summary_estimate_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#CCC0DA',
            "num_format": '#,##0',
        })
        company_summary_default_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#A9D08E',
            "num_format": '#,##0',
        })
        company_summary_estimate_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#FFFF00',
            "num_format": '#,##0',
        })

        row = 0
        sheet.write_string(row, 0, budget.name, bold)
        row = 2
        column = 0
        sheet.write_string(row + 1, column, "Проектный офис", head_format_left_part)
        sheet.write_string(row + 2, column, "", head_format_left_part)
        sheet.set_column(column, column, 21.5)
        column += 1
        sheet.merge_range(row - 2, column, row - 1, column, "Расчетный План:", summary_format)
        sheet.write_string(row + 1, column, "КАМ", head_format_left_part)
        sheet.write_string(row + 2, column, "", head_format_left_part)
        sheet.set_column(column, column, 19.75)
        column += 1
        sheet.write_string(row - 2, column, "Обязательство", summary_format)
        sheet.write_string(row - 1, column, "Резерв", summary_format)
        sheet.write_string(row + 1, column, "Заказчик", head_format_left_part)
        sheet.write_string(row + 2, column, "", head_format_left_part)
        sheet.set_column(column, column, 25)
        column += 1
        sheet.write_number(row - 2, column, 1, summary_format_percent)
        sheet.write_number(row - 1, column, 0.6, summary_format_percent)
        sheet.write_string(row + 1, column, "Наименование Проекта", head_format_left_part)
        sheet.write_string(row + 2, column, "", head_format_left_part)
        sheet.set_column(column, column, 12.25)
        column += 1
        sheet.write_string(row + 1, column, "Номер этапа проекта CRM", head_format_left_part)
        sheet.write_string(row + 2, column, "", head_format_left_part)
        column += 1
        sheet.write_string(row + 1, column, "Номер этапа проекта AX", head_format_left_part)
        sheet.write_string(row + 2, column, "", head_format_left_part)
        column += 1
        sheet.write_string(row + 1, column, "Сумма проекта/этапа, руб.", head_format_left_part)
        sheet.write_string(row + 2, column, "", head_format_left_part)
        column += 1
        sheet.write_string(row + 1, column, "Дата контрактования", head_format_left_part)
        sheet.write_string(row + 2, column, "", head_format_left_part)
        column += 1
        sheet.write_string(row + 1, column, "Прибыльность, экспертно, %", head_format_left_part)
        sheet.write_string(row + 2, column, "", head_format_left_part)
        sheet.set_column(4, 9, False, False, {'hidden': 1, 'level': 1})
        column += 1
        sheet.write_string(row + 1, column, "", head_format_left_part)
        sheet.write_string(row + 2, column, "", head_format_left_part)
        sheet.set_column(column, column, 2)
        column += 1

        sheet.freeze_panes(5, self.START_COLUMN)

        forecast_ids = {
            'commitment': self.env.ref('project_budget_nkk.project_budget_forecast_probability_commitment').id,
            'reserve': self.env.ref('project_budget_nkk.project_budget_forecast_probability_reserve').id,
            'potential': self.env.ref('project_budget_nkk.project_budget_forecast_probability_potential').id,
        }

        data = self.get_sections_dict(year)
        data = self.add_periods_to_sections(data)
        data = self.add_start_columns_to_sections(data)
        data = self.add_total_columns_to_cols(data)
        data = self.add_head_format_to_sections(data, workbook)
        data = self.add_format_to_cols(data, workbook)

        start_col = self.START_COLUMN

        for section in data:  # печатаем шапку
            if section['type'] != 'blank':
                for period in section['periods']:
                    sheet.merge_range(row, column, row, column + len(period['cols']) - 1, period['name'], section['head_format'])
                    for i, col in enumerate(period['cols']):

                        if col['type'] in ('plan', 'plan66', 'fact'):
                            sheet.merge_range(row + 2, column, row + 1, column, col['name'], col['head_format'])
                        else:
                            sheet.write_string(row + 2, column, col['name'], col['head_format'])

                        if col['type'] == 'commitment':
                            sheet.merge_range(row + 1, column, row + 1, column + (len(period['cols']) - i - 1), 'Прогноз до конца периода (на дату отчета)', col['head_format'])

                        column += 1
                sheet.merge_range(row - 1, start_col, row - 1, column - 1, section['name'], section['head_format'])
            else:
                column += 1
            start_col = column

        financial_indicators = self.env['project.budget.financial.indicator'].search([
            ('commercial_budget_id', '=', budget.id),
            ('date', '>=', datetime.datetime(day=1, month=1, year=year)),
            ('date', '<=', datetime.datetime(day=31, month=12, year=year + 2))
        ], order='company_id, project_office_id, key_account_manager_id, stage_id, project_id')

        office_plans = {
            year: self.env['project_budget.budget_plan_supervisor_spec'].search([
                ('budget_plan_supervisor_id.is_company_plan', '=', False),
                ('budget_plan_supervisor_id.year', '=', year)]),
            year + 1: self.env['project_budget.budget_plan_supervisor_spec'].search([
                ('budget_plan_supervisor_id.is_company_plan', '=', False),
                ('budget_plan_supervisor_id.year', '=', year + 1)]),
            year + 2: self.env['project_budget.budget_plan_supervisor_spec'].search([
                ('budget_plan_supervisor_id.is_company_plan', '=', False),
                ('budget_plan_supervisor_id.year', '=', year + 2)]),
        }

        kam_plans = {
            year: self.env['project_budget.budget_plan_kam_spec'].search([
                ('budget_plan_kam_id.year', '=', year)]),
            year + 1: self.env['project_budget.budget_plan_kam_spec'].search([
                ('budget_plan_kam_id.year', '=', year + 1)]),
            year + 2: self.env['project_budget.budget_plan_kam_spec'].search([
                ('budget_plan_kam_id.year', '=', year + 2)]),
        }

        row += 3

        office_parent_rows = {}

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
                    for stage in financial_indicators.stage_id.sorted(lambda s: s.sequence, reverse=True):
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
                                format = row_format_left_part
                                if project.stage_id.project_state == 'cancel':
                                    format = row_format_left_part_red
                                column = self.START_COLUMN
                                sheet.write_string(row, 0, office.name, format)
                                sheet.write_string(row, 1, kam.name, format)
                                sheet.write_string(row, 2, project.project_id, format)
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
                                                    format = col['column_format']
                                                    if project.stage_id.project_state == 'won':
                                                        format = col['column_format_won']
                                                    elif project.stage_id.project_state == 'cancel':
                                                        format = col['column_format_cancel']
                                                    sheet.write_number(row, column, res[section['indicator']].get(forecast_ids.get(col['type'], col['type']), 0), format)
                                                    column += 1
                                            else:
                                                for col in period['cols']:
                                                    format = col['column_format']
                                                    if project.stage_id.project_state == 'won':
                                                        format = col['column_format_won']
                                                    elif project.stage_id.project_state == 'cancel':
                                                        format = col['column_format_cancel']
                                                    if col.get('total_columns', False):  # суммируем кварталы, полугодия и года
                                                        formula = '=sum(' + ','.join(xl_col_to_name(c) + str(row + 1) for c in col['total_columns']) + ')'
                                                        sheet.write_formula(row, column, formula, format)
                                                    else:
                                                        sheet.write_number(row, column, 0, format)
                                                    column += 1
                                    else:
                                        column += 1
                                row += 1
                        if stage_is_present:  # суммируем по вероятностям
                            sheet.merge_range(row, 0, row, self.START_COLUMN - 1, kam.name + ' ' + stage.name, stage_summary_default_format)
                            column = self.START_COLUMN
                            for section in data:
                                if section['type'] != 'blank':
                                    for period in section['periods']:
                                        for col in period['cols']:
                                            formula = '=sum({0}{1}:{0}{2})'.format(xl_col_to_name(column), stage_start_row, row)
                                            sheet.write_formula(row, column, formula, col['stage_summary_format'])
                                            column += 1
                                else:
                                    column += 1
                            row += 1
                            stage_rows.append(row)
                    if kam_is_present:  #суммируем по КАМам
                        sheet.merge_range(row, 0, row, self.START_COLUMN - 1, 'ИТОГО: ' + kam.name, kam_summary_default_format)
                        sheet.merge_range(row + 1, 0, row + 1, self.START_COLUMN - 1, 'ИТОГО: Расчетный План по ' + kam.name,
                                          kam_summary_estimate_format)
                        column = self.START_COLUMN
                        for section in data:
                            if section['type'] != 'blank':
                                for period in section['periods']:
                                    for col in period['cols']:
                                        if col['type'] in ('plan', 'plan66'):
                                            if col.get('plan_period', False):
                                                plan = kam_plans[section['year']].filtered(lambda p: p.budget_plan_kam_id.key_account_manager_id.id == kam.id and p.type_row == section['plan_type'])[col['plan_period']]
                                                sheet.write_number(row, column, 0, col['kam_summary_format'])
                                                sheet.write_number(row + 1, column, plan, col['kam_estimate_format'])
                                            elif col.get('total_columns', False):  # суммируем кварталы, полугодия и года
                                                formula = '=sum(' + ','.join(
                                                    xl_col_to_name(c) + str(row + 2) for c in
                                                    col['total_columns']) + ')'
                                                sheet.write_number(row, column, 0, col['kam_summary_format'])
                                                sheet.write_formula(row + 1, column, formula, col['kam_estimate_format'])
                                        else:
                                            formula = '=sum(' + ','.join(xl_col_to_name(column) + str(r) for r in stage_rows) + ')'
                                            sheet.write_formula(row, column, formula, col['kam_summary_format'])
                                            if col['type'] == 'fact':
                                                formula = f'={xl_col_to_name(column)}{row + 1}'
                                                sheet.write_formula(row + 1, column, formula, col['kam_estimate_format'])
                                            elif col['type'] == 'commitment':
                                                formula = '={1}{0}*$D$1+{2}{0}*$D$2'.format(
                                                    row + 1,
                                                    xl_col_to_name(column),
                                                    xl_col_to_name(column + 1),
                                                )
                                                sheet.merge_range(row + 1, column, row + 1, column + 1, formula, col['kam_estimate_format'])
                                            elif col['type'] == 'potential':
                                                sheet.write_number(row + 1, column, 0, col['kam_estimate_format'])
                                        column += 1
                            else:
                                column += 1
                        row += 2
                        kam_rows.append(row - 1)

                # суммируем по ПО
                sheet.merge_range(row, 0, row, self.START_COLUMN - 1, 'ИТОГО: ' + office.name, office_summary_default_format)
                sheet.merge_range(row + 1, 0, row + 1, self.START_COLUMN - 1, 'ИТОГО: Расчетный План по ' + office.name,
                                  office_summary_estimate_format)
                column = self.START_COLUMN
                for section in data:
                    if section['type'] != 'blank':
                        for period in section['periods']:
                            for col in period['cols']:
                                if col['type'] in ('plan', 'plan66'):
                                    if col.get('plan_period', False):
                                        plan = office_plans[section['year']].filtered(lambda p: p.budget_plan_supervisor_id.project_office_id.id == office.id and p.type_row == section['plan_type'])[col['plan_period']]
                                        formula = '=sum(' + str(plan) + ',' + ','.join(xl_col_to_name(column) + str(r + 1) for r in office_parent_rows.get(office.id, [])) + ')'
                                        sheet.write_number(row, column, 0, col['office_summary_format'])
                                        sheet.write_formula(row + 1, column, formula, col['office_estimate_format'])
                                    elif col.get('total_columns', False):  # суммируем кварталы, полугодия и года
                                        formula = '=sum(' + ','.join(
                                            xl_col_to_name(c) + str(row + 2) for c in
                                            col['total_columns']) + ')'
                                        sheet.write_number(row, column, 0, col['office_summary_format'])
                                        sheet.write_formula(row + 1, column, formula, col['office_estimate_format'])
                                else:
                                    formula = '=sum(' + ','.join(xl_col_to_name(column) + str(r) for r in kam_rows + office_parent_rows.get(office.id, [])) + ')'
                                    sheet.write_formula(row, column, formula, col['office_summary_format'])
                                    if col['type'] == 'fact':
                                        formula = f'={xl_col_to_name(column)}{row + 1}'
                                        sheet.write_formula(row + 1, column, formula, col['office_estimate_format'])
                                    elif col['type'] == 'commitment':
                                        formula = '={1}{0}*$D$1+{2}{0}*$D$2'.format(
                                            row + 1,
                                            xl_col_to_name(column),
                                            xl_col_to_name(column + 1),
                                        )
                                        sheet.merge_range(row + 1, column, row + 1, column + 1, formula,
                                                          col['office_estimate_format'])
                                    elif col['type'] == 'potential':
                                        sheet.write_number(row + 1, column, 0, col['office_estimate_format'])
                                column += 1
                    else:
                        column += 1
                row += 2
                if office.parent_id:
                    office_parent_rows.setdefault(office.parent_id.id, [])
                    office_parent_rows[office.parent_id.id].append(row - 1)
                else:
                    office_rows.append(row - 1)

            # суммируем по компании
            sheet.merge_range(row, 0, row, self.START_COLUMN - 1, 'ИТОГО: ' + company.name, company_summary_default_format)
            sheet.merge_range(row + 1, 0, row + 1, self.START_COLUMN - 1, 'ИТОГО: Расчетный План по ' + company.name,
                              company_summary_estimate_format)
            column = self.START_COLUMN
            for section in data:
                if section['type'] != 'blank':
                    for period in section['periods']:
                        for col in period['cols']:
                            if col['type'] in ('plan', 'plan66'):
                                formula = '=sum(' + ','.join(
                                    xl_col_to_name(column) + str(r + 1) for r in office_rows) + ')'
                                sheet.write_number(row, column, 0, col['company_summary_format'])
                                sheet.write_formula(row + 1, column, formula, col['company_estimate_format'])
                            else:
                                formula = '=sum(' + ','.join(
                                    xl_col_to_name(column) + str(r) for r in office_rows) + ')'
                                sheet.write_formula(row, column, formula, col['company_summary_format'])
                                if col['type'] == 'fact':
                                    formula = f'={xl_col_to_name(column)}{row + 1}'
                                    sheet.write_formula(row + 1, column, formula, col['company_estimate_format'])
                                elif col['type'] == 'commitment':
                                    formula = '={1}{0}*$D$1+{2}{0}*$D$2'.format(
                                        row + 1,
                                        xl_col_to_name(column),
                                        xl_col_to_name(column + 1),
                                    )
                                    sheet.merge_range(row + 1, column, row + 1, column + 1, formula,
                                                      col['company_estimate_format'])
                                elif col['type'] == 'potential':
                                    sheet.write_number(row + 1, column, 0, col['company_estimate_format'])
                            column += 1
                else:
                    column += 1
            row += 2
            company_rows.append(row - 1)

        sheet.merge_range(row, 0, row, self.START_COLUMN - 1, 'ИТОГО по отчету', company_summary_default_format)
        sheet.merge_range(row + 1, 0, row + 1, self.START_COLUMN - 1, 'ИТОГО: Расчетный План по отчету',
                          company_summary_estimate_format)
        column = self.START_COLUMN
        for section in data:
            if section['type'] != 'blank':
                for period in section['periods']:
                    for col in period['cols']:
                        if col['type'] in ('plan', 'plan66'):
                            formula = '=sum(' + ','.join(
                                xl_col_to_name(column) + str(r + 1) for r in company_rows) + ')'
                            sheet.write_number(row, column, 0, col['total_summary_format'])
                            sheet.write_formula(row + 1, column, formula, col['total_estimate_format'])
                        else:
                            formula = '=sum(' + ','.join(
                                xl_col_to_name(column) + str(r) for r in company_rows) + ')'
                            sheet.write_formula(row, column, formula, col['total_summary_format'])
                            if col['type'] == 'fact':
                                formula = f'={xl_col_to_name(column)}{row + 1}'
                                sheet.write_formula(row + 1, column, formula, col['total_estimate_format'])
                            elif col['type'] == 'commitment':
                                formula = '={1}{0}*$D$1+{2}{0}*$D$2'.format(
                                    row + 1,
                                    xl_col_to_name(column),
                                    xl_col_to_name(column + 1),
                                )
                                sheet.merge_range(row + 1, column, row + 1, column + 1, formula,
                                                  col['total_estimate_format'])
                            elif col['type'] == 'potential':
                                sheet.write_number(row + 1, column, 0, col['total_estimate_format'])
                        column += 1
            else:
                column += 1
        row += 2

    def generate_xlsx_report(self, workbook, data, budgets):

        year = data['year']
        commercial_budget_id = data['commercial_budget_id']

        budget = self.env['project_budget.commercial_budget'].search([('id', '=', commercial_budget_id)])

        stages = self.env['project_budget.project.stage'].search([('code', '!=', '10')], order='sequence desc')  # для сортировки так делаем
        self.print_worksheet(workbook, budget, 'Прогноз', year)
