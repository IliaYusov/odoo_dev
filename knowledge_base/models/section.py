from odoo import _, models, fields, api


class Section(models.Model):
    _name = 'knowledge_base.section'
    _description = "section of article"

    name = fields.Char(string="Section name", required=True, index=True, copy=True, group_operator='count')
    description = fields.Text(string='Section description')
    articles = fields.One2many(comodel_name='knowledge_base.article', inverse_name='section',
                               string="Articles of a section",
                               auto_join=True)
    parent_id = fields.Many2one('knowledge_base.section', string="Parent section")
    child_ids = fields.One2many('knowledge_base.section', 'parent_id',  string="Child sections")
