from odoo import api, models


class ResUser(models.Model):
    _inherit = ['res.users']

    @api.model
    def action_get(self):
        if self.env.context.get('from_workplace', False):
            return self.env['ir.actions.act_window']._for_xml_id('workplace_employee.action_res_users_my_profile')
        return super(ResUser, self).action_get()
