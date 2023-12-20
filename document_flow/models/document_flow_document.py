from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Document(models.Model):
    _name = 'document_flow.document'
    _description = 'Document'
    _check_company_auto = True

    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_access_ids(self):
        return [
            (0, 0, {'user_ref': 'res.users,%d' % self.env.user.id})
        ]

    def _default_employee_id(self):
        employee = self.env['hr.employee'].search([
            ('user_id', '=', self.env.user.id),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        return employee.id

    code = fields.Char(string='Code', copy=False, readonly=True, required=True, default=lambda self: _('New'))
    name = fields.Char(string='Name', copy=True, required=True, tracking=True)
    date = fields.Date(string='Date', copy=False, required=True, tracking=True, default=fields.Date.context_today)
    company_id = fields.Many2one('res.company', string='Company', copy=False, required=True,
                                 default=lambda self: self.env.company)
    author_id = fields.Many2one('hr.employee', string='Author', check_company=True, default=_default_employee_id,
                                required=True)
    kind_id = fields.Many2one('document_flow.document.kind', string='Kind', copy=True, ondelete='restrict',
                              required=True, tracking=True)
    template_id = fields.Many2one(related='kind_id.template_id', string='Template', copy=False, readonly=True)
    description = fields.Html(string='Description', copy=False)
    active = fields.Boolean(copy=False, default=True, index=True)
    access_ids = fields.One2many('document_flow.document.access', 'document_id', string='Access', copy=False,
                                 required=True, default=_default_access_ids)
    properties = fields.Properties('Properties', definition='kind_id.properties_definition', copy=True)

    process_id = fields.Many2one('document_flow.process', string='Process', compute='_compute_process_id')
    process_state = fields.Selection(related='process_id.state', string='State', readonly=True)
    attachment_ids = fields.One2many('ir.attachment', string='Attachments', compute='_compute_attachment_ids')
    attachment_count = fields.Integer(compute='_compute_attachment_count', string='Attachment Count')

    # @api.model
    # def fields_get(self, allfields=None, attributes=None):
    #     fields = super().fields_get(allfields=allfields, attributes=attributes)
    #
    #     public_fields = {field_name: description for field_name, description in fields.items()}
    #
    #     for field_name, description in public_fields.items():
    #         if field_name == 'properties' and not description.get('readonly', False) and not self.env.user.has_group(
    #                 'document_flow.group_document_flow_manager'):
    #             description['readonly'] = True
    #
    #     return public_fields

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

    def unlink(self):
        if self.process_id:
            if any(self.process_id.task_ids.filtered(lambda task: task.is_closed)):
                raise UserError(_('You cannot delete this document because some tasks were closed.'))

            self.process_id.mapped('task_history_ids').unlink()
            self.process_id.mapped('task_ids').unlink()

            process = self.process_id
            processing = self.env['document_flow.processing'].search([
                ('parent_ref', '=', '%s,%d' % (self._name, self.id))
            ])
            processing.unlink()
            process.unlink()

        result = super(Document, self).unlink()
        return result

    def toggle_active(self):
        res = super(Document, self).toggle_active()
        unarchived_documents = self.filtered(lambda document: document.active and document.process_id)
        for task in unarchived_documents.process_id.task_ids.filtered(lambda t: not t.active and not t.is_closed):
            task.write({'active': True})
        archived_documents = self.filtered(lambda document: not document.active and document.process_id)
        for task in archived_documents.process_id.active_task_ids.filtered(lambda t: t.active and not t.is_closed):
            task.write({'active': False})
        return res

    def _compute_process_id(self):
        for document in self:
            document.process_id = self.env['document_flow.processing'].search([
                ('parent_ref', '=', '%s,%d' % (document._name, document.id))
            ]).process_ids[-1:]

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
            'context': "{'default_res_model': '%s','default_res_id': %d, 'search_default_group_by_res_model': True, 'create': %s, 'edit': %s 'delete': %s}" % (
                self._name, self.id, can_edit, can_edit, can_edit),
            'help': """
                        <p class="o_view_nocontent_smiling_face">%s</p>
                        """ % _('Add attachments for this document')
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
                'default_document_kind_id': self.kind_id.id
            }
        }
