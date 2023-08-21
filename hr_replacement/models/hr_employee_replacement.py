from odoo import api, models, fields


class HrEmployeeReplacement(models.Model):
    _name = 'hr.employee.replacement'
    _description = 'Replacement Employee'
    _order = 'date_start desc'

    replaceable_employee_id = fields.Many2one('hr.employee', string='Replaceable Employee', required=True,
                                              check_company=True)
    replacement_employee_id = fields.Many2one('hr.employee', string='Replacement Employee', required=True,
                                              check_company=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)

    date_start = fields.Date(string='Date Start', required=True)
    date_end = fields.Date(string='Date End')
    active = fields.Boolean(default=True, index=True)
    comment = fields.Html(string='Comment', copy=True)

    def write(self, vals):
        self.clear_caches()
        res = super(HrEmployeeReplacement, self).write(vals)
        return res
