from odoo import _, models, fields, api


class Tags(models.Model):
    _name = 'knowledge_base.tags'
    _description = "tags of article"

    name = fields.Char(string="Tag name", required=True, index=True, group_operator='count')
    description = fields.Text(string='Tag description')
