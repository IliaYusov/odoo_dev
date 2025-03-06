from odoo import api, fields, models


class Project(models.Model):
    _inherit = 'project_budget.projects'

    order_line_ids = fields.One2many('sale.order.line', 'opportunity_id', string='Sale Order Lines', copy=False,
                                     groups='sale_mngmnt.sale_group_user')
    order_id = fields.Many2one('sale.order', compute='_compute_sale_order_data', compute_sudo=True,
                               groups='sale_mngmnt.sale_group_user')
    order_amount_untaxed = fields.Monetary(compute='_compute_sale_order_data', compute_sudo=True,
                                           groups='sale_mngmnt.sale_group_user', readonly=True)
    order_amount_tax = fields.Monetary(compute='_compute_sale_order_data', compute_sudo=True,
                                       groups='sale_mngmnt.sale_group_user', readonly=True)
    order_amount_total = fields.Monetary(compute='_compute_sale_order_data', compute_sudo=True,
                                         groups='sale_mngmnt.sale_group_user', readonly=True)
    order_amount_purchase_total = fields.Monetary(compute='_compute_sale_order_data', compute_sudo=True,
                                                  groups='sale_mngmnt.sale_group_user', readonly=True)
    auto_create_sale_order = fields.Boolean(related='company_id.auto_create_sale_order',
                                            groups='sale_mngmnt.sale_group_user', readonly=True)

    # ------------------------------------------------------
    # COMPUTE METHODS
    # ------------------------------------------------------

    @api.depends('order_line_ids.price_subtotal', 'order_line_ids.price_tax', 'order_line_ids.price_total')
    def _compute_sale_order_data(self):
        for rec in self:
            rec.order_id = rec.order_ids[0].id if rec.order_ids else False
            rec.order_amount_untaxed = rec.order_id.amount_untaxed
            rec.order_amount_tax = rec.order_id.amount_tax
            rec.order_amount_total = rec.order_id.amount_total
            rec.order_amount_purchase_total = rec.order_id.amount_purchase_total

    # ------------------------------------------------------
    # CRUD
    # ------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        results = super().create(vals_list)
        sale_order_create_vals_list = []
        for opportunity, vals in zip(results, vals_list):
            if opportunity.step_status == 'project' and opportunity.budget_state == 'work' \
                    and opportunity.auto_create_sale_order:
                sale_order_create_vals_list.append(dict(
                    state='sale',
                    partner_id=opportunity.partner_id.id,
                    company_id=opportunity.company_id.id,
                    currency_id=opportunity.currency_id.id,
                    salesperson_id=opportunity.key_account_manager_id.id,
                    opportunity_id=opportunity.id
                ))
        if sale_order_create_vals_list:
            self.env['sale.order'].create(sale_order_create_vals_list)

        return results

    def write(self, vals):
        result = super(Project, self).write(vals)
        for rec in self.filtered(
                lambda pr: pr.step_status == 'project' and pr.budget_state == 'work' and pr.auto_create_sale_order):
            sale_order_write_vals = dict()
            if 'partner_id' in vals:
                sale_order_write_vals['partner_id'] = vals.get('partner_id', 0)
            if 'company_id' in vals:
                sale_order_write_vals['company_id'] = vals.get('company_id', 0)
            if 'currency_id' in vals:
                sale_order_write_vals['currency_id'] = vals.get('currency_id', 0)
            if 'key_account_manager_id' in vals:
                sale_order_write_vals['salesperson_id'] = vals.get('key_account_manager_id', 0)
            if sale_order_write_vals:
                rec.order_id.write(sale_order_write_vals)

        return result

    # ------------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------------

    @api.model
    def _init_data_sale_order(self):
        self.search([
            ('step_status', '=', 'project'),
            ('budget_state', '=', 'work'),
            ('auto_create_sale_order', '=', True),
            ('order_ids', '=', False)
        ])._create_sale_order()

    def _create_sale_order(self):
        for rec in self:
            self.env['sale.order'].create(dict(
                state='sale',
                partner_id=rec.partner_id.id,
                company_id=rec.company_id.id,
                currency_id=rec.currency_id.id,
                salesperson_id=rec.key_account_manager_id.id,
                opportunity_id=rec.id
            ))
