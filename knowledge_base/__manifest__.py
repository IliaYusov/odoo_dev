{
    'name': 'Knowledge Base',
    'version': '1.0.0',
    'category': '',
    'depends': ['base', 'mail'],
    'description': """
    """,
    'author': '',
    'support': '',
    'application': True,
    'installable': True,
    'auto_install': False,
    'data': [
        'security/knowledge_security.xml',
        'security/ir.model.access.csv',
        'views/knowledge_article_views.xml',
        'views/knowledge_section_views.xml',
        'views/knowledge_tags_views.xml',
        'views/knowledge_menu.xml',
        'report/article_templates.xml',
        'report/article_reports.xml',
    ],
    'license': 'LGPL-3'
}