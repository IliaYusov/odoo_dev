{
    'name': 'HR Replacement',
    'version': '1.0.1',
    'category': 'Human Resources/Employees',
    'depends': ['hr'],
    'description': 'HR replacements employees',
    'author': '',
    'support': '',
    'installable': True,
    'auto_install': True,
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
