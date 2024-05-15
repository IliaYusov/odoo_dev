from odoo import fields, models


class DocumentKind(models.Model):
    _inherit = 'document_flow.document.kind'

    workflow_id = fields.Many2one(related='template_id.workflow_id', readonly=True)
