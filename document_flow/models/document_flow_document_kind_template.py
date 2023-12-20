from odoo import api, Command, fields, models
from .document_flow_process import selection_executor_model


class DocumentKindType(models.Model):
    _name = "document_flow.document.kind.type"
    _description = "Document Kind Type"
    _order = 'sequence, id'

    template_id = fields.Many2one('document_flow.document.kind.template', index=True, ondelete='cascade', required=True)
    name = fields.Char('Type', required=True)
    sequence = fields.Integer('Sequence', help='Determine the display order', index=True)

    def _get_type_name(self):
        return '%s - %s' % (self.template_id.name, self.name)


class DocumentKindTemplate(models.Model):
    _name = 'document_flow.document.kind.template'
    _description = 'Document Kind Template'

    name = fields.Char(string='Name', required=True, copy=True)
    sequence_id = fields.Many2one('ir.sequence', string='Document Kind Sequence', copy=False, ondelete='restrict',
                                  domain=lambda self: [('code', '=', self._name)])
    keep_records_by_type = fields.Boolean(string='Keep Records By Type', default=False)
    type_ids = fields.One2many('document_flow.document.kind.type', 'template_id', string='Types')
    kind_ids = fields.One2many('document_flow.document.kind', 'template_id', string='Kinds')

    access_setting_ids = fields.One2many('document_flow.document.kind.accessibility.setting', 'template_id',
                                         string='Accessibility Settings')

    @api.model_create_multi
    def create(self, vals_list):
        records = super(DocumentKindTemplate, self).create(vals_list)
        records._create_kind_variant_ids()
        return records

    def write(self, vals):
        res = super(DocumentKindTemplate, self).write(vals)
        if 'type_ids' in vals:
            self._create_kind_variant_ids()
        return res

    def _create_kind_variant_ids(self):
        for tmp_id in self:
            existing_variants = [{
                'name': variant.name,
                'type_id': variant.type_id.id
            } for variant in tmp_id.kind_ids]
            if tmp_id.keep_records_by_type:
                all_combination = [{
                    'name': type_id._get_type_name(),
                    'type_id': type_id.id
                } for type_id in tmp_id.type_ids]
            else:
                all_combination = [{
                    'name': tmp_id.name
                }]
            variants_to_create = [variant for variant in all_combination if variant not in existing_variants]
            variants_to_unlink = [variant for variant in existing_variants if variant not in all_combination]
            if any(variants_to_unlink):
                for variant in variants_to_unlink:
                    [k.unlink() for k in tmp_id.kind_ids.filtered(
                        lambda k: k.name == variant.get('name') and not k.type_id if not variant.get(
                            'type_id') else k.type_id == variant.get('type_id'))]

            if any(variants_to_create):
                for variant in variants_to_create:
                    variant['template_id'] = tmp_id.id
                self.env['document_flow.document.kind'].create(variants_to_create)


class DocumentKindAccessibilitySetting(models.Model):
    _name = 'document_flow.document.kind.accessibility.setting'
    _description = 'Document Kind Accessibility Setting'

    @api.model
    def _selection_executor_model(self):
        return selection_executor_model()

    template_id = fields.Many2one('document_flow.document.kind.template', string='Document Kind', copy=True,
                                  index=True, required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company', copy=False, default=lambda self: self.env.company,
                                 required=True)
    user_ref = fields.Reference(string='User', selection='_selection_executor_model', copy=False, required=True)
