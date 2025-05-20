import logging

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from werkzeug.urls import url_join

LICENSE_STATE = [
    ('new', 'New'),
    ('active', 'Active'),
    ('expired', 'Expired')
]

_logger = logging.getLogger(__name__)


class License(models.Model):
    _name = 'license.license'
    _description = 'License'
    _inherit = ['mail.thread']

    code = fields.Char(string='Code', copy=False, default=lambda self: _('New'), required=True, readonly=True)
    state = fields.Selection(LICENSE_STATE, string='State', copy=False, default='new', required=True, tracking=True)
    active = fields.Boolean('Active', default=True, tracking=True)
    url = fields.Char(string='URL', compute='_compute_url')
    customer_id = fields.Many2one('res.partner', string='Customer', copy=True, ondelete='restrict', required=True,
                                  tracking=True)
    product_id = fields.Many2one('product.product', string='Product', copy=True, domain="[('sale_ok', '=', True)]",
                                 ondelete='restrict', required=True, tracking=True)
    version = fields.Char(string='Version', copy=True, required=True, tracking=True)
    number_users = fields.Integer(string='Number Users', copy=False, default=1, required=True)
    number_users_is_unlimited = fields.Boolean(string='Unlimited', copy=True, default=False, tracking=True)
    type_id = fields.Many2one('license.type', string='Type', copy=True)
    date_start = fields.Date(string='Date Start', copy=False, default=fields.Date.context_today, required=True,
                             tracking=True)
    date_end = fields.Date(string='Date End', copy=False, default=fields.Date.context_today, tracking=True)
    is_unlimited = fields.Boolean(string='Unlimited', copy=True, default=False, tracking=True)
    os_id = fields.Many2one('license.os', string='Operating System', copy=True, ondelete='restrict', tracking=True)
    comment = fields.Text(string='Comment', copy=False, tracking=True)

    attachment_ids = fields.One2many('ir.attachment', 'res_id', string='Attachments', copy=False,
                                     domain="[('res_model', '=', 'license.license')]")
    company_id = fields.Many2one('res.company', string='Company', copy=False, default=lambda self: self.env.company,
                                 required=True)
    can_edit = fields.Boolean(compute='_compute_can_edit', default=True)

    license_key = fields.Char(string='Key', copy=False, readonly=True)

    def name_get(self):
        res = []
        for record in self:
            name = '%s [%s]' % (record.code, record.customer_id.name)
            res += [(record.id, name)]
        return res

    # ------------------------------------------------------
    # CONSTRAINS
    # ------------------------------------------------------

    @api.constrains('is_unlimited', 'date_end')
    def _check_date_end(self):
        for rec in self:
            if not rec.is_unlimited:
                if not rec.date_end:
                    raise ValidationError(_("Field 'Date End' is required for not unlimited license."))

    # ------------------------------------------------------
    # COMPUTE METHODS
    # ------------------------------------------------------

    def _compute_url(self):
        for rec in self:
            if not rec.ids:
                rec.url = False
            else:
                rec.url = url_join(rec.get_base_url(), '/web#id=%d&view_type=form&model=%s' % (self.id, self._name))

    def _compute_can_edit(self):
        for rec in self:
            rec.can_edit = rec.active and rec.state == 'new'

    # ------------------------------------------------------
    # CRUD
    # ------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('license.license') or _('New')
        return super(License, self).create(vals_list)

    # ------------------------------------------------------
    # ONCHANGE METHODS
    # ------------------------------------------------------

    @api.onchange('is_unlimited')
    def _onchange_is_unlimited(self):
        self.date_end = False if self.is_unlimited else self.date_end

    @api.onchange('number_users_is_unlimited')
    def _onchange_number_users_is_unlimited(self):
        self.number_users = False if self.number_users_is_unlimited else self.number_users_is_unlimited

    # ------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------

    def activate_license(self):
        self.write({'state': 'active'})

    def deactivate_license(self):
        self.write({'state': 'new'})

    @api.model
    def retrieve_dashboard(self):
        self.check_access_rights('read')

        today = fields.Date.today()

        result = {
            'expired_in_30_days': self.env['license.license'].search_count([
                ('state', '=', 'active'),
                ('date_end', '>', today + relativedelta(days=15)),
                ('date_end', '<=', today + relativedelta(days=30))
            ]),
            'expired_in_15_days': self.env['license.license'].search_count([
                ('state', '=', 'active'),
                ('date_end', '>=', today),
                ('date_end', '<=', today + relativedelta(days=15))
            ]),
            'expired': self.env['license.license'].search_count([
                ('state', '=', 'expired')
            ])
        }

        return result

    @api.model
    def _cron_license_expiry(self):
        licenses = self.env['license.license'].search([
            ('state', '=', 'active'),
            ('date_end', '<', fields.Date.today())
        ])
        licenses.write({'state': 'expired'})

        return True
