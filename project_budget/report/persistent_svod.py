from odoo import _, models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import pytz
from datetime import timedelta

class persistent_svod(models.Model):
    _name = 'project_budget.persistent_svod'
    _description = "report persisnetn svod parameters"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    commercial_budget_id = fields.Many2one('project_budget.commercial_budget',  required = True, copy = True, tracking=True)
    year = fields.Integer(string="Budget year report", required=True, index=True)




