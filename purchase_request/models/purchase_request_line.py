from odoo import api, Command, fields, models, _
from odoo.tools import get_lang


class PurchaseRequestLine(models.Model):
    _name = 'purchase.request.line'
    _description = "Purchase Request Line"
    _order = 'request_id, sequence, id'
    _check_company_auto = True

    name = fields.Text(string='Description', compute='_compute_name', required=True, store=True)
    request_id = fields.Many2one('purchase.request', string='Request', ondelete='cascade', copy=True, index=True)
    company_id = fields.Many2one(related='request_id.company_id', string='Company', copy=False, index=True,
                                 precompute=True, store=True)
    sequence = fields.Integer(string='Sequence', copy=True, default=1)
    vendor_id = fields.Many2one('res.partner', string='Vendor', copy=False, domain="[('is_company', '=', True)]")
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict', copy=False,
                                 change_default=True, check_company=True, index='btree_not_null',
                                 domain="[('purchase_ok', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    product_template_id = fields.Many2one('product.template', string='Product Template',
                                          compute='_compute_product_template_id',
                                          readonly=False, search='_search_product_template_id',
                                          domain=[('purchase_ok', '=', True)])
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', copy=False,
                                              depends=['product_id'], readonly=True)
    product_barcode = fields.Char(related='product_id.barcode', string='Barcode', copy=False, depends=['product_id'],
                                  readonly=True)
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure', compute='_compute_product_uom',
                                     ondelete='restrict', copy=False, readonly=False, precompute=True, store=True,
                                     domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_qty = fields.Float(string='Quantity', copy=False,
                                   digits='Product Unit of Measure', default=1.0, store=True, readonly=False,
                                   required=True, precompute=True)
    guarantee_on_demand = fields.Integer(string='Guarantee On Demand', copy=False)
    software_certification = fields.Char(string='Software Certification', copy=False)
    licence_start_date = fields.Date(string='Licence Start', copy=False)
    licence_end_date = fields.Date(string='Licence End', copy=False)
    technical_requirements = fields.Boolean(string='Only Technical Requirements', default=False)

    component_ids = fields.One2many('purchase.request.line.component', 'request_line_id', string='Components')
    characteristic_ids = fields.One2many('purchase.request.line.characteristic', 'request_line_id',
                                         string='Characteristics')
    position_type = fields.Char(string='Type', copy=False, default='request', store=False)

    estimation_count = fields.Integer(string='Estimation Count', compute='_compute_estimation_count')
    estimation_ids = fields.One2many('purchase.request.line.estimation', string='Estimations',
                                     compute='_compute_estimation_ids')

    def _search_product_template_id(self, operator, value):
        return [('product_id.product_tmpl_id', operator, value)]

    @api.depends('product_id')
    def _compute_name(self):
        for line in self:
            if not line.product_id:
                continue
            if not line.name:
                product_ctx = {'lang': get_lang(line.env, self.env.user.company_id.partner_id.lang).code}
                line.name = line._get_product_purchase_description(line.product_id.with_context(product_ctx))

    @api.depends('product_id')
    def _compute_product_template_id(self):
        for line in self:
            line.product_template_id = line.product_id.product_tmpl_id

    @api.depends('product_id')
    def _compute_product_uom(self):
        for line in self:
            if not line.product_uom_id or (line.product_id.uom_id.id != line.product_uom_id.id):
                line.product_uom_id = line.product_id.uom_id

    def _compute_estimation_ids(self):
        for line in self:
            line.estimation_ids = self.env['purchase.request.line.estimation'].search([
                ('request_line_id', '=', line.id)
            ])

    @api.depends('estimation_ids')
    def _compute_estimation_count(self):
        for line in self:
            line.estimation_count = len(line.estimation_ids)

    def _get_product_purchase_description(self, product_lang):
        self.ensure_one()
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase

        return name

    def action_open_estimations(self):
        self.ensure_one()
        components = []
        characteristics = []
        for component in self.component_ids:
            components.append((Command.CREATE, 0, dict(
                request_line_id=False,
                sequence=component.sequence,
                vendor_id=component.vendor_id.id,
                product_id=component.product_id.id,
                product_uom_id=component.product_uom_id.id,
                product_uom_qty=component.product_uom_qty
            )))
        for characteristic in self.characteristic_ids:
            characteristics.append((Command.CREATE, 0, dict(
                request_line_id=False,
                sequence=characteristic.sequence,
                characteristic_id=characteristic.characteristic_id.id,
                characteristic_uom_id=characteristic.characteristic_uom_id.id,
                characteristic_value=characteristic.characteristic_value
            )))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Estimations'),
            'res_model': 'purchase.request.line.estimation',
            'views': [[self.env.ref('purchase_request.purchase_request_line_estimation_view_tree').id, 'list'],
                      [self.env.ref('purchase_request.purchase_request_line_estimation_view_form').id, 'form']],
            'domain': [('id', 'in', self.estimation_ids.ids)],
            'context': {
                'default_request_id': self.request_id.id,
                'default_request_line_id': self.id,
                'default_vendor_id': self.vendor_id.id,
                'default_presale_id': self.id,
                'default_product_id': self.product_id.id,
                'default_product_uom_id': self.product_uom_id.id,
                'default_product_uom_qty': self.product_uom_qty,
                'default_currency_id': self.company_id.currency_id.id,
                'default_technical_requirements': self.technical_requirements,
                'default_component_ids': components,
                'default_characteristic_ids': characteristics,
                'hide_add_info': True
            }
        }
