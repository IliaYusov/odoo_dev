{
    'name': 'Task Management',
    'version': '16.0.1.0.7',
    'category': '',
    'depends': ['base', 'mail', 'crnd_web_diagram_plus'],
    'external_dependencies': {'python': ['html2text']},
    'description': """
    """,
    'author': '',
    'support': '',
    'application': True,
    'installable': True,
    'auto_install': False,
    'images': ['static/description/icon.png'],
    'assets': {
        'web.assets_backend': [
            'task/static/src/scss/task_form.scss',
            'task/static/src/components/**/*'
        ]
    },
    'data': [
        'data/mail_template_data.xml',
        'data/task_data.xml',
        'security/task_security.xml',
        'security/ir.model.access.csv',
        'views/task_views.xml',
        'views/task_type_views.xml',
        'views/task_stage_views.xml',
        'views/task_stage_type_views.xml',
        'views/task_stage_route_views.xml',
        'views/task_menu.xml',
        'wizard/task_wizard_done.xml'
    ],
    'demo': [
    ],
    'license': 'LGPL-3'
}
