from odoo import api, fields, models
from io import BytesIO

import base64
import qrcode


class Article(models.Model):
    _name = 'knowledge.article'
    _description = 'Knowledge Article'
    _inherit = 'mail.thread'

    @api.model
    def action_get(self):
        return self.env['ir.actions.act_window']._for_xml_id('knowledge_base.action_view_all_articles')

    name = fields.Char(string='Name', copy=True, group_operator='count', index=True, required=True)
    body = fields.Html(string='Body')
    parent_id = fields.Many2one('knowledge.article', string='Parent Article', copy=True, ondelete='cascade')
    child_ids = fields.One2many('knowledge.article', 'parent_id', string='Child Articles', copy=False)
    section_id = fields.Many2one('knowledge.section', string='Section')
    tag_ids = fields.Many2many('knowledge.tags', string='Tags')

    group_ids = fields.Many2many('res.groups', string='Groups who can view the article')
    base64_qr = fields.Text(compute='_generate_qr', store=True)
    base_url = fields.Text(compute='_generate_qr', store=True)

    # TODO: необходимо расширить функциональность html_field, пока так
    attachment_ids = fields.Many2many('ir.attachment', 'knowledge_article_attachment_rel',
                                      column1='article_id', column2='attachment_id', string='Attachments',
                                      help='You may attach files to article')

    def _generate_qr(self):
        for article in self:
            qr_code = qrcode.QRCode(version=4, box_size=4, border=1)
            base_url = article.env['ir.config_parameter'].get_param('web.base.url')
            if 'localhost' not in base_url:
                if 'http://' in base_url:
                    base_url = base_url.replace('http://', 'https://')
            base_url = base_url + '/web#id=' + str(article.id) + '&model=knowledge.article&view_type=form&cids='
            qr_code.add_data(base_url)
            article.base_url = base_url
            qr_code.make(fit=True)
            qr_img = qr_code.make_image()
            im = qr_img._img.convert("RGB")
            buffered = BytesIO()
            im.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode('ascii')
            article.base64_qr = img_str
