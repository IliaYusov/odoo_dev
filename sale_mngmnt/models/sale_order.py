from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

SALE_ORDER_STATES = [
    ('draft', 'Quotation'),
    ('sent', 'Quotation Sent'),
    ('sale', 'Sales Order'),
    ('cancel', 'Cancelled')
]


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['mail.thread']
    _description = 'Sales Order'
    _order = 'date_order desc, id desc'
    _check_company_auto = True

    _sql_constraints = [
        ('date_order_conditional_required',
         "CHECK((state = 'sale' AND date_order IS NOT NULL) OR state != 'sale')",
         'A confirmed sales order requires a confirmation date.'),
    ]

    def _get_salesperson_id_domain(self):
        return "[('user_id.groups_id', 'in', %s), '|', ('company_id', '=', False), ('company_id', '=', company_id)]" \
            % self.env.ref('sale_mngmnt.sale_group_user').id

    def _get_default_account_price_include(self):
        return True if self.env.company.account_price_include == 'tax_included' else False

    name = fields.Char(string='Name', copy=False, default=lambda self: _('New'), index='trigram', readonly=True,
                       required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, index=True, required=True)
    partner_id = fields.Many2one('res.partner', string='Customer', copy=True,
                                 domain="[('is_company', '=', True), ('company_id', 'in', (False, company_id))]",
                                 index=True, ondelete='restrict', required=True, tracking=True)
    state = fields.Selection(SALE_ORDER_STATES, string='Status', copy=False, default='draft', index=True, readonly=True,
                             tracking=True)
    date_order = fields.Date(string='Order Date', copy=False, default=fields.Datetime.today, index=True,
                             required=True, tracking=True)
    date_validity = fields.Date(string='Expiration', compute='_compute_date_validity', copy=False, precompute=True,
                                readonly=False, store=True,
                                help='Validity of the order, after that you will not able to sign & pay the quotation.')
    fiscal_position_id = fields.Many2one('account.fiscal.position', compute='_compute_fiscal_position_id',
                                         string='Fiscal Position', copy=False, check_company=True, precompute=True,
                                         readonly=False, store=True,
                                         help='Fiscal positions are used to adapt taxes and accounts for particular customers or sales orders/invoices.'
                                              'The default value comes from the customer.')
    comment = fields.Html(string='Comment')
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', compute='_compute_pricelist_id',
                                   domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                   precompute=True, readonly=False, tracking=True, store=True,
                                   help='If you change the pricelist, only newly added lines will be affected.')
    currency_id = fields.Many2one('res.currency', string='Currency', compute='_compute_currency_id', copy=False,
                                  ondelete='restrict', precompute=True, tracking=True, store=True)
    currency_rate = fields.Float(string='Currency Rate', compute='_compute_currency_rate', precompute=True, store=True)
    salesperson_id = fields.Many2one('hr.employee', string='Salesperson', copy=True, domain=_get_salesperson_id_domain,
                                     index=True, tracking=True)
    line_ids = fields.One2many('sale.order.line', 'order_id', string='Order Lines', copy=True)

    account_price_include = fields.Boolean(string='Price Include', default=_get_default_account_price_include,
                                           required=True,
                                           help='Check this if the price you use on the product includes this tax.')
    amount_untaxed = fields.Monetary(string='Untaxed Amount', compute='_compute_amount', tracking=True, store=True)
    amount_tax = fields.Monetary(string='Taxes', compute='_compute_amount', store=True)
    amount_total = fields.Monetary(string='Amount With Tax', compute='_compute_amount', tracking=True, store=True)

    show_update_fpos = fields.Boolean(string='Has Fiscal Position Changed', store=False)
    can_edit = fields.Boolean(compute='_compute_can_edit', default=True)

    # ------------------------------------------------------
    # CONSTRAINS
    # ------------------------------------------------------

    @api.constrains('company_id', 'line_ids')
    def _check_line_company_id(self):
        for order in self:
            companies = order.line_ids.product_id.company_id
            if companies and companies != order.company_id:
                bad_products = order.line_ids.product_id.filtered(
                    lambda p: p.company_id and p.company_id != order.company_id)
                raise ValidationError(_(
                    'Your quotation contains products from company %(product_company)s whereas your quotation belongs to company %(quote_company)s.'
                    'Please change the company of your quotation or remove the products from other companies (%(bad_products)s).',
                    product_company=', '.join(companies.mapped('display_name')),
                    quote_company=order.company_id.display_name,
                    bad_products=', '.join(bad_products.mapped('display_name')),
                ))

    # ------------------------------------------------------
    # COMPUTE METHODS
    # ------------------------------------------------------

    def _compute_can_edit(self):
        for rec in self:
            rec.can_edit = rec.state == 'draft'

    @api.depends('company_id')
    def _compute_date_validity(self):
        today = fields.Date.context_today(self)
        for order in self:
            days = order.company_id.quotation_validity_days
            if days > 0:
                order.date_validity = today + timedelta(days)
            else:
                order.date_validity = False

    @api.depends('partner_id', 'company_id')
    def _compute_fiscal_position_id(self):
        cache = {}
        for rec in self:
            if not rec.partner_id:
                rec.fiscal_position_id = False
                continue
            fpos_id_before = rec.fiscal_position_id.id
            key = (rec.company_id.id, rec.partner_id.id)
            if key not in cache:
                cache[key] = self.env['account.fiscal.position'].with_company(rec.company_id).\
                    _get_fiscal_position(rec.partner_id).id
            if fpos_id_before != cache[key] and rec.line_ids:
                rec.show_update_fpos = True
            rec.fiscal_position_id = cache[key]

    @api.depends('currency_id', 'date_order', 'company_id')
    def _compute_currency_rate(self):
        for rec in self:
            rec.currency_rate = self.env['res.currency']._get_conversion_rate(
                from_currency=rec.company_id.currency_id,
                to_currency=rec.currency_id,
                company=rec.company_id,
                date=(rec.date_order or fields.Date.today())
            )

    @api.depends('partner_id', 'company_id')
    def _compute_pricelist_id(self):
        for rec in self:
            if rec.state != 'draft':
                continue
            if not rec.partner_id:
                rec.pricelist_id = False
                continue
            rec = rec.with_company(rec.company_id)
            rec.pricelist_id = rec.partner_id.property_product_pricelist

    @api.depends('pricelist_id', 'company_id')
    def _compute_currency_id(self):
        for rec in self:
            rec.currency_id = rec.pricelist_id.currency_id or rec.company_id.currency_id

    @api.depends('line_ids.price_subtotal', 'line_ids.price_tax', 'line_ids.price_total')
    def _compute_amount(self):
        for rec in self:
            lines = rec.line_ids

            if rec.company_id.tax_calculation_rounding_method == 'round_globally':
                tax_results = self.env['account.tax']._compute_taxes([
                    line._convert_to_tax_base_line_dict()
                    for line in lines
                ])
                totals = tax_results['totals']
                amount_untaxed = totals.get(rec.currency_id, {}).get('amount_untaxed', 0.0)
                amount_tax = totals.get(rec.currency_id, {}).get('amount_tax', 0.0)
            else:
                amount_untaxed = sum(lines.mapped('price_subtotal'))
                amount_tax = sum(lines.mapped('price_tax'))

            rec.amount_untaxed = amount_untaxed
            rec.amount_tax = amount_tax
            rec.amount_total = rec.amount_untaxed + rec.amount_tax

    # ------------------------------------------------------
    # CRUD
    # ------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'company_id' in vals:
                self = self.with_company(vals['company_id'])
            if vals.get('name', _('New')) == _('New'):
                seq_date = fields.Datetime.context_timestamp(
                    self, fields.Datetime.to_datetime(vals['date_order'])
                ) if 'date_order' in vals else None
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'sale.order', sequence_date=seq_date) or _('New')

        return super().create(vals_list)

    # ------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------

    def action_quotation_sent(self):
        if self.filtered(lambda so: so.state != 'draft'):
            raise UserError(_('Only draft orders can be marked as sent directly.'))
        self.write({'state': 'sent'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_confirm(self):
        self.write({'state': 'sale'})

    # ------------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------------

    def _get_lang(self):
        self.ensure_one()

        if self.partner_id.lang and not self.partner_id.is_public:
            return self.partner_id.lang

        return self.env.lang
