from odoo import api, fields, models, _

LICENSE_STATE = [
    ('new', 'New'),
    ('to_be_agreed', 'To Be Agreed'),
    ('active', 'Active'),
    ('expired', 'Expired')
]


class License(models.Model):
    _inherit = 'license.license'

    state = fields.Selection(LICENSE_STATE, compute='_compute_state', ondelete={'to_be_agreed': 'set default'},
                             readonly=False, store=True)
    workflow_id = fields.Many2one(related='company_id.license_workflow_id', readonly=True, required=False)
    workflow_process_id = fields.Many2one('workflow.process', string='Process', compute='_compute_workflow_process_id')
    workflow_process_state = fields.Selection(related='workflow_process_id.state', string='Workflow State',
                                              readonly=True)
    activity_history_ids = fields.One2many('workflow.process.activity.history', 'res_id', string='History',
                                           domain="[('res_model', '=', 'license.license')]", readonly=True)

    # ------------------------------------------------------
    # COMPUTE METHODS
    # ------------------------------------------------------

    def _compute_can_edit(self):
        super(License, self)._compute_can_edit()
        for rec in self:
            rec.can_edit = rec.can_edit and (
                not rec.workflow_process_state or rec.workflow_process_state in ('break', 'canceled'))

    def _compute_workflow_process_id(self):
        for rec in self:
            rec.workflow_process_id = self.env['workflow.process'].search([
                ('res_model', '=', self._name),
                ('res_id', '=', rec.id)
            ])[-1:]

    @api.depends('workflow_process_state')
    def _compute_state(self):
        for rec in self:
            rec.state = 'new' if rec.workflow_process_state == 'break' else rec.state

    # ------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------

    def activate_license(self):
        for rec in self:
            if rec.workflow_id:
                self.workflow_id.run(self._name, rec.id)
            else:
                super(License, rec).activate_license()

    def send_generated_license(self):
        template = self.env.ref('license_mngmnt_workflow.license_license_mail_template_license_generated',
                                raise_if_not_found=False)
        if not template:
            return False

        template.send_mail(self.id, email_layout_xmlid='mail.mail_notification_layout',
                           email_values=dict(attachment_ids=self.attachment_ids))

        return True
