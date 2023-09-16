from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, date, timedelta


def selection_parent_model():
    return [
        ('document_flow.event', _('Event')),
        ('document_flow.event.decision', _('Decision')),
        ('document_flow.action', _('Action')),
        ('document_flow.document', _('Document'))
    ]


class Processing(models.Model):
    _name = 'document_flow.processing'
    _description = 'Processing'

    @api.model
    def _selection_parent_model(self):
        return selection_parent_model()

    process_id = fields.Many2one('document_flow.process', string='Process', ondelete='restrict', readonly=True,
                                 index=True)
    state = fields.Selection(string='State', related='process_id.state', readonly=True)
    parent_ref = fields.Reference(string='Parent', selection='_selection_parent_model', ondelete='restrict',
                                  required=True, readonly=True)
    parent_ref_id = fields.Integer(string='Parent Id', index=True)
    parent_ref_type = fields.Char(string='Parent Type', index=True)

    template_id = fields.Many2one('document_flow.process.template', string='Template',
                                  domain="[('model_id', '=', parent_ref_type)]")
    action_ids = fields.One2many('document_flow.action', 'parent_ref_id', string='Actions',
                                 domain=lambda self: [('parent_ref_type', '=', self._name)])
    task_history_ids = fields.One2many('document_flow.task.history', related='process_id.task_history_ids',
                                       string='Processing History')

    def fill_by_template(self):
        if self.template_id:
            for action in self.template_id.action_ids:
                act = self.env['document_flow.action'].create({
                    'parent_ref': '%s,%s' % (self._name, self.id),
                    'parent_ref_type': self._name,
                    'parent_ref_id': self.id,
                    'name': action.name,
                    'type': action.type,
                    'sequence': action.sequence,
                    'compute_condition': action.compute_condition
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
            name=_('Processing') + ' ' + self.parent_ref.name,
            template_id=self.template_id.id,
            company_ids=self.parent_ref.company_id,
            type='complex'
        ))
        for action in self.action_ids:
            simple_process = self.env['document_flow.process'].create({
                'name': action.name,
                'type': action.type,
                'parent_id': process.id,
                'task_sequence': action.task_sequence,
                'sequence': action.sequence,
                'reviewer_ref': action.reviewer_ref,
                'compute_condition': action.compute_condition
            })
            for executor in action.executor_ids:
                self.env['document_flow.process.executor'].create({
                    'process_id': simple_process.id,
                    'sequence': executor.sequence,
                    'type_sequence': executor.type_sequence,
                    'executor_ref': '%s,%s' % (type(executor.executor_ref).__name__, executor.executor_ref.id),
                    'period': executor.period
                })
        process.action_start_process()
        self.process_id = process.id
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

    def resume_processing_from_last_stage(self):
        if self.process_id:
            self.process_id.resume_from_last_stage()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'sticky': False,
                'message': _("Processing was resumed"),
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }
