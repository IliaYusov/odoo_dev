{
    'name': 'Contract: Approval',
    'version': '1.0.3',
    'category': '',
    'depends': ['base', 'contract', 'contract_project_budget', 'report_docx', 'workflow'],
    'description': """
    """,
    'author': '',
    'support': '',
    'installable': True,
    'auto_install': True,
    'images': ['static/description/icon.png'],
    'assets': {
        'web.assets_backend': [
        ]
    },
    'data': [
        'data/contract_data.xml',
        'security/contract_approval_security.xml',
        'security/ir.model.access.csv',
        'views/contract_contract_views.xml',
        'views/contract_type_views.xml',
        'views/workflow_workflow_views.xml',
        'report/report.xml',
        'views/contract_menu.xml'
    ],
    'demo': [
    ],
    'license': 'LGPL-3'
}
