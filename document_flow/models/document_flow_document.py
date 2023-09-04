from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, date, timedelta


class DocumentKind(models.Model):
    _name = 'document_flow.document.kind'
    _description = 'Document Kind'

    name = fields.Char(string='Name', required=True, copy=True)


class Document(models.Model):
    _name = 'document_flow.document'
    _description = 'Document'

    name = fields.Char(string='Name', required=True, copy=True)
    date = fields.Date(string='Date', required=True, copy=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    attachment_count = fields.Integer(compute='_compute_attachment_count', string='Attachments')

    def _compute_attachment_count(self):
        for task in self:
            task.attachment_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', self._name),
                ('res_id', '=', task.id)
            ])

    def action_open_attachments(self):
        self.ensure_one()
        return {
            'name': _('Attachments'),
            'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,tree,form',
            'context': "{'default_res_model': '%s','default_res_id': %d}" % (self._name, self.id),
            'help': """
                <p class="o_view_nocontent_smiling_face">%s</p>
                """ % _("Add attachments for this document")
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
