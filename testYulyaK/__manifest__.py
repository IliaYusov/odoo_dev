{
    'name':'test YulyaK',
    'author':'yulyaK',
    'version': '1.0',
    'summary': 'Custom module for handling invoices and warehouse orders',
    'description': 'Custom module for managing invoices and warehouse orders in Odoo',
    'category': 'Custom',
    'depends': ['base','product','account','purchase','sale','hr','stock','stock_account'],
    'data':[
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/order.xml',
        'views/invoice.xml',

    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}