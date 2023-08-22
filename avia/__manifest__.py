{
    'name' : 'AVIA',
    'version' : '1.0',
    'category': 'AVIA',
    'depends': ['base','mail','uom','stock_account'],
    'description':"""
    """,
    'data': [
        'views/avia_base.xml',
        'views/avia_menu.xml',
        'security/ir.model.access.csv',
    ],
    'demo':[

    ],
    'installable':True,
    'auto_install': False,
    'license': 'LGPL-3',
}