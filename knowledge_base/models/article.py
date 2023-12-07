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
    section = fields.Many2one('knowledge_base.section', string='Section')
    tags = fields.Many2many('knowledge_base.tags', string='Tags')
    article_has_childs = fields.Boolean(compute="_article_has_childs")
    base64_qr = fields.Text(compute='_generate_qr')
    base_url = fields.Text(compute='_generate_qr')

    def _article_has_childs(self):
        for article in self:
            if self.env['knowledge_base.article'].search([('parent_id', '=', article.id)], limit=1):
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
