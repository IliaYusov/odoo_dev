{
    'name': 'Margins in Sales Orders',
    'version': '1.0.0',
    'category': 'Sales/Sales',
    'description': """
This module adds the 'Margin' on sales order.
=============================================

This gives the profitability by calculating the difference between the Unit Price and Cost Price.
    """,
    'depends': ['sale_mngmnt'],
    'data': [
        'views/sale_order_views.xml',
    ],
    'license': 'LGPL-3'
}
