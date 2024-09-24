import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class DmsDirectory(models.Model):
    _name = 'dms.directory'
    _description = 'DMS Directory'

    def _get_default_parent_id(self):
        context = self.env.context
        if context.get("active_model") == self._name and context.get("active_id"):
            return context["active_id"]
        else:
            return False

    name = fields.Char(index='btree', required=True, translate=True)
    storage_id = fields.Many2one('dms.storage', compute='_compute_storage_id', string='Storage', compute_sudo=True,
                                 ondelete='restrict', readonly=True, store=True)
    storage_id_save_type = fields.Selection(related='storage_id.save_type', store=False)
    is_hidden = fields.Boolean(related='storage_id.is_hidden', string='Storage is Hidden', readonly=True, store=True)
    company_id = fields.Many2one(related='storage_id.company_id', string='Company', index='btree', readonly=True,
                                 store=True)
    parent_id = fields.Many2one('dms.directory', string='Parent Directory', copy=True,
                                default=lambda self: self._get_default_parent_id(), index='btree', ondelete='restrict')
    child_ids = fields.One2many('dms.directory', 'parent_id', string='Subdirectories', copy=False)
    directory_count = fields.Integer(compute='_compute_directory_count', string='Subdirectories Count')
    file_ids = fields.One2many('dms.document', 'directory_id', string='Files', copy=False)
    file_count = fields.Integer(compute='_compute_file_count', string='Files Count')
    file_total_count = fields.Integer(compute='_compute_file_total_count', string='Total Files')
    size = fields.Float(compute='_compute_size')

    group_ids = fields.Many2many('res.groups', string='Write Groups',
                                 help='Groups able to see the directory and read/create/edit its documents.')
    read_group_ids = fields.Many2many('res.groups', 'dms_directory_document_read_groups', column1='directory_id',
                                      column2='group_id', string='Read Groups',
                                      help='Groups able to see the directory and only read its documents.')

    @api.constrains('parent_id')
    def _check_directory_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('Error! You cannot create a recursive hierarchy of directories.'))
        return True

    def name_get(self):
        name_array = []
        hierarchical_naming = self.env.context.get('hierarchical_naming', True)
        for record in self:
            if hierarchical_naming and record.parent_id:
                name_array.append(tuple([record.id, "%s / %s" % (record.parent_id.name, record.name)]))
            else:
                name_array.append(tuple([record.id, record.name]))
        return name_array

    @api.depends('parent_id')
    def _compute_storage_id(self):
        for directory in self:
            if directory.parent_id:
                directory.storage_id = directory.parent_id.storage_id
            else:
                directory.storage_id = directory.storage_id

    @api.depends('child_ids')
    def _compute_directory_count(self):
        for directory in self:
            directory.directory_count = len(directory.child_ids)

    @api.depends('file_ids')
    def _compute_file_count(self):
        for directory in self:
            directory.file_count = len(directory.file_ids)

    def _compute_file_total_count(self):
        for directory in self:
            directory.file_total_count = self.env['dms.document'].search_count(
                [('directory_id', 'child_of', directory.id)]) if directory.id else 0

    def _compute_size(self):
        for directory in self:
            if not directory.id:
                directory.size = 0
                continue
            documents = self.env['dms.document'].sudo().search_read(
                domain=[('directory_id', 'child_of', directory.id)],
                fields=['size'],
            )
            directory.size = sum(document.get('size', 0) for document in documents)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('parent_id', False):
                parent = self.browse([vals['parent_id']])
                data = next(iter(parent.sudo().read(['storage_id'])), {})
                vals['storage_id'] = self._convert_to_write(data).get('storage_id')
        res = super(DmsDirectory, self).create(vals_list)
        return res

    def write(self, vals):
        if vals.get('storage_id'):
            for directory in self:
                if directory.storage_id.id != vals['storage_id']:
                    raise UserError(_('It is not possible to change the storage.'))
        if vals.get('parent_id'):
            parent = self.browse([vals['parent_id']])
            for directory in self:
                if directory.parent_id.storage_id != parent.storage_id:
                    raise UserError(_('It is not possible to change parent to other storage.'))
        res = super().write(vals)
        return res

    def unlink(self):
        self.document_ids.unlink()
        if self.child_ids:
            self.child_ids.unlink()
        return super().unlink()

    # ------------------------------------------------------
    # SEARCH PANEL
    # ------------------------------------------------------

    @api.model
    def _search_panel_domain_image(self, field_name, domain, set_count=False, limit=False):
        if field_name == 'parent_id':
            res = dict()
            for item in self.search_read(domain=domain, fields=['id', 'name', 'directory_count']):
                res[item['id']] = dict(
                    id=item['id'],
                    display_name=item['name'],
                    __count=item['directory_count']
                )
            return res
        return super()._search_panel_domain_image(field_name=field_name, domain=domain, set_count=set_count,
                                                  limit=limit)

    # ------------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------------

    def _get_root_directories(self):
        res = self.env['dms.directory'].search_read([
            ('is_hidden', '=', False),
            ('parent_id', '=', False)
        ])
        return [value['id'] for value in res]
