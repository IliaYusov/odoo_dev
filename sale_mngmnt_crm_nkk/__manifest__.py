{
    'name': 'Sales: CRM NKK',
    'version': '1.0.2',
    'category': 'Sales/Sales',
    'description': """
    """,
    'depends': ['sale_mngmnt_crm', 'sale_mngmnt_margin'],
    'assets': {
        'web.assets_backend': [
            'sale_mngmnt_crm_nkk/static/src/scss/project_budget.scss',
        ],
    },
    'data': [
        'security/sale_crm_groups.xml',
        'security/sale_crm_security.xml',
        'data/sale_crm_data.xml',
        'views/project_budget_project_views.xml',
        'views/product_category_views.xml',
        'views/res_config_settings_views.xml',
        'views/sale_crm_menus.xml'
    ],
    'auto_install': True,
    'license': 'LGPL-3'
}
