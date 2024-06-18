{
    "name": "Workflow",
    "summary": "Workflow engine",
    "version": "1.1.2",
    "category": "Extra Tools",
    "depends": ['base', 'task'],
    'application': True,
    'installable': True,
    'auto_install': False,
    "assets": {
        "web.assets_backend": [
        ],
    },
    "data": [
        'data/workflow_data.xml',
        'security/workflow_security.xml',
        'security/ir.model.access.csv',
        'views/workflow_group_executors_views.xml',
        'views/workflow_auto_substitution_views.xml',
        'views/workflow_views.xml',
        'views/workflow_activity_views.xml',
        'views/workflow_transition_views.xml',
        'wizard/workflow_process_stop_wizard.xml',
        'wizard/workflow_process_resume_wizard.xml',
        'views/workflow_process_views.xml',
        'views/workflow_process_activity_views.xml',
        'views/workflow_process_activity_history_views.xml',
        'views/workflow_parent_access_views.xml',
        'views/task_stage_views.xml',
        'views/task_task_views.xml',
        'views/workflow_menu.xml'
    ],
    "license": "LGPL-3"
}
