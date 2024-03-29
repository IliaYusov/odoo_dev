from ast import literal_eval
from odoo import models, fields, api
from odoo.tools.misc import get_lang

class project_type(models.Model):
    _name = 'project_budget.project_type'
    _description = "project_type"
    name = fields.Char(string="project_type name", required=True, translate=True)
    code = fields.Char(string="project_type code", required=True)
    descr = fields.Char(string="project_type description", translate=True)

    is_revenue_from_the_sale_of_works = fields.Boolean(string='is_revenue_from_the_sale_of_works(services)',tracking=True, default=True)
    is_revenue_from_the_sale_of_goods = fields.Boolean(string='is_revenue_from the sale of goods',tracking=True, default=True)
    is_cost_of_goods = fields.Boolean(string='is_cost_of_goods', tracking=True, default=True)
    is_own_works_fot = fields.Boolean(string='is_own_works_fot', tracking=True, default=True)
    is_third_party_works = fields.Boolean(string='is_third_party_works(subcontracting)', tracking=True, default=True)
    is_awards_on_results_project = fields.Boolean(string='is_Awards based on the results of the project', tracking=True, default=True)
    is_transportation_expenses = fields.Boolean(string='is_transportation_expenses', tracking=True, default=True)
    is_travel_expenses = fields.Boolean(string='is_travel_expenses', tracking=True, default=True)
    is_representation_expenses = fields.Boolean(string='is_representation_expenses', tracking=True, default=True)
    is_warranty_service_costs = fields.Boolean(string='is_Warranty service costs', tracking=True, default=True)
    is_rko_other = fields.Boolean(string='is_rko_other', tracking=True, default=True)
    is_other_expenses = fields.Boolean(string='is_other_expenses', tracking=True, default=True)


class project_steps_type(models.Model):
    _name = 'project_budget.project_steps_type'
    _description = "project steps type"
    name = fields.Char(string="name", required=True, translate=True)
    is_revenue_from_the_sale_of_works =fields.Boolean(string='is_revenue_from_the_sale_of_works(services)',tracking=True, default = True)
    is_revenue_from_the_sale_of_goods = fields.Boolean(string='is_revenue_from the sale of goods',tracking=True, default = True)
    is_cost_of_goods = fields.Boolean(string='is_cost_of_goods',tracking=True, default = True)
    is_own_works_fot = fields.Boolean(string='is_own_works_fot',tracking=True, default = True)
    is_third_party_works = fields.Boolean(string='is_third_party_works(subcontracting)',tracking=True, default = True)
    is_awards_on_results_project = fields.Boolean(string='is_Awards based on the results of the project',tracking=True, default = True)
    is_transportation_expenses = fields.Boolean(string='is_transportation_expenses',tracking=True, default = True)
    is_travel_expenses = fields.Boolean(string='is_travel_expenses',tracking=True, default = True)
    is_representation_expenses = fields.Boolean(string='is_representation_expenses',tracking=True, default = True)
    is_warranty_service_costs = fields.Boolean(string='is_Warranty service costs',tracking=True, default = True)
    is_rko_other = fields.Boolean(string='is_rko_other',tracking=True, default = True)
    is_other_expenses = fields.Boolean(string='is_other_expenses',tracking=True, default = True)

