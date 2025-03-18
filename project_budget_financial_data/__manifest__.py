{
    'name': 'Project Budget Financial Data',
    'version': '1.0.0',
    'category': 'Project',
    'depends': ['project_budget', 'base_automation', 'project_budget_nkk'],
    'description': """
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/res_company_views.xml',
        'views/project_budget_amount_specifications.xml',
        'views/project_budget_project_type_views.xml',
        'views/project_budget_project_views.xml',
    ],
    'installable': True,
    'auto_install': ['project_budget'],
    'license': 'LGPL-3'
}
