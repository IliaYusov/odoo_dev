import base64
import logging
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.addons.base.models.ir_mail_server import MailDeliveryException

_logger = logging.getLogger(__name__)


class ScheduledReport(models.Model):
    _name = 'project_budget.scheduled.report'
    _description = "Scheduled Report"
    _check_company_auto = True

    report_id = fields.Many2one('ir.actions.report', string='Report', copy=True, required=True)
    company_id = fields.Many2one('res.company', string='Company', copy=True, required=True)
    user_ids = fields.Many2many('res.users', relation='scheduled_report_user_rel', column1='scheduled_report_id',
                                column2='user_id', string='Recipients', check_company=True, copy=True,
                                context={'active_test': False})

    def _send_email(self, data):
        result, report_format = self.env['ir.actions.report'].with_context(
            allowed_company_ids=[self.company_id.id])._render(self.report_id.report_name, res_ids=[], data=data)

        report_name = self.with_context(
            lang=self.env.user.lang).report_id.print_report_name if self.report_id.print_report_name else self.with_context(
            lang=self.env.user.lang).report_id.name
        ext = '.' + report_format
        if not report_name.endswith(ext):
            report_name += ext

        data_record = base64.b64encode(result)
        ir_values = {
            'name': report_name,
            'type': 'binary',
            'datas': data_record,
            'store_fname': report_name,
            'mimetype': 'application/vnd.ms-excel',
            'res_model': 'project_budget.projects'
        }
        attachment = self.env['ir.attachment'].sudo().create(ir_values)

        vals = {
            'subject': _("%s for company '%s'", report_name, self.company_id.name),
            'body_html': _("Dear %s,<br/><br/>'%s' for company '%s' was generated.",
                           ', '.join(self.user_ids.mapped('name')), report_name, self.company_id.name),
            'email_to': ', '.join(self.user_ids.mapped('email')),
            'auto_delete': False,
            'reply_to': False,
            'attachment_ids': [(4, attachment.id)]
        }

        mail_id = self.env['mail.mail'].sudo().create(vals)
        mail_id.sudo().send()

    @api.model
    def _cron_send_reports_email(self):
        data = dict(
            year=fields.date.today().year,
            year_end=fields.date.today().year,
            date_start=fields.date.today(),
            date_end=fields.date.today() + timedelta(days=7),
            commercial_budget_id=self.env['project_budget.commercial_budget'].search([
                ('budget_state', '=', 'work')
            ], limit=1).id,
            koeff_reserve=1,
            koeff_potential=1,
            pds_accept='pds',
            report_with_projects=True,
        )
        schedule_reports = self.env['project_budget.scheduled.report'].search([])
        for sr in schedule_reports:
            try:
                sr._send_email(data)
            except MailDeliveryException as e:
                _logger.warning('MailDeliveryException while sending report %d. Report is now scheduled for next cron update.', sr.id)
