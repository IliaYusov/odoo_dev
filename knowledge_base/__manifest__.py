{
    'name' : 'Knowledge base',
    'version' : '1',
    'category': '',
    'depends': ['base', 'mail'],
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
        'security/knowledge_base_security.xml',
        'security/ir.model.access.csv',
        'views/knowledge_base_menu.xml',
        'views/knowledge_base_article.xml',
        'views/knowledge_base_section.xml',
        'views/knowledge_base_tags.xml',
        'report/article_reports.xml',
        'report/article_templates.xml',
    ],
    'demo':[
    ],
    'license': 'LGPL-3',
}