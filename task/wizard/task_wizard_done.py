from odoo import fields, models, _
from odoo.exceptions import UserError

import html2text


class TaskWizardDone(models.TransientModel):
    _name = 'task.wizard.done'
    _description = 'Task Wizard: Done'

    task_id = fields.Many2one('task.task', string='Task', required=True, ondelete='cascade')
    route_id = fields.Many2one('task.stage.route', string='Done As', required=True, ondelete='cascade')
    require_comment = fields.Boolean(related="route_id.require_comment", readonly=True)
    comment = fields.Html(string='Comment')
    attachment_ids = fields.Many2many('ir.attachment', 'task_wizard_done_attachment_rel',
                                      column1='task_wizard_done_id', column2='attachment_id', string='Attachments',
                                      help='You may attach files to comment')

    def action_done_task(self):
        self.ensure_one()

        if self.require_comment and not self.comment:
            raise UserError(_('Comment is required!'))

        self.task_id.write({'execution_result': self.comment, 'stage_id': self.route_id.stage_to_id.id})
        self.task_id.close_task(self.route_id.stage_to_id.result_type)

        if self.attachment_ids:
            self._task_link_response_attachments(self.task_id.id)

        return None

    def _task_link_response_attachments(self, task_id):
        self.ensure_one()
        parser = html2text.HTML2Text()
        parser.ignore_images = True
        for attachment in self.attachment_ids:
            vals = dict(
                res_model='task.task',
                res_id=task_id
            )
            if self.comment:
                vals['description'] = parser.handle(self.comment)
            attachment.sudo().write(vals)
