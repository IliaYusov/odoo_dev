{
    'name' : 'Change ODOO colors TEST',
    'version' : '1.0',
    'depends': ['base'],
    'description':"""
        Change ODOO colors TEST TEST TEST
    """,
    'assets': {
        'web.assets_backend': [
            'change_odoo_colors_test/static/src/scss/change_color.scss',
        ]
    },

    'application':True,
    'installable':True,
    'auto_install': False,
    'license': 'LGPL-3',
}