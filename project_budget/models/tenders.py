from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import pytz
from datetime import timedelta

class tenders(models.Model):
    _name = 'project_budget.tenders'
    _description = "projects tenders"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name_to_show'
    _check_company_auto = True
    _order = 'date_of_filling_in'
    # _rec_names_search = ['project_id', 'essence_project']

    def _get_responsible_dkp_domain(self):
        domain = False
        dkp_department_id = self.env['ir.config_parameter'].sudo().get_param('project_budget.tender_department_id', False)
        if dkp_department_id:
            domain = [('department_id', '=', int(dkp_department_id))]
        return domain

    def _get_domain_signer_id(self):
        return [('id', 'in', self.env['res.company'].sudo().search([]).partner_id.ids)]

    tender_id = fields.Char(string="Tender ID", required=True, index=True, copy=True, group_operator = 'count',
                             default='ID') #lambda self: self.env['ir.sequence'].sudo().next_by_code('project_budget.projects'))
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    is_need_projects = fields.Boolean(string="is_need_projects", copy=True, default = False,tracking=True)
    projects_id = fields.Many2one('project_budget.projects', tracking=True, domain = "[('budget_state', '=', 'work')]")  # TODO убрать после миграции на множественные проекты
    project_ids = fields.Many2many('project_budget.projects', tracking=True, domain="[('budget_state', '=', 'work')]")
    currency_id = fields.Many2one('res.currency', string='Main Account Currency',  required = True, copy = True,
                                  default=lambda self: self.env['res.currency'].search([('name', '=', 'RUB')], limit=1),tracking=True)
    vat_attribute_id = fields.Many2one('project_budget.vat_attribute', string='vat_attribute', copy=True, tracking=True, required=True)

    key_account_manager_ids = fields.Many2many('hr.employee', compute='_compute_data_from_projects', readonly=True, store=True)

    essence_projects = fields.Text(readonly=True, compute='_compute_data_from_projects')

    date_of_filling_in = fields.Date(string='date_of_filling_in tender', required=True, default=fields.Date.context_today, tracking=True)
    participant_id = fields.Many2one('project_budget.legal_entity_signing',
                                    string='legal_entity_signing a contract from the NCC', copy=True, tracking=True)  # TODO удалить после миграции на signer_id
    signer_id = fields.Many2one('res.partner', string='legal_entity_signing a contract from the NCC', required=True,
                                domain=_get_domain_signer_id, copy=True, tracking=True)
    auction_number = fields.Char(string='auction_number', default = "",tracking=True, required = True)
    url_tender = fields.Html(string='url of tender', default = "",tracking=True, required = True)
    url_contract = fields.Html(string='url of contract', default="", tracking=True)
    partner_id = fields.Many2one('res.partner', string='customer_organization', copy=True, tracking=True,
                                 domain="[('is_company','=',True)]")   # TODO убрать после миграции на множественные проекты
    partner_ids = fields.Many2many('res.partner', string='customer_organizations', required=True, copy=True, tracking=True,
                                 domain="[('is_company','=',True)]")
    organizer_partner_id = fields.Many2one('res.partner', string='organizer', copy=True, tracking=True,
                                           domain="[('is_company','=',True)]")

    contact_information = fields.Text(string='contact_information', default = "",tracking=True)
    name_of_the_purchase = fields.Text(string='name_of_the_purchase', default = "",tracking=True, required = True)
    is_need_initial_maximum_contract_price = fields.Boolean(string="is_need_initial_maximum_contract_price", copy=True, default = False)
    is_need_securing_the_application  = fields.Boolean(string="is_need_securing_the_application", copy=True, default = False)

    okpd2 = fields.Text(string='okpd2', default="", tracking=True)

    is_need_contract_security  = fields.Boolean(string="is_need_contract_security", copy=True, default = False)
    is_need_provision_of_GO  = fields.Boolean(string="is_need_provision_of_GO", copy=True, default = False)
    is_need_licenses_SRO  = fields.Boolean(string="is_need_licenses_SRO", copy=True, default = False,tracking=True)
    licenses_SRO = fields.Char(string='licenses_SRO',tracking=True)
    current_status = fields.Many2one('project_budget.tender_current_status', required=True, tracking=True)

    responsible_ids = fields.Many2many('hr.employee', relation='tender_employee_rel', column1='tender_id',
                                       column2='employee_id', string='responsibles')
    responsible_dkp_ids = fields.Many2many('hr.employee', relation='dkp_employee_rel', column1='tender_id',
                                           column2='employee_id', string='responsibles_dkp',
                                           domain=_get_responsible_dkp_domain)
    responsible_dkp_str = fields.Text(string='responsibles_dkp', compute='_compute_responsible_dkp_str',
                                      compute_sudo=True)

    is_need_payment_for_the_victory = fields.Boolean(string="is_need_payment_for_the_victory", copy=True, default=False)
    is_need_site_payment = fields.Boolean(string="is_need_site_payment", copy=True, default=False, tracking=True)

    tender_comments_ids = fields.One2many(comodel_name='project_budget.tender_comments',inverse_name='tenders_id',string="tenders comments", auto_join=True, copy=True)

    tender_sums_ids = fields.One2many(comodel_name='project_budget.tender_sums', inverse_name='tenders_id',
                                          string="tender sums", auto_join=True, copy=True)
    presale_number = fields.Char(string="presale_number", copy=True, default ="")

    attachment_count = fields.Integer(compute='_compute_attachment_count', string='Attachments')

    name_to_show = fields.Char(string='name_to_show', compute='_get_name_to_show')

    @api.depends('responsible_dkp_ids')
    def _compute_responsible_dkp_str(self):
        for rec in self:
            rec.responsible_dkp_str = ', '.join(rec.responsible_dkp_ids.mapped('name'))

    @api.depends('project_ids')
    def _compute_data_from_projects(self):
        for rec in self:
            rec.key_account_manager_ids = rec.project_ids.key_account_manager_id
            essence = ''
            for project in rec.project_ids:
                if project.essence_project:
                    essence += project.essence_project + '\n\n'
            rec.essence_projects = essence.strip()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('tender_id') or vals['tender_id'] == 'ID':
                vals['tender_id'] = self.env['ir.sequence'].sudo().next_by_code('project_budget.tenders')
        return super().create(vals_list)


    @api.depends('date_of_filling_in','partner_id','name_of_the_purchase')
    def _get_name_to_show(self):
        for tender in self:
            tender.name_to_show = tender.date_of_filling_in.strftime('%Y-%m-%d') + '|'+ (tender.partner_id.name or '') + '|' + (tender.name_of_the_purchase or '')+'...'

    def _compute_attachment_count(self):
        for tender in self:
            tender.attachment_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', self._name),
                ('res_id', '=', tender.id)
            ])

    @api.depends('signer_id')
    def _get_allowed_signer_ids(self):  # формируем домен партнеров, которые являются нашими компаниями
        for record in self:
            record.allowed_signer_ids = self.env['res.company'].search([]).partner_id

    def action_open_attachments(self):
        self.ensure_one()
        return {
            'name': _('Attachments'),
            'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,tree,form',
            'context': "{'default_res_model': '%s','default_res_id': %d}" % (self._name, self.id),
            'help': """
                <p class="o_view_nocontent_smiling_face">%s</p>
                """ % _("Add attachments for this tender")
        }

    @api.onchange('is_need_projects','project_ids','currency_id','signer_id','auction_number','url_tender'
        ,'contact_information','name_of_the_purchase','is_need_initial_maximum_contract_price'
        ,'is_need_securing_the_application','is_need_contract_security','is_need_provision_of_GO'
        ,'is_need_licenses_SRO','licenses_SRO','current_status','responsible_ids','is_need_payment_for_the_victory'
        ,'is_need_site_payment','tender_comments_ids','tender_sums_ids','presale_number')
    def _check_changes_tender(self):
        for row in self:
            if row.is_need_projects == False:
                row.project_ids = False
            # Федоренко сказала убрать - будут рками ставить
            # if row.date_of_filling_in != fields.datetime.now():
            #     row.date_of_filling_in = fields.datetime.now()

    # @api.onchange('project_ids')
    # def _check_partner_ids(self):
    #     for row in self:
    #         row.partner_ids = row.project_ids.partner_id

    # @api.onchange('is_need_initial_maximum_contract_price','is_need_securing_the_application','is_need_contract_security'
    #               ,'is_need_provision_of_GO','is_need_licenses_SRO','is_need_payment_for_the_victory')
    # def _check_changes_tender(self):
    #     for row in self:
    #         if row.is_need_initial_maximum_contract_price ==False : row.initial_maximum_contract_price=0
    #         if row.is_need_securing_the_application==False : row.securing_the_application=0
    #         if row.is_need_contract_security ==False : row.contract_security =0
    #         if row.is_need_provision_of_GO ==False : row.provision_of_GO = 0
    #         if row.is_need_licenses_SRO ==False : row.licenses_SRO = ''
    #         if row.is_need_payment_for_the_victory == False : row.payment_for_the_victory = ''


