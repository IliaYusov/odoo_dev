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
    # _rec_names_search = ['project_id', 'essence_project']

    tender_id = fields.Char(string="Tender ID", required=True, index=True, copy=True, group_operator = 'count',
                             default='ID') #lambda self: self.env['ir.sequence'].sudo().next_by_code('project_budget.projects'))
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    is_need_projects = fields.Boolean(string="is_need_projects", copy=True, default = False,tracking=True)
    projects_id = fields.Many2one('project_budget.projects', tracking=True, domain = "[('budget_state', '=', 'work')]")
    currency_id = fields.Many2one('res.currency', string='Main Account Currency',  required = True, copy = True,
                                  default=lambda self: self.env['res.currency'].search([('name', '=', 'RUB')], limit=1),tracking=True)
    vat_attribute_id = fields.Many2one('project_budget.vat_attribute', string='vat_attribute', copy=True, tracking=True, required=True)
    project_office_id = fields.Many2one(related='projects_id.project_office_id', readonly=True)
    project_supervisor_id = fields.Many2one(related='projects_id.project_supervisor_id', readonly=True)
    project_manager_id = fields.Many2one(related='projects_id.project_manager_id', readonly=True)
    rukovoditel_project_id = fields.Many2one(related='projects_id.rukovoditel_project_id', readonly=True)

    essence_project = fields.Text(related='projects_id.essence_project', readonly=True)

    date_of_filling_in = fields.Date(string='date_of_filling_in tender', required=True, default=fields.datetime.now(), tracking=True)
    participant_id = fields.Many2one('project_budget.legal_entity_signing',
                                              string='legal_entity_signing a contract from the NCC', required=True,
                                              copy=True, tracking=True)
    auction_number = fields.Char(string='auction_number', default = "",tracking=True, required = True)
    url_tender = fields.Html(string='url of tender', default = "",tracking=True, required = True)
    customer_organization_id = fields.Many2one('project_budget.customer_organization', string='customer_organization',
                                               required=True, copy=True,tracking=True)
    contact_information = fields.Text(string='contact_information', default = "",tracking=True)
    name_of_the_purchase = fields.Text(string='name_of_the_purchase', default = "",tracking=True, required = True)
    is_need_initial_maximum_contract_price = fields.Boolean(string="is_need_initial_maximum_contract_price", copy=True, default = False)
    is_need_securing_the_application  = fields.Boolean(string="is_need_securing_the_application", copy=True, default = False)

    is_need_contract_security  = fields.Boolean(string="is_need_contract_security", copy=True, default = False)
    is_need_provision_of_GO  = fields.Boolean(string="is_need_provision_of_GO", copy=True, default = False)
    is_need_licenses_SRO  = fields.Boolean(string="is_need_licenses_SRO", copy=True, default = False,tracking=True)
    licenses_SRO = fields.Char(string='licenses_SRO',tracking=True)
    project_manager_id = fields.Many2one(related='projects_id.project_manager_id', readonly=True)
    current_status = fields.Many2one('project_budget.tender_current_status', required=True, tracking=True)

    responsible_ids = fields.Many2many('hr.employee', relation='tender_employee_rel', column1='tender_id', column2='employee_id', string='responsibles', required = True)

    is_need_payment_for_the_victory = fields.Boolean(string="is_need_payment_for_the_victory", copy=True, default = False)
    is_need_site_payment  = fields.Boolean(string="is_need_site_payment", copy=True, default = False,tracking=True)

    tender_comments_ids = fields.One2many(comodel_name='project_budget.tender_comments',inverse_name='tenders_id',string="tenders comments", auto_join=True, copy=True)

    tender_sums_ids = fields.One2many(comodel_name='project_budget.tender_sums', inverse_name='tenders_id',
                                          string="tender sums", auto_join=True, copy=True)
    presale_number = fields.Char(string="presale_number", copy=True, default ="")

    attachment_count = fields.Integer(compute='_compute_attachment_count', string='Attachments')

    name_to_show = fields.Char(string='name_to_show', compute='_get_name_to_show')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('tender_id') or vals['tender_id'] == 'ID':
                vals['tender_id'] = self.env['ir.sequence'].sudo().next_by_code('project_budget.tenders')
        return super().create(vals_list)


    @api.depends('date_of_filling_in','customer_organization_id','name_of_the_purchase')
    def _get_name_to_show(self):
        for tender in self:
            tender.name_to_show = tender.date_of_filling_in.strftime('%Y-%m-%d') + '|'+ (tender.customer_organization_id.name or '') + '|' + (tender.name_of_the_purchase[:30] or '')+'...'

    def _compute_attachment_count(self):
        for tender in self:
            tender.attachment_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', self._name),
                ('res_id', '=', tender.id)
            ])

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

    @api.onchange('is_need_projects','projects_id','currency_id','participant_id','auction_number','url_tender'
        ,'contact_information','name_of_the_purchase','is_need_initial_maximum_contract_price'
        ,'is_need_securing_the_application','is_need_contract_security','is_need_provision_of_GO'
        ,'is_need_licenses_SRO','licenses_SRO','current_status','responsible_ids','is_need_payment_for_the_victory'
        ,'is_need_site_payment','tender_comments_ids','tender_sums_ids','presale_number')
    def _check_changes_tender(self):
        for row in self:
            if row.is_need_projects == False:
                row.projects_id = False
            if row.date_of_filling_in != fields.datetime.now():
                row.date_of_filling_in = fields.datetime.now()

    @api.onchange('projects_id')
    def _check_customer_organization_id(self):
        for row in self:
            row.customer_organization_id = row.projects_id.customer_organization_id



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
    currency_id = fields.Many2one('res.currency', string='Account Currency',  required = True, copy = True,
                                  default=lambda self: self.tenders_id.currency_id,tracking=True)
    participants_offer = fields.Monetary(string='participants_offer', tracking=True, required=True)
    participants_offer_descr = fields.Text(string='participants_offer description', tracking=True)
    initial_maximum_contract_price =fields.Monetary(string='initial_maximum_contract_price',tracking=True)
    initial_maximum_contract_price_descr =fields.Text(string='initial_maximum_contract_price description',tracking=True)
    payment_for_the_victory = fields.Monetary(string="payment_for_the_victory", copy=True, default ="")
    payment_for_the_victory_descr = fields.Text(string="payment_for_the_victory description", copy=True, default="")
    securing_the_application = fields.Monetary(string='securing_the_application', tracking=True)
    securing_the_application_descr = fields.Text(string='securing_the_application description', tracking=True)
    contract_security = fields.Monetary(string='contract_security',tracking=True)
    contract_security_descr = fields.Text(string='contract_security description', tracking=True)
    provision_of_GO = fields.Monetary(string='provision_of_GO',tracking=True)
    provision_of_GO_descr = fields.Text(string='provision_of_GO description', tracking=True)
    site_payment = fields.Monetary(string='site_payment',tracking=True)
    site_payment_descr = fields.Text(string='site_payment description', tracking=True)

    @api.depends('tenders_id.currency_id','currency_id')
    def _compute_is_main_currency(self):
        for row in self:
            if row.currency_id.id == row.tenders_id.currency_id.id:
                row.is_main_currency = True
            else:
                row.is_main_currency = False

    @api.onchange('currency_id','participants_offer','participants_offer_descr','initial_maximum_contract_price'
                 ,'initial_maximum_contract_price_descr','payment_for_the_victory','payment_for_the_victory_descr'
                 ,'securing_the_application','securing_the_application_descr','contract_security','contract_security_descr'
                 ,'provision_of_GO','provision_of_GO_descr','site_payment','site_payment_descr'
                 )
    def _check_changes_tender(self):
        for row in self:
            if row.tenders_id.date_of_filling_in != fields.datetime.now():
                row.tenders_id.date_of_filling_in = fields.datetime.now()

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


    tenders_id = fields.Many2one('project_budget.tenders',string='tender id', required=True, copy=True, tracking=True, ondelete='cascade',)
    date_comment = fields.Date(string='date of the comment', required=True, default=fields.datetime.now(), tracking=True)
    is_need_type = fields.Boolean(string="is need comment type ", copy=True, default = True)
    type_comment_id = fields.Many2one('project_budget.tender_comments_type',string='tender comments type', copy=True, tracking=True)
    text_comment = fields.Text(string="text of the comment", copy=True, default ="")

    @api.onchange('date_comment','type_comment_id','text_comment')
    def _check_changes_tender(self):
        for row in self:
            if row.tenders_id.date_of_filling_in != fields.datetime.now():
                row.tenders_id.date_of_filling_in = fields.datetime.now()


