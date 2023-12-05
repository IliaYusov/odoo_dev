from odoo import _, models, fields, api


class Article(models.Model):
    _name = 'knowledge_base.article'
    _description = "article of knowledge base"

    name = fields.Char(string="Article name", required=True, index=True, copy=True, group_operator='count')
    text = fields.Html(string='Article text')
    parent_article = fields.Many2one('knowledge_base.article', string="Parent article")
    child_articles = fields.One2many(comodel_name='knowledge_base.article', inverse_name='parent_article', string='Child articles')
    section = fields.Many2one('knowledge_base.section', string='Section')
    tags = fields.Many2many('knowledge_base.tags', string='Tags')
    article_has_childs = fields.Boolean(compute="_article_has_childs")

    def _article_has_childs(self):
        for article in self:
            if self.env['knowledge_base.article'].search([('parent_article', '=', article.id)],limit=1):
                article.article_has_childs = True
            else:
                article.article_has_childs = False