class tender_sums(models.Model):
    _name = 'project_budget.tender_sums'
    _description = "projects tender sums"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    tenders_id = fields.Many2one('project_budget.tenders',string='tender id', required=True, copy=True, tracking=True, ondelete='cascade',)
    is_main_currency = fields.Boolean(string="is_main_currency", compute="_compute_is_main_currency", default = True)
    currency_id = fields.Many2one('res.currency', string='Currency',  copy = True,
                                  default=lambda self: self.tenders_id.currency_id,tracking=True)
    participants_offer = fields.Monetary(string='participants_offer', tracking=True, required=True)
    participants_offer_currency_id = fields.Many2one('res.currency', string='participants_offer_ Currency',  required = True, copy = True,
                                  default=lambda self: self.tenders_id.currency_id,tracking=True)
    participants_offer_descr = fields.Text(string='participants_offer description', tracking=True)
    participants_offer_vat_attribute_id = fields.Many2one('project_budget.vat_attribute', string='participants_offer vat_attribute', copy=True, tracking=True,
                                       required=True)
    initial_maximum_contract_price =fields.Monetary(string='initial_maximum_contract_price',tracking=True)
    initial_maximum_contract_price_currency_id = fields.Many2one('res.currency', string='initial_maximum_contract_price Currency',   copy = True,
                                  default=lambda self: self.tenders_id.currency_id,tracking=True)
    initial_maximum_contract_price_descr =fields.Text(string='initial_maximum_contract_price description',tracking=True)
    initial_maximum_contract_price_vat_attribute_id = fields.Many2one('project_budget.vat_attribute',
                                                          string='initial_maximum_contract_price vat_attribute', copy=True,
                                                          tracking=True,)
    payment_for_the_victory = fields.Monetary(string="payment_for_the_victory", copy=True, default ="")
    payment_for_the_victory_currency_id = fields.Many2one('res.currency', string='payment_for_the_victory Currency',   copy = True,
                                  default=lambda self: self.tenders_id.currency_id,tracking=True)
    payment_for_the_victory_descr = fields.Text(string="payment_for_the_victory description", copy=True, default="")
    securing_the_application = fields.Monetary(string='securing_the_application', tracking=True)
    securing_the_application_currency_id = fields.Many2one('res.currency', string='securing_the_application Currency', copy = True,
                                  default=lambda self: self.tenders_id.currency_id,tracking=True)
    securing_the_application_descr = fields.Text(string='securing_the_application description', tracking=True)
    contract_security = fields.Monetary(string='contract_security',tracking=True)
    contract_security_currency_id = fields.Many2one('res.currency', string='contract_security Currency', copy = True,
                                  default=lambda self: self.tenders_id.currency_id,tracking=True)
    contract_security_descr = fields.Text(string='contract_security description', tracking=True)
    provision_of_GO = fields.Monetary(string='provision_of_GO',tracking=True)
    provision_of_GO_currency_id = fields.Many2one('res.currency', string='provision_of_GO Currency', copy = True,
                                  default=lambda self: self.tenders_id.currency_id,tracking=True)
    provision_of_GO_descr = fields.Text(string='provision_of_GO description', tracking=True)
    site_payment = fields.Monetary(string='site_payment',tracking=True)
    site_payment_currency_id = fields.Many2one('res.currency', string='site_payment Currency', copy = True,
                                  default=lambda self: self.tenders_id.currency_id,tracking=True)
    site_payment_descr = fields.Text(string='site_payment description', tracking=True)

    @api.depends('tenders_id.currency_id','currency_id')
    def _compute_is_main_currency(self):
        for row in self:
            if row.currency_id.id == row.tenders_id.currency_id.id:
                row.is_main_currency = True
            else:
                row.is_main_currency = False

    # Федоренко сказала убрать - будут рками ставить
    # @api.onchange('currency_id','participants_offer','participants_offer_descr','initial_maximum_contract_price'
    #              ,'initial_maximum_contract_price_descr','payment_for_the_victory','payment_for_the_victory_descr'
    #              ,'securing_the_application','securing_the_application_descr','contract_security','contract_security_descr'
    #              ,'provision_of_GO','provision_of_GO_descr','site_payment','site_payment_descr'
    #              )
    # def _check_changes_tender(self):
    #     for row in self:
    #         if row.tenders_id.date_of_filling_in != fields.datetime.now():
    #             row.tenders_id.date_of_filling_in = fields.datetime.now()

    # @api.onchange('is_main_currency')
    # def _check_changes_tender(self):
    #     for row in self:
    #         print('row.tenders_id = ',row.tenders_id.id.origin)
    #         other_sums = self.env['project_budget.tender_sums'].search(
    #             [('tenders_id', '=', row.tenders_id.id.origin), ('id', '!=', row.id.origin),('is_main_currency','=',True)])
    #         print('row = ', len(other_sums))
    #
    #         if other_sums:
    #             if row.is_main_currency == False:
    #                 row.is_main_currency = True
    #             else:
    #                 for other_sum in other_sums:
    #                     other_sum.is_main_currency = False
    #         else:
    #             if row.is_main_currency == False:
    #                 row.is_main_currency = True

class tender_comments(models.Model):
    _name = 'project_budget.tender_comments'
    _description = "projects tender comments"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_comment'

    tenders_id = fields.Many2one('project_budget.tenders',string='tender id', required=True, copy=True, tracking=True, ondelete='cascade',)
    date_comment = fields.Date(string='date of the comment', required=True, default=fields.Date.context_today, tracking=True)
    is_need_type = fields.Boolean(string="is need comment type ", copy=True, default = True)
    type_comment_id = fields.Many2one('project_budget.tender_comments_type',string='tender comments type', copy=True, tracking=True)
    text_comment = fields.Text(string="text of the comment", copy=True, default ="")

    # Федоренко сказала убрать - будут рками ставить
    # @api.onchange('date_comment','type_comment_id','text_comment')
    # def _check_changes_tender(self):
    #     for row in self:
    #         if row.tenders_id.date_of_filling_in != fields.datetime.now():
    #             row.tenders_id.date_of_filling_in = fields.datetime.now()


