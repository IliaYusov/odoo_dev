{
    'name': 'Workplace Employee: Task',
    'version': '1.0.0',
    'category': '',
    'depends': ['workplace_employee', 'task'],
    'description': """
    """,
    'author': '',
    'support': '',
    'application': True,
    'installable': True,
    'auto_install': False,
    'assets': {
        'web.assets_backend': [
            'workplace_employee_task/static/src/components/**/*.js',
            'workplace_employee_task/static/src/components/**/*.xml',
            'workplace_employee_task/static/src/css/workplace_employee_task_dashboard.css'
        ]
    },
    'license': 'LGPL-3'
}
