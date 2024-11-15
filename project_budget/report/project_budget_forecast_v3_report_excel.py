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
                        'level':  {'hidden': 1, 'level': 3},
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
                            'level': {'hidden': 1, 'level': 2},
                            'cols': [
                                {
                                    'type': 'plan',
                                    'plan_period': ('q1_plan',),
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
                            'level': {'hidden': 1, 'level': 2},
                            'cols': [
                                {
                                    'type': 'plan',
                                    'plan_period': ('q2_plan',),
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
                            'level': {'hidden': 1, 'level': 1},
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
                            'level': {'hidden': 1, 'level': 2},
                            'cols': [
                                {
                                    'type': 'plan',
                                    'plan_period': ('q3_plan',),
                                    'amount': 0,
                                    'name': 'План Q3',
                                },
                                {
                                    'type': 'plan66',
                                    'plan_period': ('q3_plan_6_6',),
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
                            'level': {'hidden': 1, 'level': 2},
                            'cols': [
                                {
                                    'type': 'plan',
                                    'plan_period': ('q4_plan',),
                                    'amount': 0,
                                    'name': 'План Q4',
                                },
                                {
                                    'type': 'plan66',
                                    'plan_period': ('q4_plan_6_6',),
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
                            'level': {'hidden': 1, 'level': 1},
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
                                    'plan_period': ('q1_fact', 'q2_fact', 'q3_plan_6_6', 'q4_plan_6_6'),
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
                    'level': {'hidden': 1, 'level': 2},
                    'cols': [
                        {
                            'type': 'plan',
                            'plan_period': ('q1_plan',),
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
                    'level': {'hidden': 1, 'level': 2},
                    'cols': [
                        {
                            'type': 'plan',
                            'plan_period': ('q2_plan',),
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
                    'level': {'hidden': 1, 'level': 1},
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
                    'level': {'hidden': 1, 'level': 2},
                    'cols': [
                        {
                            'type': 'plan',
                            'plan_period': ('q3_plan',),
                            'amount': 0,
                            'name': 'План Q3',
                        },
                        {
                            'type': 'plan66',
                            'plan_period': ('q3_plan_6_6',),
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
                    'level': {'hidden': 1, 'level': 2},
                    'cols': [
                        {
                            'type': 'plan',
                            'plan_period': ('q4_plan',),
                            'amount': 0,
                            'name': 'План Q4',
                        },
                        {
                            'type': 'plan66',
                            'plan_period': ('q4_plan_6_6',),
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
                    'level': {'hidden': 1, 'level': 1},
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
                            'plan_period': ('q1_fact', 'q2_fact', 'q3_plan_6_6', 'q4_plan_6_6'),
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
                            'plan_period': ('year_plan',),
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
        center_summary_default_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#8DB4E2',
            "num_format": '#,##0',
        })
        center_summary_estimate_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#CCC0DA',
            "num_format": '#,##0',
            'align': 'center',
        })
        center_summary_estimate_format_cross = workbook.add_format({
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
        center_summary_format = {
            'plan': column_format_plan_cross,
            'plan66': column_format_plan_cross,
            'fact': center_summary_default_format,
            'commitment': center_summary_default_format,
            'reserve': center_summary_default_format,
            'potential': center_summary_default_format,
        }
        center_estimate_format = {
            'plan': column_format_plan,
            'plan66': column_format_plan,
            'fact': center_summary_estimate_format,
            'commitment': center_summary_estimate_format,
            'reserve': center_summary_estimate_format,
            'potential': center_summary_estimate_format_cross,
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
                        col['center_summary_format'] = center_summary_format[col['type']]
                        col['center_estimate_format'] = center_estimate_format[col['type']]
                        col['company_summary_format'] = company_summary_format[col['type']]
                        col['company_estimate_format'] = company_estimate_format[col['type']]
                        col['total_summary_format'] = total_summary_format[col['type']]
                        col['total_estimate_format'] = total_estimate_format[col['type']]
        return data

    def get_child_centers_ids(self, center_ids, res: list):
        if center_ids:
            res.extend(center_ids)
            child_centers_ids = self.env['account.analytic.account'].search([
                ('parent_id', 'in', center_ids),
                ('plan_id', '=', self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
            ]).ids
            if child_centers_ids:
                res = self.get_child_centers_ids(child_centers_ids, res)
            return res
        else:
            return []

    def print_worksheet(self, workbook, budget, worksheet_name, responsibility_center_ids, systematica_forecast, oblako_row, diff_name, year):

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
            "num_format": '#,##0',
        })
        row_format_left_part_red = workbook.add_format({
            'border': 1,
            'font_size': 10,
            'font_color': 'red',
            "num_format": '#,##0',
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
        center_summary_default_format = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#8DB4E2',
            "num_format": '#,##0',
        })
        center_summary_estimate_format = workbook.add_format({
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
        row_format_number_itogo = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#A9D08E',
            "num_format": '#,##0',
        })
        row_format_itogo_estimated_plan_left = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#FFFF00',
            "num_format": '#,##0',
        })
        row_format_itogo_estimated_plan = workbook.add_format({
            'border': 1,
            'font_size': 10,
            "bold": True,
            "fg_color": '#FFFF00',
            "num_format": '#,##0',
            'align': 'center',
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

        year_columns = {}

        for section in data:  # печатаем шапку
            if section['type'] != 'blank':
                for period in section['periods']:
                    sheet.merge_range(row, column, row, column + len(period['cols']) - 1, period['name'], section['head_format'])
                    if period.get('level', False):
                        sheet.set_column(column, column + len(period['cols']) - 1, False, False, period['level'])
                    for i, col in enumerate(period['cols']):
                        if col.get('level', False):
                            sheet.set_column(column, column, False, False, col['level'])
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
        ], order='company_id, responsibility_center_id, key_account_manager_id, stage_id, project_id')

        center_plans = {
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

        use_6_6_plan = False
        for plan in center_plans[year]:
            if plan.q3_plan_6_6 != 0 or plan.q4_plan_6_6 != 0:
                use_6_6_plan = True
                continue

        row += 3

        center_parent_rows = {}

        active_responsibility_centers = self.env['account.analytic.account'].search([
            '|', ('id', 'in', financial_indicators.responsibility_center_id.ids),
            ('id', 'in', center_plans[year].budget_plan_supervisor_id.responsibility_center_id.ids),
        ])

        selected_responsibility_centers = active_responsibility_centers.filtered(lambda o: o.id in responsibility_center_ids)

        # добавляем активных потомков в список выбранных офисов
        child_responsibility_centers = self.env['account.analytic.account'].search([
            ('parent_id', 'in', selected_responsibility_centers.ids),
            ('id', 'in', active_responsibility_centers.ids),
            ('plan_id', '=', self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
        ])
        while child_responsibility_centers:
            new_child_responsibility_centers = self.env['account.analytic.account'].search([
                ('parent_id', 'in', child_responsibility_centers.ids),
                ('id', 'in', active_responsibility_centers.ids),
                ('plan_id', '=', self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
        ])
            selected_responsibility_centers += child_responsibility_centers
            child_responsibility_centers = new_child_responsibility_centers

        company_rows = list()
        for company in financial_indicators.company_id.filtered(lambda c: c.id in selected_responsibility_centers.company_id.ids):
            center_rows = list()

            current_centers = selected_responsibility_centers.filtered(lambda o: o.company_id == company)
            current_centers_wo_parents = current_centers.filtered(lambda o: not o.parent_id)
            all_centers = list()
            all_centers_sorted = list()

            for center in current_centers:  # добавляем все промежуточные родители в список офисов
                center_parent = center.parent_id
                while center_parent:
                    if center_parent not in all_centers:
                        all_centers.append(center_parent)
                    center_parent = center_parent.parent_id
                all_centers.append(center)

            def get_center_ids(o_wo_parents, all_o, all_o_sorted):  # сортируем офисы так, чтобы потомки шли перед родителями
                for o in o_wo_parents:
                    child_centers = o.child_ids
                    if child_centers:
                        all_o_sorted = get_center_ids(child_centers, all_o, all_o_sorted)
                    if o not in all_o_sorted and o in all_o:
                        all_o_sorted.append(o)
                return all_o_sorted

            all_centers_sorted = get_center_ids(current_centers_wo_parents, all_centers, all_centers_sorted)

            for center in all_centers_sorted:
                kam_rows = list()
                for kam in financial_indicators.key_account_manager_id.filtered(lambda k: k.company_id == company):
                    stage_rows = list()
                    kam_is_present = False
                    for stage in financial_indicators.stage_id.filtered(lambda s: s.project_status != 'lead').sorted(lambda s: s.sequence, reverse=True):
                        stage_start_row = row + 1
                        stage_is_present = False

                        filtered_indicators = financial_indicators.filtered(
                            lambda fi: fi.project_id.company_id == company and
                                       fi.project_id.responsibility_center_id == center and
                                       fi.project_id.key_account_manager_id == kam and
                                       fi.project_id.stage_id == stage
                        )

                        projects = filtered_indicators.project_id
                        steps = filtered_indicators.step_id

                        project_list = list()

                        for prj in projects:
                            if prj.project_have_steps:
                                for stp in prj.step_project_child_ids:
                                    if stp in steps:
                                        project_list.append((prj, stp))
                            else:
                                project_list.append((prj, False))

                        for project, step in project_list:
                            current_indicators = financial_indicators.filtered(lambda ci: ci.project_id == project and (not ci.step_id or ci.step_id == step))
                            if current_indicators:
                                stage_is_present = True
                                kam_is_present = True
                                format = row_format_left_part
                                level = {'hidden': 1, 'level': 3}
                                if project.stage_id.project_state == 'cancel':
                                    format = row_format_left_part_red
                                    level = {'hidden': 1, 'level': 4}
                                column = self.START_COLUMN
                                sheet.set_row(row, False, False, level)
                                sheet.write_string(row, 0, center.name, format)
                                sheet.write_string(row, 1, kam.name, format)
                                sheet.write_string(row, 2, project.partner_id.name, format)
                                sheet.write_string(row, 3, project.essence_project, format)
                                sheet.write_string(row, 4, project.project_id + ('|' + step.project_id if step else ''), format)
                                sheet.write_string(row, 5, (step.step_project_number or '') if step else (project.step_project_number or ''),
                                                   format)
                                sheet.write_number(row, 6, project.total_amount_of_revenue_with_vat ,format)
                                if project.stage_id.project_state == 'won':
                                    sheet.write_datetime(row, 7, project.end_presale_project_month, format)
                                else:
                                    sheet.write(row, 7, None, format)
                                sheet.write_number(row, 8, project.profitability, format)

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
                            sheet.set_row(row, False, False, {'hidden': 1, 'level': 3})
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
                        sheet.set_row(row, False, False, {'hidden': 1, 'level': 2})
                        sheet.set_row(row + 1, False, False, {'hidden': 1, 'level': 2})
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
                                                plan = sum(kam_plans[section['year']].filtered(lambda p: p.budget_plan_kam_id.key_account_manager_id.id == kam.id and p.type_row == section['plan_type'])[plan_period] for plan_period in col['plan_period'])
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
                sheet.set_row(row, False, False, {'hidden': 1, 'level': 1})
                sheet.merge_range(row, 0, row, self.START_COLUMN - 1, 'ИТОГО: ' + center.name, center_summary_default_format)
                sheet.merge_range(row + 1, 0, row + 1, self.START_COLUMN - 1, 'ИТОГО: Расчетный План по ' + center.name,
                                  center_summary_estimate_format)
                column = self.START_COLUMN
                for section in data:
                    if section['type'] != 'blank':
                        for period in section['periods']:
                            for col in period['cols']:
                                if col['type'] in ('plan', 'plan66'):
                                    if col.get('plan_period', False):
                                        plan = sum(center_plans[section['year']].filtered(lambda p: p.budget_plan_supervisor_id.responsibility_center_id.id == center.id and p.type_row == section['plan_type'])[plan_period] for plan_period in col['plan_period'])
                                        formula = '=sum(' + str(plan) + ',' + ','.join(xl_col_to_name(column) + str(r + 1) for r in center_parent_rows.get(center.id, [])) + ')'
                                        sheet.write_number(row, column, 0, col['center_summary_format'])
                                        sheet.write_formula(row + 1, column, formula, col['center_estimate_format'])
                                    elif col.get('total_columns', False):  # суммируем кварталы, полугодия и года
                                        formula = '=sum(' + ','.join(
                                            xl_col_to_name(c) + str(row + 2) for c in
                                            col['total_columns']) + ')'
                                        sheet.write_number(row, column, 0, col['center_summary_format'])
                                        sheet.write_formula(row + 1, column, formula, col['center_estimate_format'])
                                else:
                                    summary_rows = kam_rows + center_parent_rows.get(center.id, [])
                                    if summary_rows:
                                        formula = '=sum(' + ','.join(xl_col_to_name(column) + str(r) for r in summary_rows) + ')'
                                        sheet.write_formula(row, column, formula, col['center_summary_format'])
                                    else:
                                        sheet.write_number(row, column, 0, col['center_summary_format'])
                                    if col['type'] == 'fact':
                                        formula = f'={xl_col_to_name(column)}{row + 1}'
                                        sheet.write_formula(row + 1, column, formula, col['center_estimate_format'])
                                    elif col['type'] == 'commitment':
                                        formula = '={1}{0}*$D$1+{2}{0}*$D$2'.format(
                                            row + 1,
                                            xl_col_to_name(column),
                                            xl_col_to_name(column + 1),
                                        )
                                        sheet.merge_range(row + 1, column, row + 1, column + 1, formula,
                                                          col['center_estimate_format'])
                                    elif col['type'] == 'potential':
                                        sheet.write_number(row + 1, column, 0, col['center_estimate_format'])
                                column += 1
                    else:
                        column += 1
                row += 2
                if center.parent_id:
                    center_parent_rows.setdefault(center.parent_id.id, [])
                    center_parent_rows[center.parent_id.id].append(row - 1)
                else:
                    center_rows.append(row - 1)

            # суммируем по компании
            sheet.set_row(row, False, False, {'hidden': 1, 'level': 1})
            sheet.set_row(row + 2, False, False, {'hidden': 1, 'level': 1})
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
                                    xl_col_to_name(column) + str(r + 1) for r in center_rows) + ')'
                                sheet.write_number(row, column, 0, col['company_summary_format'])
                                sheet.write_formula(row + 1, column, formula, col['company_estimate_format'])
                            else:
                                formula = '=sum(' + ','.join(
                                    xl_col_to_name(column) + str(r) for r in center_rows) + ')'
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

        total_row = row + 1
        if systematica_forecast:
            sheet.activate()
            total_row += 2

        # суммируем по отчету
        sheet.set_row(row, False, False, {'hidden': 1, 'level': 1})
        sheet.merge_range(row, 0, row, self.START_COLUMN - 1, 'ИТОГО по отчету', company_summary_default_format)
        sheet.merge_range(row + 1, 0, row + 1, self.START_COLUMN - 1, 'ИТОГО: Расчетный План по отчету',
                          company_summary_estimate_format)
        if systematica_forecast:
            sheet.set_row(row + 2, False, False, {'hidden': 1, 'level': 1})
            sheet.merge_range(row + 2, 0, row + 2, self.START_COLUMN - 1, 'ИТОГО: СА+Облако.ру по отчету',
                              row_format_number_itogo)
            sheet.merge_range(row + 3, 0, row + 3, self.START_COLUMN - 1, 'ИТОГО: СА+Облако.ру Расчетный План по отчету',
                              row_format_itogo_estimated_plan_left)
        if diff_name:  # разница
            sheet.set_row(total_row + 1, 32)
            sheet.merge_range(
                total_row + 1, 1, total_row + 1, 3,
                f'Разница Итого; План ' + (
                    '6+6' if use_6_6_plan else f'{year}') + f' ({diff_name})/ Расчетный план до конца периода (на дату отчета)',
                row_format_diff
            )
        column = self.START_COLUMN
        for section in data:
            if section['type'] != 'blank':
                for period in section['periods']:
                    for col in period['cols']:
                        if col['type'] in ('plan', 'plan66'):
                            sheet.write_number(row, column, 0, col['total_summary_format'])
                            if company_rows:
                                formula = '=sum(' + ','.join(
                                    xl_col_to_name(column) + str(r + 1) for r in company_rows) + ')'
                                sheet.write_formula(row + 1, column, formula, col['total_estimate_format'])
                            else:
                                sheet.write_number(row + 1, column, 0, col['total_estimate_format'])
                            if systematica_forecast:
                                formula = '=sum({2}{0},{3}{2}{1})'.format(
                                    row + 2, oblako_row + 1, xl_col_to_name(column), "'Прогноз (Облако.ру)'!"
                                )
                                sheet.write_number(row + 2, column, 0, col['total_summary_format'])
                                sheet.write_formula(row + 3, column, formula, col['total_estimate_format'])
                        else:
                            if company_rows:
                                formula = '=sum(' + ','.join(
                                    xl_col_to_name(column) + str(r) for r in company_rows) + ')'
                                sheet.write_formula(row, column, formula, col['total_summary_format'])
                            else:
                                sheet.write_number(row, column, 0, col['total_summary_format'])
                            if systematica_forecast:
                                formula = '=sum({2}{0},{3}{2}{1})'.format(
                                    row + 1, oblako_row, xl_col_to_name(column), "'Прогноз (Облако.ру)'!"
                                )
                                sheet.write_formula(row + 2, column, formula, col['total_summary_format'])
                            if col['type'] == 'fact':
                                formula = f'={xl_col_to_name(column)}{row + 1}'
                                sheet.write_formula(row + 1, column, formula, col['total_estimate_format'])
                                if systematica_forecast:
                                    formula = '=sum({2}{0},{3}{2}{1})'.format(
                                        row + 2, oblako_row + 1, xl_col_to_name(column), "'Прогноз (Облако.ру)'!"
                                    )
                                    sheet.write_formula(row + 3, column, formula, col['total_estimate_format'])
                            elif col['type'] == 'commitment':
                                formula = '={1}{0}*$D$1+{2}{0}*$D$2'.format(
                                    row + 1,
                                    xl_col_to_name(column),
                                    xl_col_to_name(column + 1),
                                )
                                sheet.merge_range(row + 1, column, row + 1, column + 1, formula,
                                                  col['total_estimate_format'])
                                if systematica_forecast:
                                    formula = '=sum({2}{0},{3}{2}{1})'.format(
                                        row + 2, oblako_row + 1, xl_col_to_name(column), "'Прогноз (Облако.ру)'!"
                                    )
                                    sheet.merge_range(row + 3, column, row + 3, column + 1, formula,
                                                      col['total_estimate_format'])
                            elif col['type'] == 'potential':
                                sheet.write_number(row + 1, column, 0, col['total_estimate_format'])
                                if systematica_forecast:
                                    sheet.write_number(row + 3, column, 0, col['total_estimate_format'])

                            if diff_name and col['type'] == 'fact' and not period.get('start', False):  # считаем разницы
                                if period['type'] in ('HY2', 'Q3', 'Q4', 'Y'):
                                    if use_6_6_plan:
                                        formula_diff = '=({1}{0}+{2}{0})-{3}{0}'.format(
                                            total_row + 1,
                                            xl_col_to_name(column),
                                            xl_col_to_name(column + 1),
                                            xl_col_to_name(column - 1),
                                        )
                                    else:
                                        formula_diff = '=({1}{0}+{2}{0})-{3}{0}'.format(
                                            total_row + 1,
                                            xl_col_to_name(column),
                                            xl_col_to_name(column + 1),
                                            xl_col_to_name(column - 2),
                                        )
                                else:
                                    formula_diff = '=({1}{0}+{2}{0})-{3}{0}'.format(
                                        total_row + 1,
                                        xl_col_to_name(column),
                                        xl_col_to_name(column + 1),
                                        xl_col_to_name(column - 1),
                                    )
                                sheet.merge_range(total_row + 1, column, total_row + 1, column + 2, formula_diff,
                                                  row_format_diff)

                            if period['type'] == 'Y':  # добавляем номера столбцов общих сумм в каждой секции для нижней таблички
                                year_columns[str(section['year']) + '_' + section['indicator'] + '_' + col['type']] = column

                        column += 1
            else:
                column += 1

        if systematica_forecast:
            row += 2
        if diff_name:
            row += 1

        # печатаем нижнюю сводную таблицу
        row += 3
        sheet.merge_range(row, 1, row, 2, 'Контрактование, с НДС', summary_format_border_top_center)
        sheet.write_string(row, 3, '', summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(year)}:', summary_format_border_top)
        formula = '={1}{0}+{2}{0}+{3}{0}'.format(
            total_row,
            xl_col_to_name(year_columns[f'{year}_contraction_fact']),
            xl_col_to_name(year_columns[f'{year}_contraction_commitment']),
            xl_col_to_name(year_columns[f'{year}_contraction_reserve']),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(year)}:', summary_format_border_bottom)
        formula = '={1}{0}+{2}{0}'.format(
            total_row + 1,
            xl_col_to_name(year_columns[f'{year}_contraction_fact']),
            xl_col_to_name(year_columns[f'{year}_contraction_commitment']),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(year + 1)}:', summary_format_border_top)
        formula = '={1}{0}+{2}{0}'.format(
            total_row,
            xl_col_to_name(year_columns[f'{year + 1}_contraction_commitment']),
            xl_col_to_name(year_columns[f'{year + 1}_contraction_reserve']),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(year + 1)}:',
                          summary_format_border_bottom)
        formula = '={1}{0}'.format(
            total_row + 1,
            xl_col_to_name(year_columns[f'{year + 1}_contraction_commitment']),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(year + 2)}:', summary_format_border_top)
        formula = '={1}{0}+{2}{0}'.format(
            total_row,
            xl_col_to_name(year_columns[f'{year + 2}_contraction_commitment']),
            xl_col_to_name(year_columns[f'{year + 2}_contraction_reserve']),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(year + 2)}:',
                          summary_format_border_bottom)
        formula = '={1}{0}'.format(
            total_row + 1,
            xl_col_to_name(year_columns[f'{year + 2}_contraction_commitment']),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Итого по Компании {str(year)}-{str(year + 2)}:',
                          summary_format_border_top)
        formula = '={3}{0}+{3}{1}+{3}{2}'.format(row - 1, row - 3, row - 5, xl_col_to_name(3))
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Итого Расчетный План по Компании {str(year)}-{str(year + 2)}:',
                          summary_format_border_bottom)
        formula = '={3}{0}+{3}{1}+{3}{2}'.format(row - 1, row - 3, row - 5, xl_col_to_name(3))
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)

        row += 2
        sheet.merge_range(row, 1, row, 2, 'Валовая выручка, без НДС', summary_format_border_top_center)
        sheet.write_string(row, 3, '', summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(year)}:', summary_format_border_top)
        formula = '={1}{0}+{2}{0}+{3}{0}'.format(
            total_row,
            xl_col_to_name(year_columns[f'{year}_gross_revenue_fact']),
            xl_col_to_name(year_columns[f'{year}_gross_revenue_commitment']),
            xl_col_to_name(year_columns[f'{year}_gross_revenue_reserve']),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(year)}:', summary_format_border_bottom)
        formula = '={1}{0}+{2}{0}'.format(
            total_row + 1,
            xl_col_to_name(year_columns[f'{year}_gross_revenue_fact']),
            xl_col_to_name(year_columns[f'{year}_gross_revenue_commitment']),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(year + 1)}:', summary_format_border_top)
        formula = '={1}{0}+{2}{0}'.format(
            total_row,
            xl_col_to_name(year_columns[f'{year + 1}_gross_revenue_commitment']),
            xl_col_to_name(year_columns[f'{year + 1}_gross_revenue_reserve']),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(year + 1)}:',
                          summary_format_border_bottom)
        formula = '={1}{0}'.format(
            total_row + 1,
            xl_col_to_name(year_columns[f'{year + 1}_gross_revenue_commitment']),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(year + 2)}:', summary_format_border_top)
        formula = '={1}{0}+{2}{0}'.format(
            total_row,
            xl_col_to_name(year_columns[f'{year + 2}_gross_revenue_commitment']),
            xl_col_to_name(year_columns[f'{year + 2}_gross_revenue_reserve']),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(year + 2)}:',
                          summary_format_border_bottom)
        formula = '={1}{0}'.format(
            total_row + 1,
            xl_col_to_name(year_columns[f'{year + 2}_gross_revenue_commitment']),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Итого по Компании {str(year)}-{str(year + 2)}:',
                          summary_format_border_top)
        formula = '={3}{0}+{3}{1}+{3}{2}'.format(row - 1, row - 3, row - 5, xl_col_to_name(3))
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Итого Расчетный План по Компании {str(year)}-{str(year + 2)}:',
                          summary_format_border_bottom)
        formula = '={3}{0}+{3}{1}+{3}{2}'.format(row - 1, row - 3, row - 5, xl_col_to_name(3))
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)

        row += 2
        sheet.merge_range(row, 1, row, 2, 'ПДС, с НДС', summary_format_border_top_center)
        sheet.write_string(row, 3, '', summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(year)}:', summary_format_border_top)
        formula = '={1}{0}+{2}{0}+{3}{0}'.format(
            total_row,
            xl_col_to_name(year_columns[f'{year}_cash_flow_fact']),
            xl_col_to_name(year_columns[f'{year}_cash_flow_commitment']),
            xl_col_to_name(year_columns[f'{year}_cash_flow_reserve']),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(year)}:', summary_format_border_bottom)
        formula = '={1}{0}+{2}{0}'.format(
            total_row + 1,
            xl_col_to_name(year_columns[f'{year}_cash_flow_fact']),
            xl_col_to_name(year_columns[f'{year}_cash_flow_commitment']),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(year + 1)}:', summary_format_border_top)
        formula = '={1}{0}+{2}{0}'.format(
            total_row,
            xl_col_to_name(year_columns[f'{year + 1}_cash_flow_commitment']),
            xl_col_to_name(year_columns[f'{year + 1}_cash_flow_reserve']),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(year + 1)}:',
                          summary_format_border_bottom)
        formula = '={1}{0}'.format(
            total_row + 1,
            xl_col_to_name(year_columns[f'{year + 1}_cash_flow_commitment']),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(year + 2)}:', summary_format_border_top)
        formula = '={1}{0}+{2}{0}'.format(
            total_row,
            xl_col_to_name(year_columns[f'{year + 2}_cash_flow_commitment']),
            xl_col_to_name(year_columns[f'{year + 2}_cash_flow_reserve']),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(year + 2)}:',
                          summary_format_border_bottom)
        formula = '={1}{0}'.format(
            total_row + 1,
            xl_col_to_name(year_columns[f'{year + 2}_cash_flow_commitment']),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Итого по Компании {str(year)}-{str(year + 2)}:',
                          summary_format_border_top)
        formula = '={3}{0}+{3}{1}+{3}{2}'.format(row - 1, row - 3, row - 5, xl_col_to_name(3))
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Итого Расчетный План по Компании {str(year)}-{str(year + 2)}:',
                          summary_format_border_bottom)
        formula = '={3}{0}+{3}{1}+{3}{2}'.format(row - 1, row - 3, row - 5, xl_col_to_name(3))
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)

        row += 2
        sheet.merge_range(row, 1, row, 2, 'Валовая прибыль (М1), без НДС', summary_format_border_top_center)
        sheet.write_string(row, 3, '', summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(year)}:', summary_format_border_top)
        formula = '={1}{0}+{2}{0}+{3}{0}'.format(
            total_row,
            xl_col_to_name(year_columns[f'{year}_margin_fact']),
            xl_col_to_name(year_columns[f'{year}_margin_commitment']),
            xl_col_to_name(year_columns[f'{year}_margin_reserve']),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(year)}:', summary_format_border_bottom)
        formula = '={1}{0}+{2}{0}'.format(
            total_row + 1,
            xl_col_to_name(year_columns[f'{year}_margin_fact']),
            xl_col_to_name(year_columns[f'{year}_margin_commitment']),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(year + 1)}:', summary_format_border_top)
        formula = '={1}{0}+{2}{0}'.format(
            total_row,
            xl_col_to_name(year_columns[f'{year + 1}_margin_commitment']),
            xl_col_to_name(year_columns[f'{year + 1}_margin_reserve']),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(year + 1)}:',
                          summary_format_border_bottom)
        formula = '={1}{0}'.format(
            total_row + 1,
            xl_col_to_name(year_columns[f'{year + 1}_margin_commitment']),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'По Компании {str(year + 2)}:', summary_format_border_top)
        formula = '={1}{0}+{2}{0}'.format(
            total_row,
            xl_col_to_name(year_columns[f'{year + 2}_margin_commitment']),
            xl_col_to_name(year_columns[f'{year + 2}_margin_reserve']),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Расчетный План по Компании {str(year + 2)}:',
                          summary_format_border_bottom)
        formula = '={1}{0}'.format(
            total_row + 1,
            xl_col_to_name(year_columns[f'{year + 2}_margin_commitment']),
        )
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Итого по Компании {str(year)}-{str(year + 2)}:',
                          summary_format_border_top)
        formula = '={3}{0}+{3}{1}+{3}{2}'.format(row - 1, row - 3, row - 5, xl_col_to_name(3))
        sheet.write_formula(row, 3, formula, summary_format_border_top)

        row += 1
        sheet.merge_range(row, 1, row, 2, f'Итого Расчетный План по Компании {str(year)}-{str(year + 2)}:',
                          summary_format_border_bottom)
        formula = '={3}{0}+{3}{1}+{3}{2}'.format(row - 1, row - 3, row - 5, xl_col_to_name(3))
        sheet.write_formula(row, 3, formula, summary_format_border_bottom)
        return total_row

    def generate_xlsx_report(self, workbook, data, budgets):

        year = data['year']
        commercial_budget_id = data['commercial_budget_id']
        responsibility_center_ids = data['responsibility_center_ids']
        systematica_forecast = data['systematica_forecast']

        budget = self.env['project_budget.commercial_budget'].search([('id', '=', commercial_budget_id)])

        if systematica_forecast:
            litr_codes = ('ПО_ЛИТР',)

            oblako_codes = ('05', 'ПО_Облако.ру (облачный сервис)', 'ПО_Облако.ру (облачный сервис новые)',
                            'ПО_Облако.ру (облачный сервис база)', 'ПО_Облако.ру (интеграторский сервис)')

            oblako_ids = self.get_child_centers_ids(self.env['account.analytic.account'].search([
                ('code', 'in', oblako_codes),
                ('plan_id', '=',
                 self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
            ]).ids, [])
            litr_ids = self.get_child_centers_ids(self.env['account.analytic.account'].search([
                ('code', 'in', litr_codes),
                ('plan_id', '=',
                 self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
            ]).ids, [])
            systmatica_ids = self.env['account.analytic.account'].search([
                ('id', 'in', responsibility_center_ids),
                ('id', 'not in', oblako_ids),
                ('id', 'not in', litr_ids),
                ('plan_id', '=',
                 self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
            ]).ids  # систематика без литр и облака

            self.print_worksheet(workbook, budget, 'Прогноз (ЛИТР)', litr_ids, False, 0, 'ЛИТР', year)
            oblako_row = self.print_worksheet(workbook, budget, 'Прогноз (Облако.ру)', oblako_ids, False, 0, False, year)
            self.print_worksheet(workbook, budget, 'Прогноз', systmatica_ids, True, oblako_row, 'СА+Облако.ру', year)
        else:
            self.print_worksheet(workbook, budget, 'Прогноз', responsibility_center_ids, systematica_forecast, 0, False, year)
