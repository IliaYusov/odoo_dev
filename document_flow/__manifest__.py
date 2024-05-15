{
    'name': 'Document Flow',
    'version': '1.5.5',
    'category': '',
    'depends': ['base', 'mail', 'task', 'dms', 'hr'],
    'external_dependencies': {'python': ['htmldocx', 'html2text']},
    'description': """
    """,
    'author': '',
    'support': '',
    'application': True,
    'installable': True,
    'auto_install': False,
    'images': ['static/description/icon.png'],
    'assets': {
        'web.assets_backend': [
            'document_flow/static/src/js/components/processing_chart_widget/*',
            'document_flow/static/src/js/components/processing_bar_widget/*',
            'document_flow/static/src/scss/processing_bar.variables.scss',
            'document_flow/static/src/scss/processing_bar.scss'
        ]
    },
    'data': [
        'data/document_flow_data.xml',
        'security/document_flow_security.xml',
        'security/ir.model.access.csv',
        'views/event_task_views.xml',
        'views/event_views.xml',
        'views/event_question_views.xml',
        'views/event_decision_views.xml',
        'views/event_annex_views.xml',
        'views/auto_substitution_views.xml',
        'views/executor_role_views.xml',
        'views/management_committee_views.xml',
        'views/process_views.xml',
        'views/process_template_views.xml',
        'views/document_kind_template_views.xml',
        'views/document_flow_document_views.xml',
        'wizard/document_flow_processing_wizard_resume.xml',
        'views/processing_views.xml',
        'views/task_history_views.xml',
        'views/task_views.xml',
        'views/dashboard_view.xml',
        'views/dashboard_templates.xml',
        'report/report.xml',
        'views/document_flow_menu.xml',
    ],
    'demo': [
    ],
    'license': 'LGPL-3'
}
