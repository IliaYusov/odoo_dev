{
    'name' : 'Project_budget',
    'version' : '16.0.1.1.1',
    'category': 'Project',
    'depends': ['base','mail','uom'],
    'description':"""
    """,
    'author': 'lapus',
    'support': 'lapushkov@yandex.ru',
    'assets': {
        'web._assets_primary_variables': [
            'web/static/src/scss/primary_variables.scss',
        ],
        'web.assets_backend': [
            'project_budget/static/src/js/dashboard_1.js',
            'project_budget/static/src/xml/dashboard_1.xml',
            'project_budget/static/src/scss/change_color.css',
        ],
        },
    'data': [
        'security/project_budget_users_groups.xml',
        'security/project_budget_users_rules.xml',
        'security/ir.model.access.csv',
        'data/project_budget_data.xml',
        'views/project_sequence.xml',
        'views/plan_kam_supervisor.xml',
        'views/fact_cash_flow.xml',
        'views/fact_acceptance_flow.xml',
        'views/project_budget_catalogs.xml',
        'views/project_budget_comercial_budget_access.xml',
        'views/project_budget_comercial_budget_search.xml',
        'views/project_budget_project_steps.xml',
        'views/project_budget_projects.xml',
        'views/project_budget_comercial_budget.xml',
        'views/Dashboard_1.xml',
        'views/tenders.xml',
        'wizard/report_tender_wizard.xml',
        'wizard/report_projects_wizard.xml',
        'views/project_budget_menu.xml',
    ],
    'demo':[

    ],
    'application':True,
    'images': ['static/description/banner.png'],
    'installable':True,
    'auto_install': False,
    'license': 'LGPL-3',
}