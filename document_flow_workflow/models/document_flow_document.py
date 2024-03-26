from odoo import api, fields, models, _


class Document(models.Model):
    _inherit = ['document_flow.document']

    def _get_default_access_ids(self):
        return [
            (0, 0, {
                'res_model': self._name,
                'res_id': self.id,
                'user_ref': 'res.users,%d' % self.env.user.id
            })
        ]

    access_ids = fields.One2many('workflow.parent.access', 'res_id', string='Access', copy=False,
                                 default=_get_default_access_ids,
                                 domain="[('res_model', '=', 'document_flow.document')]", required=True)
    workflow_id = fields.Many2one('workflow.workflow', string='Workflow', copy=False)
    workflow_id_domain = fields.Binary(string='Workflow Domain', compute='_compute_workflow_id_domain',
                                       help='Dynamic domain used for the workflow')
    workflow_process_id = fields.Many2one('workflow.process', string='Process', compute='_compute_workflow_process_id')
    workflow_process_state = fields.Selection(related='workflow_process_id.state', string='State', readonly=True)
    activity_history_ids = fields.One2many('workflow.process.activity.history', 'res_id', string='History',
                                           domain="[('res_model', '=', 'contract.contract')]", readonly=True)

    # ------------------------------------------------------
    # COMPUTE METHODS
    # ------------------------------------------------------

    def _compute_can_edit(self):
        for document in self:
            document.can_edit = document.active and \
                not (document.workflow_process_state and document.workflow_process_state not in ('break', 'canceled'))

    @api.depends('company_id', 'kind_id')
    def _compute_workflow_id_domain(self):
        for document in self:
            domain = [
                ('model_name', '=', self._name),
                '|', ('company_id', '=', False), ('company_id', '=', document.company_id.id)
            ]
            if document.kind_id:
                domain += [
                    ('document_kind_id', '=', document.kind_id.id)
                ]
            document.workflow_id_domain = domain

    def _compute_workflow_process_id(self):
        for document in self:
            document.workflow_process_id = self.env['workflow.process'].search([
                ('res_model', '=', self._name),
                ('res_id', '=', document.id)
            ])[-1:]

    # ------------------------------------------------------
    # CRUD
    # ------------------------------------------------------

    def unlink(self):
        processes = self.env['workflow.process'].search([
            ('res_model', '=', self._name),
            ('res_id', 'in', self.ids)
        ])
        processes.unlink()
        result = super(Document, self).unlink()
        return result

    # ------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------

    def toggle_active(self):
        res = super(Document, self).toggle_active()
        unarchived_documents = self.filtered(lambda document: document.active and document.process_id)
        for task in unarchived_documents.process_id.task_ids.filtered(lambda t: not t.active and not t.is_closed):
            task.write({'active': True})
        archived_documents = self.filtered(lambda document: not document.active and document.process_id)
        for task in archived_documents.process_id.active_task_ids.filtered(lambda t: t.active and not t.is_closed):
            task.write({'active': False})
        return res

    def action_open_documents(self):
        self.ensure_one()
        action_vals = super(Document, self).action_open_documents()
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

    def action_pause_processing(self):
        self.ensure_one()
        self.workflow_process_id.pause()
