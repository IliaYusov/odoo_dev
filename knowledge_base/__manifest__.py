{
    'name' : 'Knowledge base',
    'version' : '1',
    'category': '',
    'depends': ['base'],
    'description':"""
    """,
    'author': '',
    'support': '',
    'application': True,
    'installable': True,
    'auto_install': False,
    'assets': {
        },
    'data': [
        'security/ir.model.access.csv',
        'security/knowledge_base_users_groups.xml',
        'views/article.xml',
        'views/section.xml',
        'views/tags.xml',
        'views/knowledge_base_menu.xml',
        'report/article_reports.xml',
        'report/article_templates.xml',
    ],
    'demo':[
    ],
    'license': 'LGPL-3',
}