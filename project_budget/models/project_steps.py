from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import pytz
from datetime import timedelta


#TODO: убрать все явные привязки к вероятности, объединить с projects???
class project_steps(models.Model):
    _name = 'project_budget.project_steps'
    _description = "project steps"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name_to_show'

    def _get_default_stage_id(self):
        return self.env['project_budget.projects'].browse(self.projects_id).stage_id

    def _get_current_amount_spec_type(self):
        context = self.env.context
        print('_get_current_amount_spec_type context',context)
        value = ''
        if context.get("revenue_from_the_sale_of_works") == True:
            value = _('revenue_from_the_sale_of_works')
        if context.get("revenue_from_the_sale_of_goods") == True:
            value =  _('revenue_from_the_sale_of_goods')
        if context.get("cost_of_goods") == True:
            value =  _('cost_of_goods')
        if context.get("travel_expenses") == True:
            value =  _('travel_expenses')
        if context.get("third_party_works") == True:
            value =  _('third_party_works')
        if context.get("representation_expenses") == True:
            value =  _('representation_expenses')
        if context.get("rko_other") == True:
            value =  _('rko_other')
        if context.get("warranty_service_costs") == True:
            value =  _('warranty_service_costs')
        if context.get("other_expenses") == True:
            value =  _('other_expenses')
        if context.get("transportation_expenses") == True:
            value =  _('transportation_expenses')
        print('_get_current_amount_spec_type value = ', value)
        self.current_amount_spec_type = value

    def _get_domainamount_spec(self):
        domain = []
        context = self.env.context
        if context.get("revenue_from_the_sale_of_works") == True:
            domain = [('type', '=', "revenue_from_the_sale_of_works")]
        if context.get("revenue_from_the_sale_of_goods") == True:
            domain = [('type', '=', "revenue_from_the_sale_of_goods")]
        if context.get("cost_of_goods") == True:
            domain = [('type', '=', "cost_of_goods")]
        if context.get("travel_expenses") == True:
            domain = [('type', '=', "travel_expenses")]
        if context.get("third_party_works") == True:
            domain = [('type', '=', "third_party_works")]
        if context.get("transportation_expenses") == True:
            domain = [('type', '=', "transportation_expenses")]
        if context.get("representation_expenses") == True:
            domain = [('type', '=', "representation_expenses")]
        if context.get("rko_other") == True:
            domain = [('type', '=', "rko_other")]
        if context.get("warranty_service_costs") == True:
            domain = [('type', '=', "warranty_service_costs")]
        if context.get("other_expenses") == True:
            domain = [('type', '=', "other_expenses")]
        return domain

    def _get_amount_spec_type(self, amount_spec_ids, type):
        for amount_spec in amount_spec_ids:
            if amount_spec.type == type: return True
        return False

    def _get_sums_from_amount_spec_type(self, row, type):
        sum = 0
        project_currency_rates = self.env['project_budget.project_currency_rates']
        for amount_spec in row.amount_spec_ids:
            # _rate_prj = self.env['res.currency']._get_conversion_rate(from_currency=amount_spec.currency_id,
            #                                               to_currency=row.currency_id, date=)
            if amount_spec.type == type:
                sum += amount_spec.summa * project_currency_rates._get_currency_rate_for_project_currency(row.projects_id, amount_spec.currency_id.id)
                       # *row.company_id.currency_id
        return sum

    def _compute_sums_from_amount_spec(self):
        for row in self:
            print('project_steps _compute_sums_from_amount_spec row=',row)
            print('project_steps _compute_sums_from_amount_spec row.revenue_from_the_sale_of_works_amount_spec_exist = ', row.revenue_from_the_sale_of_works_amount_spec_exist)
            if row.revenue_from_the_sale_of_works_amount_spec_exist == True:
                row.revenue_from_the_sale_of_works = self._get_sums_from_amount_spec_type(row, 'revenue_from_the_sale_of_works')
            if row.revenue_from_the_sale_of_goods_amount_spec_exist == True:
                row.revenue_from_the_sale_of_goods = self._get_sums_from_amount_spec_type(row, 'revenue_from_the_sale_of_goods')
            if row.cost_of_goods_amount_spec_exist == True:
                row.cost_of_goods = self._get_sums_from_amount_spec_type(row, 'cost_of_goods')
            if row.travel_expenses_amount_spec_exist == True:
                row.travel_expenses = self._get_sums_from_amount_spec_type(row, 'travel_expenses')
            if row.third_party_works_amount_spec_exist == True:
                row.third_party_works = self._get_sums_from_amount_spec_type(row, 'third_party_works')
            if row.transportation_expenses_amount_spec_exist == True:
                row.transportation_expenses = self._get_sums_from_amount_spec_type(row, 'transportation_expenses')
            if row.representation_expenses_amount_spec_exist == True:
                row.representation_expenses = self._get_sums_from_amount_spec_type(row, 'representation_expenses')
            if row.rko_other_amount_spec_exist == True:
                row.rko_other = self._get_sums_from_amount_spec_type(row, 'rko_other')
            if row.warranty_service_costs_amount_spec_exist == True:
                row.warranty_service_costs = self._get_sums_from_amount_spec_type(row, 'warranty_service_costs')
            if row.other_expenses_amount_spec_exist == True:
                row.other_expenses = self._get_sums_from_amount_spec_type(row, 'other_expenses')


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

    name_to_show = fields.Char(string = 'name_to_show', compute = '_get_name_to_show')
    projects_id = fields.Many2one('project_budget.projects', string='projects_id', index=True, ondelete='cascade')
    different_project_offices_in_steps = fields.Boolean(related='projects_id.legal_entity_signing_id.different_project_offices_in_steps', readonly=True)
    etalon_budget = fields.Boolean(related='projects_id.etalon_budget', readonly=True)
    date_actual = fields.Datetime(related='projects_id.date_actual', readonly=True, store=True)
    budget_state = fields.Selection(related='projects_id.budget_state', readonly=True, store=True)
    approve_state = fields.Selection(related='projects_id.approve_state', readonly=True, store=True)
    can_edit = fields.Boolean(related='projects_id.can_edit')
    # name = fields.Char(string="step name", required=True, copy=True)
    code = fields.Char(string="step code", copy=True)
    essence_project = fields.Text(string='essence_project', default = "")
    step_id = fields.Char(string="step_id", required=True, copy=True, default = '-',index=True)
    # date_step = fields.Date(string="step date" , required=True, copy=True)
    # sum_without_vat = fields.Monetary(string="sum without vat", required=True, copy=True)
    # sum_with_vat = fields.Monetary(string="sum_with_vat", compute='_compute_sum', readonly=True)
    # margin_income = fields.Monetary(string="margin", required=True, copy=True)
    dogovor_number = fields.Char(string='Dogovor number', store=True, tracking=True)
    stage_id = fields.Many2one('project_budget.project.stage', string='Stage', copy=True, default=_get_default_stage_id,
                               required=True, tracking=True)
    currency_id = fields.Many2one('res.currency', string='Account Currency', related='projects_id.currency_id', readonly=True)
    project_steps_type_id = fields.Many2one('project_budget.project_steps_type', string='project steps type', required=True, copy=True)
    # TODO: необходимо убрать домен и перейти на стандартное поле active
    project_office_id = fields.Many2one('project_budget.project_office', string='Project Office', copy=True,
                                        domain="[('is_prohibit_selection','=', False)]", tracking=True)

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

    # vat_attribute_id = fields.Many2one('project_budget.vat_attribute', string='vat_attribute', copy=True, required=True
    #                                     ,default = lambda self: self.env['project_budget.vat_attribute'].search([],limit=1))
    vat_attribute_id = fields.Many2one('project_budget.vat_attribute', string='vat_attribute', copy=True, required=True, domain ="[('is_prohibit_selection','=', False)]")
                                       # default = lambda self: self.env['project_budget.vat_attribute'].search([],limit=1))

    # profitability = fields.Float(string="profitability", compute='_compute_sum', readonly=True)
    end_presale_project_quarter = fields.Char(string='End date of the Presale project(quarter)',
                                              compute='_compute_quarter', store=True, tracking=True)
    end_presale_project_month = fields.Date(string='Date of transition to the Production Budget(MONTH)', required=True,
                                            default=fields.Date.context_today, tracking=True)
    end_sale_project_quarter = fields.Char(string='End date of the Sale project(quarter)', compute='_compute_quarter',
                                           store=True, tracking=True)
    end_sale_project_month = fields.Date(string='The period of shipment or provision of services to the Client(MONTH)',
                                         required=True, default=fields.Date.context_today, tracking=True)

    total_amount_of_revenue = fields.Monetary(string='total_amount_of_revenue', compute='_compute_spec_totals',
                                              store=True, tracking=True)
    total_amount_of_revenue_with_vat = fields.Monetary(string='total_amount_of_revenue_with_vat',compute='_compute_spec_totals',
                                                       store=True, tracking=True)
    revenue_from_the_sale_of_works = fields.Monetary(string='revenue_from_the_sale_of_works(services)')
    revenue_from_the_sale_of_goods = fields.Monetary(string='revenue_from the sale of goods')
    cost_price = fields.Monetary(string='cost_price', compute='_compute_spec_totals', store=True, tracking=True)
    cost_of_goods = fields.Monetary(string='cost_of_goods')
    own_works_fot = fields.Monetary(string='own_works_fot')
    third_party_works = fields.Monetary(string='third_party_works(subcontracting)')
    awards_on_results_project = fields.Monetary(string='Awards based on the results of the project')
    transportation_expenses = fields.Monetary(string='transportation_expenses')
    travel_expenses = fields.Monetary(string='travel_expenses')
    representation_expenses = fields.Monetary(string='representation_expenses')

    taxes_fot_premiums = fields.Monetary(string='taxes_FOT and premiums',  store=True,
                                         tracking=True)
    warranty_service_costs = fields.Monetary(string='Warranty service costs')
    rko_other = fields.Monetary(string='rko_other')
    other_expenses = fields.Monetary(string='other_expenses')
    margin_income = fields.Monetary(string='Margin income', compute='_compute_spec_totals', store=True)
    profitability = fields.Float(string='Profitability(share of Sale margin in revenue)',
                                 compute='_compute_spec_totals', store=True, tracking=True)

    was_changes = fields.Boolean(string="was_changes", copy=True, default=True)

    current_amount_spec_type = fields.Char(string= "current amount spec type", compute="_get_current_amount_spec_type")

    @api.onchange('currency_id','essence_project','end_presale_project_month','end_sale_project_month','vat_attribute_id','total_amount_of_revenue',
                  'total_amount_of_revenue_with_vat','revenue_from_the_sale_of_works','revenue_from_the_sale_of_goods','cost_price','cost_of_goods','own_works_fot',
                  'third_party_works','awards_on_results_project','transportation_expenses','travel_expenses','representation_expenses','taxes_fot_premiums','warranty_service_costs',
                  'rko_other','other_expenses','margin_income','profitability','stage_id','legal_entity_signing_id','project_steps_type_id',
                  'code','dogovor_number','amount_spec_ids'
                )
    def _check_changes_step(self):
        print('_check_changes_step')
        for row in self:
            print('_check_changes_step = ', row.id)
            self._compute_sums_from_amount_spec()
            if row.project_steps_type_id.is_revenue_from_the_sale_of_works == False: row.revenue_from_the_sale_of_works = 0
            if row.project_steps_type_id.is_revenue_from_the_sale_of_goods == False: row.revenue_from_the_sale_of_goods = 0
            if row.project_steps_type_id.is_cost_of_goods == False: row.cost_of_goods = 0
            if row.project_steps_type_id.is_own_works_fot == False: row.own_works_fot = 0
            if row.project_steps_type_id.is_third_party_works == False: row.third_party_works = 0
            if row.project_steps_type_id.is_awards_on_results_project == False: row.awards_on_results_project = 0
            if row.project_steps_type_id.is_transportation_expenses == False: row.transportation_expenses = 0
            if row.project_steps_type_id.is_travel_expenses== False: row.travel_expenses = 0
            if row.project_steps_type_id.is_representation_expenses== False: row.representation_expenses = 0
            if row.project_steps_type_id.is_warranty_service_costs == False: row.warranty_service_costs = 0
            if row.project_steps_type_id.is_rko_other == False: row.rko_other = 0
            if row.project_steps_type_id.is_other_expenses== False: row.other_expenses = 0

    @api.constrains('stage_id', 'total_amount_of_revenue', 'cost_price')
    def _check_financial_data_is_present(self):
        for step in self:
            if (step.stage_id.code in ('30', '50', '75', '100')
                    and step.total_amount_of_revenue == 0
                    and step.cost_price == 0
                    and step.projects_id.budget_state == 'work'
                    and not step.projects_id.is_correction_project):
                raisetext = _("Please enter financial data to project {0} step {1}")
                raisetext = raisetext.format(step.projects_id.project_id, step.step_id)
                raise ValidationError(raisetext)

    @api.constrains('stage_id', 'code')
    def _check_step_axapta_code(self):
        for step in self:
            if (step.stage_id.name in ('75', '100')
                    and not step.code
                    and step.projects_id.budget_state == 'work'
                    and not step.projects_id.is_correction_project):  # Проект без кода этапа из AXAPTA
                raisetext = _("Please enter AXAPTA code to project {0} step {1}")
                raisetext = raisetext.format(step.projects_id.project_id, step.step_id)
                raise ValidationError(raisetext)

    @api.depends("planned_cash_flow_ids.sum_cash")
    def _compute_planned_cash_flow_sum(self):
        for row in self:
            row.planned_cash_flow_sum = 0
            for row_flow in row.planned_cash_flow_ids:
                row.planned_cash_flow_sum = row.planned_cash_flow_sum + row_flow.sum_cash

    @api.depends("planned_acceptance_flow_ids.sum_cash")
    def _compute_planned_acceptance_flow_sum(self):
        for row in self:
            row.planned_acceptance_flow_sum_without_vat = 0
            for row_flow in row.planned_acceptance_flow_ids:
                row.planned_acceptance_flow_sum_without_vat += row_flow.sum_cash_without_vat

    @api.depends('essence_project', 'step_id')
    def _get_name_to_show(self):
        for step in self:
            step.name_to_show = step.step_id + '|' + (step.code or '') + '| ' + step.essence_project

    @api.depends("revenue_from_the_sale_of_works", 'revenue_from_the_sale_of_goods', 'cost_of_goods', 'own_works_fot',
                 'third_party_works', "awards_on_results_project", 'transportation_expenses', 'travel_expenses',
                 'representation_expenses',"warranty_service_costs", 'rko_other', 'other_expenses', 'vat_attribute_id',
                 'projects_id.legal_entity_signing_id', 'taxes_fot_premiums')
    def _compute_spec_totals(self):
        for budget_spec in self:
            self._compute_sums_from_amount_spec()
            budget_spec.total_amount_of_revenue = budget_spec.revenue_from_the_sale_of_works + budget_spec.revenue_from_the_sale_of_goods

            budget_spec.cost_price = budget_spec.cost_of_goods + budget_spec.own_works_fot + budget_spec.third_party_works + budget_spec.awards_on_results_project
            budget_spec.cost_price = budget_spec.cost_price + budget_spec.transportation_expenses + budget_spec.travel_expenses + budget_spec.representation_expenses
            budget_spec.cost_price = budget_spec.cost_price + budget_spec.warranty_service_costs + budget_spec.rko_other + budget_spec.other_expenses
            if budget_spec.is_percent_fot_manual == False:
                budget_spec.taxes_fot_premiums = (budget_spec.awards_on_results_project + budget_spec.own_works_fot) * budget_spec.projects_id.legal_entity_signing_id.percent_fot / 100
            budget_spec.cost_price = budget_spec.cost_price + budget_spec.taxes_fot_premiums

            budget_spec.margin_income = budget_spec.total_amount_of_revenue - budget_spec.cost_price

            budget_spec.total_amount_of_revenue_with_vat = (budget_spec.revenue_from_the_sale_of_works + budget_spec.revenue_from_the_sale_of_goods) * (1 + budget_spec.vat_attribute_id.percent / 100)

            if budget_spec.total_amount_of_revenue == 0:
                budget_spec.profitability = 0
            else:
                budget_spec.profitability = budget_spec.margin_income / budget_spec.total_amount_of_revenue * 100

    @api.depends('end_presale_project_month','end_sale_project_month')
    def _compute_quarter(self):
        for fieldquarter in self:
            if fieldquarter.end_presale_project_month == False:
                continue
            tmp_date = fieldquarter.end_presale_project_month
            month = tmp_date.month
            year = tmp_date.year
            if 0 <= int(month) <= 3:
                fieldquarter.end_presale_project_quarter = 'Q1 ' + str(year)
            elif 4 <= int(month) <= 6:
                fieldquarter.end_presale_project_quarter = 'Q2 ' + str(year)
            elif 7 <= int(month) <= 9:
                fieldquarter.end_presale_project_quarter = 'Q3 ' + str(year)
            elif 10 <= int(month) <= 12:
                fieldquarter.end_presale_project_quarter = 'Q4 ' + str(year)
            else:
                fieldquarter.end_presale_project_quarter = 'NA'
            tmp_date = fieldquarter.end_sale_project_month
            month = tmp_date.month
            year = tmp_date.year
            if 0 <= int(month) <= 3:
                fieldquarter.end_sale_project_quarter = 'Q1 ' + str(year)
            elif 4 <= int(month) <= 6:
                fieldquarter.end_sale_project_quarter = 'Q2 ' + str(year)
            elif 7 <= int(month) <= 9:
                fieldquarter.end_sale_project_quarter = 'Q3 ' + str(year)
            elif 10 <= int(month) <= 12:
                fieldquarter.end_sale_project_quarter = 'Q4 ' + str(year)
            else:
                fieldquarter.end_sale_project_quarter = 'NA'

    @api.model_create_multi
    def create(self, vals_list):
        print('---****-----STEPS CREATE', self.env.context)
        for vals in vals_list:
            if not vals.get('step_id') or vals['step_id'] == '-':
                vals['step_id'] = self.env['ir.sequence'].sudo().next_by_code('project_budget.project_steps')
            if self.env.context.get('form_fix_budget'):
                f = 1
            else:
                vals['step_id'] = self.env['ir.sequence'].sudo().next_by_code('project_budget.project_steps')
        return super().create(vals_list)

    def unlink(self):
        """
        need check exists  step in etalon budget and

        """
        print('unlink ')
        for record in self:
            print('record = ', record)
            print('record.step_id = ',record.step_id)
            print('record.id = ',record.id)
            if record.approve_state != 'need_approve_manager' :
                raisetext = _("only in state 'need approve manager' project can be deleted")
                raise ValidationError(raisetext)

            if record.budget_state == 'fixed' :
                raisetext = _("only in 'Working' budget project step can be deleted")
                raise ValidationError(raisetext)

            fact_cash_flow = self.env['project_budget.project_steps'].search([('step_id', '=', record.step_id),('id','!=',record.id)], limit =1)
            if fact_cash_flow:
                raisetext = _("step exist in another version of budget")
                raise ValidationError(raisetext)


            fact_cash_flow = self.env['project_budget.fact_cash_flow'].search([('project_steps_id', '=', record.id)], limit =1)
            if fact_cash_flow:
                raisetext = _("fact_cash_flow exist with this step")
                raise ValidationError(raisetext)

            planned_cash_flow = self.env['project_budget.planned_cash_flow'].search([('project_steps_id', '=', record.id)], limit =1)
            if planned_cash_flow:
                raisetext = _("planned_cash_flow exist with this step")
                raise ValidationError(raisetext)

            planned_acceptance_flow = self.env['project_budget.planned_acceptance_flow'].search([('project_steps_id', '=', record.id)], limit =1)
            if planned_acceptance_flow:
                raisetext = _("planned_acceptance_flow exist with this step")
                raise ValidationError(raisetext)

            fact_acceptance_flow = self.env['project_budget.fact_acceptance_flow'].search([('project_steps_id', '=', record.id)], limit =1)
            if fact_acceptance_flow:
                raisetext = _("fact_acceptance_flow exist with this step")
                raise ValidationError(raisetext)

        return super().unlink()

    @api.model
    def get_data_dashboard_1(self):
        print('get_data_dashboard_1')
        """Returns data to the tiles of dashboard"""
        etalon_projects = self.env['project_budget.projects'].search([('etalon_budget', '=', True),('budget_state','=','fixed')])
        current_projects = self.env['project_budget.projects'].search([('etalon_budget', '=', False), ('budget_state', '=', 'work')])
        print('len(etalon_projects) = ', len(etalon_projects))
        print('len(current_projects) = ', len(current_projects))
        return {
            'etalon_projects': len(etalon_projects),
            'current_projects': len(current_projects),
        }

    def action_copy_step(self):
        self.ensure_one()
        if self.projects_id.date_actual:  # сделка в зафиксированном бюджете
            raisetext = _("This project is in fixed budget. Copy deny")
            raise (ValidationError(raisetext))
        self.env['project_budget.project_steps'].sudo().browse(self.id).copy({'step_id': '-'})
