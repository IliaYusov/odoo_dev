from odoo import api, fields, models, _


# NOTE: временная прослойка, удалить во время перехода на целевую архитектуру модуля бюджетирования
class PlannedCostFlow(models.Model):
    _name = 'project_budget.planned_cost_flow'
    _description = 'Planned Cost Flow'
    _inherit = ['project_budget.flow.mixin']

    flow_id = fields.Char(string='Flow Id', copy=True, default='-', index=True, readonly=True, required=True)
    supplier_id = fields.Many2one('res.partner', string='Supplier', copy=True, domain="[('is_company', '=', True)]")
    budget_item_id = fields.Many2one('account.budget.item', string='Budget Item', copy=True,
                                     domain="[('direction', '=', 'expense'), ('child_ids', '=', False), ('company_ids', 'in', company_id)]")
    account_type_id = fields.Many2one('res.partner.bank.type', string='Account Type', copy=True)
    tax_id = fields.Many2one('account.tax', string='Tax', copy=True,
                             domain="[('company_id', '=', company_id), ('type_tax_use', '=', 'purchase')]",
                             required=True)
    amount_untaxed = fields.Monetary(string='Untaxed Amount', required=True, copy=True)
    amount_untaxed_in_company_currency = fields.Monetary(string='Amount In Company Currency',
                                                         compute='_compute_amount_in_company_currency', copy=True,
                                                         currency_field='company_currency_id', precompute=True,
                                                         store=True)
    amount_tax = fields.Float(string='Amount Tax', compute='_compute_amount', copy=True, precompute=True, store=True)
    amount = fields.Monetary(compute='_compute_amount', precompute=True, copy=True, store=True)

    # ------------------------------------------------------
    # COMPUTE METHODS
    # ------------------------------------------------------

    @api.depends('amount_untaxed', 'tax_id')
    def _compute_amount(self):
        for rec in self:
            tax_results = self.env['account.tax']._compute_taxes(base_lines=[rec._convert_to_tax_base_line_dict()])
            totals = list(tax_results['totals'].values())[0]
            amount_untaxed = totals['amount_untaxed']
            amount_tax = totals['amount_tax']

            rec.update({
                'amount_tax': amount_tax,
                'amount': amount_untaxed + amount_tax
            })

    @api.depends('amount_untaxed', 'amount', 'currency_rate')
    def _compute_amount_in_company_currency(self):
        for rec in self:
            if rec.currency_id == rec.company_currency_id:
                rec.amount_untaxed_in_company_currency = rec.amount_untaxed
                rec.amount_in_company_currency = rec.amount
            else:
                rec.amount_untaxed_in_company_currency = rec.amount_untaxed * rec.currency_rate

    # ------------------------------------------------------
    # CRUD
    # ------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('flow_id') or vals['flow_id'] == '-':
                vals['flow_id'] = self.env['ir.sequence'].sudo().next_by_code('project_budget.planned_cost_flow')
        return super(PlannedCostFlow, self).create(vals_list)

    # ------------------------------------------------------
    # CORE METHODS OVERRIDES
    # ------------------------------------------------------

    def name_get(self):
        result = []
        for rec in self:
            name = rec.date.strftime('%d/%m/%Y') + _(' | cost ') + rec.flow_id + _(
                ' | sum cash ') + f'{rec.amount:_.2f}'
            if rec.project_have_steps:
                name += _(' | step ') + (rec.step_project_child_id.project_id or '') + _(' | code ') + (
                        rec.step_project_child_id.step_project_number or '') + _(' | essence_project ') + (
                                rec.step_project_child_id.essence_project or '')
            result.append((rec.id, name))
        return result

    # ------------------------------------------------------
    # FLOW MIXIN
    # ------------------------------------------------------

    def action_copy_flow(self):
        super(PlannedCostFlow, self).action_copy_flow({'flow_id': '-'})

    # ------------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------------

    def _convert_to_tax_base_line_dict(self):
        self.ensure_one()
        return self.env['account.tax']._convert_to_tax_base_line_dict(
            self,
            partner=self.supplier_id,
            currency=self.currency_id,
            taxes=self.tax_id,
            price_unit=self.amount_untaxed,
            quantity=1
        )
