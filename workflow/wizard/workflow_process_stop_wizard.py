from odoo import fields, models, _
from odoo.exceptions import UserError


class WorkflowProcessStop(models.TransientModel):
    _name = 'workflow.process.stop.wizard'
    _description = 'Workflow Process Wizard: Stop'

    process_id = fields.Many2one('workflow.process', string='Process', required=True, ondelete='cascade')
    cancel_reason = fields.Html(string='Reason For The Cancellation', required=True)

    def action_stop_processing(self):
        self.ensure_one()
        if not self.cancel_reason:
            raise UserError(_('Reason for the cancellation is required!'))

        self.process_id.stop(cancel_reason=self.cancel_reason)

        return {'type': 'ir.actions.act_window_close'}
