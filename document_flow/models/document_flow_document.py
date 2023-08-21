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

    template_id = fields.Many2one('document_flow.process.template', string='Template')
    action_ids = fields.One2many('document_flow.action', 'parent_ref_id', string='Actions',
                                 domain=lambda self: [('parent_ref_type', '=', self._name)])
    attachment_count = fields.Integer(compute='_compute_attachment_count', string='Attachments')
    is_processing_started = fields.Boolean(compute='_compute_is_processing_started')

    def _compute_attachment_count(self):
        for task in self:
            task.attachment_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', self._name),
                ('res_id', '=', task.id)
            ])

    def _compute_is_processing_started(self):
        for document in self:
            document.is_processing_started = self.env['document_flow.process.parent_object'].search_count([
                ('parent_ref_type', '=', self._name),
                ('parent_ref_id', '=', document.id),
                ('process_id', '!=', False),
                ('process_id.type', '=', 'complex'),
                ('process_id.state', 'in', ('on_registration', 'started', 'finished'))
            ]) > 0

    def fill_by_template(self):
        if self.template_id:
            for action in self.template_id.action_ids:
                act = self.env['document_flow.action'].create({
                    'parent_ref': '%s,%s' % (self._name, self.id),
                    'parent_ref_type': self._name,
                    'parent_ref_id': self.id,
                    'name': action.name,
                    'type': action.type,
                    'sequence': action.sequence
                })
                for executor in action.executor_ids:
                    self.env['document_flow.action.executor'].create({
                        'action_id': act.id,
                        'sequence': executor.sequence,
                        'type_sequence': executor.type_sequence,
                        'executor_ref': '%s,%s' % (type(executor.executor_ref).__name__, executor.executor_ref.id),
                        'period': executor.period
                    })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }

    def action_start_processing(self):
        process = self.env['document_flow.process'].create(dict(
            name=self.name,
            template_id=self.template_id.id,
            company_ids=self.company_id,
            type='complex'
        ))
        for action in self.action_ids:
            simple_process = self.env['document_flow.process'].create({
                'name': action.name,
                'type': action.type,
                'parent_id': process.id,
                'task_sequence': action.task_sequence,
                'sequence': action.sequence,
                'reviewer_ref': action.reviewer_ref
            })
            for executor in action.executor_ids:
                self.env['document_flow.process.executor'].create({
                    'process_id': simple_process.id,
                    'sequence': executor.sequence,
                    'type_sequence': executor.type_sequence,
                    'executor_ref': '%s,%s' % (type(executor.executor_ref).__name__, executor.executor_ref.id),
                    'period': executor.period
                })
            self.env['document_flow.process.parent_object'].create({
                'process_id': simple_process.id,
                'parent_ref': '%s,%s' % (type(action).__name__, action.id),
                'parent_ref_id': action.id,
                'parent_ref_type': type(action).__name__
            })
        self.env['document_flow.process.parent_object'].create({
            'process_id': process.id,
            'parent_ref': '%s,%s' % (self._name, self.id),
            'parent_ref_id': self.id,
            'parent_ref_type': self._name
        })
        process.action_start_process()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'sticky': False,
                'message': _("Processing was started"),
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }

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
