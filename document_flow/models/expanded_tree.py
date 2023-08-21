from odoo import _, models, fields, api


class ExpandedTree(models.Model):
    _name = 'document_flow.expanded_tree'
    _description = 'Expanded Tree'
    name = fields.Char(string='Name', required=True, copy=True)
    parent_id = fields.Many2one('document_flow.expanded_tree', string='Parent Process', ondelete='cascade')
    child_ids = fields.One2many('document_flow.expanded_tree', 'parent_id', string='Processes')

    tree_id = fields.Char(string='TreeId', compute='_compute_tree_id')
    expanded = fields.Boolean(string='Expanded', compute='', Default=False)
    branch_depth = fields.Integer(string='BranchDepth', compute='_compute_branch_depth')
