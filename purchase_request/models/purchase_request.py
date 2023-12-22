from odoo import api, Command, fields, models, _
from odoo.exceptions import ValidationError

REQUEST_STATES = [
    ('draft', _('RFP')),
    ('done', _('Done')),
    ('cancel', _('Canceled'))
]


class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _description = 'Purchase Request'
    _check_company_auto = True

    _inherit = ['mail.thread', 'mail.activity.mixin']

    code = fields.Char(string='Code', compute='_compute_code', copy=False, required=True, store=True, default=_('New'))
    name = fields.Char(string='Name', copy=True, required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', copy=False, required=True,
                                 default=lambda self: self.env.company)
    state = fields.Selection(REQUEST_STATES, string='Status', copy=False, index=True, readonly=True, tracking=True,
                             default='draft')
    project_id = fields.Many2one('project_budget.projects', string='Project', copy=True, required=True, tracking=True,
                                 domain="[('budget_state', '=', 'work')]")
    partner_id = fields.Many2one('res.partner', related='project_id.partner_id',
                                 string='Partner', copy=False, readonly=True, required=True)
    partner_vat = fields.Char(related='partner_id.vat', string='Vat', copy=False, readonly=True, required=True)
    request_type_id = fields.Many2one('purchase.request.type', string='Request Type', copy=True, required=True)
    competition_link = fields.Char(string='Competition Link', copy=False, tracking=True)
    application_deadline = fields.Datetime(string='Application Deadline', copy=False, required=True, tracking=True,
                                           default=fields.Datetime.now())
    date_price = fields.Date(string='Date Price', copy=False, required=True, tracking=True,
                             default=fields.Date.context_today)
    date_delivery = fields.Date(string='Delivery Date', copy=False, required=True, tracking=True,
                                default=fields.Date.context_today)
    responsible_ids = fields.Many2many('hr.employee', relation='purchase_request_employee_rel',
                                       column1='request_id', column2='employee_id', string='Responsible', copy=False,
                                       check_company=True)
    partner_payment_term_id = fields.Many2one('account.payment.term', string='Partner Payment Terms', copy=False,
                                              check_company=True, required=True, tracking=True, precompute=True,
                                              store=True, default=lambda self: self.partner_id.property_payment_term_id)
    calc_delivery_cost = fields.Boolean(string='Calculation Delivery Cost', copy=False, default=False, tracking=True)
    partial_shipment = fields.Boolean(string='Partial Shipment', copy=False, default=False, tracking=True)
    special_conditions = fields.Html(string='Special Conditions', copy=False)

    number_packages = fields.Integer(string='Number Packages', copy=False, tracking=True)

    currency_id = fields.Many2one('res.currency', string='Currency', copy=False, required=True,
                                  default=lambda self: self.env.ref('base.RUB').id)
    sum = fields.Monetary(string='Sum', copy=False, required=False, tracking=True)
    line_ids = fields.One2many('purchase.request.line', 'request_id', string='Request Lines')
    line_delivery_ids = fields.One2many('purchase.request.line.delivery', 'request_id',
                                        string='Request Lines Delivery')

    process_id = fields.Many2one('document_flow.process', string='Process', compute='_compute_process_id')
    process_state = fields.Selection(string='State', related='process_id.state', readonly=True)

    estimation_count = fields.Integer(string='Estimation Count', compute='_compute_estimation_count')
    estimation_ids = fields.One2many('purchase.request.line.estimation', string='Estimations',
                                     compute='_compute_estimation_ids')

    attachment_count = fields.Integer(string='Attachment Count', compute='_compute_attachment_count')
    attachment_ids = fields.One2many('ir.attachment', string='Attachments', compute='_compute_attachment_ids')

    def _compute_process_id(self):
        for request in self:
            request.process_id = self.env['document_flow.processing'].search([
                ('parent_ref', '=', '%s,%d' % (request._name, request.id))
            ]).process_id

    def _compute_estimation_ids(self):
        for request in self:
            request.estimation_ids = self.env['purchase.request.line.estimation'].search([
                ('request_id', '=', request.id)
            ])

    @api.depends('estimation_ids')
    def _compute_estimation_count(self):
        for request in self:
            request.estimation_count = len(request.estimation_ids)

    def _compute_attachment_ids(self):
        for request in self:
            request.attachment_ids = self.env['ir.attachment'].search([
                '|',
                '&', ('res_model', '=', self._name), ('res_id', 'in', [request.id]),
                '&', ('res_model', '=', 'task.task'), ('res_id', 'in', request.process_id.task_ids.ids)
            ])

    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        for request in self:
            request.attachment_count = len(request.attachment_ids)

    @api.depends('name', 'project_id')
    def _compute_code(self):
        for request in self:
            request.code = 'CRM %s-%s-%s-%s' % (
                request.project_id.project_id,
                request.name,
                request.project_id.project_office_id.name,
                request.project_id.project_manager_id.user_id.name
            )

    @api.model
    def create(self, vals_list):
        res = super(PurchaseRequest, self).create(vals_list)
        res._check_delivery_addresses()
        return res

    def write(self, vals):
        if vals.get('special_conditions'):
            self.message_post(body=_('<ul><li>%(old_value)s --> %(new_value)s (Special Conditions)</li></ul>',
                                     old_value=self.special_conditions, new_value=vals.get('special_conditions')))
        # self._check_delivery_addresses()
        res = super(PurchaseRequest, self).write(vals)
        return res

    def _check_delivery_addresses(self):
        if self.calc_delivery_cost and (not self.line_delivery_ids or any(
                self.line_delivery_ids.filtered(lambda line: not line.delivery_address_id))):
            raise ValidationError(_('You must indicate delivery addresses'))

    def action_open_attachments(self):
        self.ensure_one()
        return {
            'name': _('Attachments'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,tree,form',
            'domain': ['|',
                       '&', ('res_model', '=', self._name), ('res_id', 'in', [self.id]),
                       '&', ('res_model', '=', 'task.task'), ('res_id', 'in', self.process_id.task_ids.ids)
                       ],
            'context': "{'default_res_model': '%s','default_res_id': %d}" % (self._name, self.id)
        }

    def action_estimation_completed(self):
        self.ensure_one()
        if any(self.line_ids.filtered(lambda l: l.estimation_count == 0)):
            raise ValidationError(_('Not all positions of request were regarded'))
        if self.process_id:
            if len(self.process_id.active_task_ids) == 1:
                self.process_id.active_task_ids[0]._close_task_forcibly('ok')
        self.write({'state': 'done'})

    def action_open_estimations(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Estimations'),
            'res_model': 'purchase.request.line.estimation',
            'views': [[self.env.ref('purchase_request.purchase_request_line_estimation_view_tree').id, 'list'],
                      [self.env.ref('purchase_request.purchase_request_line_estimation_view_form').id, 'form']],
            'domain': [('id', 'in', self.estimation_ids.ids)],
            'context': {
                'search_default_group_by_request_line_id': True
            },
            'flags': {'mode': 'readonly'}
        }

    def action_open_processing(self):
        self.ensure_one()
        processing = self.env['document_flow.processing'].search([
            ('parent_ref', '=', '%s,%d' % (self._name, self.id))
        ])
        return {
            'view_mode': 'form',
            'res_model': 'document_flow.processing',
            'type': 'ir.actions.act_window',
            'res_id': processing.id,
            'context': {
                'default_parent_ref': '%s,%d' % (self._name, self.id),
                'default_parent_ref_type': self._name,
                'default_parent_ref_id': self.id
            }
        }

    def action_fill_delivery_info_by_lines(self):
        self.ensure_one()
        if self.calc_delivery_cost:
            if self.line_delivery_ids:
                self.line_delivery_ids.unlink()
            addresses = self.env['res.partner'].search([
                ('parent_id', '=', self.partner_id.id),
                ('type', '=', 'delivery')
            ])
            for line in self.line_ids.filtered(lambda l: l.product_id.detailed_type != 'service'):
                self.env['purchase.request.line.delivery'].with_context(create_without_delivery=True).create(dict(
                    request_id=self.id,
                    request_line_id=line.id,
                    delivery_address_id=addresses[0].id if any(addresses) else False
                ))
