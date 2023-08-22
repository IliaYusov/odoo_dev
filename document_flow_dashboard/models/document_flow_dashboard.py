from odoo import _, models, fields, api
import calendar


class Task(models.Model):
    _inherit = 'task.task'

    @api.model
    def check_user_group(self):
        """Checking user group"""
        user = self.env.user
        if user.has_group('base.group_user'):
            return True
        else:
            return False

    @api.model
    def get_tasks_count(self):
        my_tasks_to_do_count = self.env['task.task'].search_count([
            ('state', 'in', ['to_do', 'assigned', 'in_progress']),
            ('date_deadline', '>=', fields.Datetime.now()),
            ('user_ids', 'in', self.env.uid)
        ])
        my_tasks_overdue_count = self.env['task.task'].search_count([
            ('state', 'not in', ('done', 'cancel')),
            ('date_deadline', '<', fields.Datetime.now()),
            ('user_ids', 'in', self.env.uid)
        ])
        by_me_tasks_to_do_count = self.env['task.task'].search_count([
            ('state', 'in', ['to_do', 'assigned', 'in_progress']),
            ('date_deadline', '>=', fields.Datetime.now()),
            ('write_uid', '=', self.env.uid)
        ])
        by_me_tasks_overdue_count = self.env['task.task'].search_count([
            ('state', 'not in', ('done', 'cancel')),
            ('date_deadline', '<', fields.Datetime.now()),
            ('write_uid', '=', self.env.uid)
        ])

        tasks = self.env['task.task'].search([
            ('state', 'in', ['to_do', 'assigned', 'in_progress'])
        ])
        p_tasks = []
        for task in tasks:
            p_tasks.append(task.name)

        values = {
            'my_to_do_count': my_tasks_to_do_count,
            'my_overdue_count': my_tasks_overdue_count,
            'by_me_to_do_count': by_me_tasks_to_do_count,
            'by_me_overdue_count': by_me_tasks_overdue_count,
            'p_tasks': p_tasks
        }
        return values

    @api.model
    def get_tasks_view(self):
        my_tasks_to_do = self.env['task.task'].search([
            ('state', 'in', ['to_do', 'assigned', 'in_progress']),
            ('date_deadline', '>=', fields.Datetime.now()),
            ('user_ids', 'in', self.env.uid)
        ])
        my_tasks_overdue = self.env['task.task'].search([
            ('state', 'not in', ('done', 'cancel')),
            ('date_deadline', '<', fields.Datetime.now()),
            ('user_ids', 'in', self.env.uid)
        ])
        by_me_tasks_to_do = self.env['task.task'].search([
            ('state', 'in', ['to_do', 'assigned', 'in_progress']),
            ('date_deadline', '>=', fields.Datetime.now()),
            ('write_uid', '=', self.env.uid)
        ])
        by_me_tasks_overdue = self.env['task.task'].search_count([
            ('state', 'not in', ('done', 'cancel')),
            ('date_deadline', '<', fields.Datetime.now()),
            ('write_uid', '=', self.env.uid)
        ])

        my_to_do_list = []
        my_overdue_list = []
        by_me_to_do_list = []
        by_me_overdue_list = []

        for task in my_tasks_to_do:
            my_to_do_list.append(task.name)
        for task in my_tasks_overdue:
            my_overdue_list.append(task.name)
        for task in by_me_tasks_to_do:
            by_me_to_do_list.append(task.name)
        for task in by_me_tasks_overdue:
            by_me_overdue_list.append(task.name)

        tasks = self.env['task.task'].search[(
            'state', 'in', ['to_do', 'assigned']
        )]
        p_tasks = []
        for task in tasks:
            p_tasks.append(task.name)

        values = {
            'my_to_do_count': len(my_tasks_to_do),
            'my_overdue_count': len(my_tasks_overdue),
            'by_me_to_do_count': len(by_me_tasks_to_do),
            'by_me_overdue_count': len(by_me_tasks_overdue),

            'my_to_do_tasks': my_to_do_list,
            'my_overdue_tasks': my_overdue_list,
            'by_me_to_do_tasks': by_me_to_do_list,
            'by_me_overdue_tasks': by_me_overdue_list,
            'p_tasks': p_tasks
        }
        return values

    @api.model
    def get_done_tasks_pie(self):
        result = []
        tasks_count = self.env['task.task'].search_count([])
        tasks_done_count = self.env['task.task'].search_count([
            ('is_closed', '=', True)
        ])
        result.append(tasks_done_count)
        result.append(tasks_count - tasks_done_count)

        return result
    #
    # @api.model
    # def get_team_ticket_count_pie(self):
    #     """bar chart"""
    #     ticket_count = []
    #     team_list = []
    #     tickets = self.env['help.ticket'].search([])
    #
    #     for rec in tickets:
    #         if rec.team_id:
    #             team = rec.team_id.name
    #             if team not in team_list:
    #                 team_list.append(team)
    #             ticket_count.append(team)
    #
    #     team_val = []
    #     for index in range(len(team_list)):
    #         value = ticket_count.count(team_list[index])
    #         team_name = team_list[index]
    #         team_val.append({'label': team_name, 'value': value})
    #     name = []
    #     for record in team_val:
    #         name.append(record.get('label'))
    #     #
    #     count = []
    #     for record in team_val:
    #         count.append(record.get('value'))
    #     #
    #     team = [count, name]
    #     return team
    #
    # @api.model
    # def get_project_ticket_count(self):
    #     """bar chart"""
    #     ticket_count = []
    #     project_list = []
    #     tickets = self.env['help.ticket'].search([])
    #
    #     for rec in tickets:
    #         if rec.project_id:
    #             project = rec.project_id.name
    #             if project not in project_list:
    #                 project_list.append(project)
    #             ticket_count.append(project)
    #
    #     project_val = []
    #     for index in range(len(project_list)):
    #         value = ticket_count.count(project_list[index])
    #         project_name = project_list[index]
    #         project_val.append({'label': project_name, 'value': value})
    #     name = []
    #     for record in project_val:
    #         name.append(record.get('label'))
    #     #
    #     count = []
    #     for record in project_val:
    #         count.append(record.get('value'))
    #     #
    #     project = [count, name]
    #     return project
    #
    # @api.model
    # def get_billed_task_team_chart(self):
    #     """polarArea chart"""
    #     ticket_count = []
    #     team_list = []
    #     tasks=[]
    #     project_task = self.env['project.task'].search([('ticket_billed', '=', True)])
    #     for rec in project_task:
    #         tasks.append(rec.ticket_id.id)
    #     tickets = self.env['help.ticket'].search([('id', 'in', tasks)])
    #
    #
    #     for rec in tickets:
    #         # if rec.id in teams.ids:
    #         team = rec.team_id.name
    #         if team not in team_list:
    #             team_list.append(team)
    #         ticket_count.append(team)
    #
    #     team_val = []
    #     for index in range(len(team_list)):
    #         value = ticket_count.count(team_list[index])
    #         team_name = team_list[index]
    #         team_val.append({'label': team_name, 'value': value})
    #     name = []
    #     for record in team_val:
    #         name.append(record.get('label'))
    #     #
    #     count = []
    #     for record in team_val:
    #         count.append(record.get('value'))
    #     #
    #     team = [count, name]
    #     return team
    #
    # @api.model
    # def get_team_ticket_done_pie(self):
    #     """bar chart"""
    #     ticket_count = []
    #     team_list = []
    #     tickets = self.env['help.ticket'].search(
    #         [('stage_id.name', '=', 'Done')])
    #
    #     for rec in tickets:
    #         if rec.team_id:
    #             team = rec.team_id.name
    #             if team not in team_list:
    #                 team_list.append(team)
    #             ticket_count.append(team)
    #
    #     team_val = []
    #     for index in range(len(team_list)):
    #         value = ticket_count.count(team_list[index])
    #         team_name = team_list[index]
    #         team_val.append({'label': team_name, 'value': value})
    #     name = []
    #     for record in team_val:
    #         name.append(record.get('label'))
    #     #
    #     count = []
    #     for record in team_val:
    #         count.append(record.get('value'))
    #     #
    #     team = [count, name]
    #     return team
