{
    'name': 'Purchase Request',
    'version': '16.0.1.0.0',
    'category': 'Inventory/Purchase',
    'depends': ['base', 'project_budget', 'document_flow', 'purchase', 'sale'],
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
        # 'data/presale_data.xml',
        'security/ir.model.access.csv',
        'views/purchase_request_component_characteristic_views.xml',
        'views/purchase_request_views.xml',
        'views/purchase_request_line_views.xml',
        'views/purchase_request_line_component_views.xml',
        'views/purchase_request_line_characteristic_views.xml',
        'views/purchase_request_line_delivery_views.xml',
        'views/purchase_request_line_estimation_views.xml',
        'views/purchase_request_type_views.xml',
        'views/projects_views.xml',
        'views/purchase_request_menu.xml',
        'views/sale_order_views.xml'
    ],
    'demo': [
    ],
    'license': 'LGPL-3'
}
