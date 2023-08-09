{
    'name' : 'Change colors',
    'version' : '1.0',
    'depends': ['base'],
    'description':"""
        Change colors
    """,
    'assets': {
        'web.assets_backend': [
            'change_colors/static/src/scss/change_color.css',
        ]
    },

    'application':True,
    'installable':True,
    'auto_install': False,
    'license': 'LGPL-3',
}