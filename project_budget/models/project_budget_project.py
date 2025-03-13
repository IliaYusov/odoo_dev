from odoo import api, Command, fields, models, _
from odoo.exceptions import ValidationError
from .project_budget_project_stage import PROJECT_STATUS
from collections import defaultdict
import datetime


# TODO: необходимо убрать явные привязки из кода к вероятности
class Project(models.Model):
    _name = 'project_budget.projects'
    _description = 'Project'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name_to_show'
    _check_company_auto = True
    _rec_names_search = ['project_id', 'essence_project']

    STEP_STATUS = [('project', 'project'), ('step', 'step')]

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        return self.env['project_budget.project.stage'].search([], order=order)
       
    def _get_signer_id_domain(self):
        return [('id', 'in', self.env['res.company'].sudo().search([]).partner_id.ids)]

    def _get_default_stage_id(self):
        return self.env['project_budget.project.stage'].search([
            ('fold', '=', False),
            '|', ('company_ids', '=', False), ('company_ids', 'in', [self.env.company.id])
        ], limit=1)

    def _get_default_key_account_manager_id(self):
        employee = self._get_current_employee()
        return employee.id if employee.user_id.has_group(
            'project_budget.project_budget_group_key_account_manager') else False

    def _get_key_account_manager_id_domain(self):
        return "[('user_id.groups_id', 'in', %s), '|', ('company_id', '=', False), ('company_id', '=', company_id)]" \
            % self.env.ref('project_budget.project_budget_group_key_account_manager').id

    def _get_project_manager_id_domain(self):
        return "[('user_id.groups_id', 'in', %s), '|', ('company_id', '=', False), ('company_id', '=', company_id)]" \
            % self.env.ref('project_budget.project_budget_group_project_manager').id

    def _get_project_curator_id_domain(self):
        return "[('user_id.groups_id', 'in', %s), '|', ('company_id', '=', False), ('company_id', '=', company_id)]" \
            % self.env.ref('project_budget.project_budget_group_project_curator').id

    # def _get_supervisor_list(self):  # TODO убрать после миграции на кураторов
    #     domain = []
    #     supervisor_access = self.env['project_budget.project_supervisor_access'].search([('user_id.id', '=', self.env.user.id)])
    #     supervisor_list = []
    #     for each in supervisor_access:
    #         supervisor_list.append(each.project_supervisor_id.id)
    #     if supervisor_list:
    #         domain = [('id', 'in', supervisor_list)]
    #         return domain
    #     return domain


    def _get_commercial_budget_list(self):
        domain = [('id', 'in','-1')]
        commercial_budget = self.env['project_budget.commercial_budget'].search([('budget_state', '=', 'work')])
        commercial_budget_list = []
        for each in commercial_budget:
            commercial_budget_list.append(each.id)
        if commercial_budget_list:
            domain = [('id', 'in', commercial_budget_list)]
            return domain
        return domain

    active = fields.Boolean('Active', default=True, tracking=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    project_id = fields.Char(string='Project_ID', copy=True, default='ID', group_operator='count', index=True,
                             required=True)
    stage_id = fields.Many2one('project_budget.project.stage', string='Stage', copy=True, default=_get_default_stage_id,
                               domain="['|', ('company_ids', '=', False), ('company_ids', 'in', company_id)]",
                               group_expand='_read_group_stage_ids', index=True, ondelete='restrict', required=True,
                               tracking=True)
    project_status = fields.Selection(selection=PROJECT_STATUS, string='Project Status',
                                      compute='_compute_project_status', index=True, readonly=True, tracking=True,
                                      store=True)
    color = fields.Integer(related='stage_id.color', readonly=True)
    approve_state = fields.Selection([('need_approve_manager', 'need managers approve'), ('need_approve_supervisor'
                                     , 'need supervisors approve'), ('approved','approved'),('-','-')],
                                     required=True, index=True, default='need_approve_manager', store=True, copy=True, tracking=True)
    currency_id = fields.Many2one('res.currency', string='Account Currency', copy=True,
                                  default=lambda self: self.env.company.currency_id, required=True, tracking=True)
    etalon_budget = fields.Boolean(related='commercial_budget_id.etalon_budget', readonly=True)
    date_actual = fields.Datetime(related='commercial_budget_id.date_actual', readonly=True, store=True)
    isRukovoditel_required_in_project = fields.Boolean(related='project_office_id.isRukovoditel_required_in_project', readonly=True, store=True)
    commercial_budget_id = fields.Many2one('project_budget.commercial_budget', string='commercial_budget-',required=True, ondelete='cascade', index=True, copy=False
                                           ,default=lambda self: self.env['project_budget.commercial_budget'].search([('budget_state', '=', 'work')], limit=1)
                                           , domain=_get_commercial_budget_list)
    was_changes = fields.Boolean(string="was_changes", copy=True, default = True)
    vgo = fields.Selection([('-', '-'), ('vgo1', 'vgo1'),('vgo2', 'vgo2')], required=True, default='-', copy = True,tracking=True)

    # budget_state = fields.Selection([('work', 'Working'), ('fixed', 'Fixed')], required=True, index=True, default='work', copy = False,
    #                                 compute='_compute_reference', store=True, tracking=True)

    budget_state = fields.Selection(related='commercial_budget_id.budget_state', index=True, readonly=True, store=True)
    # project_supervisor_id = fields.Many2one('project_budget.project_supervisor', string='project_supervisor',
    #                                         required=True, copy=True, domain=_get_supervisor_list, tracking=True, check_company=True)
    project_supervisor_id = fields.Many2one('project_budget.project_supervisor', string='Project Supervisor',
                                            copy=True, domain="[('company_id', 'in', (False, company_id))]",
                                            store=True, tracking=True)  # TODO убрать после миграции на кураторов
    project_curator_id = fields.Many2one('hr.employee', string='Project Curator',
                                             compute='_compute_project_curator_id',
                                             inverse='_inverse_project_curator_id', copy=True, required=True,
                                             domain="[('company_id', 'in', (False, company_id))]",
                                             store=True, tracking=True)
    key_account_manager_id = fields.Many2one('hr.employee', string='Key Account Manager',
                                             compute='_compute_key_account_manager_id',
                                             inverse='_inverse_key_account_manager_id', copy=True,
                                             default=_get_default_key_account_manager_id,
                                             domain=_get_key_account_manager_id_domain, required=True, store=True,
                                             tracking=True)
    project_manager_id = fields.Many2one('hr.employee', string='Project Manager', compute='_compute_project_manager_id',
                                         inverse='_inverse_project_manager_id', copy=True,
                                         domain=_get_project_manager_id_domain, required=False, store=True,
                                         tracking=True)
    project_curator_id = fields.Many2one('hr.employee', string='Project Curator', copy=True,
                                         domain=_get_project_curator_id_domain, required=True, tracking=True)
    responsibility_center_id = fields.Many2one('account.analytic.account', string='Responsibility Center', copy=True,
                                               depends=['key_account_manager_id'], required=True, tracking=True)
    responsibility_center_id_domain = fields.Binary(compute='_compute_responsibility_center_id_domain')
    # TODO: необходимо мигрировать на поле responsibility_center_id
    project_office_id = fields.Many2one('project_budget.project_office', string='Project Office', copy=True,
                                        depends=['key_account_manager_id'], required=False, tracking=True)
    project_office_id_domain = fields.Binary(compute='_compute_project_office_id_domain')
    project_member_ids = fields.One2many('project_budget.project.member', 'project_id', string='Members', copy=False)
    partner_id = fields.Many2one('res.partner', string='Customer', copy=True,
                                 domain="[('is_company', '=', True)]", ondelete='restrict', required=True,
                                 tracking=True)
    industry_id = fields.Many2one('project_budget.industry', string='industry', required=True, copy=True,tracking=True)
    essence_project = fields.Text(string='essence_project', default = "",tracking=True)
    end_presale_project_quarter = fields.Char(string='End date of the Presale project(quarter)', compute='_compute_quarter', store=True, tracking=True)
    end_presale_project_month = fields.Date(string='Date of transition to the Production Budget(MONTH)', required=True, default=fields.Date.context_today, tracking=True)
    end_sale_project_quarter = fields.Char(string='End date of the Sale project(quarter)', compute='_compute_quarter', store=True, tracking=True)
    end_sale_project_month = fields.Date(string='The period of shipment or provision of services to the Client(MONTH)', required=True,default=fields.Date.context_today, tracking=True)
    vat_attribute_id = fields.Many2one('project_budget.vat_attribute', string='vat_attribute', copy=True,tracking=True , domain ="[('is_prohibit_selection','=', False)]")

    total_amount_of_revenue = fields.Monetary(string='total_amount_of_revenue', compute='_compute_spec_totals', store=True, tracking=True)
    total_amount_of_revenue_with_vat = fields.Monetary(string='total_amount_of_revenue_with_vat', compute='_compute_spec_totals',
                                              store=True, tracking=True)
    cost_price = fields.Monetary(string='cost_price', compute='_compute_spec_totals', store=True, tracking=True)
    margin_income = fields.Monetary(string='Margin income', compute='_compute_spec_totals', store=True)
    profitability = fields.Float(string='Profitability(share of Sale margin in revenue)', compute='_compute_spec_totals', store=True, tracking=True)

    signer_id = fields.Many2one('res.partner', string='Signer', copy=True,
                                default=lambda self: self.env.company.partner_id, domain=_get_signer_id_domain,
                                required=True, tracking=True)
    comments = fields.Text(string='comments project', default="")
    step_project_number = fields.Char(string='step project number', store=True, tracking=True)  # номер из AXAPTA
    dogovor_number = fields.Char(string='Dogovor number', store=True, tracking=True)

    planned_cash_flow_sum = fields.Monetary(string='planned_cash_flow_sum', compute='_compute_planned_cash_flow_sum',
                                            store=False, tracking=True)
    planned_cash_flow_ids = fields.One2many(
        comodel_name='project_budget.planned_cash_flow',
        inverse_name='projects_id',
        string="planned cash flow", auto_join=True, copy=False
    )

    planned_acceptance_flow_sum = fields.Monetary(string='planned_acceptance_flow_sum',
                                                  compute='_compute_planned_acceptance_flow_sum', store=False,
                                                  tracking=True)
    planned_acceptance_flow_sum_without_vat = fields.Monetary(
        string='planned_acceptance_flow_sum_without_vat',
        compute='_compute_planned_acceptance_flow_sum', store=False, tracking=True
    )
    planned_acceptance_flow_ids = fields.One2many(
        comodel_name='project_budget.planned_acceptance_flow',
        inverse_name='projects_id',
        string="planned acceptance flow", auto_join=True, copy=False
    )

    fact_cash_flow_sum = fields.Monetary(string='fact_cash_flow_sum', compute='_compute_fact_cash_flow_sum', store=False
                                         , tracking=True)
    fact_cash_flow_ids = fields.One2many(
        comodel_name='project_budget.fact_cash_flow',
        inverse_name='projects_id',
        string="fact cash flow", auto_join=True, copy=False
    )

    fact_acceptance_flow_sum = fields.Monetary(string='fact_acceptance_flow_sum',
                                               compute='_compute_fact_acceptance_flow_sum',
                                               store=False, tracking=True)
    fact_acceptance_flow_sum_without_vat = fields.Monetary(
        string='fact_acceptance_flow_sum_without_vat',
        compute='_compute_fact_acceptance_flow_sum', store=False, tracking=True
    )
    fact_acceptance_flow_ids = fields.One2many(
        comodel_name='project_budget.fact_acceptance_flow',
        inverse_name='projects_id',
        string="fact acceptance flow", auto_join=True, copy=False
    )

    step_status = fields.Selection(selection=STEP_STATUS, string="project is step-project", default='project',
                                   copy=True, tracking=True, index=True)

    step_project_parent_id = fields.Many2one('project_budget.projects', default=False, string='step-project parent id',
                                             ondelete='cascade', copy=True, index=True)
    step_project_child_ids = fields.One2many(comodel_name='project_budget.projects',
                                             inverse_name='step_project_parent_id',
                                             string="step-project child ids", compute='_compute_step_project_details',
                                             copy=False, store=True, auto_join=True)

    planned_step_cash_flow_ids = fields.One2many(
        comodel_name='project_budget.planned_cash_flow',
        inverse_name='step_project_child_id',
        string="planned cash flow", auto_join=True
    )
    planned_step_acceptance_flow_ids = fields.One2many(
        comodel_name='project_budget.planned_acceptance_flow',
        inverse_name='step_project_child_id',
        string="planned acceptance flow", auto_join=True
    )
    fact_step_cash_flow_ids = fields.One2many(
        comodel_name='project_budget.fact_cash_flow',
        inverse_name='step_project_child_id',
        string="fact cash flow", auto_join=True
    )
    fact_step_acceptance_flow_ids = fields.One2many(
        comodel_name='project_budget.fact_acceptance_flow',
        inverse_name='step_project_child_id',
        string="fact acceptance flow", auto_join=True
    )
    project_have_steps = fields.Boolean(string="project have steps", default=False, copy=True, tracking=True)
    is_framework = fields.Boolean(string="project is framework", default=False, copy=True, tracking=True)

    different_project_offices_in_steps = fields.Boolean(compute='_get_signer_settings', readonly=True)

    project_currency_rates_ids = fields.One2many(
        comodel_name='project_budget.project_currency_rates',
        inverse_name='projects_id',
        string="project currency rates", auto_join=True, copy=True, )

    name_to_show = fields.Char(string='name_to_show', compute='_get_name_to_show')

    attachment_count = fields.Integer(compute='_compute_attachment_count', string='Attachments')

    tenders_count = fields.Integer(compute='_compute_tenders_count', string='Tenders')

    parent_id = fields.Many2one('project_budget.projects', string='Parent Project', copy=False, index=True,
                                ondelete='cascade', tracking=True)
    child_ids = fields.One2many('project_budget.projects', 'parent_id', string='Child Projects', copy=False)
    child_count = fields.Integer(compute='_compute_child_count', string='Child Count')

    company_partner_id = fields.Many2one('res.company.partner', string='Company Partner', copy=True, check_company=True,
                                         domain="[('company_id', '=', company_id)]", ondelete='restrict')
    lost_reason_id = fields.Many2one('crm.lost.reason', string='Lost Reason', index=True, ondelete='restrict',
                                     tracking=True)
    can_edit = fields.Boolean(compute='_compute_can_edit', default=True)

    # ------------------------------------------------------
    # SETTINGS
    # ------------------------------------------------------

    is_correction_project = fields.Boolean(string="project for corrections", default=False)
    is_not_for_mc_report = fields.Boolean(string="project is not for MC report", default=False)

    # ------------------------------------------------------
    # CONSTRAINS
    # ------------------------------------------------------

    @api.constrains('project_member_ids')
    def _check_project_member_ids(self):
        required_members = self.env['project_budget.project.role'].search([
            ('is_required', '=', True)
        ])
        for record in self.filtered(lambda pr: pr.step_status == 'project'):
            diff = set(required_members) - set(record.project_member_ids.mapped('role_id'))
            if self.env.ref(
                    'project_budget.project_role_key_account_manager') in diff and record.key_account_manager_id:
                diff.remove(self.env.ref('project_budget.project_role_key_account_manager'))
            if self.env.ref('project_budget.project_role_project_manager') in diff and record.project_manager_id:
                diff.remove(self.env.ref('project_budget.project_role_project_manager'))
            if self.env.ref('project_budget.project_role_project_curator') in diff and record.project_curator_id:
                diff.remove(self.env.ref('project_budget.project_role_project_curator'))
            if diff:
                raise ValidationError(_("Roles '%s' are required for the project!") % ', '.join([r.name for r in diff]))

    @api.constrains('stage_id', 'company_id')
    def _check_company_id(self):
        for rec in self.filtered(lambda pr: pr.step_status == 'project' and pr.budget_state == 'work'):
            if rec.stage_id.company_ids and rec.company_id.id not in rec.stage_id.company_ids.ids:
                raise ValidationError(_('The selected stage belongs to another company than the project.'))

    # ------------------------------------------------------
    # COMPUTE METHODS
    # ------------------------------------------------------

    def _compute_can_edit(self):
        for rec in self:
            rec.can_edit = rec.active and (
                (rec.approve_state == 'need_approve_manager' and rec.budget_state != 'fixed') or (
                    self.env.user.has_group(
                        'project_budget.project_budget_group_project_fixed_editor') and rec.budget_state == 'fixed'))

    @api.depends('key_account_manager_id')
    def _compute_responsibility_center_id_domain(self):
        for rec in self:
            domain = [
                ('plan_id', 'child_of',
                 self.env.ref('analytic_responsibility_center.account_analytic_plan_responsibility_centers').id),
                '|', ('company_id', '=', False), ('company_id', '=', rec.company_id.id)
            ]
            responsibility_centers = self.env['account.analytic.account'].search([
                ('id', '=',
                    rec.key_account_manager_id.department_id.responsibility_center_id.id or 0)
            ])
            if responsibility_centers:
                domain = [
                    ('id', 'in', responsibility_centers.ids)
                ]
            rec.responsibility_center_id_domain = domain

    @api.depends('key_account_manager_id')
    def _compute_project_office_id_domain(self):
        for rec in self:
            domain = [
                ('is_prohibit_selection', '=', False),
                '|', ('company_id', '=', False), ('company_id', '=', rec.company_id.id)
            ]
            project_offices = self.env['project_budget.project_office'].search([
                ('responsibility_center_id', '=',
                 rec.key_account_manager_id.department_id.responsibility_center_id.id or 0)
            ])
            if project_offices:
                domain = [
                    ('id', 'in', project_offices.ids)
                ]
            rec.project_office_id_domain = domain

    def _compute_attachment_count(self):
        for rec in self:
            rec.attachment_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', self._name),
                ('res_id', '=', rec.id)
            ])

    def _compute_tenders_count(self):
        for project in self:
            project.tenders_count = self.env['project_budget.tenders'].search_count([
                ('projects_id', '=', project.id)
            ])

    @api.depends('project_id', 'step_project_number')
    def _get_name_to_show(self):
        for prj in self:
            name = (prj.project_id + '|' + (prj.step_project_number or '') + '|' + (prj.essence_project or ''))
            prj.name_to_show = name

    @api.depends('stage_id')
    def _compute_project_status(self):
        for rec in self:
            rec.project_status = rec.stage_id.project_status
            if rec.stage_id.code == '0':
                if rec.step_project_child_ids:
                    for step in rec.step_project_child_ids:
                        if step.stage_id.code in ('100', '100(done)'):
                            raise ValidationError(_("Can't 'cancel' project with step {0} in {1} state").format(
                                step.project_id, step.stage_id.code))
                        step.stage_id = rec.stage_id
            elif rec.stage_id.code == '100(done)':
                if rec.project_have_steps and rec.step_project_child_ids:
                    for step in rec.step_project_child_ids:
                        if step.stage_id.code != '0':
                            step.stage_id = rec.stage_id

    @api.depends('project_supervisor_id.user_id')
    def _get_supervisor_user_id(self):
        for row in self:
            row.project_supervisor_user_id = row.project_supervisor_id.user_id

    @api.depends("planned_cash_flow_ids.sum_cash")
    def _compute_planned_cash_flow_sum(self):
        for row in self:
            row.planned_cash_flow_sum = 0
            if row.step_status == 'project':
                for row_flow in row.planned_cash_flow_ids:
                    row.planned_cash_flow_sum = row.planned_cash_flow_sum + row_flow.sum_cash
            elif row.step_status == 'step':
                for row_flow in row.planned_step_cash_flow_ids:
                    row.planned_cash_flow_sum = row.planned_cash_flow_sum + row_flow.sum_cash


    @api.depends("planned_acceptance_flow_ids.sum_cash")
    def _compute_planned_acceptance_flow_sum(self):
        for row in self:
            row.planned_acceptance_flow_sum = 0
            row.planned_acceptance_flow_sum_without_vat = 0
            if row.step_status == 'project':
                for row_flow in row.planned_acceptance_flow_ids:
                    row.planned_acceptance_flow_sum += row_flow.sum_cash
                    row.planned_acceptance_flow_sum_without_vat += row_flow.sum_cash_without_vat
            elif row.step_status == 'step':
                for row_flow in row.planned_step_acceptance_flow_ids:
                    row.planned_acceptance_flow_sum += row_flow.sum_cash
                    row.planned_acceptance_flow_sum_without_vat += row_flow.sum_cash_without_vat

    @api.depends("fact_cash_flow_ids.sum_cash")
    def _compute_fact_cash_flow_sum(self):
        for row in self:
            row.fact_cash_flow_sum = 0
            if row.step_status == 'project':
                for row_flow in row.fact_cash_flow_ids:
                    row.fact_cash_flow_sum = row.fact_cash_flow_sum + row_flow.sum_cash
            elif row.step_status == 'step':
                for row_flow in row.fact_step_cash_flow_ids:
                    row.fact_cash_flow_sum = row.fact_cash_flow_sum + row_flow.sum_cash
    @api.depends("fact_acceptance_flow_ids.sum_cash")
    def _compute_fact_acceptance_flow_sum(self):
        for row in self:
            row.fact_acceptance_flow_sum = 0
            row.fact_acceptance_flow_sum_without_vat = 0
            if row.step_status == 'project':
                for row_flow in row.fact_acceptance_flow_ids:
                    row.fact_acceptance_flow_sum += row_flow.sum_cash
                    row.fact_acceptance_flow_sum_without_vat += row_flow.sum_cash_without_vat
            elif row.step_status == 'step':
                for row_flow in row.fact_step_acceptance_flow_ids:
                    row.fact_acceptance_flow_sum += row_flow.sum_cash
                    row.fact_acceptance_flow_sum_without_vat += row_flow.sum_cash_without_vat
    @api.depends('company_id', 'currency_id', 'commercial_budget_id', 'key_account_manager_id', 'project_curator_id',
                 'project_manager_id', 'industry_id', 'signer_id',
                 'partner_id', 'project_office_id', 'is_correction_project', 'is_not_for_mc_report',
                 'approve_state')
    def _compute_step_project_details(self):
        for row in self:
            if row.project_have_steps and row.step_project_child_ids:
                for step_project_child_id in row.step_project_child_ids:
                    step_project_child_id.company_id = row.company_id
                    step_project_child_id.currency_id = row.currency_id
                    step_project_child_id.commercial_budget_id = row.commercial_budget_id
                    step_project_child_id.key_account_manager_id = row.key_account_manager_id
                    step_project_child_id.project_curator_id = row.project_curator_id
                    step_project_child_id.project_manager_id = row.project_manager_id
                    step_project_child_id.industry_id = row.industry_id
                    step_project_child_id.signer_id = row.signer_id
                    step_project_child_id.partner_id = row.partner_id
                    step_project_child_id.approve_state = row.approve_state
                    if row.different_project_offices_in_steps:  # проверям меняли ли ПО в проекте-этапе
                        try:
                            cur_id = int(str(row.id).replace('NewId_', ''))
                            cur_office = self.env['project_budget.projects'].search([('id', '=', cur_id)], limit=1).project_office_id
                            if cur_office == step_project_child_id.project_office_id:
                                step_project_child_id.project_office_id = row.project_office_id
                        except:
                            pass
                    else:
                        step_project_child_id.project_office_id = row.project_office_id
                    step_project_child_id.is_correction_project = row.is_correction_project
                    step_project_child_id.is_not_for_mc_report = row.is_not_for_mc_report

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

    @api.depends('child_ids')
    def _compute_child_count(self):
        for project in self:
            project.child_count = len(project.child_ids)

    @api.depends('project_member_ids.role_id')
    def _compute_key_account_manager_id(self):
        for project in self:
            project.key_account_manager_id = project.project_member_ids.filtered(lambda t: t.role_id == self.env.ref(
                'project_budget.project_role_key_account_manager'))[:1].employee_id or False

    @api.onchange('key_account_manager_id')
    def _inverse_key_account_manager_id(self):
        for project in self.filtered(
                lambda pr: pr.step_status == 'project' and pr.budget_state == 'work' and pr.key_account_manager_id):
            member_team = self.project_member_ids.filtered(lambda t: t.role_id == self.env.ref(
                'project_budget.project_role_key_account_manager'))[:1]
            if member_team:
                member_team.employee_id = project.key_account_manager_id
            else:
                project.project_member_ids = [Command.create({
                    'role_id': self.env.ref('project_budget.project_role_key_account_manager').id,
                    'employee_id': project.key_account_manager_id.id
                })]

    @api.depends('project_member_ids.role_id')
    def _compute_project_manager_id(self):
        for project in self:
            project.project_manager_id = project.project_member_ids.filtered(lambda t: t.role_id == self.env.ref(
                'project_budget.project_role_project_manager'))[:1].employee_id or False

    @api.onchange('project_manager_id')
    def _inverse_project_manager_id(self):
        for project in self.filtered(
                lambda pr: pr.step_status == 'project' and pr.budget_state == 'work' and pr.project_manager_id):
            member_team = self.project_member_ids.filtered(lambda t: t.role_id == self.env.ref(
                'project_budget.project_role_project_manager'))[:1]
            if member_team:
                member_team.employee_id = project.project_manager_id
            else:
                project.project_member_ids = [Command.create({
                    'role_id': self.env.ref('project_budget.project_role_project_manager').id,
                    'employee_id': project.project_manager_id.id
                })]

    @api.depends('project_member_ids.role_id')
    def _compute_project_curator_id(self):
        for project in self:
            project.project_curator_id = project.project_member_ids.filtered(lambda t: t.role_id == self.env.ref(
                'project_budget.project_role_project_curator'))[:1].employee_id or False

    @api.onchange('project_curator_id')
    def _inverse_project_curator_id(self):
        for project in self.filtered(lambda pr: pr.budget_state == 'work' and pr.project_curator_id):
            member_team = self.project_member_ids.filtered(lambda t: t.role_id == self.env.ref(
                'project_budget.project_role_project_curator'))[:1]
            if member_team:
                member_team.employee_id = project.project_curator_id
            else:
                project.project_member_ids = [Command.create({
                    'role_id': self.env.ref('project_budget.project_role_project_curator').id,
                    'employee_id': project.project_curator_id.id
                })]

    # @api.depends('project_member_ids.role_id')
    # def _compute_project_supervisor_id(self): # TODO убрать после миграции на кураторов
    #     for project in self:
    #         curator = project.project_member_ids.filtered(lambda t: t.role_id == self.env.ref(
    #             'project_budget.project_role_project_curator'))[:1].employee_id
    #         project.project_supervisor_id = self.env['project_budget.project_supervisor'].search([
    #             ('user_id', '=', curator.user_id.id or 0),
    #             ('company_id', '=', project.company_id.id)
    #         ])[:1] or False
    #
    # def _inverse_project_supervisor_id(self): # TODO убрать после миграции на кураторов
    #     for project in self.filtered(lambda pr: pr.budget_state == 'work' and pr.project_supervisor_id):
    #         member_team = self.project_member_ids.filtered(lambda t: t.role_id == self.env.ref(
    #             'project_budget.project_role_project_curator'))[:1]
    #         if member_team:
    #             member_team.employee_id = self.env['hr.employee'].search([
    #                 ('user_id', '=', project.project_supervisor_id.user_id.id),
    #                 ('company_id', '=', project.company_id.id)
    #             ])[:1]
    #         else:
    #             project.project_member_ids = [Command.create({
    #                 'role_id': self.env.ref('project_budget.project_role_project_curator').id,
    #                 'employee_id': self.env['hr.employee'].search([
    #                     ('user_id', '=', project.project_supervisor_id.user_id.id),
    #                     ('company_id', '=', project.company_id.id)
    #                 ])[:1].id or 0
    #             })]

    @api.depends('signer_id')
    def _get_signer_settings(self):  # получаем настройки подписывающего юр лица из компании
        for record in self:
            company = self.env['res.company'].sudo().search([('partner_id', '=', record.signer_id.id)])
            record.different_project_offices_in_steps = company.different_project_offices_in_steps

    def action_open_project(self):
        return {
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'res_model': 'project_budget.projects',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'context': self._context,
            'flags': {'initial_mode': 'view'}
        }

    # def user_is_supervisor(self,supervisor_id):
    #     supervisor_access = self.env['project_budget.project_supervisor_access'].search([('user_id.id', '=', self.env.user.id)
    #                                                                                     ,('project_supervisor_id.id', '=', supervisor_id)
    #                                                                                     ,('can_approve_project','=',True)])
    #     if not supervisor_access :
    #         return False
    #     else: return True

    def user_is_curator(self, curator):
        if curator.user_id.user_has_groups('project_budget.group_project_budget_can_approve_projects'):
            return True
        curator_access = self.env['hr.employee.replacement'].search([
            ('replaceable_employee_id.user_id.id', '=', curator.user_id.id),
            ('replacement_employee_id.user_id.id', '=', self.env.user.id),
            ('date_start', '<=', fields.Date.today()),
            '|', ('date_end', '=', False), ('date_end', '>=', fields.Date.today()),
            ('replaceable_groups_ids', '=', self.env.ref('project_budget.group_project_budget_can_approve_projects').id)
        ])
        if curator_access :
            return True
        else:
            return False

    @api.constrains(
        'stage_id', 'planned_acceptance_flow_ids', 'planned_cash_flow_ids', 'planned_step_cash_flow_ids',
        'planned_step_acceptance_flow_ids',
        )
    def _check_allowed_forecast_stages(self):  # проверяем чтобы вероятности прогнозов были связаны с вероятностью проектов
        for project in self:
            if project.budget_state == 'work' and not project.is_correction_project:
                raisetext = ''
                if project.step_status == 'step':
                    accs_ids = project.planned_step_acceptance_flow_ids
                    cash_ids = project.planned_step_cash_flow_ids
                elif project.step_status == 'project':
                    accs_ids = project.planned_acceptance_flow_ids
                    cash_ids = project.planned_cash_flow_ids
                for acceptance in accs_ids:
                    if acceptance.forecast != 'from_project':
                        if project.stage_id.code == '100' and acceptance.forecast != 'commitment':
                            raisetext = _("Project\step is '100' acceptance {0} should be 'commitment' or 'from_project'")
                        elif project.stage_id.code == '75' and acceptance.forecast not in ('commitment', 'reserve'):
                            raisetext = _("Project\step is '75' acceptance {0} should be 'commitment', 'reserve' or 'from_project'")
                        elif project.stage_id.code == '50' and acceptance.forecast not in ('potential', 'reserve'):
                            raisetext = _("Project\step is '50' acceptance {0} should be 'potential', 'reserve' or 'from_project'")
                        elif project.stage_id.code in ('30', '10') and acceptance.forecast != 'potential':
                            raisetext = _("Project\step is '30' or '10' acceptance {0} should be 'potential' or 'from_project'")
                    if raisetext:
                        raisetext = raisetext.format(acceptance.acceptance_id)
                        raise ValidationError(raisetext)
                for cash in cash_ids:
                    if cash.forecast != 'from_project':
                        if project.stage_id.code == '100' and cash.forecast != 'commitment':
                            raisetext = _("Project\step is '100' cash {0} should be 'commitment' or 'from_project'")
                        elif project.stage_id.code == '75' and cash.forecast not in ('commitment', 'reserve'):
                            raisetext = _("Project\step is '75' cash {0} should be 'commitment', 'reserve' or 'from_project'")
                        elif project.stage_id.code == '50' and cash.forecast not in ('potential', 'reserve'):
                            raisetext = _("Project\step is '50' cash {0} should be 'potential', 'reserve' or 'from_project'")
                        elif project.stage_id.code in ('30', '10') and cash.forecast != 'potential':
                            raisetext = _("Project\step is '30' or '10' cash {0} should be 'potential' or 'from_project'")
                    if raisetext:
                        raisetext = raisetext.format(cash.cash_id)
                        raise ValidationError(raisetext)

    # ------------------------------------------------------
    # ONCHANGE METHODS
    # ------------------------------------------------------

    @api.onchange('stage_id')
    def _reset_forecasts_stages(self):  # сбрасываем вероятности прогнозов до вероятности проекта при изменении последнего
        for project in self:
            has_changed = False
            if project.step_status == 'step':
                accs_ids = project.planned_step_acceptance_flow_ids
                cash_ids = project.planned_step_cash_flow_ids
            elif project.step_status == 'project' and not project.project_have_steps:
                accs_ids = project.planned_acceptance_flow_ids
                cash_ids = project.planned_cash_flow_ids
            else:
                return
            for acceptance in accs_ids:
                if acceptance.forecast != 'from_project':
                    acceptance.forecast = 'from_project'
                    has_changed = True
            for cash in cash_ids:
                if cash.forecast != 'from_project':
                    cash.forecast = 'from_project'
                    has_changed = True
        if has_changed:
            message = _("Project\step stage has changed, acceptance and cash forecasts set to 'from_project'")
            return {
                'warning': {'title': "Warning", 'message': message},
            }

    @api.onchange('key_account_manager_id')
    def _onchange_key_account_manager_id(self):
        project_office = self._get_employee_project_office(self.key_account_manager_id)
        if project_office:
            self.project_office_id = project_office.id

    def check_overdue_date(self, vals_list):
        for project in self:

            end_presale_project_month = project.end_presale_project_month
            end_sale_project_month = project.end_sale_project_month
            # print('vals_list = ',vals_list)

            stage_id_name = project.stage_id.code

            if vals_list:
                if 'end_presale_project_month' in vals_list:
                    end_presale_project_month = datetime.datetime.strptime(vals_list['end_presale_project_month'], "%Y-%m-%d").date()
                if 'end_sale_project_month' in vals_list:
                    end_sale_project_month = datetime.datetime.strptime(vals_list['end_sale_project_month'], "%Y-%m-%d").date()
                if 'stage_id' in vals_list:
                    stage_id = int(vals_list['stage_id'])
                    stage_id_obj = self.env['project_budget.project.stage'].search([('id', '=', stage_id)], limit=1)
                    stage_id_name = stage_id_obj.code

            if stage_id_name not in ('0', '100', '100(done)'):
                if end_presale_project_month < fields.datetime.now().date() :
                    raisetext = _("DENIED. Project {0} have overdue end presale project month {1}")
                    raisetext=raisetext.format(project.project_id,str(end_presale_project_month))
                    return False, raisetext, {'end_presale_project_month':str(end_presale_project_month)}
            if stage_id_name not in ('0', '100', '100(done)'): # Алина сказала, что даже если на исполнение то не проверять даты контрактования
                if end_sale_project_month < fields.datetime.now().date() :
                    raisetext = _("DENIED. Project {0} have overdue end sale project month {1}")
                    raisetext = raisetext.format(project.project_id, str(end_sale_project_month))
                    return False, raisetext, {'end_sale_project_month': str(end_sale_project_month)}

            vals_list_steps = False

            dict_formula = {}

            if project.project_have_steps:
                for step in project.step_project_child_ids:
                    stage_id_name = step.stage_id.code
                    end_presale_project_month = step.end_presale_project_month
                    end_sale_project_month = step.end_sale_project_month

                    if vals_list:
                        if 'step_project_child_ids' in vals_list:
                            vals_list_steps = vals_list['step_project_child_ids']
                            if vals_list_steps:

                                for vals_list_step in vals_list_steps:
                                    print('vals_list_steps =', vals_list_step)
                                    if step.id == vals_list_step[1]:

                                        vals_one_step = vals_list_step[2]
                                        print('vals_one_step = ', vals_one_step)
                                        if vals_one_step:
                                            if 'stage_id' in vals_one_step:
                                                stage_id = int(vals_one_step['stage_id'])
                                                stage_id_obj = self.env[
                                                    'project_budget.project.stage'].search(
                                                    [('id', '=', stage_id)], limit=1)
                                                stage_id_name = stage_id_obj.code


                                            if 'end_presale_project_month' in vals_one_step:
                                                end_presale_project_month = datetime.datetime.strptime(
                                                    vals_one_step['end_presale_project_month'], "%Y-%m-%d").date()
                                            if 'end_sale_project_month' in vals_one_step:
                                                end_sale_project_month = datetime.datetime.strptime(
                                                    vals_one_step['end_sale_project_month'], "%Y-%m-%d").date()

                    step_id_str = str(step.id)
                    dict_formula[step_id_str] = stage_id_name

                    if stage_id_name not in ('0', '100', '100(done)'):
                        print('step.id = ', step.id)
                        if end_presale_project_month < fields.datetime.now().date():
                            raisetext = _("DENIED. Project {0} step {1} have overdue end presale project month {2}")
                            raisetext = raisetext.format(project.project_id, step.project_id, str(end_presale_project_month))
                            return False, raisetext, {'step_id': step.project_id, 'end_presale_project_month': str(end_presale_project_month)}

                    if stage_id_name not in ('0', '100', '100(done)'):
                        if end_sale_project_month < fields.datetime.now().date():
                            raisetext = _("DENIED. Project {0} step {1} have overdue end sale project month {2}")
                            raisetext = raisetext.format(project.project_id, step.project_id, str(end_sale_project_month))
                            return False, raisetext, {'step_id': step.project_id, 'end_sale_project_month': str(end_sale_project_month)}

            if stage_id_name in ('0', '100(done)'):
               if project.project_have_steps == False:
                   return True, "", {}

            vals_list_planaccepts = False
            buffer_new_distr_plan_accept_ids = set()
            buffer_del_distr_accept_ids = set()
            buffer_new_distr_accept_ids = set()

            if vals_list:
                if 'planned_acceptance_flow_ids' in vals_list:
                    vals_list_planaccepts = vals_list['planned_acceptance_flow_ids']

                if 'fact_acceptance_flow_ids' in vals_list:  # проверяем Факт Акты в буфере
                    for fact_acceptance_flow_id in vals_list['fact_acceptance_flow_ids']:
                        if fact_acceptance_flow_id[0] == 0:  # создание Факт Акта
                            if 'distribution_acceptance_ids' in fact_acceptance_flow_id[2]:
                                for distribution_acceptance_id in fact_acceptance_flow_id[2]['distribution_acceptance_ids']:
                                    if distribution_acceptance_id[0] == 0:  # создание распределения
                                        if distribution_acceptance_id[2]['sum_cash'] > 0:
                                            buffer_new_distr_plan_accept_ids.add(distribution_acceptance_id[2]['planned_acceptance_flow_id'])
                        elif fact_acceptance_flow_id[0] == 1:  # изменение Факт Акта
                            if 'distribution_acceptance_ids' in fact_acceptance_flow_id[2]:
                                for distribution_acceptance_id in fact_acceptance_flow_id[2]['distribution_acceptance_ids']:
                                    if distribution_acceptance_id[0] == 0:  # создание распределения
                                        if distribution_acceptance_id[2]['sum_cash'] > 0:
                                            buffer_new_distr_plan_accept_ids.add(distribution_acceptance_id[2]['planned_acceptance_flow_id'])
                                    elif distribution_acceptance_id[0] == 1:  # изменение распределения
                                        if 'planned_acceptance_flow_id' in distribution_acceptance_id[2]:  # если поменялся Прогноз для распределения
                                            if ('sum_cash' not in distribution_acceptance_id[2] or distribution_acceptance_id[2]['sum_cash'] != 0):
                                                buffer_new_distr_plan_accept_ids.add(distribution_acceptance_id[2]['planned_acceptance_flow_id'])
                                            buffer_del_distr_accept_ids.add(distribution_acceptance_id[1])
                                        elif 'sum_cash' in distribution_acceptance_id[2]: # если поменялась сумма распределения
                                            if distribution_acceptance_id[2]['sum_cash'] == 0:
                                                buffer_del_distr_accept_ids.add(distribution_acceptance_id[1])
                                            else:
                                                buffer_new_distr_accept_ids.add(distribution_acceptance_id[1])
                                    elif distribution_acceptance_id[0] == 2:  # удаление распределения
                                        buffer_del_distr_accept_ids.add(distribution_acceptance_id[1])
                        elif fact_acceptance_flow_id[0] == 2:  # удаление Факт Акта
                            for fact_acceptance in project.fact_acceptance_flow_ids:
                                if fact_acceptance.id == fact_acceptance_flow_id[1]:
                                    buffer_del_distr_accept_ids.update(fact_acceptance.distribution_acceptance_ids.ids)

                # print('buffer_new_distr_plan_accept_ids-', buffer_new_distr_plan_accept_ids, 'buffer_del_distr_accept_ids-', buffer_del_distr_accept_ids, 'buffer_new_distr_accept_ids', buffer_new_distr_accept_ids)

            for plan_accept in project.planned_acceptance_flow_ids:
                date_cash = plan_accept.date_cash
                step_id_str = str(plan_accept.step_project_child_id.id)
                # print('step_id_str = ',step_id_str)
                if step_id_str in dict_formula :
                    if dict_formula[step_id_str] in ('0', '100(done)'):
                        continue

                if vals_list_planaccepts:
                    for vals_list_planaccept in vals_list_planaccepts:
                        # print('vals_list_planaccept =', vals_list_planaccept)
                        if plan_accept.id == vals_list_planaccept[1]:
                            vals_one_accept = vals_list_planaccept[2]
                            # print('vals_one_accept = ', vals_one_accept)
                            if vals_one_accept == False: # по идее это удаление, потому просто добавим день к дате, чтобы условие ниже прошло
                                date_cash = fields.datetime.now().date() + datetime.timedelta(days=1)
                            else:
                                if 'date_cash' in vals_one_accept:
                                    date_cash = datetime.datetime.strptime(
                                        vals_one_accept['date_cash'], "%Y-%m-%d").date()

                if date_cash < fields.datetime.now().date():
                    # print('plan_accept.distribution_acceptance_ids =', plan_accept.distribution_acceptance_ids, 'plan_accept.id =', plan_accept.id)
                    if (any(distribution.id not in buffer_del_distr_accept_ids for distribution in plan_accept.distribution_acceptance_ids if (distribution.sum_cash_without_vat > 0 or distribution.id in buffer_new_distr_accept_ids))
                            or plan_accept.id in buffer_new_distr_plan_accept_ids):
                        ok = True
                    else:
                        raisetext = _("DENIED. Project {0} have overdue planned acceptance flow  without fact {1}")
                        raisetext = raisetext.format(project.project_id, str(date_cash))
                        return False, raisetext, {'planned_acceptance_flow': str(date_cash)}

            vals_list_plancashs = False
            buffer_new_distr_plan_cash_ids = set()
            buffer_del_distr_cash_ids = set()
            buffer_new_distr_cash_ids = set()

            if vals_list:
                if 'planned_cash_flow_ids' in vals_list:
                    vals_list_plancashs = vals_list['planned_cash_flow_ids']

                if 'fact_cash_flow_ids' in vals_list:  # проверяем Факт ПДС в буфере
                    for fact_cash_flow_id in vals_list['fact_cash_flow_ids']:
                        if fact_cash_flow_id[0] == 0:  # создание Факт ПДС
                            if 'distribution_cash_ids' in fact_cash_flow_id[2]:
                                for distribution_cash_flow_id in fact_cash_flow_id[2]['distribution_cash_ids']:
                                    if distribution_cash_flow_id[0] == 0:  # создание распределения
                                        if distribution_cash_flow_id[2]['sum_cash'] > 0:
                                            buffer_new_distr_plan_cash_ids.add(distribution_cash_flow_id[2]['planned_cash_flow_id'])
                        elif fact_cash_flow_id[0] == 1:  # изменение Факт ПДС
                            if 'distribution_cash_ids' in fact_cash_flow_id[2]:
                                for distribution_cash_flow_id in fact_cash_flow_id[2]['distribution_cash_ids']:
                                    if distribution_cash_flow_id[0] == 0:  # создание распределения
                                        if distribution_cash_flow_id[2]['sum_cash'] > 0:
                                            buffer_new_distr_plan_cash_ids.add(distribution_cash_flow_id[2]['planned_cash_flow_id'])
                                    elif distribution_cash_flow_id[0] == 1:  # изменение распределения
                                        if 'planned_cash_flow_id' in distribution_cash_flow_id[2]:  # если поменялся Прогноз для распределения
                                            if ('sum_cash' not in distribution_cash_flow_id[2] or distribution_cash_flow_id[2]['sum_cash'] != 0):
                                                buffer_new_distr_plan_cash_ids.add(distribution_cash_flow_id[2]['planned_cash_flow_id'])
                                            buffer_del_distr_cash_ids.add(distribution_cash_flow_id[1])
                                        elif 'sum_cash' in distribution_cash_flow_id[2]: # если поменялась сумма распределения
                                            if distribution_cash_flow_id[2]['sum_cash'] == 0:
                                                buffer_del_distr_cash_ids.add(distribution_cash_flow_id[1])
                                            else:
                                                buffer_new_distr_cash_ids.add(distribution_cash_flow_id[1])
                                    elif distribution_cash_flow_id[0] == 2:  # удаление распределения
                                        buffer_del_distr_cash_ids.add(distribution_cash_flow_id[1])
                        elif fact_cash_flow_id[0] == 2:  # удаление Факт ПДС
                            for fact_cash in project.fact_cash_flow_ids:
                                if fact_cash.id == fact_cash_flow_id[1]:
                                    buffer_del_distr_cash_ids.update(fact_cash.distribution_cash_ids.ids)

            for plan_cash in project.planned_cash_flow_ids:
                date_cash = plan_cash.date_cash

                step_id_str = str(plan_cash.step_project_child_id.id)
                if step_id_str in dict_formula :
                    if dict_formula[step_id_str] in ('0', '100(done)'):
                        continue

                if vals_list_plancashs:
                    for vals_list_plancash in vals_list_plancashs:
                        # print('vals_list_planaccept =', vals_list_plancash)
                        if plan_cash.id == vals_list_plancash[1]:
                            vals_one_cash = vals_list_plancash[2]
                            # print('vals_one_cash = ', vals_one_cash)
                            if vals_one_cash == False: # по идее это удаление, потому просто добавим день к дате, чтобы условие ниже прошло
                                date_cash = fields.datetime.now().date() +  datetime.timedelta(days=1)
                            else:
                                if 'date_cash' in vals_one_cash:
                                    date_cash = datetime.datetime.strptime(
                                        vals_one_cash['date_cash'], "%Y-%m-%d").date()
                if date_cash < fields.datetime.now().date():
                    if (any(distribution.id not in buffer_del_distr_cash_ids for distribution in
                            plan_cash.distribution_cash_ids if
                            (distribution.sum_cash_without_vat > 0 or distribution.id in buffer_new_distr_cash_ids))
                            or plan_cash.id in buffer_new_distr_plan_cash_ids):
                        ok = True
                    else:
                        raisetext = _("DENIED. Project {0} have overdue planned cash flow  without fact {1}" )
                        raisetext = raisetext.format(project.project_id, str(date_cash))
                        return False, raisetext, {'planned_cash_flow': str(date_cash)}

        return True, "", {}

    def print_budget(self):
        for rows in self:
            print()

    def set_approve_manager(self):
        for rows in self:
            # if rows.estimated_probability_id.name in ('50','75','100'):
            #     if rows.total_amount_of_revenue_with_vat != rows.planned_acceptance_flow_sum:
            #         raisetext = _("DENIED. planned_acceptance_flow_sum <> total_amount_of_revenue_with_vat")
            #         raise ValidationError(raisetext)
            #
            #     if rows.total_amount_of_revenue_with_vat != rows.planned_cash_flow_sum:
            #         raisetext = _("DENIED. planned_cash_flow_sum <> total_amount_of_revenue_with_vat")
            #         raise ValidationError(raisetext)

            isok, raisetext, emptydict =self.check_overdue_date(False)
            if isok == False:
                raise ValidationError(raisetext)

            print('0_0')
            if rows.approve_state=="need_approve_manager" and rows.budget_state == 'work' and rows.project_status !='cancel':
                print('before rows.id = ', rows.id)
                rows.write({'approve_state': "need_approve_supervisor"})

                # rows.approve_state = "need_approve_supervisor"
                print('rows.id = ', rows.id)

                # Get a reference to the mail.activity model
                activity_model = self.env['mail.activity']
                # Use the search method to find the activities that need to be marked as done
                activities = activity_model.search([('res_id','=', rows.id),
                                                    ('activity_type_id','=',self.env.ref('project_budget.mail_act_send_project_to_supervisor_for_approval').id)
                                                   ])
                print('activities = ', activities)
                # Update the state of each activity to 'done'
                for activitie in activities:
                    activitie.action_done()

                user_id = rows.project_curator_id.user_id.id
                print('user_id = ',user_id)
                if rows.project_office_id.receive_tasks_for_approve_project: # не куратору посылать, а руководителю проектного офиса надо
                    if rows.project_office_id.user_id: # вдруг просто галочка стоит, а пользователь не выбран
                        user_id = rows.project_office_id.user_id.id
                print('user_id (after project_office_id) = ', user_id)
                res_model_id_project_budget = self.env['ir.model'].search([('model', '=', 'project_budget.projects')]).id
                print('res_model_id_project_budget = ', res_model_id_project_budget)
                self.env['mail.activity'].create({
                    'display_name': _('You have to approve or decline project'),
                    'summary': _('You have to approve or decline project'),
                    'date_deadline': fields.datetime.now(),
                    'user_id': user_id,
                    'res_id': rows.id,
                    'res_model_id': res_model_id_project_budget,
                    'activity_type_id': self.env.ref('project_budget.mail_act_approve_project_by_supervisor').id
                    })

                    # rows.approve_state="need_approve_supervisor"
        return False

    # def set_approve_supervisor(self):  # TODO убрать после миграции на кураторов
    #     for rows in self:
    #         if rows.approve_state=="need_approve_supervisor" and rows.budget_state == 'work' and rows.project_status !='cancel':
    #
    #             isok, raisetext,emptydict = self.check_overdue_date(False)
    #             if isok == False:
    #                 raise ValidationError(raisetext)
    #
    #             user_id = False
    #             if rows.project_office_id.receive_tasks_for_approve_project: # не только куратор может утвекрждать, но и руководитель проектного офиса надо
    #                 if rows.project_office_id.user_id: # вдруг просто галочка стоит, а пользователь не выбран
    #                     user_id = rows.project_office_id.user_id.id
    #
    #             if self.user_is_supervisor(rows.project_supervisor_id.id) or self.user_has_groups('project_budget.project_budget_admin') or self.env.user.id == user_id :
    #                 # rows.approve_state="approved"
    #                rows.write({
    #                    'approve_state': "approved"
    #                  })
    #                activity_model = self.env['mail.activity']
    #                activities = activity_model.search([('res_id', '=', rows.id),
    #                                                     ('activity_type_id', '=', self.env.ref(
    #                                                         'project_budget.mail_act_approve_project_by_supervisor').id)
    #                                                     ])
    #                # Update the state of each activity to 'done'
    #                for activitie in activities:
    #                    activitie.action_done()
    #     return False

    def set_approve_curator(self):
        for rows in self:
            if rows.approve_state=="need_approve_supervisor" and rows.budget_state == 'work' and rows.project_status !='cancel':

                isok, raisetext,emptydict = self.check_overdue_date(False)
                if isok == False:
                    raise ValidationError(raisetext)

                user_id = False
                if rows.project_office_id.receive_tasks_for_approve_project: # не только куратор может утвекрждать, но и руководитель проектного офиса надо
                    if rows.project_office_id.user_id: # вдруг просто галочка стоит, а пользователь не выбран
                        user_id = rows.project_office_id.user_id.id

                if self.user_is_curator(rows.project_curator_id) or self.user_has_groups('project_budget.project_budget_admin') or self.env.user.id == user_id :
                    # rows.approve_state="approved"
                   rows.write({
                       'approve_state': "approved"
                     })
                   activity_model = self.env['mail.activity']
                   activities = activity_model.search([('res_id', '=', rows.id),
                                                        ('activity_type_id', '=', self.env.ref(
                                                            'project_budget.mail_act_approve_project_by_supervisor').id)
                                                        ])
                   # Update the state of each activity to 'done'
                   for activitie in activities:
                       activitie.action_done()
        return False

    # def cancel_approve(self):  # TODO убрать после миграции на кураторов
    #     for rows in self:
    #         if (rows.approve_state=="approved" or rows.approve_state=="need_approve_supervisor") and rows.budget_state == 'work' and rows.project_status !='cancel':
    #             user_id = False
    #             if rows.project_office_id.receive_tasks_for_approve_project: # не только куратор может утвекрждать, но и руководитель проектного офиса надо
    #                 if rows.project_office_id.user_id: # вдруг просто галочка стоит, а пользователь не выбран
    #                     user_id = rows.project_office_id.user_id.id
    #
    #             if self.user_is_supervisor(rows.project_supervisor_id.id) or self.user_has_groups('project_budget.project_budget_admin') or self.env.user.id == user_id :
    #                 # rows.approve_state="need_approve_manager"
    #                 rows.write({
    #                     'approve_state': "need_approve_manager"
    #                 })
    #                 activity_model = self.env['mail.activity']
    #                 activities = activity_model.search([('res_id','=', rows.id),
    #                                                     ('activity_type_id','=',self.env.ref('project_budget.mail_act_approve_project_by_supervisor').id)
    #                                                    ])
    #                 # Update the state of each activity to 'done'
    #                 for activitie in activities:
    #                     activitie.action_done()
    #
    #                 self.env['mail.activity'].create({
    #                     'display_name': _('Supervisor declined project. Change nessesary values and send supervisor for approval'),
    #                     'summary': _('Supervisor declined project. Change nessesary values and send supervisor for approval'),
    #                     'date_deadline': fields.datetime.now(),
    #                     'user_id': rows.key_account_manager_id.user_id.id,
    #                     'res_id': rows.id,
    #                     'res_model_id': self.env['ir.model'].search([('model', '=', 'project_budget.projects')]).id,
    #                     'activity_type_id': self.env.ref('project_budget.mail_act_send_project_to_supervisor_for_approval').id
    #                 })
    #     return False

    def cancel_approve_curator(self):
        for rows in self:
            if (rows.approve_state=="approved" or rows.approve_state=="need_approve_supervisor") and rows.budget_state == 'work' and rows.project_status !='cancel':
                user_id = False
                if rows.project_office_id.receive_tasks_for_approve_project: # не только куратор может утвекрждать, но и руководитель проектного офиса надо
                    if rows.project_office_id.user_id: # вдруг просто галочка стоит, а пользователь не выбран
                        user_id = rows.project_office_id.user_id.id

                if self.user_is_curator(rows.project_curator_id) or self.user_has_groups('project_budget.project_budget_admin') or self.env.user.id == user_id :
                    # rows.approve_state="need_approve_manager"
                    rows.write({
                        'approve_state': "need_approve_manager"
                    })
                    activity_model = self.env['mail.activity']
                    activities = activity_model.search([('res_id','=', rows.id),
                                                        ('activity_type_id','=',self.env.ref('project_budget.mail_act_approve_project_by_supervisor').id)
                                                       ])
                    # Update the state of each activity to 'done'
                    for activitie in activities:
                        activitie.action_done()

                    self.env['mail.activity'].create({
                        'display_name': _('Supervisor declined project. Change nessesary values and send supervisor for approval'),
                        'summary': _('Supervisor declined project. Change nessesary values and send supervisor for approval'),
                        'date_deadline': fields.datetime.now(),
                        'user_id': rows.key_account_manager_id.user_id.id,
                        'res_id': rows.id,
                        'res_model_id': self.env['ir.model'].search([('model', '=', 'project_budget.projects')]).id,
                        'activity_type_id': self.env.ref('project_budget.mail_act_send_project_to_supervisor_for_approval').id
                    })
        return False

    def open_record(self):
        self.ensure_one()
        # first you need to get the id of your record
        # you didn't specify what you want to edit exactly
        rec_id = self.id
        # then if you have more than one form view then specify the form id
        form_id = self.env.ref('project_budget.show_comercial_budget_spec_form')
        # then open the form
        return {
            'type': 'ir.actions.act_window',
            'name': 'Edit Project',
            'res_model': 'project_budget.projects',
            'res_id': rec_id,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': form_id.id,
            'context': {},
            # if you want to open the form in edit mode direclty
            'flags': {'initial_mode': 'edit'},
            'target': 'new',
        }

    def action_open_attachments(self):
        self.ensure_one()
        return {
            'name': _('Attachments'),
            'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,tree,form',
            'context': "{'default_res_model': '%s','default_res_id': %d}" % (self._name, self.id),
            'help': """
                <p class="o_view_nocontent_smiling_face">%s</p>
                """ % _("Add attachments for this project")
        }

    def action_open_tenders(self):
        self.ensure_one()
        return {
            'name': _('Tenders'),
            'domain': [('projects_id', '=', self.id)],
            'res_model': 'project_budget.tenders',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'context': "{'default_projects_id': %d}" % (self.id),
            'help': """
                <p class="o_view_nocontent_smiling_face">%s</p>
                """ % _("Add tenders for this project")
        }

    # def reopen(self):
    #     """
    #     return not fixed project from '-' to 'need_approve_manager' status.
    #     for admins only
    #     """
    #     for record in self:
    #         user_id = False
    #         if record.project_office_id.receive_tasks_for_approve_project:  # не только куратор может утвекрждать, но и руководитель проектного офиса надо
    #             if record.project_office_id.user_id:  # вдруг просто галочка стоит, а пользователь не выбран
    #                 user_id = record.project_office_id.user_id.id
    #
    #         if not (self.user_is_supervisor(record.project_supervisor_id.id) or self.user_has_groups(
    #             'project_budget.project_budget_admin') or self.env.user.id == user_id):
    #             raise_text = _("only project admin or supervisor or project office manager can reopen projects")
    #             raise ValidationError(raise_text)
    #
    #         if record.approve_state != '-':
    #             raise_text = _("only project in '-' status can be reopened")
    #             raise ValidationError(raise_text)
    #
    #         if record.budget_state == 'fixed':
    #             raise_text = _("only project not in fixed budget can be reopened")
    #             raise ValidationError(raise_text)
    #
    #         record.approve_state = 'need_approve_manager'

    def reopen_curator(self):
        """
        return not fixed project from '-' to 'need_approve_manager' status.
        for admins only
        """
        for record in self:
            user_id = False
            if record.project_office_id.receive_tasks_for_approve_project:  # не только куратор может утвекрждать, но и руководитель проектного офиса надо
                if record.project_office_id.user_id:  # вдруг просто галочка стоит, а пользователь не выбран
                    user_id = record.project_office_id.user_id.id

            if not (self.user_is_curator(record.project_curator_id) or self.user_has_groups(
                'project_budget.project_budget_admin') or self.env.user.id == user_id):
                raise_text = _("only project admin or supervisor or project office manager can reopen projects")
                raise ValidationError(raise_text)

            if record.approve_state != '-':
                raise_text = _("only project in '-' status can be reopened")
                raise ValidationError(raise_text)

            if record.budget_state == 'fixed':
                raise_text = _("only project not in fixed budget can be reopened")
                raise ValidationError(raise_text)

            record.approve_state = 'need_approve_manager'

    def action_open_settings(self):
        self.ensure_one()
        return {
            'name': _('Settings'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'project_budget.projects',
            'view_id': self.env.ref('project_budget.project_budget_project_settings_view_form').id,
            'res_id': self.id,
            'target': 'new'
        }

    # ------------------------------------------------------
    # CRUD
    # ------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._check_required_fields(vals)
            if not vals.get('project_id') or vals['project_id'] == 'ID':
                if not vals.get('step_status') or vals['step_status'] == 'project':  # разные типы ID у проектов и проектов-этапов
                    vals['project_id'] = self.env['ir.sequence'].sudo().next_by_code('project_budget.projects')
                elif vals['step_status'] == 'step':
                    vals['project_id'] = self.env['ir.sequence'].sudo().next_by_code('project_budget.project_steps')
        return super().create(vals_list)

    def write(self, vals):
        self._check_required_fields(vals)
        for row in self:
            if row.env.context.get('form_fix_budget') or row.env.context.get('cancel_approve'):
            # TODO не проверять проекты при добавлении их в качестве дочерних
                # or self.env.context.get('form_view_projects'): ##из коммерческих бюджетов фиксация идет или  дублируем сделку из формы
                f = 1
                # print('form_fix_budget or cancel_approve')
            else:
                if row.approve_state == 'need_approve_manager':
                    isok, raisetext,emptydict = row.check_overdue_date(vals)
                    if isok == False:
                        raise ValidationError(raisetext)

        res = super().write(vals)
        return res

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}

        if self.date_actual:  # сделка в зафиксированном бюджете
            raise ValidationError(_('This project is in fixed budget. Copy deny'))

        if not self.env.context.get('form_fix_budget', False):
            default['project_id'] = 'ID'
            default['essence_project'] = _('__COPY__ ') + self.project_id + '__' + self.essence_project

        result = super(Project, self).copy(default=default)
        mapping_old_to_new_steps = self._copy_steps(result)
        if self.env.context.get('form_fix_budget', False):
            self._copy_flows_and_distributions(result, mapping_old_to_new_steps, 'acceptance')
            self._copy_flows_and_distributions(result, mapping_old_to_new_steps, 'cash')

        return result

    def unlink(self):
        """
        unlink if project is not in fixed budgets and not in 'need_approve_manager' status
        """
        print('unlink ')

        for record in self:
            print('record = ', record)
            print('record.project_id = ', record.project_id)
            print('record.id = ', record.id)

            if record.approve_state != 'need_approve_manager':
                raise_text = _("only project in 'need approve manager' can be deleted")
                raise ValidationError(raise_text)

            # NOTE: sudo используется из-за проблем с доступ к проетам в зафиксированном бюджете
            project_is_in_fixed_budgets = self.env['project_budget.projects'].sudo().search([
                ('project_id', '=', record.project_id),
                ('id', '!=', record.id)
            ], limit=1)
            if project_is_in_fixed_budgets:
                raise_text = _("only project not in fixed budget can be deleted")
                raise ValidationError(raise_text)

        res = super().unlink()

        if res:  # use action to return to tree view after unlink
            res = self.env["ir.actions.actions"]._for_xml_id("project_budget.action_project_budget_projects")
            res['target'] = 'main'
            return res

    # ------------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------------

    def _check_required_fields(self, changed_fields):
        for rec in self:
            stage = rec.stage_id
            if changed_fields.get('stage_id', False):
                stage = self.env['project_budget.project.stage'].browse(changed_fields.get('stage_id', 0))

            required_fields = stage.required_field_ids
            empty_fields = []
            for required_field in required_fields:
                if (not rec[required_field.name] and not changed_fields.get(required_field.name, False)) or (
                        rec[required_field.name] and not changed_fields.get(required_field.name, True)):
                    empty_fields.append(required_field.field_description)

            if empty_fields:
                raise ValidationError(
                    _("Fields '%s' are required at the stage '%s'!") % (', '.join(empty_fields), stage.name))

    def _get_current_employee(self):
        employee = self.env['hr.employee'].search([
            ('user_id', '=', self.env.user.id),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        return employee

    def _get_employee_project_office(self, employee):
        project_office = self.env['project_budget.project_office'].search([
            ('responsibility_center_id', '=', employee.department_id.responsibility_center_id.id or 0)
        ], limit=1)
        return project_office

    def _copy_steps(self, copied_project):
        self.ensure_one()

        mapping_old_to_new_steps = dict()
        if self.project_have_steps and self.step_project_child_ids:
            for step in self.step_project_child_ids:
                copied_step = step.copy({
                    'commercial_budget_id': copied_project.commercial_budget_id.id,
                    'step_project_parent_id': copied_project.id
                })
                mapping_old_to_new_steps[step.id] = copied_step.id

        return mapping_old_to_new_steps

    def _copy_flows_and_distributions(self, copied_project, mapping_old_to_new_steps, flow_type):
        self.ensure_one()

        mapping_old_to_new_flows = dict()
        for flow in self['planned_' + flow_type + '_flow_ids']:
            copied_flow = flow.copy({
                'projects_id': copied_project.id,
                'step_project_child_id': mapping_old_to_new_steps.get(flow.step_project_child_id.id, False)
            })
            mapping_old_to_new_flows[flow.id] = copied_flow.id

        for flow in self['fact_' + flow_type + '_flow_ids']:
            copied_flow = flow.copy({
                'projects_id': copied_project.id,
                'step_project_child_id': mapping_old_to_new_steps.get(flow.step_project_child_id.id, False)
            })
            for distribution in flow['distribution_' + flow_type + '_ids']:
                distribution.copy({
                    'fact_' + flow_type + '_flow_id': copied_flow.id,
                    'planned_' + flow_type + '_flow_id': mapping_old_to_new_flows.get(
                        distribution['planned_' + flow_type + '_flow_id'].id)
                })

    def toggle_active(self):
        for project in self:
            if project.project_have_steps:
                project_without_active_test = (self.env['project_budget.projects'].with_context({'active_test': False})
                                               .search([('id', '=', project.id)]))
                for step in project_without_active_test.step_project_child_ids:
                    step.active = not project.active
        return super(Project, self).toggle_active()

    def action_copy_step(self):
        self.ensure_one()
        if self.date_actual:  # сделка в зафиксированном бюджете
            raisetext = _("This project is in fixed budget. Copy deny")
            raise (ValidationError(raisetext))
        self.sudo().copy()
