from odoo import models, fields, _
from odoo.exceptions import UserError
from io import BytesIO
from datetime import date

class report_tender_wizard(models.TransientModel):
    _name = 'project_budget.tender.report.wizard'
    _description = 'Tender report Wizard'
    date_from = fields.Date(string='event date from', required=True,default=date(date.today().year, 1, 1))
    date_to   = fields.Date(string='event  date to', required=True,default=fields.datetime.now())
    is_report_for_management = fields.Boolean(string="is_report_for_management", default = False)

    def action_print_report(self):
        self.ensure_one()
        tenders_list = self.env['project_budget.tenders'].search([('date_of_filling_in', '>=', self.date_from),('date_of_filling_in', '<=', self.date_to)], order='date_of_filling_in desc', limit=1)
        if not tenders_list:
            raise UserError(_("Tenders with thet term not found!"))
        datas ={}
        # datas['report_type'] = 'xlsx'
        # datas['report_name'] = 'project_budget.report_tender_excel'
        # datas['report_file'] = 'project_budget.report_tender_excel'
        datas['date_from']= str(self.date_from.strftime("%d-%m-%Y"),)
        datas['date_to']= str(self.date_to.strftime("%d-%m-%Y"),)
        datas['is_report_for_management'] = self.is_report_for_management
        print('data=',datas)
        report_name = 'Tender_list_'+self.date_from.strftime("%d-%m-%Y")+'_'+self.date_to.strftime("%d-%m-%Y")+'.xlsx'
        # self.env.ref('project_budget.action_tender_list_report_xlsx').report_file = report_name
        return self.env.ref('project_budget.action_tender_list_report_xlsx').report_action(self, data=datas)
