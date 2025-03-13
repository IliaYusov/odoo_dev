from odoo import models, fields


class ProjectType(models.Model):
    _name = 'project_budget.project_type'
    _description = "project_type"

    name = fields.Char(string="project_type name", required=True, translate=True)
    code = fields.Char(string="project_type code", required=True)
    descr = fields.Char(string="project_type description", translate=True)
