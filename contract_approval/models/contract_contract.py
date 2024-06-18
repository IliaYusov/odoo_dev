from odoo import api, Command, fields, models, _


class Contract(models.Model):
    _inherit = 'contract.contract'

    def _get_default_access_ids(self):
        return [
            (0, 0, {
                'res_model': self._name,
                'res_id': self.id,
                'user_ref': 'res.users,%d' % self.env.user.id
            })
        ]

    state_id = fields.Many2one('contract.state', compute='_compute_state_id', readonly=False, store=True)
    access_ids = fields.One2many('workflow.parent.access', 'res_id', string='Access', copy=False,
                                 default=_get_default_access_ids, domain="[('res_model', '=', 'contract.contract')]",
                                 required=True)
    workflow_id = fields.Many2one('workflow.workflow', string='Workflow', copy=False)
    workflow_id_domain = fields.Binary(string='Workflow Domain', compute='_compute_workflow_id_domain',
                                       help='Dynamic domain used for the workflow')
    workflow_process_id = fields.Many2one('workflow.process', string='Process', compute='_compute_workflow_process_id')
    workflow_process_state = fields.Selection(related='workflow_process_id.state', string='Workflow State',
                                              readonly=True, store=True)
    activity_history_ids = fields.One2many('workflow.process.activity.history', 'res_id', string='History',
                                           domain="[('res_model', '=', 'contract.contract')]", readonly=True)

    # ------------------------------------------------------
    # COMPUTE METHODS
    # ------------------------------------------------------

    def _compute_can_edit(self):
        for contract in self:
            contract.can_edit = contract.active and \
                not (self.workflow_process_state and self.workflow_process_state not in ('break', 'canceled'))

    @api.depends('company_id', 'type_id', 'kind_id')
    def _compute_workflow_id_domain(self):
        for contract in self:
            domain = [
                ('model_name', '=', self._name),
                '|', ('company_id', '=', False), ('company_id', '=', contract.company_id.id)
            ]
            if contract.type_id:
                domain += [
                    ('contract_type_id', '=', contract.type_id.id)
                ]
            contract.workflow_id_domain = domain

    def _compute_workflow_process_id(self):
        for contract in self:
            contract.workflow_process_id = self.env['workflow.process'].search([
                ('res_model', '=', self._name),
                ('res_id', '=', contract.id)
            ])[-1:]

    @api.depends('workflow_process_state')
    def _compute_state_id(self):
        for contract in self:
            contract.state_id = self.env.ref('contract.contract_state_draft') if contract.workflow_process_state in (
                'canceled', 'break') else contract.state_id

    # ------------------------------------------------------
    # CRUD
    # ------------------------------------------------------

    def unlink(self):
        processes = self.env['workflow.process'].search([
            ('res_model', '=', self._name),
            ('res_id', 'in', self.ids)
        ])
        processes.unlink()
        result = super(Contract, self).unlink()
        return result

    # ------------------------------------------------------
    # ONCHANGE METHODS
    # ------------------------------------------------------

    @api.onchange('project_id')
    def _onchange_project_id(self):
        if self._origin:
            access_delete = [self._origin.project_id.key_account_manager_id.user_id,
                             self._origin.project_id.project_manager_id.user_id,
                             self._origin.project_id.project_supervisor_id.user_id]
            if self._origin.project_id != self.project_id:
                [Command.delete(access.id) for access in
                 self.access_ids.filtered(lambda acc: acc.user_id in set(access_delete))]
        access_insert = [self.author_id.user_id,
                         self.project_id.key_account_manager_id.user_id,
                         self.project_id.project_manager_id.user_id,
                         self.project_id.project_supervisor_id.user_id]
        access_ids = []
        for usr in filter(None, set(access_insert)):
            access = next(iter(self.access_ids.filtered(lambda acc: acc.ids == usr.id)), False)
            vals = {
                'user_ref': 'res.users,%d' % usr.id,
                'res_model': self._name,
                'res_id': self.id.origin if self._origin else self.id
            }
            access_ids.append(Command.update(access.id, vals) if access else Command.create(vals))
        field = self._fields['access_ids']
        value = field.convert_to_cache(access_ids, self, validate=False)
        self._update_cache(dict(access_ids=field.convert_to_write(value, self)), validate=False)

    # ------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------

    def toggle_active(self):
        res = super(Contract, self).toggle_active()
        unarchived_documents = self.filtered(lambda d: d.active and d.workflow_process_id)
        for task in unarchived_documents.workflow_process_id.task_ids.filtered(
                lambda t: not t.active and not t.is_closed):
            task.write({'active': True})
        unarchived_documents.filtered(lambda d: d.workflow_process_state == 'canceled').workflow_process_id.write(
            {'state': 'in_progress'})
        archived_documents = self.filtered(lambda d: not d.active and d.workflow_process_id)
        for task in archived_documents.workflow_process_id.task_ids.filtered(
                lambda t: t.active and not t.is_closed):
            task.write({'active': False})
        archived_documents.filtered(lambda d: d.workflow_process_state != 'completed').workflow_process_id.write(
            {'state': 'canceled'})
        return res

    def action_open_documents(self):
        self.ensure_one()
        action_vals = super(Contract, self).action_open_documents()
        if not self.can_edit:
            action_vals.update({
                'context': {**action_vals['context'], **{
                    'create': self.can_edit,
                    'edit': self.can_edit,
                    'delete': self.can_edit
                }},
                'flags': {
                    'mode': 'readonly'
                }
            })
        return action_vals

    def action_start_processing(self):
        self.ensure_one()
        self.workflow_id.run(self._name, self.id)
        self.write({'state_id': self.env.ref('contract_approval.contract_state_on_approval')})

    def action_pause_processing(self):
        self.ensure_one()
        self.workflow_process_id.pause()
        self.write({'state_id': self.env.ref('contract.contract_state_draft')})
