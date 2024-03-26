from odoo import _, http
from odoo.http import content_disposition, request
from odoo.osv.expression import OR
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.web.controllers.utils import ensure_db

import base64


class CustomerPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'dms_directory_count' in counters:
            ids = request.env['dms.directory']._get_root_directories()
            values['dms_directory_count'] = len(ids)
        return values

    @http.route(['/my/dms'], type='http', auth='user')
    def portal_my_dms(self, sortby=None, filterby=None, search=None, search_in="name", **kw):
        values = self._prepare_portal_layout_values()
        searchbar_sortings = {'name': {'label': _('Name'), 'order': 'name asc'}}
        # default sortby br
        if not sortby:
            sortby = 'name'
        sort_br = searchbar_sortings[sortby]['order']
        # search
        searchbar_inputs = {
            'name': {'input': 'name', 'label': _('Name')},
        }
        if not filterby:
            filterby = 'name'
        # domain
        domain = [
            (
                'id',
                'in',
                request.env['dms.directory']._get_root_directories(),
            )
        ]
        # search
        if search and search_in:
            search_domain = []
            if search_in == 'name':
                search_domain = OR([search_domain, [('name', 'ilike', search)]])
            domain += search_domain
        # content according to pager and archive selected
        items = request.env['dms.directory'].search(domain, order=sort_br)
        request.session['my_dms_directory_history'] = items.ids
        # values
        values.update(
            {
                'dms_directories': items,
                'page_name': 'dms_directory',
                'default_url': '/my/dms',
                'searchbar_sortings': searchbar_sortings,
                'searchbar_inputs': searchbar_inputs,
                'search_in': search_in,
                'sortby': sortby,
                'filterby': filterby,
            }
        )
        return request.render('dms.portal_my_dms', values)
