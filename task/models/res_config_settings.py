from odoo import fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = "res.config.settings"

    assign_task_only_to_subordinates = fields.Boolean(string='Assign Task Only To Subordinates',
                                                      config_parameter='task.assign_task_only_to_subordinates')
