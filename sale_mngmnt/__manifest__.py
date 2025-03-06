{
    'name': 'Sales',
    'version': '1.0.4',
    'category': 'Sales/Sales',
    'summary': 'From projects to invoices',
    'depends': ['account', 'hr'],
    'data': [
        'security/sale_groups.xml',
        'security/sale_security.xml',
        'security/ir.model.access.csv',
        'data/sale_data.xml',
        'views/product_views.xml',
        'views/res_config_settings_views.xml',
        'views/sale_order_views.xml',
        'views/sale_order_line_views.xml',
        'views/sale_menus.xml'
    ],
    'application': True,
    'installable': True,
    'license': 'LGPL-3'
}
