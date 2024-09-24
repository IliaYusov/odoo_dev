{
    'name': 'Project Budget Forecast',
    'version': '1.0.0',
    'category': 'Project',
    'depends': ['project_budget'],
    'description': """
    Project Budget Forecast
    """,
    'data': [
        'data/project_budget_data.xml',
        'security/ir.model.access.csv',
        'views/project_budget_forecast_probability_views.xml',
        'views/project_budget_project_stage_views.xml',
        'views/project_budget_acceptance_flow_views.xml',
        'views/project_budget_cash_flow_views.xml',
        'views/project_budget_forecast_menu.xml'
    ],
    'installable': True,
    'auto_install': True,
    'license': 'LGPL-3'
}
