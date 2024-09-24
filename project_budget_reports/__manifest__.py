{
    'name': 'Project Budget Reports',
    'version': '1.0.0',
    'category': 'Project',
    'depends': ['project_budget', 'project_budget_forecast'],
    'description': """
    Project Budget Reports
    """,
    'assets': {
        'web.assets_backend': [
            'project_budget_reports/static/src/components/**/*'
        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'security/project_budget_security.xml',
        'views/sales_forecast_dashboard.xml'
    ],
    'installable': True,
    'auto_install': True,
    'license': 'LGPL-3'
}
