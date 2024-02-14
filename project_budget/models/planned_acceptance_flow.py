from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import pytz
from datetime import date

class planned_acceptance_flow(models.Model):

    _name = 'project_budget.planned_acceptance_flow'
    _description = "planned acceptance flow"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name_to_show'
    def compute_distribution_sum(self):
        for row in self:
            row.distribution_sum_with_vat = row.distribution_sum_without_vat = 0
            row.distribution_sum_with_vat_ostatok = row.distribution_sum_without_vat_ostatok =0
            for distribution_acceptance in row.distribution_acceptance_ids:
                row.distribution_sum_with_vat += distribution_acceptance.sum_cash
                row.distribution_sum_without_vat += distribution_acceptance.sum_cash_without_vat
            row.distribution_sum_with_vat_ostatok =row.sum_cash - row.distribution_sum_with_vat
            row.distribution_sum_without_vat_ostatok = row.sum_cash_without_vat - row.distribution_sum_without_vat

    acceptance_id = fields.Char(string="acceptance_id", required=True, copy=True, default='-'
                                # lambda self: self.env['ir.sequence'].sudo().next_by_code('project_budget.planned_acceptance_flow')
                                , index=True, readonly=True)

    name_to_show = fields.Char(string='name_to_show', compute='_get_name_to_show')
    projects_id = fields.Many2one('project_budget.projects', string='projects_id', index=True, ondelete='cascade')
    etalon_budget = fields.Boolean(related='projects_id.etalon_budget', readonly=True)
    date_actual = fields.Datetime(related='projects_id.date_actual', readonly=True)
    budget_state = fields.Selection(related='projects_id.budget_state', readonly=True, store=True)
    approve_state = fields.Selection(related='projects_id.approve_state', readonly=True, store=True)

    project_have_steps = fields.Boolean(string="project have steps", related='projects_id.project_have_steps',
                                        readonly=True)
    project_steps_id = fields.Many2one('project_budget.project_steps', string='project_steps_id', index=True,ondelete='cascade')
    date_cash = fields.Date(string="date_cash" , required=True, copy=True)
    currency_id = fields.Many2one('res.currency', string='Account Currency', compute='_compute_reference')
    sum_cash_without_vat = fields.Monetary(string="sum_cash_without_vat", required=True, copy=True)
    sum_cash = fields.Monetary(string="sum_cash", required=True, copy=True, compute='_compute_sum')
    doc_cash = fields.Char(string="doc_cash", copy=True) #20230403 Вавилова Ирина сказла убрать из формы...

    distribution_acceptance_ids = fields.One2many(
        comodel_name='project_budget.distribution_acceptance',
        inverse_name='planned_acceptance_flow_id',
        string="distribution cash fact by plan", auto_join=True,copy=False)

    distribution_sum_with_vat = fields.Monetary(string="distribution sum with vat", compute='_compute_distribution_sum')
    distribution_sum_without_vat = fields.Monetary(string="distribution sum without vat", compute='_compute_distribution_sum')
    distribution_sum_without_vat_ostatok = fields.Monetary(string="distribution_sum_without_vat_ostatok", compute='_compute_distribution_sum')
    distribution_sum_with_vat_ostatok = fields.Monetary(string="distribution_sum_with_vat_ostatok", compute='_compute_distribution_sum')

    forecast = fields.Selection([('from_project', 'From project/step')
                                    , ('commitment', 'Commitment')
                                    , ('reserve', 'Reserve')
                                    , ('potential', 'Potential')], required=True, index=True, default='from_project'
                                , copy=True, tracking=True,
            help = "1 Of the project/stage - is calculated from the probability of the project (75 and higher - commitment, 50 - reserves, less than 50- potential "
                   "\n 2 Commitment – falls into the forecast until the end of the 'commitment' period"
                   "\n 3. Reserve – is included in the forecast until the end of the 'reserve' period"
                   "\n 4. Potential – the amounts do not fall into the forecast until the end of the period, but can be entered by the seller to record information on the project (in this case, the absence of such will not be an error)."

                                )

    @api.depends('date_cash','project_steps_id','acceptance_id','sum_cash_without_vat')
    def _get_name_to_show(self):
        for prj in self:
            prj.name_to_show = prj.date_cash.strftime("%d/%m/%Y") + _(' | acceptance ') + prj.acceptance_id + _(' | sum cash without vat ') + f'{prj.sum_cash_without_vat:_.2f}'
            if prj.project_have_steps == True:
                prj.name_to_show += _(' | step ') + (prj.project_steps_id.step_id or '') + _(' | code ') + (prj.project_steps_id.code or '') + _(' | essence_project ') + (prj.project_steps_id.essence_project or '')

    @ api.depends('projects_id.currency_id')
    def _compute_reference(self):
        for row in self:
            row.currency_id = row.projects_id.currency_id

    @api.depends("sum_cash_without_vat","project_steps_id.vat_attribute_id","projects_id.vat_attribute_id")
    def _compute_sum(self):
        for row in self:
            if row.project_steps_id:
                row.sum_cash = row.sum_cash_without_vat * (1 + row.project_steps_id.vat_attribute_id.percent / 100)
            else:
                row.sum_cash = row.sum_cash_without_vat * (1 + row.projects_id.vat_attribute_id.percent / 100)

    @api.onchange("distribution_acceptance_ids")
    def _compute_distribution_sum(self):
        self.compute_distribution_sum()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('acceptance_id') or vals['acceptance_id'] == '-':
                vals['acceptance_id'] = self.env['ir.sequence'].sudo().next_by_code('project_budget.planned_acceptance_flow')
        return super().create(vals_list)

    def action_copy_planned_acceptance(self):
        self.ensure_one()
        if self.projects_id.budget_state == 'fixed':  # сделка в зафиксированном бюджете
            raise_text = _("This project is in fixed budget. Copy deny")
            raise (ValidationError(raise_text))
        self.env['project_budget.planned_acceptance_flow'].browse(self.id).copy({'acceptance_id': '-'})

    # @api.returns('self', lambda value: value.id)
    # def copy(self, default=None):
    #     self.ensure_one()
    #     print('planned_acceptance_flow self.env.context = ', self.env.context)
    #
    #     if self.env.context.get('form_fix_budget'):
    #         return super(planned_acceptance_flow, self).copy()
    #     else:
    #         return False
