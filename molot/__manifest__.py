{
    'name' : 'Molot',
    'version' : '1.0',
    'category': 'Manufacturing',
    'depends': ['base','mail','uom'],
    'description':"""
    Manufacturing tools management
    """,
    'author': 'lapus',
    'support': 'lapushkov@yandex.ru',
    'assets': {
        'web._assets_primary_variables': [
            'web/static/src/scss/primary_variables.scss'
        ]
    },
    'data': [
        'security/molot_users_groups.xml',
        'security/ir.model.access.csv',
        'views/molot_catalogs.xml',
        'views/molot_menu.xml',
    ],
    'demo':[

    ],
    'application':True,
    'images': ['static/description/banner.png'],
    'installable':True,
    'auto_install': False,
    'license': 'LGPL-3',
}