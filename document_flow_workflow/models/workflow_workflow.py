from odoo import fields, models


class Workflow(models.Model):
    _inherit = 'workflow.workflow'

    _sql_constraints = [
        ('document_kind_uniq',
         'UNIQUE (document_kind_id, company_id)',
         'Document kind must be uniq for workflow')
    ]

    document_kind_id = fields.Many2one('document_flow.document.kind', string='Document Kind')
