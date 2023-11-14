from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import test_python_expr


class AutoSubstitution(models.Model):
    _name = 'document_flow.auto_substitution'
    _description = 'Auto-substitution'

    name = fields.Char(string='Name', copy=True, required=True, translate=True)
    expression = fields.Text(string='Expression', required=True, copy=True)
    description = fields.Html(string='Description')
    active = fields.Boolean(default=True, index=True)

    @api.constrains('expression')
    def _verify_expression(self):
        for subs in self.filtered('expression'):
            msg = test_python_expr(expr=subs.expression.strip(), mode='exec')
            if msg:
                raise ValidationError(msg)
