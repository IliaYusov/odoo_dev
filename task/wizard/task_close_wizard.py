from lxml import etree
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class TaskCloseWizard(models.TransientModel):
    _name = 'task.close.wizard'
    _description = 'Task Wizard: Close'

    task_id = fields.Many2one('task.task', string='Task', required=True, ondelete='cascade')
    route_id = fields.Many2one('task.stage.route', string='Done As', required=True, ondelete='cascade')
    require_comment = fields.Boolean(related='route_id.require_comment', readonly=True)
    comment = fields.Html(string='Comment')
    attachment_ids = fields.Many2many('ir.attachment', 'task_close_wizard_attachment_rel',
                                      column1='task_close_wizard_id', column2='attachment_id', string='Attachments',
                                      help='You may attach files to comment')

    # @api.model
    # def get_view(self, view_id=None, view_type='form', **options):
    #     res = super().get_view(view_id, view_type, **options)
    #     print('get_view %s', view_type)
    #     if view_type == 'form':
    #         arch = etree.XML(res['arch'])
    #         for node in arch.xpath("//form/footer/button[@name='action_close_task']"):
    #             node.set('string', 'Хз')
    #         res['arch'] = etree.tostring(arch, encoding='utf-8')
    #     return res

    def action_close_task(self):
        self.ensure_one()

        if self.require_comment and not self.comment:
            raise UserError(_('Comment is required!'))

        self.task_id.close_task(stage_id=self.route_id.stage_to_id, comment=self.comment,
                                attachment_ids=self.attachment_ids)

        return {'type': 'ir.actions.act_window_close'}
