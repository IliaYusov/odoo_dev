from odoo import models, fields, _
from odoo.exceptions import UserError
from io import BytesIO
from datetime import date


class report_tender_wizard(models.TransientModel):
    _name = 'project_budget.tender.report.wizard'
    _description = 'Tender report Wizard'
    date_from = fields.Date(string='event date from', required=True, default=date(date.today().year, 1, 1))
    date_to = fields.Date(string='event  date to', required=True, default=fields.Date.context_today)
    is_report_for_management = fields.Boolean(string="is_report_for_management", default=False)
    include_old_open_tenders = fields.Boolean(string="include_old_open_tenders", default=False)
    FileName = fields.Char('File name', compute='_getFileName')
    type_report = fields.Selection([
        ('tender', 'Tender report'),
        ('new_tender', 'New tender report'),
    ],
        required=True, default='tender')

    def _getFileName(self):
        self.FileName = 'Tender_list_' + self.date_from.strftime("%d-%m-%Y") + '_' + self.date_to.strftime("%d-%m-%Y") + '.xlsx'

    def action_print_report(self):
        self.ensure_one()
        tenders_list = self.env['project_budget.tenders'].search([
            ('date_of_filling_in', '>=', self.date_from),
            ('date_of_filling_in', '<=', self.date_to)
        ],
            order='date_of_filling_in desc', limit=1)
        if not tenders_list:
            raise UserError(_("Tenders with that term not found!"))
        datas ={}
        # datas['report_type'] = 'xlsx'
        # datas['report_name'] = 'project_budget.report_tender_excel'
        # datas['report_file'] = 'project_budget.report_tender_excel'
        datas['date_from'] = str(self.date_from.strftime("%d-%m-%Y"),)
        datas['date_to'] = str(self.date_to.strftime("%d-%m-%Y"),)
        datas['is_report_for_management'] = self.is_report_for_management
        datas['include_old_open_tenders'] = self.include_old_open_tenders
        print('data=', datas)
        print('FileName = ', self.FileName)
        report_name = 'Tender_list_'+self.date_from.strftime("%d-%m-%Y")+'_'+self.date_to.strftime("%d-%m-%Y")+'.xlsx'
        self.env.ref('project_budget.action_tender_list_report_xlsx').sudo().name = report_name
        # return self.env.ref('project_budget.action_tender_list_report_xlsx').report_action(self, data=datas)
        if self.type_report == 'tender':
            return self.env.ref('project_budget.action_tender_list_report_xlsx').report_action(self, data=datas)

        if self.type_report == 'new_tender':
            return self.env.ref('project_budget.action_new_tender_list_report_xlsx').report_action(self, data=datas)

        # return self.env['ir.actions.report']._render('project_budget.action_tender_list_report_xlsx', res_ids=[], data=datas)