from odoo import models, fields, api, _


class TicketTask(models.Model):
    _inherit = 'task.task'

    @api.model
    def _selection_parent_model(self):
        types = super(TicketTask, self)._selection_parent_model()
        types.append(('helpdesk.ticket', _('Ticket')))
        return types
