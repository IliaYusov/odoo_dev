from odoo import http
from odoo.http import request


class DocumentFlowTasks(http.Controller):
    @http.route(['/document_flow/tasks'], type="json", auth="user")
    def elearning_snippet(self):
        tasks = []
        new_tasks = request.env['task.task'].search([
            ('state', 'in', ['to_do', 'assigned'])
        ])
        for task in new_tasks:
            tasks.append(
                {'name': task.name, 'id': task.id}
            )
        values = {
            'h_tasks': tasks
        }
        response = http.Response(
            template='document_flow.dashboard_tasks',
            qcontext=values)
        return response.render()
