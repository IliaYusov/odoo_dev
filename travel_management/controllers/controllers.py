import datetime
from odoo.http import Controller, request, route, content_disposition
from odoo import fields

class Travel(Controller):
    @route('/travel/documents', website=True, auth='public')
    def travel_documents(self,**kw):
        documents = request.env['travel.travel'].sudo().search([('doc_date', '<=', fields.Datetime.now()-datetime.timedelta(days=5))])
        return request.render("travel_management.template_test_page", {
            "documents":documents
        })