# catalogs
class project_office(models.Model):
    _name = 'project_budget.project_office'
    _description = "project_office"
    name = fields.Char(string="project_office name", required=True, translate=True)
    code = fields.Char(string="project_office code", required=True)
    descr = fields.Char(string="project_office description")
    company_id = fields.Many2one('res.company',default=lambda self: self.env.company)
    parent_id = fields.Many2one('project_budget.project_office', string='Parent project_office', copy=True, tracking=True, domain='[("id", "!=", id)]')
    child_ids = fields.One2many('project_budget.project_office', 'parent_id', string="Sub project_office")
    user_id = fields.Many2one('res.users', string='Office manager', )
    avatar_128 = fields.Image(related='user_id.avatar_128', readonly=True)
    receive_tasks_for_approve_project = fields.Boolean(string="Recieve tasks for approve project as supervisor", default = False)
    isRukovoditel_required_in_project = fields.Boolean(string="mark rukovoditel required in prject", default=False)
    print_rukovoditel_in_kb = fields.Boolean(string="Print rukovoditel instead KAM in KB form",
                                                       default=False)
    is_prohibit_selection = fields.Boolean(string="is prohibit selection in projects", default=False)
    report_name = fields.Char(string="name for report")
    report_sort = fields.Integer(string="sorting for report", default=0, required=True)


class project_supervisor(models.Model):
    _name = 'project_budget.project_supervisor'
    _description = "project_supervisor"
    name = fields.Char(string="project_supervisor name", required=True, translate=True)
    code = fields.Char(string="project_supervisor code", required=True)
    descr = fields.Char(string="project_supervisor description", translate=True)
    company_id = fields.Many2one('res.company',default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='user id',  required=True,)
    avatar_128 = fields.Image(related='user_id.avatar_128', readonly=True)
    project_supervisor_access_ids = fields.One2many(
            comodel_name='project_budget.project_supervisor_access',
            inverse_name='project_supervisor_id',
            string="project_supervisor_access",
            copy=True, auto_join=True)

class project_supervisor_access(models.Model):
    _name = 'project_budget.project_supervisor_access'
    _description = "project_supervisor_access"
    project_supervisor_id = fields.Many2one('project_budget.project_supervisor', string='project supervisor id',  required=True,)
    user_id = fields.Many2one('res.users', string='user id',  required=True,)
    can_approve_project = fields.Boolean(string="Can approve project as supervisor", default = False)
    descr = fields.Char(string="project supervisor access description" , translate=True)

class project_manager(models.Model):
    _name = 'project_budget.project_manager'
    _description = "project_manager"
    company_id = fields.Many2one('res.company',default=lambda self: self.env.company)
    name = fields.Char(string="project_manager name", required=True, translate=True)
    code = fields.Char(string="project_manager code", required=True)
    descr = fields.Char(string="project_manager description", translate=True)
    user_id = fields.Many2one('res.users', string='user id', required=True,)
    avatar_128 = fields.Image(related='user_id.avatar_128', readonly=True)
    project_manager_access_ids = fields.One2many(
        comodel_name='project_budget.project_manager_access',
        inverse_name='project_manager_id',
        string="project_manager_access",
        copy=True, auto_join=True)

class project_manager_access(models.Model):
    _name = 'project_budget.project_manager_access'
    _description = "project_manager access"
    project_manager_id = fields.Many2one('project_budget.project_manager', string='project manager id', required=True,)
    user_id = fields.Many2one('res.users', string='user id', required=True,)
    descr = fields.Char(string="project manager access description", translate=True)

class rukovoditel_project(models.Model):
    _name = 'project_budget.rukovoditel_project'
    _description = "rukovoditel_project"
    company_id = fields.Many2one('res.company',default=lambda self: self.env.company)
    name = fields.Char(string="rukovoditel_project name", required=True, translate=True)
    code = fields.Char(string="rukovoditel_project code", required=True)
    descr = fields.Char(string="rukovoditel_project description", translate=True)
    user_id = fields.Many2one('res.users', string='user id', required=True,)
    avatar_128 = fields.Image(related='user_id.avatar_128', readonly=True)
    rukovoditel_project_access_ids = fields.One2many(
        comodel_name='project_budget.rukovoditel_project_access',
        inverse_name='rukovoditel_project_id',
        string="rukovoditel_project_access",
        copy=True, auto_join=True)

