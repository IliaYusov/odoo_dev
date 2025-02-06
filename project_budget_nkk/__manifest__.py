{
    'name': 'Project Budget NKK',
    'version': '1.0.3',
    'category': 'Project',
    'depends': ['project_budget', 'base_automation'],
    'description': """
    """,
    'data': [
        'security/project_budget_users_rules.xml',
        'security/ir.model.access.csv',
        'data/project_budget_data.xml',
        'views/project_budget_technological_direction_views.xml',
        'views/project_budget_project_views.xml',
        'views/project_budget_menus.xml'
    ],
    'installable': True,
    'auto_install': ['project_budget'],
    'license': 'LGPL-3'
}
