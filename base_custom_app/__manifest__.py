{
    'name': 'Customize ODOO',
    'version': '2.0.0',
    'depends': ['base', 'web'],
    'category': 'Productivity',
    'description': """
        Customize ODOO application
    """,
    'assets': {
        'web._assets_primary_variables': [
            'base_custom_app/static/src/scss/primary_variables_custom.scss',
        ],
        'web.assets_backend': [
            'base_custom_app/static/src/webclient/webclient.js',
            'base_custom_app/static/src/js/set_width.js',
            'base_custom_app/static/src/js/set_title.js',
            'base_custom_app/static/src/js/user_menu.js',
            'base_custom_app/static/src/scss/new_layout.scss',
            'base_custom_app/static/src/css/main.css',
            'base_custom_app/static/src/css/navbar.css',
            'base_custom_app/static/src/css/header.css',
            'base_custom_app/static/src/css/form.css',
            'base_custom_app/static/src/css/list.css',
            'base_custom_app/static/src/css/kanban.css',
            'base_custom_app/static/src/css/calendar.css',
            'base_custom_app/static/src/css/pivot.css',
            'base_custom_app/static/src/css/graph.css',
            'base_custom_app/static/src/css/mail.css',
            'base_custom_app/static/src/css/activity.css',
            'base_custom_app/static/src/css/card.css',
            'base_custom_app/static/src/css/dashboard.css',
            'base_custom_app/static/src/css/chatter.css',
            'base_custom_app/static/src/css/other.css',
        ]
    },
    'data': [
        'views/webclient_templates.xml'
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3'
}
