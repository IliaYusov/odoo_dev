{
    'name': 'Project Budget NKK',
    'version': '1.2.3',
    'category': 'Project',
    'depends': ['project_budget', 'base_automation', 'account_budget_mngmnt'],
    'description': """
    """,
    'data': [
        'security/project_budget_groups.xml',
        'security/project_budget_users_rules.xml',
        'security/ir.model.access.csv',
        'data/project_budget_data.xml',
        'views/project_budget_project_supervisor_views.xml',
        'views/project_budget_project_type_views.xml',
        'views/project_budget_acceptance_flow_views.xml',
        'views/project_budget_cash_flow_views.xml',
        'views/project_budget_cost_flow_views.xml',
        'views/project_budget_plan_kam_supervisor_views.xml',
        'views/project_budget_technological_direction_views.xml',
        'views/project_budget_project_member_views.xml',
        'views/project_budget_project_views.xml',
        'wizard/project_budget_project_print_report_views.xml',
        'views/project_budget_menus.xml'
    ],
    'installable': True,
    'auto_install': ['project_budget'],
    'license': 'LGPL-3'
}
