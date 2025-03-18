import re

from odoo import api, Command, fields, models, _
from odoo.exceptions import ValidationError


class Project(models.Model):
    _inherit = 'project_budget.projects'

    def _get_domain_amount_spec(self):
        domain = []
        context = self.env.context
        if context.get("revenue_from_the_sale_of_works"):
            domain = [('type', '=', "revenue_from_the_sale_of_works")]
        if context.get("revenue_from_the_sale_of_goods"):
            domain = [('type', '=', "revenue_from_the_sale_of_goods")]
        if context.get("cost_of_goods"):
            domain = [('type', '=', "cost_of_goods")]
        if context.get("travel_expenses"):
            domain = [('type', '=', "travel_expenses")]
        if context.get("third_party_works"):
            domain = [('type', '=', "third_party_works")]
        if context.get("transportation_expenses"):
            domain = [('type', '=', "transportation_expenses")]
        if context.get("representation_expenses"):
            domain = [('type', '=', "representation_expenses")]
        if context.get("rko_other"):
            domain = [('type', '=', "rko_other")]
        if context.get("warranty_service_costs"):
            domain = [('type', '=', "warranty_service_costs")]
        if context.get("other_expenses"):
            domain = [('type', '=', "other_expenses")]
        return domain

    def _get_current_amount_spec_type(self):
        context = self.env.context
        value = ''
        if context.get("revenue_from_the_sale_of_works"):
            value = _('revenue_from_the_sale_of_works')
        if context.get("revenue_from_the_sale_of_goods"):
            value =  _('revenue_from_the_sale_of_goods')
        if context.get("cost_of_goods"):
            value =  _('cost_of_goods')
        if context.get("travel_expenses"):
            value =  _('travel_expenses')
        if context.get("third_party_works"):
            value =  _('third_party_works')
        if context.get("representation_expenses"):
            value =  _('representation_expenses')
        if context.get("rko_other"):
            value =  _('rko_other')
        if context.get("warranty_service_costs"):
            value =  _('warranty_service_costs')
        if context.get("other_expenses"):
            value =  _('other_expenses')
        if context.get("transportation_expenses"):
            value =  _('transportation_expenses')
        self.current_amount_spec_type = value

    def _get_amount_spec_type(self, amount_spec_ids, type):
        for amount_spec in amount_spec_ids:
            if amount_spec.type == type: return True
        return False

    def _exists_amount_spec(self):
        for row in self:
            row.revenue_from_the_sale_of_works_amount_spec_exist = self._get_amount_spec_type(row.amount_spec_ids, 'revenue_from_the_sale_of_works')
            row.revenue_from_the_sale_of_goods_amount_spec_exist = self._get_amount_spec_type(row.amount_spec_ids, 'revenue_from_the_sale_of_goods')
            row.cost_of_goods_amount_spec_exist = self._get_amount_spec_type(row.amount_spec_ids, 'cost_of_goods')
            row.travel_expenses_amount_spec_exist = self._get_amount_spec_type(row.amount_spec_ids, 'travel_expenses')
            row.third_party_works_amount_spec_exist = self._get_amount_spec_type(row.amount_spec_ids, 'third_party_works')
            row.transportation_expenses_amount_spec_exist = self._get_amount_spec_type(row.amount_spec_ids, 'transportation_expenses')
            row.representation_expenses_amount_spec_exist = self._get_amount_spec_type(row.amount_spec_ids, 'representation_expenses')
            row.rko_other_amount_spec_exist = self._get_amount_spec_type(row.amount_spec_ids, 'rko_other')
            row.warranty_service_costs_amount_spec_exist = self._get_amount_spec_type(row.amount_spec_ids, 'warranty_service_costs')
            row.other_expenses_amount_spec_exist = self._get_amount_spec_type(row.amount_spec_ids, 'other_expenses')

    def _get_sums_from_amount_spec_type(self, row, type):
        sum = 0
        project_currency_rates = self.env['project_budget.project_currency_rates']
        for amount_spec in row.amount_spec_ids:
            # _rate_prj = self.env['res.currency']._get_conversion_rate(from_currency=amount_spec.currency_id,
            #                                               to_currency=row.currency_id, date=)
            if amount_spec.type == type:
                sum += amount_spec.summa * project_currency_rates._get_currency_rate_for_project_currency(row, amount_spec.currency_id.id)
                       # *row.company_id.currency_id
        return sum

    def _compute_sums_from_amount_spec(self):
        for row in self:
            # print('row=',row)
            # print('row.revenue_from_the_sale_of_works_amount_spec_exist = ', row.revenue_from_the_sale_of_works_amount_spec_exist)
            if row.revenue_from_the_sale_of_works_amount_spec_exist:
                row.revenue_from_the_sale_of_works = self._get_sums_from_amount_spec_type(row, 'revenue_from_the_sale_of_works')
            if row.revenue_from_the_sale_of_goods_amount_spec_exist:
                row.revenue_from_the_sale_of_goods = self._get_sums_from_amount_spec_type(row, 'revenue_from_the_sale_of_goods')
            if row.cost_of_goods_amount_spec_exist:
                row.cost_of_goods = self._get_sums_from_amount_spec_type(row, 'cost_of_goods')
            if row.travel_expenses_amount_spec_exist:
                row.travel_expenses = self._get_sums_from_amount_spec_type(row, 'travel_expenses')
            if row.third_party_works_amount_spec_exist:
                row.third_party_works = self._get_sums_from_amount_spec_type(row, 'third_party_works')
            if row.transportation_expenses_amount_spec_exist:
                row.transportation_expenses = self._get_sums_from_amount_spec_type(row, 'transportation_expenses')
            if row.representation_expenses_amount_spec_exist:
                row.representation_expenses = self._get_sums_from_amount_spec_type(row, 'representation_expenses')
            if row.rko_other_amount_spec_exist:
                row.rko_other = self._get_sums_from_amount_spec_type(row, 'rko_other')
            if row.warranty_service_costs_amount_spec_exist:
                row.warranty_service_costs = self._get_sums_from_amount_spec_type(row, 'warranty_service_costs')
            if row.other_expenses_amount_spec_exist:
                row.other_expenses = self._get_sums_from_amount_spec_type(row, 'other_expenses')

    total_amount_of_revenue = fields.Monetary(string='total_amount_of_revenue', compute='_compute_spec_totals',
                                              inverse='_inverse_spec_totals', store=True, tracking=True)
    cost_price = fields.Monetary(string='cost_price', compute='_compute_spec_totals', inverse='_inverse_spec_totals',
                                 store=True, tracking=True)

    revenue_from_the_sale_of_works = fields.Monetary(string='revenue_from_the_sale_of_works(services)',tracking=True, )
    revenue_from_the_sale_of_works_amount_spec_exist = fields.Boolean(string='revenue_from_the_sale_of_works_amount_spec_exist', compute="_exists_amount_spec")
    revenue_from_the_sale_of_goods_amount_spec_exist = fields.Boolean(string='revenue_from_the_sale_of_goods_amount_spec_exist', compute="_exists_amount_spec")
    cost_of_goods_amount_spec_exist = fields.Boolean(string='cost_of_goods_amount_spec_exist', compute="_exists_amount_spec")
    travel_expenses_amount_spec_exist = fields.Boolean(string='travel_expenses_amount_spec_exist', compute="_exists_amount_spec")
    third_party_works_amount_spec_exist= fields.Boolean(string='third_party_works_amount_spec_exist', compute="_exists_amount_spec")
    transportation_expenses_amount_spec_exist= fields.Boolean(string='transportation_expenses_amount_spec_exist', compute="_exists_amount_spec")
    representation_expenses_amount_spec_exist= fields.Boolean(string='representation_expenses_amount_spec_exist', compute="_exists_amount_spec")
    rko_other_amount_spec_exist= fields.Boolean(string='rko_other_amount_spec_exist', compute="_exists_amount_spec")
    warranty_service_costs_amount_spec_exist= fields.Boolean(string='warranty_service_costs_amount_spec_exist', compute="_exists_amount_spec")
    other_expenses_amount_spec_exist= fields.Boolean(string='other_expenses_amount_spec_exist', compute="_exists_amount_spec")
    current_amount_spec_type = fields.Char(string= "current amount spec type", compute="_get_current_amount_spec_type")

    amount_spec_ids = fields.One2many(
        comodel_name='project_budget.amount_spec',
        inverse_name='projects_id', string="amount spec revenue from the sale of works", auto_join=True, copy=True,
        domain = _get_domain_amount_spec,
    )
    revenue_from_the_sale_of_goods = fields.Monetary(string='revenue_from the sale of goods',tracking=True, )

    cost_of_goods = fields.Monetary(string='cost_of_goods',tracking=True, )
    third_party_works = fields.Monetary(string='third_party_works(subcontracting)',tracking=True, )
    transportation_expenses = fields.Monetary(string='transportation_expenses',tracking=True, )
    travel_expenses = fields.Monetary(string='travel_expenses',tracking=True, )
    representation_expenses = fields.Monetary(string='representation_expenses',tracking=True, )
    warranty_service_costs = fields.Monetary(string='Warranty service costs',tracking=True, )
    rko_other = fields.Monetary(string='rko_other',tracking=True, )
    other_expenses = fields.Monetary(string='other_expenses',tracking=True, )

    awards_on_results_project = fields.Monetary(string='Awards based on the results of the project',tracking=True)
    own_works_fot = fields.Monetary(string='own_works_fot',tracking=True)
    taxes_fot_premiums = fields.Monetary(string='taxes_FOT and premiums', store=True, tracking=True)

    is_revenue_from_the_sale_of_works =fields.Boolean(related='project_type_id.is_revenue_from_the_sale_of_works', readonly=True)
    is_revenue_from_the_sale_of_goods = fields.Boolean(related='project_type_id.is_revenue_from_the_sale_of_goods', readonly=True)
    is_cost_of_goods = fields.Boolean(related='project_type_id.is_cost_of_goods', readonly=True)
    is_own_works_fot = fields.Boolean(related='project_type_id.is_own_works_fot', readonly=True)
    is_third_party_works = fields.Boolean(related='project_type_id.is_third_party_works', readonly=True)
    is_awards_on_results_project = fields.Boolean(related='project_type_id.is_awards_on_results_project', readonly=True)
    is_transportation_expenses = fields.Boolean(related='project_type_id.is_transportation_expenses', readonly=True)
    is_travel_expenses = fields.Boolean(related='project_type_id.is_travel_expenses', readonly=True)
    is_representation_expenses = fields.Boolean(related='project_type_id.is_representation_expenses', readonly=True)
    is_warranty_service_costs = fields.Boolean(related='project_type_id.is_warranty_service_costs', readonly=True)
    is_rko_other = fields.Boolean(related='project_type_id.is_rko_other', readonly=True)
    is_other_expenses = fields.Boolean(related='project_type_id.is_other_expenses', readonly=True)

    is_percent_fot_manual = fields.Boolean(compute='_get_signer_settings_fot', readonly=True)
    percent_fot = fields.Float(compute='_get_signer_settings_fot', readonly=True)

    use_financial_data = fields.Boolean(related='company_id.use_financial_data', readonly=True)

    # ------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------

    def action_open_amount_spec_revenue_from_the_sale_of_works(self):
        return {
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'res_model': 'project_budget.projects',
            'view_id': self.env.ref("project_budget_financial_data.show_amount_spec").id,
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'context': {'revenue_from_the_sale_of_works': True},
            'flags': {'initial_mode': 'view'}
        }

    def action_open_amount_spec_revenue_from_the_sale_of_goods(self):
        return {
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'res_model': 'project_budget.projects',
            'view_id': self.env.ref("project_budget_financial_data.show_amount_spec").id,
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'context': {'revenue_from_the_sale_of_goods': True},
                'flags': {'initial_mode': 'view'}
        }

    def action_open_amount_spec_cost_of_goods(self):
        return {
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'res_model': 'project_budget.projects',
            'view_id': self.env.ref("project_budget_financial_data.show_amount_spec").id,
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'context': {'cost_of_goods': True},
            'flags': {'initial_mode': 'view'}
        }

    def action_open_amount_spec_travel_expenses(self):
        return {
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'res_model': 'project_budget.projects',
            'view_id': self.env.ref("project_budget_financial_data.show_amount_spec").id,
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'context': {'travel_expenses': True},
            'flags': {'initial_mode': 'view'}
        }

    def action_open_amount_spec_third_party_works(self):
        return {
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'res_model': 'project_budget.projects',
            'view_id': self.env.ref("project_budget_financial_data.show_amount_spec").id,
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'context': {'third_party_works': True},
            'flags': {'initial_mode': 'view'}
        }

    def action_open_amount_spec_representation_expenses(self):
        return {
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'res_model': 'project_budget.projects',
            'view_id': self.env.ref("project_budget_financial_data.show_amount_spec").id,
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'context': {'representation_expenses': True},
            'flags': {'initial_mode': 'view'}
        }

    def action_open_amount_spec_transportation_expenses(self):
        return {
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'res_model': 'project_budget.projects',
            'view_id': self.env.ref("project_budget_financial_data.show_amount_spec").id,
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'context': {'transportation_expenses': True},
            'flags': {'initial_mode': 'view'}
        }

    def action_open_amount_spec_rko_other(self):
        return {
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'res_model': 'project_budget.projects',
            'view_id': self.env.ref("project_budget_financial_data.show_amount_spec").id,
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'context': {'rko_other': True},
            'flags': {'initial_mode': 'view'}
        }

    def action_open_amount_spec_warranty_service_costs(self):
        return {
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'res_model': 'project_budget.projects',
            'view_id': self.env.ref("project_budget_financial_data.show_amount_spec").id,
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'context': {'warranty_service_costs': True},
            'flags': {'initial_mode': 'view'}
        }

    def action_open_amount_spec_other_expenses(self):
        return {
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'res_model': 'project_budget.projects',
            'view_id': self.env.ref("project_budget_financial_data.show_amount_spec").id,
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'context': {'other_expenses': True},
            'flags': {'initial_mode': 'view'}
        }

    # ------------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------------

    @api.depends('signer_id')
    def _get_signer_settings_fot(self):  # получаем настройки подписывающего юр лица из компании
        for record in self:
            company = self.env['res.company'].sudo().search([('partner_id', '=', record.signer_id.id)])
            record.is_percent_fot_manual = company.is_percent_fot_manual
            record.percent_fot = company.percent_fot

    def _calculate_all_sums(self, project):
        if not project.project_have_steps:
            self._compute_sums_from_amount_spec()

            project.total_amount_of_revenue = project.revenue_from_the_sale_of_works + project.revenue_from_the_sale_of_goods

            project.cost_price = project.cost_of_goods + project.own_works_fot + project.third_party_works + project.awards_on_results_project
            project.cost_price = project.cost_price + project.transportation_expenses + project.travel_expenses + project.representation_expenses
            project.cost_price = project.cost_price + project.warranty_service_costs + project.rko_other + project.other_expenses
            if not project.is_percent_fot_manual:
                project.taxes_fot_premiums = (project.awards_on_results_project + project.own_works_fot) * project.percent_fot / 100

            project.cost_price = project.cost_price + project.taxes_fot_premiums

        elif project.project_have_steps and project.step_status == 'project':
            # self._compute_sums_from_amount_spec()
            print('elif project.project_have_steps == True: row.amount_spec_ids =', project.amount_spec_ids)

            for amount_spec in project.amount_spec_ids:
                cur_idstr = str(amount_spec.id)
                if cur_idstr.isdigit():
                    print('elif project.project_have_steps == True: amount_spec =', amount_spec)
                    amount_spec.unlink()
                # self.env["project_budget.amount_spec"].sudo().search([("id", "in", project.amount_spec_ids)]).unlink()

            project.total_amount_of_revenue = 0
            project.cost_price = 0
            project.taxes_fot_premiums = 0
            project.profitability = 0
            project.revenue_from_the_sale_of_works = 0
            project.revenue_from_the_sale_of_goods = 0
            project.cost_of_goods = 0
            project.own_works_fot = 0
            project.third_party_works = 0
            project.awards_on_results_project = 0
            project.transportation_expenses = 0
            project.travel_expenses = 0
            project.representation_expenses = 0
            project.warranty_service_costs = 0
            project.rko_other = 0
            project.other_expenses = 0
            for step in project.step_project_child_ids:
                if step.stage_id.code != '0':
                    project.total_amount_of_revenue += step.total_amount_of_revenue
                    project.cost_price += step.cost_price
                    project.taxes_fot_premiums += step.taxes_fot_premiums
                    project.revenue_from_the_sale_of_works += step.revenue_from_the_sale_of_works
                    project.revenue_from_the_sale_of_goods += step.revenue_from_the_sale_of_goods
                    project.cost_of_goods += step.cost_of_goods
                    project.own_works_fot += step.own_works_fot
                    project.third_party_works += step.third_party_works
                    project.awards_on_results_project += step.awards_on_results_project
                    project.transportation_expenses += step.transportation_expenses
                    project.travel_expenses += step.travel_expenses
                    project.representation_expenses += step.representation_expenses
                    project.warranty_service_costs += step.warranty_service_costs
                    project.rko_other += step.rko_other
                    project.other_expenses += step.other_expenses

    @api.depends('taxes_fot_premiums', "revenue_from_the_sale_of_works", 'revenue_from_the_sale_of_goods',
                 'cost_of_goods', 'own_works_fot', 'third_party_works', "awards_on_results_project",
                 'transportation_expenses', 'travel_expenses', 'representation_expenses', "warranty_service_costs",
                 'rko_other', 'other_expenses', 'signer_id','project_have_steps', 'amount_spec_ids',
                 "step_project_child_ids",)
    def _compute_spec_totals(self):
        for project in self.sorted(lambda p: p.step_status == 'project'):  # сначала этапы, потом проекты
            if project.company_id.use_financial_data:
                self._calculate_all_sums(project)

    def _inverse_spec_totals(self):
        pass

    # @api.onchange('project_office_id','project_status','currency_id','project_curator_id','key_account_manager_id',
    #               'industry_id','essence_project','end_presale_project_month','end_sale_project_month','vat_attribute_id','total_amount_of_revenue',
    #               'total_amount_of_revenue_with_vat','revenue_from_the_sale_of_works','revenue_from_the_sale_of_goods','cost_price','cost_of_goods','own_works_fot',
    #               'third_party_works','awards_on_results_project','transportation_expenses','travel_expenses','representation_expenses','taxes_fot_premiums','warranty_service_costs',
    #               'rko_other','other_expenses','margin_income','profitability','stage_id','signer_id','project_type_id','comments',
    #               'planned_cash_flow_sum','planned_cash_flow_ids','step_project_number','dogovor_number','planned_acceptance_flow_sum','planned_acceptance_flow_ids','fact_cash_flow_sum',
    #               'fact_cash_flow_ids','fact_acceptance_flow_sum','fact_acceptance_flow_ids','project_have_steps','step_project_child_ids'
    #             )
    # def _check_changes_project(self):
    #     for row in self:
    #         if not row.was_changes:
    #             try:
    #                 cur_idstr = str(row.id)
    #                 cur_idstr = cur_idstr.replace('NewId_','')
    #                 cur_id = int(cur_idstr)
    #                 curprj = self.env['project_budget.projects'].search([('id', '=', cur_id)],limit=1)
    #                 print(cur_id)
    #                 if curprj:
    #                     curprj.was_changes = True
    #             except: return False
    #         if not row.project_have_steps:
    #             if not row.project_type_id.is_revenue_from_the_sale_of_works: row.revenue_from_the_sale_of_works = 0
    #             if not row.project_type_id.is_revenue_from_the_sale_of_goods: row.revenue_from_the_sale_of_goods = 0
    #             if not row.project_type_id.is_cost_of_goods: row.cost_of_goods = 0
    #             if not row.project_type_id.is_own_works_fot: row.own_works_fot = 0
    #             if not row.project_type_id.is_third_party_works: row.third_party_works = 0
    #             if not row.project_type_id.is_awards_on_results_project: row.awards_on_results_project = 0
    #             if not row.project_type_id.is_transportation_expenses: row.transportation_expenses = 0
    #             if not row.project_type_id.is_travel_expenses: row.travel_expenses = 0
    #             if not row.project_type_id.is_representation_expenses: row.representation_expenses = 0
    #             if not row.project_type_id.is_warranty_service_costs: row.warranty_service_costs = 0
    #             if not row.project_type_id.is_rko_other: row.rko_other = 0
    #             if not row.project_type_id.is_other_expenses: row.other_expenses = 0
