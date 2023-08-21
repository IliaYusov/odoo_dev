{
    'name' : 'Ierarchy',
    'version' : '1.0',
    'category': 'Ierarchy',
    'depends': ['base','mail','uom','stock_account'],
    'description':"""
    """,
    'data': [
        'views/ierarchy_base.xml',
        'views/ierarchy_menu.xml',
        'security/ir.model.access.csv',
    ],
    'demo':[

    ],
    'installable':True,
    'auto_install': False,
    'license': 'LGPL-3',
}