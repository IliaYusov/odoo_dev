{
    'name' : 'SKLAD',
    'version' : '1.0',
    'category': 'SKLAD',
    'depends': ['base','mail','uom','stock_account'],
    'description':"""
    """,
    'data': [
        'views/Orders.xml',
        'views/sklad_menu.xml',
        'security/ir.model.access.csv',
    ],
    'demo':[

    ],
    'installable':True,
    'auto_install': False,
    'license': 'LGPL-3',
}