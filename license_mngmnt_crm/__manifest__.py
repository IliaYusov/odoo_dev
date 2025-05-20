{
    'name': 'License Management: CRM',
    'version': '16.0.1.0.0',
    'category': 'Services',
    'depends': ['license_mngmnt', 'project_budget'],
    'installable': True,
    'auto_install': True,
    'data': [
        'security/ir.model.access.csv',
        'data/ir_action_data.xml',
        'views/license_license_views.xml',
        'wizard/crm_lead_create_license_views.xml'
    ],
    'license': 'LGPL-3'
}
