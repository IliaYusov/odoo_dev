from ast import literal_eval
from odoo import models, fields, api

class estimated_probability(models.Model):
    _name = 'project_budget.estimated_probability'
    _description = "project_estimated_probability"
    _order = "code"
    name = fields.Char(string="estimated_probability name", required=True, )
    code = fields.Char(string="estimated_probability code", required=True, )
    color = fields.Integer('Color')
    # count_approve_state_manager = fields.Integer(compute='_compute_probability_count')
    # count_approve_state_supervisor = fields.Integer(compute='_compute_probability_count')
    # count_approve_state_approved = fields.Integer(compute='_compute_probability_count')
    count_approve_state_total = fields.Integer(compute='_compute_probability_count')
    # sum_revenue_approve_state_manager = fields.Integer(compute='_compute_probability_count')
    # sum_revenue_approve_state_supervisor = fields.Integer(compute='_compute_probability_count')
    # sum_revenue_approve_state_approved = fields.Integer(compute='_compute_probability_count')
    sum_revenue_approve_state_total = fields.Integer(compute='_compute_probability_count')
    sum_margin_income_total  = fields.Integer(compute='_compute_probability_count')
    sum_cost_price_total  = fields.Integer(compute='_compute_probability_count')
    def _compute_probability_count(self):
        domains = {
            # 'count_approve_state_manager' : [('approve_state', '=', 'need_approve_manager')],
            # 'count_approve_state_supervisor' : [('approve_state', '=', 'need_approve_supervisor')],
            # 'count_approve_state_approved' : [('approve_state', '=', 'approved')],
            'count_approve_state_total':[]
        }
        for field in domains:
            data = self.env['project_budget.projects']._read_group(domains[field]+
                [('budget_state','=','work'),('estimated_probability_id', 'in', self.ids)]
                ,['estimated_probability_id'], ['estimated_probability_id'])
            count = {
                x['estimated_probability_id'][0]: x['estimated_probability_id_count']
                for x in data if x['estimated_probability_id']
            }
            for record in self:
                record[field] = count.get(record.id, 0)

        domains = {
            # 'sum_revenue_approve_state_manager': [('approve_state', '=', 'need_approve_manager')],
            # 'sum_revenue_approve_state_supervisor': [('approve_state', '=', 'need_approve_supervisor')],
            # 'sum_revenue_approve_state_approved': [('approve_state', '=', 'approved')],
            'sum_revenue_approve_state_total': []
        }
        for field in domains:
            data = self.env['project_budget.projects']._read_group(domains[field]+
                [('budget_state','=','work'),('estimated_probability_id', 'in', self.ids)]
                ,['estimated_probability_id','sum_total:sum(total_amount_of_revenue)'], ['estimated_probability_id'])

            sum = {
                x['estimated_probability_id'][0]: x['sum_total']
                for x in data if x['estimated_probability_id']
            }
            for record in self:
                record[field] = sum.get(record.id, 0)

        domains = {
            # 'sum_revenue_approve_state_manager': [('approve_state', '=', 'need_approve_manager')],
            # 'sum_revenue_approve_state_supervisor': [('approve_state', '=', 'need_approve_supervisor')],
            # 'sum_revenue_approve_state_approved': [('approve_state', '=', 'approved')],
            'sum_margin_income_total': []
        }
        for field in domains:
            data = self.env['project_budget.projects']._read_group(domains[field]+
                [('budget_state','=','work'),('estimated_probability_id', 'in', self.ids)]
                ,['estimated_probability_id','sum_total:sum(margin_income)'], ['estimated_probability_id'])

            sum = {
                x['estimated_probability_id'][0]: x['sum_total']
                for x in data if x['estimated_probability_id']
            }
            for record in self:
                record[field] = sum.get(record.id, 0)

        domains = {
            # 'sum_revenue_approve_state_manager': [('approve_state', '=', 'need_approve_manager')],
            # 'sum_revenue_approve_state_supervisor': [('approve_state', '=', 'need_approve_supervisor')],
            # 'sum_revenue_approve_state_approved': [('approve_state', '=', 'approved')],
            'sum_cost_price_total': []
        }
        for field in domains:
            data = self.env['project_budget.projects']._read_group(domains[field] +
                [('budget_state', '=', 'work'), ('estimated_probability_id', 'in', self.ids)]
                , ['estimated_probability_id','sum_total:sum(cost_price)'],['estimated_probability_id'])
            sum = {
                x['estimated_probability_id'][0]: x['sum_total']
                for x in data if x['estimated_probability_id']
            }
            for record in self:
                record[field] = sum.get(record.id, 0)


    def _get_action(self, action_xmlid,context):
        action = self.env["ir.actions.actions"]._for_xml_id(action_xmlid)
        if self:
            action['display_name'] = self.display_name

        default_immediate_tranfer = True

        action_context = literal_eval(action['context'])
        context = {**action_context, **context}
        action['context'] = context
        return action

    def get_action_projects_0(self):
        context = {
            "estimated_probability_0": True
        }
        return self._get_action('project_budget.show_comercial_budget_spec',context)
    def get_action_projects_0(self):
        context = {"search_default_estimated_probability_0": True}
        return self._get_action('project_budget.show_comercial_budget_spec',context)
    def get_action_projects_10(self):
        context = {"search_default_estimated_probability_10": True}
        return self._get_action('project_budget.show_comercial_budget_spec',context)
    def get_action_projects_30(self):
        context = {"search_default_estimated_probability_30": True}
        return self._get_action('project_budget.show_comercial_budget_spec',context)
    def get_action_projects_50(self):
        context = {"search_default_estimated_probability_50": True}
        return self._get_action('project_budget.show_comercial_budget_spec',context)
    def get_action_projects_75(self):
        context = {"search_default_estimated_probability_75": True}
        return self._get_action('project_budget.show_comercial_budget_spec',context)
    def get_action_projects_100(self):
        context = {"search_default_estimated_probability_100": True}
        return self._get_action('project_budget.show_comercial_budget_spec',context)
    def get_action_projects_100done(self):
        context = {"search_default_estimated_probability_100done": True}
        return self._get_action('project_budget.show_comercial_budget_spec',context)

