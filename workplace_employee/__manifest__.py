{
    'name': 'Workplace Employee',
    'version': '1.0.0',
    'category': '',
    'depends': ['base', 'hr'],
    'description': """
    """,
    'author': '',
    'support': '',
    'application': True,
    'installable': True,
    'auto_install': False,
    'assets': {
        'web.assets_backend': [
            'workplace_employee/static/src/components/**/*.js',
            'workplace_employee/static/src/components/**/*.xml',
            'workplace_employee/static/src/css/workplace_employee_dashboard.css'
        ]
    },
    'data': [
        'views/res_users_views.xml',
        'views/workplace_employee_menu.xml'
    ],
    'license': 'LGPL-3'
}
