{
    'name': "NCC Theme",
    'version': '16.0.1.0.0',
    'category': "Themes/Backend",
    'depends': ['base', 'web', 'mail'],
    "data": [
        'views/layout.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            'ncc_theme/static/src/scss/primary_variables_custom.scss',
            ],
        'web.assets_backend': [
            'ncc_theme/static/src/css/main.css',
            'ncc_theme/static/src/css/navbar.css',
            'ncc_theme/static/src/css/header.css',
            'ncc_theme/static/src/css/form.css',
            'ncc_theme/static/src/css/list.css',
            'ncc_theme/static/src/css/kanban.css',
            'ncc_theme/static/src/css/calendar.css',
            'ncc_theme/static/src/css/pivot.css',
            'ncc_theme/static/src/css/graph.css',
            'ncc_theme/static/src/css/mail.css',
            'ncc_theme/static/src/css/activity.css',
            'ncc_theme/static/src/css/card.css',
            'ncc_theme/static/src/css/dashboard.css',
            'ncc_theme/static/src/css/chatter.css',
            'ncc_theme/static/src/css/other.css',
            'ncc_theme/static/src/scss/new_layout.scss',
        ]
    }
}
