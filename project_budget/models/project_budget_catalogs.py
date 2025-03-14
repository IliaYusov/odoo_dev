from ast import literal_eval
from odoo import models, fields, api
from odoo.tools.misc import get_lang


class project_supervisor(models.Model):  # TODO убрать после миграции на кураторов
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


class project_supervisor_access(models.Model):  # TODO убрать после миграции на кураторов
    _name = 'project_budget.project_supervisor_access'
    _description = "project_supervisor_access"
    project_supervisor_id = fields.Many2one('project_budget.project_supervisor', string='project supervisor id')
    user_id = fields.Many2one('res.users', string='user id',  required=True,)
    can_approve_project = fields.Boolean(string="Can approve project as supervisor", default = False)
    descr = fields.Char(string="project supervisor access description" , translate=True)


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


class legal_entity_signing(models.Model):  # TODO: удалить после миграции на signer_id
    _name = 'project_budget.legal_entity_signing'
    _description = "project_legal entity signing"
    name = fields.Char(string="legal_entity_signing name", required=True, translate=True)
    code = fields.Char(string="legal_entity_signing code", required=True)
    percent_fot = fields.Float(string="fot_percent", required=True, default=0)
    is_percent_fot_manual = fields.Boolean(string="Manual fot_percent", default=0)
    descr = fields.Char(string="legal_entity_signing description", translate=True)
    different_project_offices_in_steps = fields.Boolean(string='different project offices in steps', default=False)
    # Для миграции на res.partner
    partner_id = fields.Many2one('res.partner', string='Partner')


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
