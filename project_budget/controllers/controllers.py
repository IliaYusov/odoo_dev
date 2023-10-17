# -*- coding: utf-8 -*-

from odoo import http


class ProjectBudget(http.Controller):

    @http.route('/project_budget/statistics', type='json', auth='user')
    def get_statistics(self):
        return http.request.env['project_budget.projects'].get_statistics()
