{
    'name': 'Project_budget',
    'version': '16.0.1.1.2',
    'category': 'Project',
    'depends': ['base', 'mail', 'hr'],
    'external_dependencies': {'python': ['openpyxl']},
    'description': """
    """,
    'author': 'lapus',
    'support': 'lapushkov@yandex.ru',
    'assets': {
        'web.assets_backend': [
            'project_budget/static/src/views/**/*.js',
            'project_budget/static/src/views/**/*.xml',
            'project_budget/static/src/scss/change_color.css'
        ],
    },
    'data': [
        'security/project_budget_users_groups.xml',
        'security/project_budget_users_rules.xml',
        'security/ir.model.access.csv',
        'data/project_budget_data.xml',
        'data/ir_cron_data.xml',
        'views/project_sequence.xml',
        'views/plan_kam_supervisor.xml',
        'views/fact_cash_flow.xml',
        'views/tender_search.xml',
        'views/fact_acceptance_flow.xml',
        'views/project_budget_catalogs.xml',
        'views/project_budget_comercial_budget_access.xml',
        'views/project_amount_specifications.xml',
        'views/project_budget_project_office_views.xml',
        'views/project_budget_project_role_views.xml',
        'views/project_budget_project_member_views.xml',
        'views/project_budget_project_stage_views.xml',
        'views/project_budget_project_views.xml',
        'views/project_budget_comercial_budget.xml',
        'views/project_currency_rates.xml',
        'views/tenders.xml',
        'views/res_partner_views.xml',
        'views/scheduled_report_views.xml',
        'views/res_config_settings.xml',
        'views/hr_employee_replacement_views.xml',
        'wizard/report_tender_wizard.xml',
        'wizard/report_projects_wizard.xml',
        'views/res_company_partner_type_views.xml',
        'views/res_company_partner_grade_views.xml',
        'views/res_company_partner_views.xml',
        'wizard/project_budget_link_project.xml',
        'data/ir_action_data.xml',
        'report/project_budget_project_overdue_report_views.xml',
        'report/project_budget_financial_data_report_views.xml',
        'wizard/open_file_wizard.xml',
        'report/project_budget_report_external_data_views.xml',
        'views/project_budget_menu.xml',
    ],
    'demo': [
    ],
    'application': True,
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3'
}
