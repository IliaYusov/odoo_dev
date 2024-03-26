from odoo import http, _
from odoo.http import request

import base64
import json
import logging

_logger = logging.getLogger(__name__)


class DmsController(http.Controller):

    @http.route('/dms/upload_attachment', type='http', methods=['POST'], auth='user')
    def upload_document(self, ufile, directory_id=False, document_id=False, partner_id=False, res_model=False,
                        res_id=False):
        files = request.httprequest.files.getlist('ufile')
        result = {
            'success': _('All files uploaded')
        }
        if document_id:
            document = request.env['dms.document'].browse(int(document_id))
            ufile = files[0]
            try:
                data = base64.encodebytes(ufile.read())
                mimetype = ufile.content_type
                document.write({
                    'name': ufile.filename,
                    'datas': data,
                    'mimetype': mimetype,
                })
            except Exception as e:
                _logger.exception('Fail to upload document %s' % ufile.filename)
                result = {
                    'error': str(e)
                }
        else:
            vals_list = []
            for ufile in files:
                try:
                    mimetype = ufile.content_type
                    datas = base64.encodebytes(ufile.read())
                    vals = {
                        'name': ufile.filename,
                        'mimetype': mimetype,
                        'datas': datas
                    }
                    if partner_id:
                        vals['partner_id'] = int(partner_id)
                    if directory_id:
                        vals['directory_id'] = int(directory_id)
                    if res_id and res_model:
                        vals['res_id'] = res_id
                        vals['res_model'] = res_model
                    vals_list.append(vals)
                except Exception as e:
                    _logger.exception('Fail to upload document %s' % ufile.filename)
                    result = {
                        'error': str(e)
                    }
            documents = request.env['dms.document'].create(vals_list)
            result['ids'] = documents.ids
        return json.dumps(result)

    @http.route([
        '/dms/image/<int:res_id>',
        '/dms/image/<int:res_id>/<int:width>x<int:height>',
    ], type='http', auth='user')
    def content_image(self, res_id=None, field='datas', width=0, height=0, crop=False, **kwargs):
        record = request.env['dms.document'].browse(int(res_id))
        if not record or not record.exists():
            raise request.not_found()

        return request.env['ir.binary']._get_image_stream_from(record, field, width=int(width), height=int(height),
                                                               crop=crop).get_response()
