from odoo import api, fields, models


class DocumentKindTemplate(models.Model):
    _inherit = 'document_flow.document.kind.template'

    workflow_id = fields.Many2one('workflow.workflow', string='Workflow', company_dependent=True, copy=False)
    workflow_id_domain = fields.Binary(string='Workflow Domain', compute='_compute_workflow_id_domain')

    # ------------------------------------------------------
    # COMPUTE METHODS
    # ------------------------------------------------------

    @api.depends('company_id')
    def _compute_workflow_id_domain(self):
        for rec in self:
            rec.workflow_id_domain = [
                ('model_name', '=', 'document_flow.document'),
                '|',
                ('company_id', '=', False),
                ('company_id', '=', rec.company_id.id if rec.company_id else self.env.company.id)
            ]
