{
    'name': 'Budget Management',
    'category': 'Accounting/Accounting',
    'description': """
Use budgets to compare actual with expected revenues and costs
""",
    'depends': ['account'],
    'data': [
        'security/account_budget_groups.xml',
        'security/account_budget_security.xml',
        'security/ir.model.access.csv',
        'views/account_budget_item_views.xml',
        'views/crossovered_budget_views.xml',
        'views/crossovered_budget_line_views.xml',
        'views/account_analytic_account_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            # 'account_budget_management/static/src/widgets/**/*'
        ]
    },
    'license': 'LGPL-3'
}
