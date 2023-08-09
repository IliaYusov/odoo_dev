{
    'name': 'Helpdesk',
    'version': '16.0.1.0.1',
    'category': '',
    'depends': ['base', 'mail', 'crnd_web_diagram_plus', 'task'],
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
        ]
    },
    'data': [
        'data/helpdesk_data.xml',
        'security/helpdesk_security.xml',
        'security/ir.model.access.csv',
        'views/team_views.xml',
        'views/ticket_views.xml',
        'views/ticket_stage_views.xml',
        'views/ticket_stage_type_views.xml',
        'views/ticket_stage_route_views.xml',
        'views/ticket_type_views.xml',
        'views/helpdesk_menu.xml'
    ],
    'demo': [
    ],
    'license': 'LGPL-3'
}
