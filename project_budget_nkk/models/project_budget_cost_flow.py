from odoo import api, fields, models, _


# NOTE: временная прослойка, удалить во время перехода на целевую архитектуру модуля бюджетирования
class PlannedCostFlow(models.Model):
    _name = 'project_budget.planned_cost_flow'
    _description = 'Planned Cost Flow'
    _inherit = ['project_budget.flow.mixin']

    flow_id = fields.Char(string='Flow Id', copy=True, default='-', index=True, readonly=True, required=True)
    supplier_id = fields.Many2one('res.partner', string='Supplier', domain="[('is_company', '=', True)]")
    budget_item_id = fields.Many2one('account.budget.item', string='Budget Item', copy=True,
                                     domain="[('direction', '=', 'expense'), ('child_ids', '=', False)]")

    # ------------------------------------------------------
    # CRUD
    # ------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('flow_id') or vals['flow_id'] == '-':
                vals['flow_id'] = self.env['ir.sequence'].sudo().next_by_code('project_budget_nkk.planned_cost_flow')
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