class rukovoditel_project_access(models.Model):
    _name = 'project_budget.rukovoditel_project_access'
    _description = "rukovoditel_project access"
    rukovoditel_project_id = fields.Many2one('project_budget.rukovoditel_project', string='rukovoditel_project id', required=True,)
    user_id = fields.Many2one('res.users', string='user id', required=True,)
    descr = fields.Char(string="rukovoditel_project access description", translate=True)



class customer_organization(models.Model):
    _name = 'project_budget.customer_organization'
    _description = "project_customer organization"
    _rec_names_search = ['name', 'inn']
    # _rec_name = 'name_to_show'
    name = fields.Char(string="customer_organization name", required=True, translate=True)
    longname = fields.Char(string="customer_organization long name", translate=True)
    code = fields.Char(string="customer_organization code", )
    inn = fields.Char(related='partner_id.vat', readonly=True, store=True)
    avatar_128 = fields.Image(related='partner_id.avatar_128', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner', copy=True, domain="[('is_company','=',True)]")
    descr = fields.Char(string="customer_organization description", translate=True)
    # name_to_show = fields.Char(string='name_to_show', compute='_get_name_to_show')

    # @api.depends('name','inn')
    # def _get_name_to_show(self):
    #     for org in self:
    #         org.name_to_show = org.name
    #         if org.inn:
    #             org.name_to_show = org.name + '|'+ str(org.inn)

class customer_status(models.Model):
    _name = 'project_budget.customer_status'
    _description = "project_customer status"
    name = fields.Char(string="customer_status name", required=True, translate=True)
    code = fields.Char(string="customer_status code", required=True)
    descr = fields.Char(string="customer_status description", translate=True)

class industry(models.Model):
    _name = 'project_budget.industry'
    _description = "project_industry"
    name = fields.Char(string="industry name", required=True, translate=True)
    code = fields.Char(string="industry code", required=True)
    descr = fields.Char(string="industry description", translate=True)

class vat_attribute(models.Model):
    _name = 'project_budget.vat_attribute'
    _description = "project_vat attribute"
    name = fields.Char(string="vat_attribute name", required=True, translate=True)
    code = fields.Char(string="vat_attribute code", required=True)
    percent = fields.Float(string="vat_percent", required=True, default=0)
    descr = fields.Char(string="vat_attribute description", translate=True)
    is_prohibit_selection = fields.Boolean(string="is prohibit selection in projects", default=False)

class legal_entity_signing(models.Model):
    _name = 'project_budget.legal_entity_signing'
    _description = "project_legal entity signing"
    name = fields.Char(string="legal_entity_signing name", required=True, translate=True)
    code = fields.Char(string="legal_entity_signing code", required=True)
    percent_fot = fields.Float(string="fot_percent", required=True, default=0)
    is_percent_fot_manual = fields.Boolean(string="Manual fot_percent", default=0)
    descr = fields.Char(string="legal_entity_signing description", translate=True)
    different_project_offices_in_steps = fields.Boolean(string='different project offices in steps', default=False)

class technological_direction(models.Model):
    _name = 'project_budget.technological_direction'
    _description = "project_technologigal direction"
    name = fields.Char(string="technological_direction name", required=True, translate=True)
    code = fields.Char(string="technological_direction code", required=True)
    descr = fields.Char(string="technological_direction description", translate=True)
    recurring_payments = fields.Boolean(string="recurring_payments", default=False)

class tender_current_status(models.Model):
    _name = 'project_budget.tender_current_status'
    _description = "tender current status"
    name = fields.Char(string="current status name", required=True, translate=True)
    code = fields.Char(string="current status code", required=True)
    descr = fields.Char(string="current status description", translate=True)
    highlight = fields.Boolean(string="highlight", default=False)

class tender_comments_type(models.Model):
    _name = 'project_budget.tender_comments_type'
    _description = "tender comments type"
    name = fields.Char(string="comment type name", required=True, translate=True)
    code = fields.Char(string="comment type code", required=True)
    descr = fields.Char(string="comment type description", translate=True)
