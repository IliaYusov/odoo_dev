{
    'name': 'HR Replacement',
    'version': '1.0.2',
    'category': 'Human Resources/Employees',
    'depends': ['hr'],
    'description': 'HR employee replacements',
    'installable': True,
    'auto_install': True,
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_replacement_views.xml'
    ],
    'license': 'LGPL-3'
}
