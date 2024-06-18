from odoo import fields, models


class Section(models.Model):
    _name = 'knowledge.section'
    _description = 'Knowledge Section'

    name = fields.Char(string='Name', copy=True, index=True, required=True)
    description = fields.Text(string='Description', copy=True)
    parent_id = fields.Many2one('knowledge.section', string='Parent Section', copy=True)
    child_ids = fields.One2many('knowledge.section', 'parent_id',  string='Child Sections', copy=False)
    article_ids = fields.One2many('knowledge.article', 'section_id', string='Articles', copy=False)
