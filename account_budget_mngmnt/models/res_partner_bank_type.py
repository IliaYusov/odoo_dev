from odoo import fields, models


class ResPartnerBankType(models.Model):
    _name = 'res.partner.bank.type'
    _description = 'Bank Account Type'
    _order = 'sequence, name, id'

    code = fields.Char(string='Code', required=True)
    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(default=1, required=True)

    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'Account type with the same code already exists.')
    ]

    def name_get(self):
        res = []
        for rec in self:
            name = '[%s] %s' % (rec.code, rec.name)
            res += [(rec.id, name)]
        return res
