from odoo import fields, models


class Workflow(models.Model):
    _inherit = 'workflow.workflow'

    document_kind_id = fields.Many2one('document_flow.document.kind', string='Document Kind')
