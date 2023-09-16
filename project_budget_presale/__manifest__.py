{
    'name': 'Project Budget: Presale',
    'version': '16.0.1.0.0',
    'category': '',
    'depends': ['base', 'project_budget', 'document_flow'],
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
        'data/presale_data.xml',
        'security/ir.model.access.csv',
        'views/presale_views.xml',
        'views/projects_views.xml'
    ],
    'demo': [
    ],
    'license': 'LGPL-3'
}
