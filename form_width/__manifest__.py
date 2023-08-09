# -*- coding: utf-8 -*-
{
    'name': 'Form Width',
    'version': '16.0',
    'category': 'Tools',
    'description': """
You can adjust the width of any form view and only these ones will be affected.
 <sheet style="max-width: 95%;"> 
    """,
    'summary': '''
    You can adjust the width of any form view and only these ones will be affected 
    ''',
    'author': 'lapus',
    'support': 'lapushkov@yandex.ru',
    'website': '',
    'depends': [
        'web',
    ],
    'data': [
    ],
    'assets': {
        'web.assets_backend': [
            'form_width/static/src/js/set_width.js',
            'form_width/static/src/js/set_title.js',
            'form_width/static/src/css/form_view_extra.css',
        ]
    },
    'test': [],
    'demo': [],
    'images': ['static/description/banner.png'],
    'installable': True,
    'active': False,
    'application': True,
}
