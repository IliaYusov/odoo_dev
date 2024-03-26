{
    'name': 'Workplace: Task',
    'version': '1.0.0',
    'category': '',
    'depends': ['base', 'task', 'hr'],
    'description': """
    """,
    'author': '',
    'support': '',
    'application': True,
    'installable': True,
    'auto_install': False,
    'assets': {
        'web.assets_backend': [
            'workplace_task/static/src/components/**/*.js',
            'workplace_task/static/src/components/**/*.xml',
            'workplace_task/static/src/css/workplace_task_dashboard.css'
            # 'workplace_task/static/src/js/lib/Chart.bundle.js',
        ]
    },
    'data': [
        'views/workplace_menu.xml'
    ],
    'license': 'LGPL-3'
}
