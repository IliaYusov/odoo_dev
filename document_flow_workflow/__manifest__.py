{
    'name': 'Document Flow: Workflow',
    'version': '1.0.1',
    'category': 'Document Management',
    'depends': ['document_flow', 'workflow'],
    'installable': True,
    'auto_install': True,
    'data': [
        'views/document_flow_document_kind_template_views.xml',
        'views/document_flow_document_views.xml',
        'views/workflow_workflow_views.xml',
        'report/report.xml'
    ],
    'license': 'LGPL-3'
}
