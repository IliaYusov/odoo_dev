from odoo import api, fields, models, _


class Document(models.Model):
    _name = 'document_flow.document'
    _description = 'Document'
    _check_company_auto = True

    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_employee_id(self):
        employee = self.env['hr.employee'].search([
            ('user_id', '=', self.env.user.id),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        return employee.id

    code = fields.Char(string='Code', copy=False, default=lambda self: _('New'), readonly=True, required=True)
    name = fields.Char(string='Name', copy=True, required=True, tracking=True)
    date = fields.Date(string='Date', copy=False, default=fields.Date.context_today, required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', copy=False, default=lambda self: self.env.company,
                                 required=True)
    author_id = fields.Many2one('hr.employee', string='Author', check_company=True, default=_default_employee_id,
                                required=True)
    kind_id = fields.Many2one('document_flow.document.kind', string='Kind', copy=True, ondelete='restrict',
                              required=True, tracking=True)
    template_id = fields.Many2one(related='kind_id.template_id', string='Template', copy=False, readonly=True)
    description = fields.Html(string='Description', copy=False)
    active = fields.Boolean(copy=False, default=True, index=True)
    properties = fields.Properties('Properties', definition='kind_id.properties_definition', copy=True)
    can_edit = fields.Boolean(compute='_compute_can_edit', default=True)

    # ------------------------------------------------------
    # COMPUTE METHODS
    # ------------------------------------------------------

    def _compute_can_edit(self):
        for contract in self:
            contract.can_edit = contract.active

    # ------------------------------------------------------
    # CRUD
    # ------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                next_code = False
                if vals.get('kind_id', False):
                    k_id = self.env['document_flow.document.kind'].browse(vals.get('kind_id'))
                    if k_id and k_id.sequence_id:
                        next_code = k_id.sequence_id.next_by_code('document_flow.document.kind.template') or _('New')
                vals['code'] = self.env['ir.sequence'].next_by_code('document_flow.document') or _(
                    'New') if not next_code else next_code

        records = super(Document, self).create(vals_list)
        return records
