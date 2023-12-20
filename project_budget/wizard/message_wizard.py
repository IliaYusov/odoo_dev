from odoo import models, fields, _


class prj_MessageWizard(models.TransientModel):
    _name = 'prj_message.wizard'
    message = fields.Text('Message', required=True)

    def action_ok(self):
        """ close wizard"""
        return {'type': 'ir.actions.act_window_close'}