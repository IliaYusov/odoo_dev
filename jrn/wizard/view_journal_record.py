from odoo import models, fields, _
from odoo.exceptions import UserError
from odoo import api, fields, models, tools, _

list_table_names=[]

class jrn_view_journal_record(models.TransientModel):
    _name = 'jrn.view_journal_record'
    _description = 'jrn wizard for view journal record'
    jrn_id         = fields.Integer(string="jrn id", required=True, index=True, readonly=True)
    table_name     = fields.Char(string = 'table name', compute='filldata')
    table_id       = fields.Char(string="id in table", required=True, index=True, readonly=True)
    datetime_event = fields.Datetime(string="Datetime of the event", index=True, readonly = True)
    user_event     = fields.Char(string="User who make event", index=True, readonly = True)
    status         = fields.Integer(string="status", required=True, index=True, readonly=True)
    operation      = fields.Selection([('2', 'Insert'), ('4', 'Update'), ('8','Delete')]
                    ,string="type of operation", required=True, index=True, readonly=True)

    view_journal_record_spec_ids = fields.One2many(
            comodel_name='jrn.view_journal_record_spec',
            inverse_name='view_journal_record_id',
            string="view journal record rows", auto_join=True)



    def get_fields_table_for_case(self, table_name):
        sql_string = "SELECT t1.column_name FROM information_schema.columns t1  WHERE t1.table_name = 'jrn_{0}' ;"
        sql_string = sql_string.format(table_name)
        print('recreate table columns sql_string = ', sql_string)
        self.env.cr.execute(sql_string)

        case_fields_string = ''
        for record_jrn in self.env.cr.fetchall():
                case_fields_string += " when col.column_name = '"+''.join(record_jrn)+"'  then cast({0}."+'"'+ ''.join(record_jrn)+'" as text) \n'
        return  case_fields_string



    @api.depends("jrn_id")
    def filldata(self):
        # self.env.cr.commit();
        jrn = self.env['jrn.jrn'].search([('id','=',self.jrn_id)])
        self.table_name = jrn.table_name_id.name

        old_fields = self.get_fields_table_for_case(jrn.table_name_id.name).format('told')
        print('old_fields = ', old_fields)
        new_fields = self.get_fields_table_for_case(jrn.table_name_id.name).format('tnew')
        print('new_fields = ', new_fields)

        query = """
            select 
               col.column_name as Field
             , case {2}
               end as oldvalue
             , case {3}
               end as newvalue            	 	         
            from jrn_jrn jrn 
               left join jrn_{1} told on told.jrn_id = jrn.id and told.jrn_oldnewrec = 2
               left join jrn_{1} tnew on tnew.jrn_id = jrn.id and tnew.jrn_oldnewrec = 1
               join information_schema.columns col on col.table_name = 'jrn_{1}'
            where jrn.id = {0}
            and col.column_name not in('jrn_oldnewrec','jrn_id')        
                """
        query = query.format(self.jrn_id, jrn.table_name_id.name,old_fields, new_fields)
        self.env.cr.execute(query)
        view_journal_record_spec_ids=[]
        for record_jrn in self.env.cr.fetchall():
            row = [0, 0, {'field_name':record_jrn[0],'old_value': record_jrn[1], 'new_value':record_jrn[2]}]
            print(row)
            view_journal_record_spec_ids.append(row)

        print(view_journal_record_spec_ids)

        self.view_journal_record_spec_ids = view_journal_record_spec_ids

        # [(0, 0, {
        #     'product_id': self.product_3.id,
        #     'product_qty': 3,
        # })]
        # jrn_rows = self.env['jrn.view_journal_record_spec'].create(
        #     dict(
        #         view_journal_record_id=self.id,
        #         field_name='asaasas'
        #         )
        #     )

class jrn_view_journal_record_spec(models.TransientModel):
    _name = 'jrn.view_journal_record_spec'
    _description = 'jrn wizard for view journal record'
    # array_table_names  = fields.Selection(list_table_names, string='table names')

    view_journal_record_id = fields.Many2one('jrn.view_journal_record', required=True, index=True, readonly = True)
    field_name = fields.Char(string='field_name', required=True)
    old_value = fields.Text(string='field old value', )
    new_value = fields.Text(string='field new value',)





