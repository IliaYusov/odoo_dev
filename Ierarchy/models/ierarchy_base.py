import base64
from odoo import models, fields, api
from odoo.tools import ImageProcess


class ierarchy(models.Model):
    _name = 'ierarchy.base'
    _description = 'base class ierarchy'
    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
    description = fields.Char(string="description")
    #parent_id = fields.Many2one(string="Parent object", comodel_name="ierarchy.base",  select=True)
    #child_ids = fields.One2many(string="Children", comodel_name="ierarchy.base", inverse_name="parent_id", auto_join=True)