from odoo import _, models, fields, api
from .document_flow_process import recompute_sequence_actions, selection_parent_model


class Processing(models.Model):
    _name = 'document_flow.processing'
    _description = 'Processing'

    @api.model
    def _selection_parent_model(self):
        return selection_parent_model()

    def _get_action_ids_domain(self):
        return [('parent_ref_type', '=', self._name)]

    process_id = fields.Many2one('document_flow.process', string='Process', ondelete='restrict', readonly=True,
                                 index=True)
    state = fields.Selection(string='State', related='process_id.state', readonly=True)
    parent_ref = fields.Reference(string='Parent', selection='_selection_parent_model', ondelete='restrict',
                                  required=True, readonly=True)
    parent_ref_id = fields.Integer(string='Parent Id', index=True)
    parent_ref_type = fields.Char(string='Parent Type', index=True)

    document_type_id = fields.Many2one('document_flow.document.type', string='Document Type')

    template_id = fields.Many2one('document_flow.process.template', string='Template',
                                  domain="[('document_type_id', '=', document_type_id)]")
    action_ids = fields.One2many('document_flow.action', 'parent_ref_id', string='Actions',
                                 domain=_get_action_ids_domain)
    task_history_ids = fields.One2many('document_flow.task.history', related='process_id.task_history_ids',
                                       string='Processing History')

    @api.model
    def create(self, vals_list):
        if any(vals_list.get('action_ids', [])):
            recompute_sequence_actions(self.env['document_flow.action'], vals_list.get('action_ids'))
        res = super(Processing, self).create(vals_list)
        return res

    def write(self, vals):
        if any(vals.get('action_ids', [])):
            recompute_sequence_actions(self.env['document_flow.action'], vals.get('action_ids'))
        res = super(Processing, self).write(vals)
        return res

    def fill_by_template(self):
        if self.template_id:
            if self.action_ids:
                self.action_ids.unlink()
            for action in self.template_id.action_ids:
                action.copy({
                    'parent_ref': '%s,%s' % (self._name, self.id),
                    'parent_ref_type': self._name,
                    'parent_ref_id': self.id
                })
            self._get_action_ids_domain()
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'danger',
                    'sticky': False,
                    'message': _('Template is not set.'),
                    'next': {'type': 'ir.actions.act_window_close'}
                }
            }

    def action_start_processing(self):
        process = self.env['document_flow.process'].create(dict(
            name=_('Processing') + ' ' + self.parent_ref.name,
            template_id=self.template_id.id,
            company_ids=self.parent_ref.company_id if not self.parent_ref._fields.get('company_ids', False) else self.parent_ref.company_ids,
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
                'start_condition': action.start_condition,
                'description': action.description
            })
            for child in action.child_ids:
                pr = self.env['document_flow.process'].create({
                    'name': child.name,
                    'type': child.type,
                    'parent_id': simple_process.id,
                    'task_sequence': child.task_sequence,
                    'sequence': child.sequence,
                    'reviewer_ref': child.reviewer_ref,
                    'start_condition': child.start_condition,
                    'description': child.description
                })
                for executor in child.executor_ids:
                    self.env['document_flow.process.executor'].create({
                        'process_id': pr.id,
                        'sequence': executor.sequence,
                        'type_sequence': executor.type_sequence,
                        'executor_ref': '%s,%s' % (type(executor.executor_ref).__name__, executor.executor_ref.id),
                        'period': executor.period
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

    def break_processing(self):
        if self.process_id:
            self.process_id.break_execution()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'sticky': False,
                'message': _("Processing was break"),
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
