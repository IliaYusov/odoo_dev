from odoo import api, fields, models, _


class Contract(models.Model):
    _name = 'contract.contract'
    _description = 'Contract'
    _check_company_auto = True
    _order = 'id desc'

    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _get_default_employee_id(self):
        employee = self.env['hr.employee'].search([
            ('user_id', '=', self.env.user.id),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        return employee.id

    code = fields.Char(string='Code', copy=False, default=lambda self: _('New'), readonly=True, required=True)
    num = fields.Char(string='Number', copy=True, required=True, tracking=True)
    date = fields.Date(string='Date', copy=False, default=fields.Date.context_today, required=True, tracking=True)
    date_begin = fields.Date(string='Start Date', copy=False, default=fields.Date.context_today, required=True,
                             tracking=True)
    date_end = fields.Date(string='End Date', copy=False, default=fields.Date.context_today, required=True,
                           tracking=True)
    name = fields.Text(string='Name', copy=True, required=True, tracking=True)
    type_id = fields.Many2one('contract.type', string='Type', copy=True, required=True, tracking=True)
    kind_id = fields.Many2one('contract.kind', string='Kind', copy=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', copy=False, default=lambda self: self.env.company,
                                 required=True)
    partner_id = fields.Many2one('res.partner', string='Partner', copy=True, domain="[('type', '=', 'contact')]",
                                 ondelete='restrict', readonly=False, required=True, store=True, tracking=True)
    author_id = fields.Many2one('hr.employee', string='Author', check_company=True, copy=False,
                                default=_get_default_employee_id, readonly=True, required=True)
    responsible_id = fields.Many2one('hr.employee', string='Responsible', check_company=True, copy=False,
                                     default=_get_default_employee_id, required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', copy=False,
                                  default=lambda self: self.env.ref('base.RUB').id, required=True, tracking=True)
    sum = fields.Monetary(string='Sum', copy=False, tracking=True)
    description = fields.Html(string='Description', copy=False)
    active = fields.Boolean(copy=False, default=True, index=True, tracking=True)
    can_edit = fields.Boolean(compute='_compute_can_edit', default=True)
    properties = fields.Properties('Properties', definition='type_id.properties_definition', copy=True)
    property_count = fields.Integer(compute='_compute_property_count')

    attachment_ids = fields.One2many('ir.attachment', string='Attachments', compute='_compute_attachment_ids')
    attachment_count = fields.Integer(compute='_compute_attachment_count', string='Attachment Count')

    # ------------------------------------------------------
    # COMPUTE METHODS
    # ------------------------------------------------------

    def _compute_can_edit(self):
        for contract in self:
            contract.can_edit = contract.active

    def _compute_attachment_ids(self):
        for contract in self:
            contract.attachment_ids = self.env['ir.attachment'].search([
                ('res_model', '=', contract._name),
                ('res_id', '=', contract.id)
            ])

    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        for contract in self:
            contract.attachment_count = len(contract.attachment_ids)

    @api.depends('properties')
    def _compute_property_count(self):
        for contract in self:
            contract.property_count = len(contract.properties)

    # ------------------------------------------------------
    # CRUD
    # ------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('contract.contract') or _('New')

        records = super(Contract, self).create(vals_list)
        return records

    # ------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------

    def action_open_attachments(self):
        self.ensure_one()
        action_vals = {
            'name': _('Attachments'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,tree,form',
            'domain': [('id', 'in', self.attachment_ids.ids)],
            'context': "{'default_res_model': '%s','default_res_id': %d, 'search_default_group_by_res_model': True, 'create': %s, 'edit': %s 'delete': %s}" % (
                self._name, self.id, self.can_edit, self.can_edit, self.can_edit),
            'help': """
                        <p class="o_view_nocontent_smiling_face">%s</p>
                        """ % _('Add attachments for this contract')
        }
        if not self.can_edit:
            action_vals.update({'flags': {'mode': 'readonly'}})
        return action_vals
