from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class FlowMixin(models.AbstractModel):
    _name = 'project_budget.flow.mixin'
    _description = 'Flow Mixin'

    projects_id = fields.Many2one('project_budget.projects', string='Project', index=True, ondelete='cascade')
    project_have_steps = fields.Boolean(related='projects_id.project_have_steps', readonly=True)
    can_edit = fields.Boolean(related='projects_id.can_edit', readonly=True)
    company_id = fields.Many2one(related='projects_id.company_id', readonly=True)
    company_currency_id = fields.Many2one(related='company_id.currency_id', readonly=True)
    step_project_child_id = fields.Many2one('project_budget.projects', string='Step Project', index=True,
                                            ondelete='cascade')
    date = fields.Date(string='Date', copy=True, default=fields.Date.context_today, required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', copy=True,
                                  default=lambda self: self.env.company.currency_id)
    currency_id_domain = fields.Binary(compute='_compute_currency_id_domain')
    currency_rate = fields.Float(string='Currency Rate', compute='_compute_currency_rate', precompute=True, store=True)
    is_currency_company = fields.Boolean(compute='_compute_is_currency_company', default=True)
    amount = fields.Monetary(string='Amount', required=True, copy=True)
    amount_in_company_currency = fields.Monetary(string='Amount In Company Currency',
                                                 compute='_compute_amount_in_company_currency', copy=True,
                                                 currency_field='company_currency_id', precompute=True, store=True)
    # TODO: удалить данное поле после полной миграции на forecast_probability_id
    forecast = fields.Selection([
        ('from_project', 'From project/step'),
        ('commitment', 'Commitment'),
        ('reserve', 'Reserve'),
        ('potential', 'Potential')], copy=True, default='from_project', index=True, required=True,
        help="1 Of the project/stage - is calculated from the probability of the project (75 and higher - commitment, 50 - reserves, less than 50- potential "
             "\n 2 Commitment – falls into the forecast until the end of the 'commitment' period"
             "\n 3. Reserve – is included in the forecast until the end of the 'reserve' period"
             "\n 4. Potential – the amounts do not fall into the forecast until the end of the period, but can be entered by the seller to record information on the project (in this case, the absence of such will not be an error).")

    # ------------------------------------------------------
    # COMPUTE METHODS
    # ------------------------------------------------------

    @api.depends('projects_id')
    def _compute_currency_id_domain(self):
        for rec in self:
            rec.currency_id_domain = [
                ('id', 'in', [rec.projects_id.currency_id.id] + [self.env.company.currency_id.id])
            ]

    @api.depends('date', 'currency_id', 'company_currency_id')
    def _compute_currency_rate(self):
        for rec in self:
            rec.currency_rate = self.env['res.currency']._get_conversion_rate(
                from_currency=rec.currency_id,
                to_currency=rec.company_currency_id,
                company=rec.company_id,
                date=rec.date
            )

    @api.depends('amount', 'currency_rate')
    def _compute_amount_in_company_currency(self):
        for rec in self:
            if rec.currency_id == rec.company_currency_id:
                rec.amount_in_company_currency = rec.amount
            else:
                rec.amount_in_company_currency = rec.amount * rec.currency_rate

    @api.depends('currency_id', 'company_currency_id')
    def _compute_is_currency_company(self):
        for rec in self:
            rec.is_currency_company = rec.currency_id == rec.company_currency_id

    # ------------------------------------------------------
    # CRUD
    # ------------------------------------------------------

    def write(self, vals):
        if 'date' in vals:
            self._update_line_date(vals)

        result = super().write(vals)

        return result

    # ------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------

    def action_copy_flow(self, additional_values=None):
        self.ensure_one()
        if self.projects_id.budget_state == 'fixed':
            raise ValidationError(_('This project is in fixed budget. Copy deny'))
        additional_values = additional_values or {}
        self.browse(self.id).copy(additional_values)

    # ------------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------------

    def _update_line_date(self, vals):
        projects = self.mapped('projects_id')
        if self._fields.get('flow_id', False):
            for project in projects:
                flows = self.filtered(lambda x: x.projects_id == project and x.date != datetime.strptime(
                    vals['date'], DEFAULT_SERVER_DATE_FORMAT).date())
                if flows:
                    msg = '<b>' + _('The %s date has been updated.') % self.env['ir.model']._get(
                        self._name).name + '</b><ul>'
                    for flow in flows:
                        msg += '<li> %s: <br/>' % flow.flow_id
                        msg += _('Date: %(old_date)s -> %(new_date)s', old_date=flow.date.strftime('%d.%m.%Y'),
                                 new_date=datetime.strptime(vals['date'], '%Y-%m-%d').date().strftime(
                                     '%d.%m.%Y')) + '<br/>'
                    msg += '</ul>'
                    project.message_post(body=msg)
