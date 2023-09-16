from odoo import _, models, fields, api


class Presale(models.Model):
    _name = 'project_budget.presale'
    _description = 'Presale'
    _check_company_auto = True

    _inherit = ['mail.thread', 'mail.activity.mixin']

    code = fields.Char(string='Code', copy=False, required=True, readonly=True, default=lambda self: _('New'))
    name = fields.Char(string='Name', required=True, copy=True, tracking=True)
    project_id = fields.Many2one('project_budget.projects', string='Project', copy=True, required=True, tracking=True)
    customer_id = fields.Many2one('res.partner', related='project_id.customer_organization_id.partner_id',
                                  string='Customer', copy=False, readonly=True, required=True)
    company_id = fields.Many2one('res.company', string='Company', copy=False, required=True,
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.ref('base.RUB').id)
    sum = fields.Monetary(string='Sum', copy=False, required=True, tracking=True)
    description = fields.Html(string='Description', copy=False)

    process_id = fields.Many2one('document_flow.process', string='Process', compute='_compute_process_id')
    process_state = fields.Selection(string='State', related='process_id.state', readonly=True)
    attachment_ids = fields.One2many('ir.attachment', string='Attachments', compute='_compute_attachment_ids')
    attachment_count = fields.Integer(compute='_compute_attachment_count', string='Attachment Count')

    def _compute_process_id(self):
        for presale in self:
            presale.process_id = self.env['document_flow.processing'].search([
                ('parent_ref', '=', '%s,%d' % (presale._name, presale.id))
            ]).process_id

    def _compute_attachment_count(self):
        for presale in self:
            presale.attachment_count = self.env['ir.attachment'].search_count([
                '|',
                '&', ('res_model', '=', self._name), ('res_id', 'in', [presale.id]),
                '&', ('res_model', '=', 'task.task'), ('res_id', 'in', presale.process_id.task_ids.ids)
            ])

    @api.model
    def create(self, vals_list):
        if vals_list.get('code', _('New')) == _('New'):
            vals_list['code'] = self.env['ir.sequence'].next_by_code('project_budget.presale') or _('New')

        res = super(Presale, self).create(vals_list)
        return res

    def action_open_attachments(self):
        self.ensure_one()
        return {
            'name': _('Attachments'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,tree,form',
            'domain': ['|',
                       '&', ('res_model', '=', self._name), ('res_id', 'in', [self.id]),
                       '&', ('res_model', '=', 'task.task'), ('res_id', 'in', self.process_id.task_ids.ids)
                       ]
        }

    def action_open_processing(self):
        self.ensure_one()
        processing = self.env['document_flow.processing'].search([
            ('parent_ref', '=', '%s,%d' % (self._name, self.id))
        ])
        return {
            'view_mode': 'form',
            'res_model': 'document_flow.processing',
            'type': 'ir.actions.act_window',
            'res_id': processing.id,
            'context': {
                'default_parent_ref': '%s,%d' % (self._name, self.id),
                'default_parent_ref_type': self._name,
                'default_parent_ref_id': self.id
            }
        }
