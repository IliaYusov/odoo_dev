import re
import datetime

from odoo import api, Command, fields, models, _
from odoo.exceptions import ValidationError


class Project(models.Model):
    _inherit = 'project_budget.projects'

    project_supervisor_id = fields.Many2one('project_budget.project_supervisor', string='Project Curator',
                                            compute='_compute_project_curator_id',
                                            inverse='_inverse_project_curator_id', check_company=True, copy=True,
                                            domain="[('company_id', 'in', (False, company_id))]", store=True,
                                            tracking=True)
    technological_direction_id = fields.Many2one('project_budget.technological_direction',
                                                 string='Technological Direction', compute='_compute_parent_data',
                                                 copy=True, readonly=False, store=True, tracking=True)
    project_type_id = fields.Many2one('project_budget.project_type', string='Project Type', copy=True, tracking=True)

    end_sale_project_quarter = fields.Char(string='End date of the Sale project(quarter)', compute='_compute_quarter', store=True, tracking=True)
    end_sale_project_month = fields.Date(string='The period of shipment or provision of services to the Client(MONTH)', default=fields.Date.context_today, tracking=True)

    cost_price = fields.Monetary(string='Cost price', store=True, tracking=True, copy=True)
    cost_price_in_company_currency = fields.Monetary(
        string='Cost price in company currency', compute='_compute_amounts_in_company_currency',
        currency_field='company_currency_id', store=True, tracking=True
    )
    margin = fields.Monetary(string='Margin income', compute='_compute_totals', store=True)
    margin_in_company_currency = fields.Monetary(
        string='Margin income in company currency', compute='_compute_amounts_in_company_currency',
        currency_field='company_currency_id', store=True
    )
    profitability = fields.Float(string='Profitability(share of Sale margin in revenue)', compute='_compute_totals',
                                 store=True, tracking=True)

    is_parent_project = fields.Boolean(string="project is parent", default=False, copy=True, tracking=True)
    is_child_project = fields.Boolean(string="project is child", compute='_check_project_is_child')
    margin_rate_for_parent = fields.Float(string="margin rate for parent project", default=0, copy=True, tracking=True)
    parent_project_id = fields.Many2one(
        'project_budget.projects',
        string='parent project id',
        ondelete='set null', copy=True)
    child_project_ids = fields.One2many(
        comodel_name='project_budget.projects',
        inverse_name='parent_project_id',
        string="child projects", auto_join=True)
    child_count = fields.Integer(compute='_compute_child_count', string='Child Count')
    margin_from_children_to_parent = fields.Boolean(string="Margin from Children to Parent", default=True, copy=True)
    margin_from_children_to_parent_related = fields.Boolean(related="parent_project_id.margin_from_children_to_parent")
    additional_margin = fields.Monetary(string="Margin from Related Projects", compute='_compute_additional_margin',
                                        store=True, copy=True)
    total_margin_of_child_projects = fields.Monetary(string="total margin of child projects",
                                                     compute='_compute_total_margin_of_child_projects')
    total_margin = fields.Monetary(string="Total Margin", compute='_compute_total_margin')

    planned_cost_flow_ids = fields.One2many('project_budget.planned_cost_flow', 'projects_id',
                                            string='Planned Cost Flow', copy=False)
    planned_step_cost_flow_ids = fields.One2many('project_budget.planned_cost_flow', 'step_project_child_id',
                                                 string='Planned Cost Flow')
    planned_amount_total_cost_flow = fields.Monetary(string='Planned Amount With Tax Of Cost Flow',
                                                     compute='_compute_planned_amount_cost_flow',
                                                     currency_field='company_currency_id', tracking=True)

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
            if self.env.ref('project_budget.project_role_project_curator') in diff and record.project_supervisor_id:
                diff.remove(self.env.ref('project_budget.project_role_project_curator'))
            if diff:
                raise ValidationError(_("Roles '%s' are required for the project!") % ', '.join([r.name for r in diff]))

    @api.constrains('stage_id', 'amount_untaxed', 'cost_price', 'planned_acceptance_flow_ids',
                    'planned_cash_flow_ids', 'planned_step_acceptance_flow_ids', 'planned_step_cash_flow_ids')
    def _check_financial_data_is_present(self):
        for project in self.filtered(lambda pr: pr.budget_state == 'work'):
            # print(project.env.context.get('form_fix_budget'))
            if project.env.context.get('form_fix_budget'):
                continue
            if (project.stage_id.code in ('30', '50', '75', '100')
                    and project.amount_untaxed == 0
                    and project.cost_price == 0
                    and not project.project_have_steps
                    and not (project.is_parent_project and project.margin_from_children_to_parent)
                    and not (project.is_child_project and not project.margin_from_children_to_parent)
                    and project.budget_state == 'work'
                    and not project.is_correction_project):
                if project.step_status == 'project':
                    raisetext = _("Please enter financial data to project {0}")
                elif project.step_status == 'step':
                    raisetext = _("Please enter financial data to step {0}")
                raisetext = raisetext.format(project.project_id)
                raise ValidationError(raisetext)

            if project.project_have_steps:
                for step in project.step_project_child_ids:
                    if (step.stage_id.code in ('50', '75', '100')
                            and not (step.planned_step_acceptance_flow_ids and step.planned_step_cash_flow_ids)
                            and not (project.is_parent_project and project.margin_from_children_to_parent)
                            and not (project.is_child_project and not project.margin_from_children_to_parent)
                            and step.budget_state == 'work'
                            and not step.is_correction_project):
                        raisetext = _("Please enter forecast for cash or acceptance to project {0} step {1}")
                        raisetext = raisetext.format(step.step_project_parent_id.project_id, step.project_id)
                        raise ValidationError(raisetext)
            else:
                if (project.stage_id.code in ('50', '75', '100')
                        and not (project.planned_acceptance_flow_ids and project.planned_cash_flow_ids)
                        and not (project.is_parent_project and project.margin_from_children_to_parent)
                        and not (project.is_child_project and not project.margin_from_children_to_parent)
                        and project.budget_state == 'work'
                        and not project.is_correction_project
                        and project.step_status == 'project'):
                    raisetext = _("Please enter forecast for cash or acceptance to project {0}")
                    raisetext = raisetext.format(project.project_id)
                    raise ValidationError(raisetext)

    @api.constrains('end_presale_project_month', 'end_sale_project_month')
    def _check_opportunity_date_end_greater(self):
        for project in self.filtered(lambda pr: pr.budget_state == 'work'):
            if project.company_id.id != 10 and project.end_sale_project_month < project.end_presale_project_month:  # не Ландата
                raisetext = _("The opportunity's start date must be before its end date.")
                raise ValidationError(raisetext)

    # ------------------------------------------------------
    # ONCHANGE METHODS
    # ------------------------------------------------------

    def check_project_overdue(self, project, vals_dict):
        if project.company_id.id != 11:  # не ТОПС
            isok, raisetext = super(Project, self).check_project_overdue(project, vals_dict)
            if not isok:
                return False, raisetext
        return True, ""

    def check_project_overdue_dates(self, project, vals_dict, stage_code):
        isok, raisetext = super(Project, self).check_project_overdue_dates(project, vals_dict, stage_code)
        if not isok:
            return False, raisetext

        if project.company_id.id != 10:  # не Ландата
            end_sale_project_month = project.end_sale_project_month

            if vals_dict:
                if 'end_sale_project_month' in vals_dict:
                    end_sale_project_month = datetime.datetime.strptime(vals_dict['end_sale_project_month'],
                                                                        "%Y-%m-%d").date()

            if stage_code != '100': # Алина сказала, что даже если на исполнение то не проверять даты контрактования
                if end_sale_project_month < fields.datetime.now().date():
                    if project.step_status == 'project':
                        raisetext = _("DENIED. Project {0} have overdue end sale project month {1}")
                    else:
                        raisetext = _("DENIED. Step {0} have overdue end sale project month {1}")
                    raisetext = raisetext.format(project.project_id, str(end_sale_project_month))
                    return False, raisetext
        return True, ""

    def check_project_overdue_plans(self, project, plans, facts, plan_type, steps_ids_to_skip, vals_dict):
        changed_plans = {}

        plan_ids = 'planned_' + plan_type + '_flow_ids'
        plan_id = 'planned_' + plan_type + '_flow_id'
        fact_ids = 'fact_' + plan_type + '_flow_ids'
        dist_ids = 'distribution_' +  plan_type + '_ids'

        distribution_ids = set(plans[dist_ids].filtered(lambda d: d.sum_cash > 0).ids)
        plans_with_new_distribution_ids = set()

        if vals_dict:
            if plan_ids in vals_dict:
                changed_plans = {plan_value[1]: {'action': plan_value[0], 'vals': plan_value[2]} for plan_value in vals_dict.get(plan_ids, [])}

            if fact_ids in vals_dict:  # проверяем Факт Акты в буфере
                changed_facts = {fact_value[1]: {'action': fact_value[0], 'vals': fact_value[2]} for fact_value in vals_dict.get(fact_ids, [])}

                for fact_id, fact_change in changed_facts.items():
                    if fact_change['action'] == 0:  # создание Факт Акта
                        if dist_ids in fact_change['vals']:
                            changed_dists = {dist_value[1]: {'action': dist_value[0], 'vals': dist_value[2]} for dist_value in fact_change['vals'].get(dist_ids, [])}
                            for dist_id, dist_change in changed_dists.items():
                                if dist_change['action'] == 0:  # создание распределения
                                    if dist_change['vals']['sum_cash'] > 0:
                                        plans_with_new_distribution_ids.add(dist_change['vals'][plan_id])
                        elif plan_id in fact_change['vals'] and fact_change['vals'][plan_id]:  # создание плана (для Ландаты)
                            plans_with_new_distribution_ids.add(fact_change['vals'][plan_id])

                    elif fact_change['action'] == 1:  # изменение Факт Акта
                        if dist_ids in fact_change['vals']:
                            changed_dists = {dist_value[1]: {'action': dist_value[0], 'vals': dist_value[2]} for dist_value in fact_change['vals'].get(dist_ids, [])}
                            for dist_id, dist_change in changed_dists.items():
                                if dist_change['action'] == 0:  # создание распределения
                                    if dist_change['vals']['sum_cash'] > 0:
                                        plans_with_new_distribution_ids.add(dist_change['vals'][plan_id])

                                elif dist_change['action'] == 1:  # изменение распределения
                                    if plan_id in dist_change['vals']:  # если поменялся Прогноз для распределения
                                        if ('sum_cash' not in dist_change['vals'] or
                                                dist_change['vals']['sum_cash'] != 0):
                                            plans_with_new_distribution_ids.add(dist_change['vals'][plan_id])
                                        distribution_ids.discard(dist_id)
                                    elif 'sum_cash' in dist_change['vals']:  # если поменялась сумма распределения
                                        if dist_change['vals']['sum_cash'] == 0:
                                            distribution_ids.discard(dist_id)
                                        else:
                                            distribution_ids.add(dist_id)
                                elif dist_change['action'] == 2:  # удаление распределения
                                    distribution_ids.discard(dist_id)
                        elif plan_id in fact_change['vals']:
                            if fact_change['vals'][plan_id]:  # изменение факта с изменением плана (для Ландаты)
                                deleted_fact = facts.search([('id', '=', fact_id)])
                                distribution_ids -= set(deleted_fact[dist_ids].ids)
                                plans_with_new_distribution_ids.add(fact_change['vals'][plan_id])
                            else:  # изменение факта с удалением плана (для Ландаты)
                                deleted_fact = facts.search([('id', '=', fact_id)])
                                distribution_ids -= set(deleted_fact[dist_ids].ids)

                    elif fact_change['action'] == 2:  # удаление Факт Акта
                        deleted_fact = facts.search([('id', '=', fact_id)])
                        distribution_ids -= set(deleted_fact[dist_ids].ids)

        for plan in plans.filtered(lambda p: p.step_project_child_id.id not in steps_ids_to_skip and not (
                p.id in plans_with_new_distribution_ids or set(p[dist_ids].ids) & distribution_ids
        )):
            date_to_check = plan.date_cash
            plan_changes = changed_plans.get(plan.id)
            if plan_changes:
                if plan_changes['action'] == 2:  # план удален
                    continue
                else:
                    if plan_changes['vals']:
                        new_date = plan_changes['vals'].get('date_cash')
                        if new_date:
                            date_to_check = datetime.datetime.strptime(new_date, "%Y-%m-%d").date()

            if date_to_check < fields.datetime.now().date():
                raisetext = _("DENIED. Project {0} have overdue planned {2} flow without fact {1}")
                raisetext = raisetext.format(project.project_id, str(date_to_check), _(plan_type))
                return False, raisetext
        return True, ""

    # ------------------------------------------------------
    # COMPUTE METHODS
    # ------------------------------------------------------

    @api.depends('end_presale_project_month','end_sale_project_month')
    def _compute_quarter(self):
        super(Project, self)._compute_quarter()
        for project in self:
            if not project.end_presale_project_month:
                continue
            tmp_date = project.end_sale_project_month
            month = tmp_date.month
            year = tmp_date.year
            if 0 <= int(month) <= 3:
                project.end_sale_project_quarter = 'Q1 ' + str(year)
            elif 4 <= int(month) <= 6:
                project.end_sale_project_quarter = 'Q2 ' + str(year)
            elif 7 <= int(month) <= 9:
                project.end_sale_project_quarter = 'Q3 ' + str(year)
            elif 10 <= int(month) <= 12:
                project.end_sale_project_quarter = 'Q4 ' + str(year)
            else:
                project.end_sale_project_quarter = 'NA'

    def _calculate_amounts_in_company_currency(self, project):
        super(Project, self)._calculate_amounts_in_company_currency(project)
        if not project.project_have_steps:
            if project.currency_id == project.company_currency_id:
                project.cost_price_in_company_currency = project.cost_price
                project.margin_in_company_currency = project.margin
            else:
                project.cost_price_in_company_currency = project.cost_price * project.currency_rate
                project.margin_in_company_currency = project.margin * project.currency_rate
        elif project.project_have_steps and project.step_status == 'project':
            cost_price_in_company_currency = 0
            margin_in_company_currency = 0
            for step in project.step_project_child_ids:
                if step.stage_id.code != '0':
                    cost_price_in_company_currency += step.cost_price_in_company_currency
                    margin_in_company_currency += step.margin_in_company_currency
            project.cost_price_in_company_currency = cost_price_in_company_currency
            project.margin_in_company_currency = margin_in_company_currency

    @api.depends("amount_total", 'margin', 'currency_rate')
    def _compute_amounts_in_company_currency(self):
        for project in self.sorted(lambda p: p.step_status == 'project'):  # сначала этапы, потом проекты
            self._calculate_amounts_in_company_currency(project)

    def _calculate_totals(self, project):
        super(Project, self)._calculate_totals(project)
        if not project.project_have_steps:
            project.margin = project.amount_untaxed - project.cost_price
            project.profitability = (project.margin / project.amount_untaxed * 100) if project.amount_untaxed else 0
        elif project.project_have_steps and project.step_status == 'project':
            cost_price = 0
            margin = 0
            for step in project.step_project_child_ids:
                if step.stage_id.code != '0':
                    cost_price += step.cost_price
                    margin += step.margin
            profitability = (margin / project.amount_untaxed * 100) if project.amount_untaxed else 0
            project.cost_price = cost_price
            project.margin = margin
            project.profitability = profitability

    @api.depends('amount_untaxed', "cost_price", 'tax_id')
    def _compute_totals(self):
        for project in self.sorted(lambda p: p.step_status == 'project'):  # сначала этапы, потом проекты
            self._calculate_totals(project)

    @api.depends('step_project_parent_id.technological_direction_id', 'step_project_parent_id.project_supervisor_id')
    def _compute_parent_data(self):
        for rec in self.filtered(lambda pr: pr.step_status == 'step'):
            rec.technological_direction_id = rec.step_project_parent_id.technological_direction_id
            rec.project_supervisor_id = rec.step_project_parent_id.project_supervisor_id

    @api.depends('child_project_ids')
    def _compute_child_count(self):
        for project in self:
            project.child_count = len(project.child_project_ids)

    @api.depends('project_member_ids.role_id')
    def _compute_project_curator_id(self):
        for project in self:
            curator = project.project_member_ids.filtered(lambda t: t.role_id == self.env.ref(
                'project_budget.project_role_project_curator'))[:1].employee_id
            project.project_supervisor_id = self.env['project_budget.project_supervisor'].search([
                ('user_id', '=', curator.user_id.id or 0),
                ('company_id', '=', project.company_id.id)
            ])[:1] or False

    @api.onchange('project_supervisor_id')
    def _inverse_project_curator_id(self):
        for project in self.filtered(
                lambda pr: pr.step_status == 'project' and pr.budget_state == 'work' and pr.project_supervisor_id):
            member_team = self.project_member_ids.filtered(lambda t: t.role_id == self.env.ref(
                'project_budget.project_role_project_curator'))[:1]
            if member_team:
                member_team.employee_id = self.env['hr.employee'].search([
                    ('user_id', '=', project.project_supervisor_id.user_id.id),
                    ('company_id', '=', project.company_id.id)
                ])[:1]
            else:
                project.project_member_ids = [Command.create({
                    'role_id': self.env.ref('project_budget.project_role_project_curator').id,
                    'employee_id': self.env['hr.employee'].search([
                        ('user_id', '=', project.project_supervisor_id.user_id.id),
                        ('company_id', '=', project.company_id.id)
                    ])[:1].id or 0
                })]

    @api.depends('amount_untaxed', 'margin_rate_for_parent', 'cost_price', 'margin_from_children_to_parent',
                 'child_project_ids')
    def _compute_additional_margin(self):
        for rec in self:
            if rec.is_parent_project:
                if rec.margin_from_children_to_parent:
                    add_margin = 0
                    for child in rec.child_project_ids:
                        add_margin += child.margin * child.margin_rate_for_parent
                        child.additional_margin = -child.margin * child.margin_rate_for_parent
                    rec.additional_margin = add_margin
                else:
                    total_percent = 0
                    for child in rec.child_project_ids:
                        total_percent += child.margin_rate_for_parent
                        child.additional_margin = rec.margin * child.margin_rate_for_parent
                    rec.additional_margin = -(rec.margin * total_percent)
            elif rec.is_child_project:
                if rec.parent_project_id.margin_from_children_to_parent:
                    rec.additional_margin = -(rec.margin * rec.margin_rate_for_parent)
                    add_margin = 0
                    for child in rec.parent_project_id.child_project_ids:
                        add_margin += child.margin * child.margin_rate_for_parent
                    rec.parent_project_id.additional_margin = add_margin
                else:
                    rec.additional_margin = rec.parent_project_id.margin * rec.margin_rate_for_parent
                    total_percent = 0
                    for child in rec.parent_project_id.child_project_ids:
                        total_percent += child.margin_rate_for_parent
                    rec.parent_project_id.additional_margin = -(rec.parent_project_id.margin * total_percent)
            else:
                rec.additional_margin = 0

    @api.depends('child_project_ids.amount_untaxed', 'child_project_ids.cost_price', 'child_project_ids')
    def _compute_total_margin_of_child_projects(self):
        for rec in self:
            if rec.is_parent_project:
                rec.total_margin_of_child_projects = sum(
                    child_id.amount_untaxed - child_id.cost_price for child_id in rec.child_project_ids)
            else:
                rec.total_margin_of_child_projects = 0

    @api.depends('margin', 'additional_margin')
    def _compute_total_margin(self):
        for rec in self:
            rec.total_margin = rec.margin + rec.additional_margin

    @api.depends('planned_cost_flow_ids.amount_in_company_currency')
    def _compute_planned_amount_cost_flow(self):
        for rec in self:
            rec.planned_amount_total_cost_flow = 0
            if rec.step_status == 'project':
                rec.planned_amount_total_cost_flow = sum(rec.planned_cost_flow_ids.mapped('amount_in_company_currency'))
            elif rec.step_status == 'step':
                rec.planned_amount_total_cost_flow = sum(
                    rec.planned_step_cost_flow_ids.mapped('amount_in_company_currency'))

    def _check_project_is_child(self):
        for rec in self:
            rec.is_child_project = False
            if rec.parent_project_id:
                rec.is_child_project = True

    # ------------------------------------------------------
    # CORE METHODS OVERRIDES
    # ------------------------------------------------------

    def toggle_active(self):
        if not self.user_has_groups('project_budget.project_budget_admin'):
            raise_text = _("User should have admin rights")
            raise ValidationError(raise_text)
        return super(Project, self).toggle_active()

    # ------------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------------

    def _check_ax_case_step_project_number(self):
        for rec in self:
            pattern = r'(-\d{3}){3}$' if (rec.step_status == 'project' and not rec.project_have_steps) \
                or rec.step_status == 'step' else r'(?<!-\d{3})(?:-\d{3}){2}$'
            if not re.findall(pattern, rec.step_project_number):
                return False
        return True
