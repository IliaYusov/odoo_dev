{
    'name': 'Document Flow',
    'version': '16.0.1.0.5',
    'category': '',
    'depends': ['base', 'mail', 'task', 'hr_replacement'],
    'external_dependencies': {'python': ['htmldocx']},
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
            'document_flow/static/src/css/html_fields.css',
            'document_flow/static/src/css/dashboard.css',
            'document_flow/static/src/js/lib/Chart.bundle.js',
            'document_flow/static/src/xml/dashboard_view.xml',
            'document_flow/static/src/js/dashboard_view.js',
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
        'views/management_committee_views.xml',
        'views/executor_role_views.xml',
        'views/process_views.xml',
        'views/process_template_views.xml',
        'views/document_views.xml',
        'views/processing_views.xml',
        'views/task_history_views.xml',
        'views/task_views.xml',
        'views/dashboard_view.xml',
        'views/dashboard_templates.xml',
        'report/report.xml',
        'views/document_flow_menu.xml'
    ],
    'demo': [
    ],
    'license': 'LGPL-3',
}
