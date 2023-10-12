from odoo import _, models, fields, api, http,  sql_db
import odoo
from contextlib import closing
from odoo.http import request
from psycopg2 import sql

class jrn(models.Model):
    _name = 'jrn.jrn'
    _description = "main journal table"
    _order = 'datetime_event desc,id desc'
    # uuid_event     = fields.Char(string='guid', size=16, index=True, readonly = True)
    table_name_id  = fields.Many2one('jrn.tables', required=True, index=True, readonly = True)
    table_id       = fields.Char(string="id in table", required=True, index=True, readonly=True)
    datetime_event = fields.Datetime(string="Datetime of the event", index=True, readonly = True)
    user_event     = fields.Char(string="User who make event", index=True, readonly = True)
    status         = fields.Integer(string="status", required=True, index=True, readonly=True)
    operation      = fields.Selection([('2', 'Insert'), ('4', 'Update'), ('8','Delete')]
                    ,string="type of operation", required=True, index=True, readonly=True)

    def run_undo_wizard(self):
        action = self.env['ir.actions.actions']._for_xml_id('jrn.action_jrn_wizard_undo_changes')
        action['name'] = _('jrn undo changes')
        action['display_name'] = _('jrn undo changes')
        return action


    def run_wzrd_view_journal_record_spec(self):
        action = self.env['ir.actions.actions']._for_xml_id('jrn.action_view_journal_record')
        action['name'] = _('View journal record')
        action['display_name'] = _('View journal record')
        action['context'] = {
            'default_jrn_id': self.id,
            'default_datetime_event': self.datetime_event,
            'default_user_event': self.user_event,
            'default_status': self.status,
            'default_operation': self.operation,
            'default_table_id' : self.table_id
        }
        print('action', action)
        return action

class table_name(models.Model):
    _name = 'jrn.tables'
    _description = "tables in base"

    name = fields.Char(string='Table name', required = True, readonly = True)
    check_changes = fields.Boolean(string='check_changes', default = False, readonly = True)
    # check_insert = fields.Boolean(string='Check insert', default = False, readonly = True)
    # check_update = fields.Boolean(string='Check update', default = False, readonly = True)
    # check_delete = fields.Boolean(string='Check delete', default = False, readonly = True)
    is_structure_correct = fields.Boolean(string='is structure correct', default = False, readonly = True)
    is_table_exist_in_jrn = fields.Boolean(string='is table exist in jrn', default=False, readonly=True)

    def action_check_structure(self):
        context_list = self.env.context
        if context_list.get('active_ids'):
            active_ids = context_list['active_ids']
        tables = self.env['jrn.tables'].search([('id', 'in', active_ids)])

        jrn = self.env['jrn.base']
        for table in tables:
            jrn.action_check_structure_one(table)

    def action_recreate_tables(self):
        context_list = self.env.context
        if context_list.get('active_ids'):
            active_ids = context_list['active_ids']
        tables = self.env['jrn.tables'].search([('id', 'in', active_ids)])
        jrn = self.env['jrn.base']
        for table in tables:
            if table.is_table_exist_in_jrn == False:
                jrn.action_create_jrn_tables_one(table)
            else:
                if table.is_structure_correct == False:
                    jrn.action_recreate_tables_one(table)

    def action_create_jrn_tables(self):
        context_list = self.env.context
        if context_list.get('active_ids'):
            active_ids = context_list['active_ids']
        jrn = self.env['jrn.base']
        tables = self.env['jrn.tables'].search([('id', 'in', active_ids)])
        for table in tables:
            jrn.action_create_jrn_tables_one(table)
        return None

    def run_wzrd_set_table_attrs(self):
        action = self.env['ir.actions.actions']._for_xml_id('jrn.action_tables_wizard_set_attrs')
        action['name'] = _('Set tables attrs')
        action['display_name'] = _('Set tables attrs')
        return action

class fillTables_Controller(http.Controller):
    @http.route('/custom/createdb',auth="public", type='json', methods=['POST'])
    def fill_table_list(self, param1):
        model = request.env['jrn.base']
        model.fill_table_list()
        return {
                  'type': 'ir.actions.client',
                  'tag': 'reload',
            }

