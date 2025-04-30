from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

POST_DIRECTIONS = [
    ('income', 'Income'),
    ('expense', 'Expense')
]


class AccountBudgetItem(models.Model):
    _name = 'account.budget.item'
    _description = 'Budget Item'
    _order = 'sequence, name, id'

    code = fields.Char(string='Code', required=True)
    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(default=1, required=True)
    direction = fields.Selection(POST_DIRECTIONS, string='Direction', index=True, required=True)
    account_ids = fields.Many2many('account.account', relation='account_budget_rel', column1='budget_id',
                                   column2='account_id', string='Accounts',
                                   domain="[('deprecated', '=', False), ('company_id', 'in', (False, company_id))]")
    hierarchy_level = fields.Integer(string='Level', compute='_compute_hierarchy_level', precompute=True,
                                     readonly=False, recursive=True, required=True, store=True)
    parent_id = fields.Many2one('account.budget.item', string='Parent Budget Item', index=True,
                                domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    child_ids = fields.One2many('account.budget.item', 'parent_id', string='Child Items')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)

    # ------------------------------------------------------
    # CONSTRAINS
    # ------------------------------------------------------

    # @api.constrains('account_ids')
    # def _check_account_ids(self):
    #     for rec in self:
    #         if not rec.account_ids:
    #             raise ValidationError(_('The budget must have at least one account.'))

    # ------------------------------------------------------
    # COMPUTE METHODS
    # ------------------------------------------------------

    @api.depends('parent_id.hierarchy_level')
    def _compute_hierarchy_level(self):
        for rec in self:
            if rec.parent_id:
                rec.hierarchy_level = rec.parent_id.hierarchy_level + 2
            else:
                rec.hierarchy_level = 1
