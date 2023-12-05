from odoo import _, models, fields, api


class Section(models.Model):
    _name = 'knowledge_base.section'
    _description = "section of article"

    name = fields.Char(string="Section name", required=True, index=True, copy=True, group_operator='count')
    description = fields.Text(string='Section description')
    articles = fields.One2many(comodel_name='knowledge_base.article', inverse_name='section',
                               string="Articles of a section",
                               auto_join=True)
