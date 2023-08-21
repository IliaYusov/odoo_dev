{
    'name': 'Customize ODOO',
    'version': '16.0.1.0.0',
    'depends': ['base', 'web'],
    'category': 'Productivity',
    'description': """
        Customize ODOO application
    """,
    'assets': {
        'web.assets_backend': [
            'base_custom_app/static/src/webclient/webclient.js'
        ]
    },

    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3'
}
