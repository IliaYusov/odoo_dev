from odoo import _, models, fields, api, http,  sql_db
import odoo
from contextlib import closing
from odoo.http import request
from psycopg2 import sql

class jrn_base(models.Model):
    _name = 'jrn.base'
    _description = "journal base"

    def get_current_db_name(self):
        query = "SELECT current_database();"
        self.env.cr.execute(query)
        for record_jrn in self.env.cr.fetchone():
            return ''.join(record_jrn)
        return ''

    def get_journal_db_name(self):
        return self.get_current_db_name() + '_journal'

    def get_pgsql_server_port(self):
        query = "SELECT setting FROM pg_settings WHERE name = 'port';"
        self.env.cr.execute(query)
        for record_jrn in self.env.cr.fetchone():
            return ''.join(record_jrn)
        return ''

    def get_fdw_journal(self):
        # FOREIGN DATA WRAPPER for journal db
        return 'jrn_odoo_' + self.get_journal_db_name()

    def get_fdw_current(self):
        # FOREIGN DATA WRAPPER for orogonal db
        return 'jrn_odoo_' + self.get_current_db_name()

    def create_journal_base(self):
        db = odoo.sql_db.db_connect('postgres')
        db_name = self.get_current_db_name()
        db_name_journal = self.get_journal_db_name()

        with closing(db.cursor()) as cr:
            chosen_template = odoo.tools.config['db_template']
            cr.execute("SELECT datname FROM pg_database WHERE datname = %s",
                       (db_name_journal,), log_exceptions=False)
            if cr.fetchall():
                raise DatabaseExists("Journal database %r already exists!" % (db_name_journal,))
            else:
                # database-altering operations cannot be executed inside a transaction
                cr.rollback()
                cr._cnx.autocommit = True

                # 'C' collate is only safe with template0, but provides more useful indexes
                collate = sql.SQL("LC_COLLATE 'C'" if chosen_template == 'template0' else "")
                cr.execute(
                    sql.SQL("CREATE DATABASE {} ENCODING 'unicode' {} TEMPLATE {}").format(
                        sql.Identifier(db_name_journal), collate, sql.Identifier(chosen_template)
                    ))

        query = "CREATE SERVER {0} FOREIGN DATA WRAPPER postgres_fdw OPTIONS(host 'localhost', dbname '{1}', port '{2}');"
        query1 = "DROP SERVER IF EXISTS {0};"
        dbjrn = odoo.sql_db.db_connect(db_name_journal)

        with dbjrn.cursor() as cr:
            cr.execute("CREATE EXTENSION IF NOT EXISTS postgres_fdw")
            query_jrn = query1.format(self.get_fdw_current())
            print('query_jrn = ', query_jrn)
            cr.execute(query_jrn)
            query_jrn = query.format(self.get_fdw_current(), self.get_current_db_name(), self.get_pgsql_server_port())
            print('query_jrn = ', query_jrn)
            cr.execute(query_jrn)

        # db = odoo.sql_db.db_connect(db_name)
        self.env.cr.execute("CREATE EXTENSION IF NOT EXISTS postgres_fdw")
        query_orig = query1.format(self.get_fdw_journal())
        print('query_orig = ', query_orig)
        self.env.cr.execute(query_orig)
        query_orig = query.format(self.get_fdw_journal(), self.get_journal_db_name(), self.get_pgsql_server_port())
        print('query_orig = ', query_orig)
        self.env.cr.execute(query_orig)

        # query = "SELECT 'CREATE DATABASE ' || d.datname||'_journal with '||" \
        #         "' OWNER = '||pg_catalog.pg_get_userbyid(d.datdba)|| '" \
        #         " TABLESPACE = '||ts.spcname||' LC_COLLATE = '''||d.datcollate||'''' || ' LC_CTYPE = ''' ||d.datctype||'''' || " \
        #         "' CONNECTION LIMIT = -1 TEMPLATE template0;' " \
        #         " FROM pg_catalog.pg_database d" \
        #         " join pg_tablespace ts on ts.oid = d.dattablespace" \
        #         " WHERE d.datname = (SELECT current_database());"
        # print('query = ', query)
        # self.env.cr.execute(query)
        # for record_jrn in self.env.cr.fetchone():
        #     print('record_jrn[0] = ', record_jrn)
        #     query = record_jrn
        #
        # # res = super().action_confirm()
        # self.flush()
        # db = sql_db.db_connect('postgres')
        # cursor = db.cursor()
        # cursor.execute(query)
        # data = cursor.dictfetchall()

    def create_trigger_jrn_jrn_delete(self):
        query = """
        drop function if exists "jrn_jrn_jrn_delete_record_tp"() cascade;

        CREATE FUNCTION "jrn_jrn_jrn_delete_record_tp"()
                RETURNS trigger
                LANGUAGE 'plpgsql'
                COST 100
                VOLATILE NOT LEAKPROOF SECURITY DEFINER
            AS $BODY$
            DECLARE
             query_str varchar;                          
			 vtable_name varchar;
            BEGIN
				   vtable_name := (select tt.name from jrn_tables tt where tt.id = old.table_name_id);
                   query_str := 'delete from jrn_' ||vtable_name||' where jrn_id = '||cast(old.id as varchar);
				   EXECUTE query_str;
            RETURN NULL; 
			END;            
            $BODY$;            

        GRANT EXECUTE ON FUNCTION "jrn_jrn_jrn_delete_record_tp"() TO PUBLIC;

          CREATE TRIGGER "jrn_jrn_jrn_delete" 
            AFTER DELETE ON jrn_jrn
            FOR EACH ROW EXECUTE PROCEDURE "jrn_jrn_jrn_delete_record_tp"();         
        """
        self.env.cr.execute(query)

    def fill_table_list(self):
        self.create_trigger_jrn_jrn_delete()
        jrn = self.env['jrn.base']

        print('jrn.get_current_db_name() = ', jrn.get_current_db_name())

        # db_name = self.get_current_db_name()
        # dbjrn = odoo.sql_db.db_connect(db_name)
        # with dbjrn.cursor() as cr: cr.execute("""CREATE EXTENSION IF NOT EXISTS "uuid-ossp"; """)
        # self.env.cr.execute("""CREATE EXTENSION IF NOT EXISTS "uuid-ossp"; """)
        # query = "select 1 FROM pg_catalog.pg_database d WHERE d.datname = '{0}';"
        # query = query.format(jrn.get_journal_db_name())
        # self.env.cr.execute(query)
        # if self.env.cr.fetchall():
        #     f = 1
        # else:
        #     jrn.create_journal_base()

        query = """         insert into
                                jrn_tables(name)
                            select
                                table_name
                            from information_schema.tables t
                            left join jrn_tables on jrn_tables.name = t.table_name
                            where
                                table_schema = 'public'
                            and table_type = 'BASE TABLE'
                            and table_name not like 'jrn%'
                            and jrn_tables.id is null        
                """
        print('1 query = ', query)
        self.env.cr.execute(query)

        query = """UPDATE jrn_tables SET is_table_exist_in_jrn = false 
        FROM( select jrn_tables.id as jrn_tables_id
        from jrn_tables left join information_schema.tables t on t.table_schema = 'public' and t.table_name = 'jrn_'||jrn_tables.name
        where t.table_name is null )  AS subquery
        WHERE jrn_tables.id = subquery.jrn_tables_id;

        UPDATE jrn_tables SET is_table_exist_in_jrn = true
        FROM( select jrn_tables.id as jrn_tables_id
        from jrn_tables left join information_schema.tables t on t.table_schema = 'public' and t.table_name = 'jrn_'||jrn_tables.name
        where t.table_name is not null )  AS subquery
        WHERE jrn_tables.id = subquery.jrn_tables_id;	                       
        """
        print('2 query = ', query)
        self.env.cr.execute(query)

        tables = self.env['jrn.tables'].search([])
        print('tables = ', tables)
        for table in tables:
            print('table = ', table)
            self.action_check_structure_one(table)

        return {'type': 'ir.actions.client',
                'tag': 'reload'
                }

    def action_check_structure_one(self, table):
        sql_string_original = "SELECT column_name || '|' || data_type || coalesce(cast(character_maximum_length as char), '') || coalesce(cast(character_octet_length as char), '') ||" \
                              "coalesce(cast(numeric_precision as char), '') || coalesce(cast(numeric_precision_radix as char), '') || coalesce(cast(numeric_scale as char), '') || " \
                              "coalesce(cast(datetime_precision as char), '') || coalesce(cast(interval_type as char), '') FROM information_schema.columns " \
                              "WHERE table_name = '{0}' and column_name not in ('jrn_oldnewrec', 'jrn_id');"
        sql_string_jrn = "SELECT column_name || '|' || data_type || coalesce(cast(character_maximum_length as char), '') || coalesce(cast(character_octet_length as char), '') ||" \
                         "coalesce(cast(numeric_precision as char), '') || coalesce(cast(numeric_precision_radix as char), '') || coalesce(cast(numeric_scale as char), '') || " \
                         "coalesce(cast(datetime_precision as char), '') || coalesce(cast(interval_type as char), '') FROM information_schema.columns " \
                         "WHERE table_name = 'jrn_{0}' and column_name not in ('jrn_oldnewrec', 'jrn_id');"

        sql_string_original = sql_string_original.format(table.name)
        self.env.cr.execute(sql_string_original)
        structure_original = ''
        for record_original in self.env.cr.fetchall():
            structure_original += ''.join(record_original)

        sql_string_jrn = sql_string_jrn.format(table.name)
        self.env.cr.execute(sql_string_jrn)
        structure_jrn = ''
        for record_jrn in self.env.cr.fetchall():
            structure_jrn += ''.join(record_jrn)
        print('sql_string_original=', sql_string_original)
        print('sql_string_jrn=', sql_string_jrn)
        print('structure_jrn=', structure_jrn)
        print('structure_original=', structure_original)
        if structure_jrn == structure_original:
            table.is_structure_correct = True
            print('is_structure_correct', True)
        else:
            table.is_structure_correct = False
            print('is_structure_correct', False)

    def action_recreate_tables_one(self, table):
        sql_string = "DROP TABLE IF EXISTS jrn_{0}_tmp; "
        sql_string = sql_string.format(table.name)
        print('sql_string = ', sql_string)
        self.env.cr.execute(sql_string)

        sql_string = "ALTER TABLE jrn_{0} RENAME TO jrn_{0}_tmp;"
        sql_string = sql_string.format(table.name)
        self.env.cr.execute(sql_string)

        self.action_create_jrn_tables_one(table)

        sql_string = "SELECT t1.column_name FROM information_schema.columns t1" \
                     " join information_schema.columns t2 on " \
                     " t2.table_name = 'jrn_{0}' " \
                     " and t1.column_name = t2.column_name" \
                     " WHERE t1.table_name = 'jrn_{0}_tmp' ;"
        sql_string = sql_string.format(table.name)
        print('recreate table columns sql_string = ', sql_string)
        self.env.cr.execute(sql_string)

        select_fields_string = ''
        for record_jrn in self.env.cr.fetchall():
            if select_fields_string == '':
                select_fields_string += '"' + ''.join(record_jrn) + '"'
            else:
                select_fields_string += ',"' + ''.join(record_jrn) + '"'

        print('select_fields_string = ', select_fields_string)
        sql_string = "insert into jrn_{0} ({1}) select {1} from jrn_{0}_tmp; "
        sql_string = sql_string.format(table.name, select_fields_string)
        print('sql_string = ', sql_string)
        self.env.cr.execute(sql_string)
        sql_string = "DROP TABLE IF EXISTS jrn_{0}_tmp; "
        sql_string = sql_string.format(table.name)
        print('sql_string = ', sql_string)
        self.env.cr.execute(sql_string)

    def action_create_jrn_tables_one(self, table):
        jrn = self.env['jrn.base']
        # db_name = jrn.get_current_db_name()
        # db_name_journal = jrn.get_journal_db_name()
        #
        # db = odoo.sql_db.db_connect(db_name_journal)
        # with closing(db.cursor()) as cr:
        #     sql_string="SELECT 1 FROM pg_catalog.pg_tables WHERE schemaname = 'public' AND tablename = 'jrn_{0}'"
        #     sql_string = sql_string.format(table.name)
        #     cr.execute(sql_string)
        #     if cr.fetchall():
        #         f = 1
        #         print('already exists table jrn_', table.name)
        #     else:
        #         print('Start create table jrn_', table.name)
        #         sql_string = "CREATE TABLE jrn_{0} (like {0}, jrn_action integer, jrn_guid char(16), PRIMARY KEY(jrn_guid));"
        #         # sql_string = "CREATE TABLE jrn_{0}(like {0} including all, jrn_action integer, jrn_guid char(16) );"
        #         # sql_string = "create table jrn_{0} as select * from {0} with no data;"
        #         sql_string = sql_string.format(table.name)
        #         print('1 sql_string', sql_string)
        #         cr.execute(sql_string)
        #
        # db = odoo.sql_db.db_connect(db_name)

        sql_string = "SELECT 1 FROM pg_catalog.pg_tables WHERE schemaname = 'public' AND tablename = 'jrn_{0}'"
        sql_string = sql_string.format(table.name)
        self.env.cr.execute(sql_string)
        if self.env.cr.fetchall():
            f = 1
            print('already exists table jrn_', table.name)
        else:
            print('Start create table jrn_', table.name)
            sql_string = "CREATE TABLE jrn_{0} (like {0}, jrn_oldnewrec integer, jrn_id integer);"
            # sql_string = "CREATE TABLE jrn_{0}(like {0} including all, jrn_action integer, jrn_guid char(16) );"
            # sql_string = "create table jrn_{0} as select * from {0} with no data;"
            sql_string = sql_string.format(table.name)
            print('1 sql_string', sql_string)
            self.env.cr.execute(sql_string)

            sql_string = """DROP INDEX if exists jrn_id_{0} CASCADE; 
            CREATE INDEX jrn_id_{0} ON jrn_{0} USING btree(jrn_id);"""
            sql_string = sql_string.format(table.name)
            print('1q sql_string', sql_string)
            self.env.cr.execute(sql_string)

        table.is_table_exist_in_jrn = True

        self.action_check_structure_one(table)
        # sql_string = "select concat('alter table public.jrn_{0} drop constraint ', constraint_name) as my_query from information_schema.table_constraints where table_schema = 'public' and table_name = 'jrn_{0}';"
        # # and constraint_type = 'PRIMARY KEY';"
        # sql_string = sql_string.format(table.name)
        # print('2 sql_string', sql_string)
        # self.env.cr.execute(sql_string)
        # for record in self.env.cr.fetchall():
        #     print('record = ', record[0])
        #     sql_string = record[0]
        #     self.env.cr.execute(sql_string)

        # sql_string = "ALTER TABLE jrn_{0} ADD CONSTRAINT jrn_{0}_pkey PRIMARY KEY(jrn_guid); "
        # sql_string = sql_string.format(table.name)
        # print('3 sql_string', sql_string)
        # self.env.cr.execute(sql_string)

    def get_fields_table_prefix(self, table):
        sql_string = "SELECT t1.column_name FROM information_schema.columns t1  WHERE t1.table_name = '{0}' ;"
        sql_string = sql_string.format(table.name)
        print('recreate table columns sql_string = ', sql_string)
        self.env.cr.execute(sql_string)

        select_fields_string = ''
        for record_jrn in self.env.cr.fetchall():
            if select_fields_string == '':
                select_fields_string += '{0}"' + ''.join(record_jrn) + '"'
            else:
                select_fields_string += ',{0}"' + ''.join(record_jrn) + '"'
        return select_fields_string

    def get_fields_table(self, table):
        str = self.get_fields_table_prefix(table)
        str = str.format(' ')
        return str

    def get_cast_primary_key(self, table):
        query = """
            SELECT a.attname
            FROM   pg_index i
            JOIN   pg_attribute a ON a.attrelid = i.indrelid
                                 AND a.attnum = ANY(i.indkey)
            WHERE  i.indrelid = '{0}'::regclass
            AND    i.indisprimary;
                """
        query = query.format(table.name)
        self.env.cr.execute(query)

        select_fields_string = ''
        for record_jrn in self.env.cr.fetchall():
            if select_fields_string == '':
                select_fields_string += 'cast({0}."' + ''.join(record_jrn) + '" as varchar)'
            else:
                select_fields_string += '||' + "'||'||" + 'cast({0}."' + ''.join(record_jrn) + '" as varchar)'
        return select_fields_string

    def create_trigger(self, table):
        self.drop_trigger(table)

        query_function = """
            -- FUNCTION: "{0}_tp"()

            -- DROP FUNCTION "{0}_tp"();

            CREATE FUNCTION "{0}_tp"()
                RETURNS trigger
                LANGUAGE 'plpgsql'
                COST 100
                VOLATILE NOT LEAKPROOF SECURITY DEFINER
            AS $BODY$
            DECLARE
             VTABLEID varchar;                          
             VOPERATION INTEGER;
             vid integer;
             user_id integer;
             user_login varchar;
            BEGIN
                if old is distinct from new then  

                   user_id := 0;     
                   user_login := '' ;     
                   {7}                                                            

                   IF TG_OP = 'INSERT' THEN VOPERATION := 2; VTABLEID := {5};
                   ELSIF TG_OP = 'UPDATE' THEN VOPERATION := 4; VTABLEID := {5};
                   ELSE VOPERATION := 8; VTABLEID := {6};
                   END IF;

                   INSERT INTO jrn_jrn (table_name_id, table_id, datetime_event, user_event, status, operation)
                   VALUES({1}, VTABLEID,  now() at time zone 'UTC', user_login, 0, VOPERATION) RETURNING id INTO vid;

                   IF TG_OP = 'DELETE' OR TG_OP = 'UPDATE' THEN
                       INSERT INTO jrn_{0}(
                       jrn_id,jrn_oldnewrec,{2}) 
                        VALUES(
                         vid,2,{3}
                        );
                   END IF;

                   IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
                       INSERT INTO jrn_{0}(                   
                        jrn_id,jrn_oldnewrec,{2}
                        )
                        VALUES(
                         vid,1,{4}
                        );
                 END IF;
               END IF;
            RETURN NULL; END;

            $BODY$;


            GRANT EXECUTE ON FUNCTION "{0}_tp"() TO PUBLIC;
        """
        # ALTER FUNCTION "{0}_tp"() OWNER TO postgres;
        # GRANT EXECUTE ON FUNCTION "{0}_tp"() O postgres;

        fields = self.get_fields_table(table)
        index = fields.find('write_uid')
        get_user = ""
        if index == -1:
            get_user = ""
        else:
            get_user = """                   
                              IF TG_OP = 'INSERT' THEN user_id := NEW.write_uid;
                                  ELSIF TG_OP = 'UPDATE' THEN user_id := NEW.write_uid;
                                  ELSE user_id := OLD.write_uid;
                              END IF;
                              if user_id <> 0 THEN
                               user_login := (SELECT login FROM res_users where id = user_id );
                              END IF;
                              """
        print('fields = ', fields)
        old_fields = self.get_fields_table_prefix(table).format('OLD.')
        print('old_fields = ', old_fields)
        new_fields = self.get_fields_table_prefix(table).format('NEW.')
        print('new_fields = ', new_fields)
        cast_primary_key_new = self.get_cast_primary_key(table)
        cast_primary_key_new = cast_primary_key_new.format('NEW')
        cast_primary_key_old = self.get_cast_primary_key(table)
        cast_primary_key_old = cast_primary_key_old.format('OLD')
        query_function = query_function.format(table.name, table.id, fields, old_fields, new_fields,
                                               cast_primary_key_new, cast_primary_key_old, get_user)
        self.env.cr.execute(query_function)
        print('query_function = ', query_function)

        query_trg = """


        CREATE TRIGGER "jrn_{0}" 
        AFTER INSERT OR DELETE OR UPDATE ON {0} 
        FOR EACH ROW EXECUTE PROCEDURE "{0}_tp"();"""
        query_trg = query_trg.format(table.name)
        print('query_trg = ', query_trg)
        self.env.cr.execute(query_trg)
        return ''

    def drop_trigger(self, table):
        query_function = """DROP TRIGGER IF EXISTS "jrn_{0}" on "{0}" CASCADE ;
                            DROP FUNCTION IF EXISTS "{0}_tp"();"""
        query_function = query_function.format(table.name)
        print('query_function = ', query_function)
        self.env.cr.execute(query_function)
        return False

    def undo_change(self, change):
        # operation = fields.Selection([('2', 'Insert'), ('4', 'Update'), ('8','Delete')]
        table_name = change.table_name_id.name

        if change.Selection == '2':
            print('undo_change insert')

        if change.Selection == '4':
            print('undo_change update')

        if change.Selection == '8':
            print('undo_change delete')

        return False