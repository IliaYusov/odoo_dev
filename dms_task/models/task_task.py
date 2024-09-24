from odoo import api, fields, models


class Task(models.Model):
    _inherit = 'task.task'

    file_ids = fields.One2many('dms.document', string='Documents & Files', compute='_compute_file_ids')

    @api.depends('parent_ref', 'parent_ref_type', 'parent_ref_id')
    def _compute_file_ids(self):
        for task in self:
            task.file_ids = task.parent_ref.file_ids if task.parent_ref and task.parent_ref._fields.get(
                'file_ids') else False

    def _get_attachment_ids_for_email(self):
        return self.execution_result_attachment_ids.ids if self.is_closed else self.file_ids.attachment_id.ids
