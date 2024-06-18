from odoo import models


class WorkflowProcessResume(models.TransientModel):
    _inherit = 'workflow.process.resume.wizard'

    def action_start_processing(self):
        result = super(WorkflowProcessResume, self).action_start_processing()
        self.process_id.res_ref.write({'state_id': self.env.ref('contract_approval.contract_state_on_approval')})
        return result
