from odoo import models, fields, _
from odoo.exceptions import UserError


list_table_names=[]

class jrn_wizard_undo_changes(models.TransientModel):
    _name = 'jrn.wizard.undo_changes'
    _description = 'jrn wizard for undo changes'
    # array_table_names  = fields.Selection(list_table_names, string='table names')

    def action_undo_changes(self):
        context_list = self.env.context
        if context_list.get('active_ids'):
            active_ids = context_list['active_ids']

        changes = self.env['jrn.jrn'].search([('id', 'in', active_ids)], order="datetime_event")
        jrn = self.env['jrn.base']
        for change in changes:
            print('undo table.name',change.table_name_id.name)
            jrn.undo_change(change)
        return None

