{
    'name': 'Task Timesheets',
    'version': '1.0.2',
    'category': 'Services/Timesheets',
    'summary': 'Track employee time on tasks',
    'description': """This module implements a timesheet system.""",
    'depends': ['hr', 'analytic', 'uom', 'task', 'project_budget'],
    'data': [
        'security/hr_timesheet_security.xml',
        'security/ir.model.access.csv',
        'views/hr_timesheet_views.xml',
        'views/task_views.xml',
        'views/project_budget_projects_views.xml',
        'data/hr_timesheet_data.xml',
        'views/hr_timesheet_menu.xml'
    ],
    'demo': [
    ],
    'installable': True,
    'assets': {
        'web.assets_backend': [
        ],
    },
    'license': 'LGPL-3'
}
