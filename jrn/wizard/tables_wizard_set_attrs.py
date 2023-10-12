from odoo import models, fields, _
from odoo.exceptions import UserError


list_table_names=[]

class tables_wizard_set_attrs(models.TransientModel):
    _name = 'jrn.wizard.set_table_attrs'
    _description = 'jrn wizard for set table attrs'
    # array_table_names  = fields.Selection(list_table_names, string='table names')
    check_changes = fields.Boolean(string='check changes', default = False)



    def action_set_attrs(self):
        context_list = self.env.context
        if context_list.get('active_ids'):
            active_ids = context_list['active_ids']

        tables = self.env['jrn.tables'].search([('id', 'in', active_ids)])
        jrn = self.env['jrn.base']
        for table in tables:
            table.check_changes = self.check_changes
            if table.check_changes == True:
                jrn.create_trigger(table)
            else:
                jrn.drop_trigger(table)
        return None

