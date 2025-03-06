from odoo import api, fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    def _get_category_manager_ids_domain(self):
        return "[('groups_id', 'in', %s)]" % self.env.ref('sale_mngmnt_crm_nkk.sale_group_category_manager').id

    root_category_id = fields.Many2one('product.category', string='Root Category', compute='_compute_root_category_id',
                                       store=True)

    head_id = fields.Many2one('res.users', string='The Head', copy=False)
    manager_ids = fields.Many2many('res.users', 'product_category_user_rel', 'category_id', 'user_id',
                                   string='Managers', domain=_get_category_manager_ids_domain)

    # ------------------------------------------------------
    # COMPUTE METHODS
    # ------------------------------------------------------

    @api.depends('parent_id', 'parent_id.parent_path')
    def _compute_root_category_id(self):
        for rec in self:
            rec.root_category_id = int(
                rec.parent_id.parent_path[:-1].split('/')[0]) if rec.parent_id.parent_path else False

    # ------------------------------------------------------
    # CRUD
    # ------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        results = super().create(vals_list)
        for vals in vals_list:
            if 'head_id' in vals:
                self.env['res.users'].clear_caches()
                break
        return results

    def write(self, vals):
        result = super(ProductCategory, self).write(vals)
        if vals.get('head_id', False):
            self.env['res.users'].clear_caches()
        return result

    def unlink(self):
        result = super(ProductCategory, self).unlink()
        self.env['res.users'].clear_caches()
        return result
