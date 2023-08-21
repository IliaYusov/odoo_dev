{
    'name': "Document Flow Dashboard",
    'version': '16.0.0.0',
    'description': """Helpdesk Support Ticket Management Dashboard""",
    'summary': """Graphical Dashboard for Document Flow module""",
    'author': "",
    'company': '',
    'maintainer': '',
    'category': 'Website',
    'depends': ['document_flow', 'base'],
    'data': [
        'views/dashboard_view.xml',
        'views/dashboard_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'document_flow_dashboard/static/src/css/dashboard.css',
            'document_flow_dashboard/static/src/js/lib/Chart.bundle.js',
            'document_flow_dashboard/static/src/xml/dashboard_view.xml',
            'document_flow_dashboard/static/src/js/dashboard_view.js'
        ],
    },
    'images': ['static/description/icon.png'],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
