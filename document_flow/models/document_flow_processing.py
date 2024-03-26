from odoo import api, Command, fields, models, _
from .document_flow_process import recompute_sequence_actions, selection_parent_model


class Processing(models.Model):
    _name = 'document_flow.processing'
    _description = 'Processing'

    @api.model
    def _selection_parent_model(self):
        return selection_parent_model()

    def _get_action_ids_domain(self):
        return [('parent_ref_type', '=', self._name)]

    name = fields.Text(string='Description', compute='_compute_name', precompute=True, required=True, store=True)
    process_id = fields.Many2one('document_flow.process', string='Process', ondelete='restrict', readonly=True,
                                 index=True)
    process_ids = fields.Many2many('document_flow.process', relation='document_flow_processing_process_rel',
                                   column1='processing_id', column2='process_id', string='Processes', copy=False)
    state = fields.Char(string='State', compute='_compute_state')
    parent_ref = fields.Reference(string='Parent', selection='_selection_parent_model', ondelete='restrict',
                                  required=True, readonly=True)
    parent_ref_id = fields.Integer(string='Parent Id', compute='_compute_parent_ref', index=True, store=True)
    parent_ref_type = fields.Char(string='Parent Type', compute='_compute_parent_ref', index=True, store=True)

    document_kind_id = fields.Many2one('document_flow.document.kind', string='Document Kind')

    template_id = fields.Many2one('document_flow.process.template', string='Template')
    template_id_domain = fields.Binary(string='Template Domain', compute='_compute_template_id_domain',
                                       help='Dynamic domain used for the template')
    action_ids = fields.One2many('document_flow.action', 'parent_ref_id', string='Actions',
                                 domain=_get_action_ids_domain)
    action_count = fields.Integer(compute='_compute_action_count', string='Action Count')
    task_history_ids = fields.One2many('document_flow.task.history', string='Processing History',
                                       compute='_compute_task_history_ids')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if any(vals.get('action_ids', [])):
                recompute_sequence_actions(self.env['document_flow.action'], vals.get('action_ids'))

        records = super(Processing, self).create(vals_list)
        return records

    def write(self, vals):
        if any(vals.get('action_ids', [])):
            recompute_sequence_actions(self.env['document_flow.action'], vals.get('action_ids'))
        res = super(Processing, self).write(vals)
        return res

    @api.depends('parent_ref_type', 'document_kind_id')
    def _compute_template_id_domain(self):
        for rec in self:
            rec.template_id_domain = [
                ('model_id.model', '=', rec.parent_ref_type),
                ('document_kind_id', '=', rec.document_kind_id.id)
            ]

    @api.depends('process_ids.state')
    def _compute_state(self):
        for processing in self:
            process = processing.process_ids[-1:]
            processing.state = process.state if process else False

    @api.depends('process_ids')
    def _compute_task_history_ids(self):
        for processing in self:
            processing.task_history_ids = processing.process_ids.task_history_ids

    @api.depends('action_ids')
    def _compute_action_count(self):
        for processing in self:
            processing.action_count = len(processing.action_ids)

    @api.depends('parent_ref')
    def _compute_name(self):
        for processing in self:
            processing.name = _('Processing') + ' ' + processing.parent_ref.name

    @api.depends('parent_ref')
    def _compute_parent_ref(self):
        for processing in self:
            processing.parent_ref_type = type(processing.parent_ref).__name__
            processing.parent_ref_id = processing.parent_ref.id

    def fill_by_template(self):
        if self.template_id:
            if self.action_ids:
                self.action_ids.unlink()
            actions = dict()
            for action in self.template_id.action_ids:
                act = action.copy({
                    'parent_ref_type': self._name,
                    'parent_ref_id': self.id
                })
                if action.return_on_action_id:
                    act.write({'return_on_action_id': actions.get(action.return_on_action_id.id)})
                actions[action.id] = act.id
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
            type='complex',
            template_id=self.template_id.id,
            name=self.name,
            description=self.parent_ref.description,
            company_ids=self.parent_ref.company_id if not self.parent_ref._fields.get('company_ids', False) else self.parent_ref.company_ids
        ))
        main_processes = dict()
        for action in self.action_ids:
            simple_process = self.env['document_flow.process'].create({
                'name': action.name,
                'type': action.type,
                'parent_id': process.id,
                'task_sequence': action.task_sequence,
                'sequence': action.sequence,
                'reviewer_ref': action.reviewer_ref,
                'start_condition': action.start_condition,
                'description': action.description,
                'action_id': action.id,
                'return_on_process_id': False if not action.return_on_action_id else main_processes.get(
                    action.return_on_action_id.id).id,
                'company_ids': [Command.link(c_id) for c_id in action._get_executors_company_ids()]
            })
            main_processes[action.id] = simple_process
            for child in action.child_ids:
                pr = self.env['document_flow.process'].create({
                    'name': child.name,
                    'type': child.type,
                    'parent_id': simple_process.id,
                    'task_sequence': child.task_sequence,
                    'sequence': child.sequence,
                    'reviewer_ref': child.reviewer_ref,
                    'start_condition': child.start_condition,
                    'description': child.description,
                    'action_id': child.id,
                    'return_on_process_id': False if not action.return_on_action_id else self.env[
                        'document_flow.process'].search(['action_id', '=', child.id], limit=1).id,
                    'company_ids': [Command.link(c_id) for c_id in action._get_executors_company_ids()]
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
        # self.process_id = process.id
        self.process_ids = [Command.link(process.id)]
        process.action_start_process()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'sticky': False,
                'message': _('Processing was started'),
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }

    def break_processing(self):
        process = self.process_ids.filtered(lambda pr: pr.state == 'started')[:1]
        if process:
            process.break_execution()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'sticky': False,
                'message': _('Processing was break'),
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }
