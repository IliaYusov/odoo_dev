from odoo import api, fields, models


class Task(models.Model):
    _inherit = 'task.task'

    @api.model
    def get_tasks_count(self):
        my_tasks_to_do_count = self.env['task.task'].search_count([
            ('is_closed', '=', False),
            ('date_deadline', '>=', fields.Datetime.now()),
            '|', ('user_ids', '=', self.env.uid),
            ('user_ids', 'in', self.env.user.employee_ids.replaceable_employee_ids.user_id.ids)
        ])
        my_tasks_overdue_count = self.env['task.task'].search_count([
            ('is_closed', '=', False),
            ('date_deadline', '<', fields.Datetime.now()),
            '|', ('user_ids', '=', self.env.uid),
            ('user_ids', 'in', self.env.user.employee_ids.replaceable_employee_ids.user_id.ids)
        ])
        by_me_tasks_to_do_count = self.env['task.task'].search_count([
            ('is_closed', '=', False),
            ('date_deadline', '>=', fields.Datetime.now()),
            ('author_id', '=', self.env.uid)
        ])
        by_me_tasks_overdue_count = self.env['task.task'].search_count([
            ('is_closed', '=', False),
            ('date_deadline', '<', fields.Datetime.now()),
            ('author_id', '=', self.env.uid)
        ])

        groups = self.env['workflow.group.executors'].search([
            ('member_ids', 'in', self.env.uid)
        ])
        group_tasks_to_do_count = self.env['task.task'].search_count([
            ('is_closed', '=', False),
            ('date_deadline', '>=', fields.Datetime.now()),
            ('user_ids', '=', False),
            ('group_executors_id', 'in', groups.ids)
        ])
        group_tasks_overdue_count = self.env['task.task'].search_count([
            ('is_closed', '=', False),
            ('date_deadline', '<', fields.Datetime.now()),
            ('user_ids', '=', False),
            ('group_executors_id', 'in', groups.ids)
        ])
        subordinates_tasks_to_do_count = self.env['task.task'].search_count([
            ('is_closed', '=', False),
            ('date_deadline', '>=', fields.Datetime.now()),
            ('user_ids', 'in', self.env.user.employee_id.subordinate_ids.user_id.ids)
        ])
        subordinates_tasks_overdue_count = self.env['task.task'].search_count([
            ('is_closed', '=', False),
            ('date_deadline', '<', fields.Datetime.now()),
            ('user_ids', 'in', self.env.user.employee_id.subordinate_ids.user_id.ids)
        ])

        values = {
            'my_tasks_count': my_tasks_to_do_count + my_tasks_overdue_count,
            'my_to_do_count': my_tasks_to_do_count,
            'my_overdue_count': my_tasks_overdue_count,
            'by_me_tasks_count': by_me_tasks_to_do_count + by_me_tasks_overdue_count,
            'by_me_to_do_count': by_me_tasks_to_do_count,
            'by_me_overdue_count': by_me_tasks_overdue_count,
            'group_tasks_count': group_tasks_to_do_count + group_tasks_overdue_count,
            'group_to_do_count': group_tasks_to_do_count,
            'group_overdue_count': group_tasks_overdue_count,
            'subordinates_tasks_count': subordinates_tasks_to_do_count + subordinates_tasks_overdue_count,
            'subordinates_to_do_count': subordinates_tasks_to_do_count,
            'subordinates_overdue_count': subordinates_tasks_overdue_count
        }
        return values
