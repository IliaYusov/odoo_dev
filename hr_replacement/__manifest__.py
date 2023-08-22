{
    'name': 'HR Replacement',
    'version': '16.0.1.0.0',
    'category': '',
    'depends': ['hr'],
    'description': 'HR replacements employees',
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
        'security/ir.model.access.csv',
        'views/employee_replacement_views.xml'
    ],
    'demo': [
    ],
    'license': 'LGPL-3'
}
