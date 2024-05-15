{
    'name': 'Contract Management',
    'version': '1.0.2',
    'category': 'Contract Management',
    'website': '',
    'author': '',
    'depends': ['base', 'hr'],
    'data': [
        'data/contract_data.xml',
        'security/contract_security.xml',
        'security/ir.model.access.csv',
        'views/contract_views.xml',
        'views/contract_kind_views.xml',
        'views/contract_type_views.xml',
        'views/res_partner_views.xml',
        'views/contract_menu.xml'
    ],
    'application': True,
    'license': 'LGPL-3'
}
