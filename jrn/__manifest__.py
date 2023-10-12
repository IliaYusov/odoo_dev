{
    'name' : 'jrn',
    'version' : '16.0.0.0.1',
    'category': 'journal',
    'depends': ['base','web'],
    'description':"""
    """,
    'author': 'lapus',
    'support': 'lapushkov@yandex.ru',
    'data': [
        'security/ir.model.access.csv',
        'views/jrn.xml',
        'views/tables.xml',
        'wizard/tables_wizard_set_attrs.xml',
        'wizard/view_journal_record.xml',
        'wizard/jrn_wizard_undo_changes.xml',
        'views/menu.xml',
        'views/tables_add_btn.xml',
    ],
    'demo':[

    ],
    'assets': {
        'web.assets_backend': [
            'jrn/static/src/js/tables_add_btn.js',
            'jrn/static/src/xml/tables_add_button.xml',
        ],
    },
    'application':True,
    'images': ['static/description/banner.png'],
    'installable':True,
    'auto_install': False,
    'license': 'LGPL-3',
}