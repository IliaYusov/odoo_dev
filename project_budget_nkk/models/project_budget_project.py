import re

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
    margin_from_children_to_parent = fields.Boolean(string="Margin from Children to Parent", default=True, copy=True)
    margin_from_children_to_parent_related = fields.Boolean(related="parent_project_id.margin_from_children_to_parent")
    additional_margin = fields.Monetary(string="Margin from Related Projects", compute='_compute_additional_margin',
                                        store=True, copy=True)
    total_margin_of_child_projects = fields.Monetary(string="total margin of child projects",
                                                     compute='_compute_total_margin_of_child_projects')
    total_margin = fields.Monetary(string="Total Margin", compute='_compute_total_margin')

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

    # ------------------------------------------------------
    # COMPUTE METHODS
    # ------------------------------------------------------

    @api.depends('step_project_parent_id.technological_direction_id', 'step_project_parent_id.project_supervisor_id')
    def _compute_parent_data(self):
        for rec in self.filtered(lambda pr: pr.step_status == 'step'):
            rec.technological_direction_id = rec.step_project_parent_id.technological_direction_id
            rec.project_supervisor_id = rec.step_project_parent_id.project_supervisor_id

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

    @api.depends('total_amount_of_revenue', 'margin_rate_for_parent', 'cost_price', 'margin_from_children_to_parent',
                 'child_project_ids')
    def _compute_additional_margin(self):
        for rec in self:
            if rec.is_parent_project:
                if rec.margin_from_children_to_parent:
                    add_margin = 0
                    for child in rec.child_project_ids:
                        add_margin += child.margin_income * child.margin_rate_for_parent
                        child.additional_margin = -child.margin_income * child.margin_rate_for_parent
                    rec.additional_margin = add_margin
                else:
                    total_percent = 0
                    for child in rec.child_project_ids:
                        total_percent += child.margin_rate_for_parent
                        child.additional_margin = rec.margin_income * child.margin_rate_for_parent
                    rec.additional_margin = -(rec.margin_income * total_percent)
            elif rec.is_child_project:
                if rec.parent_project_id.margin_from_children_to_parent:
                    rec.additional_margin = -(rec.margin_income * rec.margin_rate_for_parent)
                    add_margin = 0
                    for child in rec.parent_project_id.child_project_ids:
                        add_margin += child.margin_income * child.margin_rate_for_parent
                    rec.parent_project_id.additional_margin = add_margin
                else:
                    rec.additional_margin = rec.parent_project_id.margin_income * rec.margin_rate_for_parent
                    total_percent = 0
                    for child in rec.parent_project_id.child_project_ids:
                        total_percent += child.margin_rate_for_parent
                    rec.parent_project_id.additional_margin = -(rec.parent_project_id.margin_income * total_percent)
            else:
                rec.additional_margin = 0

    @api.depends('child_project_ids.total_amount_of_revenue', 'child_project_ids.cost_price', 'child_project_ids')
    def _compute_total_margin_of_child_projects(self):
        for rec in self:
            if rec.is_parent_project:
                rec.total_margin_of_child_projects = sum(
                    child_id.total_amount_of_revenue - child_id.cost_price for child_id in rec.child_project_ids)
            else:
                rec.total_margin_of_child_projects = 0

    @api.depends('margin_income', 'additional_margin')
    def _compute_total_margin(self):
        for rec in self:
            rec.total_margin = rec.margin_income + rec.additional_margin

    def _check_project_is_child(self):
        for rec in self:
            rec.is_child_project = False
            if rec.parent_project_id:
                rec.is_child_project = True

    # ------------------------------------------------------
    # CONSTRAINS
    # ------------------------------------------------------

    @api.constrains('stage_id', 'total_amount_of_revenue', 'cost_price', 'planned_acceptance_flow_ids',
                    'planned_cash_flow_ids', 'planned_step_acceptance_flow_ids', 'planned_step_cash_flow_ids')
    def _check_financial_data_is_present(self):
        for project in self.filtered(lambda pr: pr.budget_state == 'work'):
            # print(project.env.context.get('form_fix_budget'))
            if project.env.context.get('form_fix_budget'):
                continue
            if (project.stage_id.code in ('30', '50', '75', '100')
                    and project.total_amount_of_revenue == 0
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
