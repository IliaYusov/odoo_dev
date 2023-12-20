from odoo import _, models, fields, api
import base64
import qrcode
from io import BytesIO


class Article(models.Model):
    _name = 'knowledge_base.article'
    _description = "article of knowledge base"
    _inherit = 'mail.thread'

    name = fields.Char(string="Article name", required=True, index=True, copy=True, group_operator='count')
    text = fields.Html(string='Article text')
    parent_id = fields.Many2one('knowledge_base.article', string="Parent article")
    child_ids = fields.One2many(comodel_name='knowledge_base.article', inverse_name='parent_id', string='Child articles')
    section_id = fields.Many2one('knowledge_base.section', string='Section')
    tag_ids = fields.Many2many('knowledge_base.tags', string='Tags')
    article_has_childs = fields.Boolean(compute="_article_has_childs")
    group_ids = fields.Many2many('res.groups', string='Groups who can view the article')
    base64_qr = fields.Text(compute='_generate_qr', store=True)
    base_url = fields.Text(compute='_generate_qr', store=True)

    @api.depends('child_ids')
    def _article_has_childs(self):
        for article in self:
            if len(article.child_ids):
                article.article_has_childs = True
            else:
                article.article_has_childs = False

    def _generate_qr(self):
        for article in self:
            qr_code = qrcode.QRCode(version=4, box_size=4, border=1)
            base_url = article.env['ir.config_parameter'].get_param('web.base.url')
            if 'localhost' not in base_url:
                if 'http://' in base_url:
                    base_url = base_url.replace('http://', 'https://')
            base_url = base_url + '/web#id=' + str(article.id) + '&model=knowledge_base.article&view_type=form&cids='
            qr_code.add_data(base_url)
            article.base_url = base_url
            qr_code.make(fit=True)
            qr_img = qr_code.make_image()
            im = qr_img._img.convert("RGB")
            buffered = BytesIO()
            im.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode('ascii')
            article.base64_qr = img_str
