{
    'name': 'License Management',
    'version': '1.0.0',
    'category': 'Services',
    'summary': 'Manage software licenses.',
    'depends': ['base', 'product',],
    'data': [
        'data/ir_cron_data.xml',
        'data/ir_sequence_data.xml',
        'data/license_data.xml',
        'security/license_groups.xml',
        'security/license_security.xml',
        'security/ir.model.access.csv',
        'views/license_os_views.xml',
        'views/license_license_views.xml',
        'views/product_views.xml',
        'views/res_partner_views.xml',
        'views/res_config_settings_views.xml',
        'report/license_license_templates.xml',
        'report/license_reports.xml',
        'views/license_menus.xml'
    ],
    'installable': True,
    'application': True,
    'assets': {
        'web.assets_backend': [
            'license_mngmnt/static/src/views/**/*.js',
            'license_mngmnt/static/src/views/**/*.xml'
        ]
    },
    'license': 'LGPL-3'
}
