{
    'name': 'Customize ODOO',
    'version': '16.0.1.0.1',
    'depends': ['base', 'web'],
    'category': 'Productivity',
    'description': """
        Customize ODOO application
    """,
    'assets': {
        'web.assets_backend': [
            'base_custom_app/static/src/webclient/webclient.js',
            'base_custom_app/static/src/scss/change_color.scss',
            'base_custom_app/static/src/js/set_width.js',
            'base_custom_app/static/src/js/set_title.js',
            'base_custom_app/static/src/scss/form_view_extra.scss',
            'base_custom_app/static/src/scss/sticky_header.scss'
        ]
    },

    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3'
}
