{
    'name': 'Analytic: Responsibility Center',
    'version': '1.0.0',
    'depends': ['hr', 'analytic'],
    'description': """
    This module allows to specify responsibility center
    """,
    'installable': True,
    'auto_install': True,
    'data': [
        'data/analytic_responsibility_center_data.xml',
        'views/account_analytic_account_views.xml',
        'views/hr_department_views.xml'
    ],
    'license': 'LGPL-3'
}
