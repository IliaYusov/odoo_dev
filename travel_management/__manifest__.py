{
    'name' : 'Travel_management',
    'version' : '1.0',
    'category': 'Extra tools',
    'depends': ['base','mail','uom','stock_account'],
    'description':"""
    """,
    'data': [
        'views/travel.xml',
        'views/travel_menu.xml',
        'views/travel_lines.xml',
        'views/template_test.xml',
        'security/ir.model.access.csv',
        'security/security.xml'
    ],
    'demo':[

    ],
    'installable':True,
    'auto_install': False,
    'license': 'LGPL-3',
}