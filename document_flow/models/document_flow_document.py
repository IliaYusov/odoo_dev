from odoo import _, models, fields, api


class DocumentType(models.Model):
    _name = 'document_flow.document.type'
    _description = 'Document Type'

    name = fields.Char(string='Name', required=True, copy=True)
    sequence_id = fields.Many2one('ir.sequence', string='Document Type Sequence', copy=False, ondelete='restrict',
                                  domain=lambda self: [('code', '=', self._name)])


class Document(models.Model):
    _name = 'document_flow.document'
    _description = 'Document'
    _check_company_auto = True

    _inherit = ['mail.thread', 'mail.activity.mixin']

    code = fields.Char(string='Code', copy=False, readonly=True, required=True, default=lambda self: _('New'))
    name = fields.Char(string='Name', copy=True, required=True, tracking=True)
    date = fields.Date(string='Date', copy=False, required=True, tracking=True, default=fields.Date.context_today)
    company_id = fields.Many2one('res.company', string='Company', copy=False, required=True,
                                 default=lambda self: self.env.company)
    type_id = fields.Many2one('document_flow.document.type', string='Type', copy=True, required=True, tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', copy=False, required=True, tracking=True,
                                  default=lambda self: self.env.ref('base.RUB').id)
    project_id = fields.Many2one('project_budget.projects', string='Project', copy=True, required=True, tracking=True,
                                 domain="[('budget_state', '=', 'work')]")
    partner_id = fields.Many2one('res.partner', related='project_id.customer_organization_id.partner_id',
                                 string='Partner', copy=False, readonly=True, required=True)
    sum = fields.Monetary(string='Sum', copy=False, tracking=True)
    description = fields.Html(string='Description', copy=False)

    process_id = fields.Many2one('document_flow.process', string='Process', compute='_compute_process_id')
    process_state = fields.Selection(string='State', related='process_id.state', readonly=True)
    attachment_ids = fields.One2many('ir.attachment', string='Attachments', compute='_compute_attachment_ids')
    attachment_count = fields.Integer(compute='_compute_attachment_count', string='Attachment Count')

    @api.model
    def create(self, vals_list):
        if vals_list.get('code', _('New')) == _('New'):
            next_code = False
            if vals_list.get('type_id', False):
                document_type = self.env['document_flow.document.type'].browse(vals_list.get('type_id'))
                if document_type and document_type.sequence_id:
                    next_code = document_type.sequence_id.next_by_code('document_flow.document.type') or _('New')
            vals_list['code'] = self.env['ir.sequence'].next_by_code('document_flow.document') or _(
                'New') if not next_code else next_code

        res = super(Document, self).create(vals_list)
        return res

    def _compute_process_id(self):
        for document in self:
            document.process_id = self.env['document_flow.processing'].search([
                ('parent_ref', '=', '%s,%d' % (document._name, document.id))
            ]).process_id

    def _compute_attachment_ids(self):
        for document in self:
            document.attachment_ids = self.env['ir.attachment'].search([
                '|',
                '&', ('res_model', '=', self._name), ('res_id', 'in', [document.id]),
                '&', ('res_model', '=', 'task.task'), ('res_id', 'in', document.process_id.task_ids.ids)
            ])

    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        for document in self:
            document.attachment_count = len(document.attachment_ids)

    def action_open_attachments(self):
        self.ensure_one()
        can_edit = True if not self.process_state or self.process_state in ('on_registration', 'break') else False
        action_vals = {
            'name': _('Attachments'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,tree,form',
            'domain': ['|',
                       '&', ('res_model', '=', self._name), ('res_id', 'in', [self.id]),
                       '&', ('res_model', '=', 'task.task'), ('res_id', 'in', self.process_id.task_ids.ids)
                       ],
            'context': "{'default_res_model': '%s','default_res_id': %d, 'dms_file': True, 'create': %s, 'edit': %s 'delete': %s}" % (
                self._name, self.id, can_edit, can_edit, can_edit),
            'help': """
                        <p class="o_view_nocontent_smiling_face">%s</p>
                        """ % _("Add attachments for this document")
        }
        if not can_edit:
            action_vals.update({'flags': {'mode': 'readonly'}})
        return action_vals

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
                'default_parent_ref_id': self.id,
                'default_document_type_id': self.type_id.id
            }
        }
