from odoo import fields, models


class WorkflowProcessResume(models.TransientModel):
    _name = 'workflow.process.resume.wizard'
    _description = 'Workflow Process Wizard: Resume'

    process_id = fields.Many2one('workflow.process', string='Process', required=True, ondelete='cascade')
    comment = fields.Html(string='Comment')

    def action_start_processing(self):
        self.ensure_one()
        self.with_context(description=self.comment).process_id.workflow_id.run(self.process_id.res_model,
                                                                               self.process_id.res_id)
        if self.comment:
            self.process_id.res_ref.message_post(body=self.comment, message_type='comment',
                                                 subtype_xmlid='mail.mt_note')
        return {'type': 'ir.actions.act_window_close'}

    def action_resume_processing(self):
        self.ensure_one()
        self.with_context(description=self.comment).process_id.run_from_last_activity()
        if self.comment:
            self.process_id.res_ref.message_post(body=self.comment, message_type='comment',
                                                 subtype_xmlid='mail.mt_note')
        return {'type': 'ir.actions.act_window_close'}
