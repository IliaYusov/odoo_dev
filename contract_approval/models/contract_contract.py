from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Contract(models.Model):
    _inherit = 'contract.contract'

    def _get_default_access_ids(self):
        return [
            (0, 0, {'user_ref': 'res.users,%d' % self.env.user.id})
        ]

    access_ids = fields.One2many('contract.access', 'contract_id', string='Access', copy=False,
                                 required=True, default=_get_default_access_ids)

    process_id = fields.Many2one('document_flow.process', string='Process', compute='_compute_process_id')
    process_state = fields.Selection(related='process_id.state', string='State', readonly=True)

    def _compute_can_edit(self):
        for contract in self:
            contract.can_edit = not (self.process_state and self.process_state not in ('on_registration', 'break'))

    def unlink(self):
        if self.process_id:
            if any(self.process_id.task_ids.filtered(lambda task: task.is_closed)):
                raise UserError(_('You cannot delete this contract because some tasks were closed.'))

            self.process_id.mapped('task_history_ids').unlink()
            self.process_id.mapped('task_ids').unlink()

            process = self.process_id
            processing = self.env['document_flow.processing'].search([
                ('parent_ref', '=', '%s,%d' % (self._name, self.id))
            ])
            processing.unlink()
            process.unlink()

        result = super(Contract, self).unlink()
        return result

    def toggle_active(self):
        res = super(Contract, self).toggle_active()
        unarchived_documents = self.filtered(lambda document: document.active and document.process_id)
        for task in unarchived_documents.process_id.task_ids.filtered(lambda t: not t.active and not t.is_closed):
            task.write({'active': True})
        archived_documents = self.filtered(lambda document: not document.active and document.process_id)
        for task in archived_documents.process_id.active_task_ids.filtered(lambda t: t.active and not t.is_closed):
            task.write({'active': False})
        return res

    def _compute_attachment_ids(self):
        for contract in self:
            processing = self.env['document_flow.processing'].search([
                ('parent_ref', '=', '%s,%d' % (contract._name, contract.id))
            ])
            contract.attachment_ids = self.env['ir.attachment'].search([
                '|',
                '&', ('res_model', '=', self._name), ('res_id', 'in', [contract.id]),
                '&', ('res_model', '=', 'task.task'), ('res_id', 'in', processing.process_ids.task_ids.ids)
            ])

    def _compute_process_id(self):
        for contract in self:
            contract.process_id = self.env['document_flow.processing'].search([
                ('parent_ref', '=', '%s,%d' % (contract._name, contract.id))
            ]).process_ids[-1:]

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
                'default_parent_ref': '%s,%d' % (self._name, self.id)
            }
        }
