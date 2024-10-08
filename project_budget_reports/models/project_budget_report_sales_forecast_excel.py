from odoo import models, api
import xlsxwriter
import base64
from io import BytesIO


class ProjectBudgetReportSalesForecastExcel(models.AbstractModel):
    _name = 'project.budget.report.sales.forecast.excel'
    _description = 'Project Budget Sales Forecast Report Excel'

    indicators = ['contraction', 'cash_flow', 'gross_revenue', 'margin']

    @api.model
    def generate_xlsx_report(self, data, options):

        rounding = options['rounding_unit_names'][options['rounding_unit']]

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet_i = workbook.add_worksheet('indicators')
        worksheet_c = workbook.add_worksheet('companies')

        column = 0
        row = 0
        for indicator in self.indicators:
            row = 0
            worksheet_i.merge_range(row, column, row, column + 1, indicator + ', ' + rounding)
            row += 1
            for k, v in data[indicator].items():
                res = v
                if k in ('plan', 'fact', 'forecast'):
                    res = v['rounded_value']
                worksheet_i.write_string(row, column, str(k))
                worksheet_i.write_number(row, column + 1, float(res))
                row += 1
            column += 3
        row += 1

        row = 0
        column = 1
        for indicator in self.indicators:
            worksheet_c.merge_range(row, column, row, column + 2, indicator + ', ' + rounding)
            for col in ('plan', 'fact', 'to_plan'):
                worksheet_c.write_string(row + 1, column, col)
                column += 1
            column += 1
        row += 2

        for company_data in data['companies']:
            column = 0
            worksheet_c.write(row, column, str(company_data['name']))
            for indicator in self.indicators:
                if company_data[indicator]:
                    if company_data[indicator].get('plan'):
                        worksheet_c.write_number(row, column + 1, float(company_data[indicator]['plan']['rounded_value']))
                    else:
                        worksheet_c.write_number(row, column + 1, 0)

                    if company_data[indicator].get('fact'):
                        worksheet_c.write_number(row, column + 2, float(company_data[indicator]['fact']['rounded_value']))
                    else:
                        worksheet_c.write_number(row, column + 2, 0)

                    if company_data[indicator].get('to_plan'):
                        worksheet_c.write_number(row, column + 3, float(company_data[indicator]['to_plan']))
                    else:
                        worksheet_c.write_number(row, column + 3, 0)
                else:
                    worksheet_c.write_number(row, column + 1, 0)
                    worksheet_c.write_number(row, column + 2, 0)
                    worksheet_c.write_number(row, column + 3, 0)
                column += 4
            row += 1
            for office_data in company_data['offices']:
                column = 0
                worksheet_c.write(row, column, str(office_data['name']))
                for indicator in self.indicators:
                    if office_data[indicator]:
                        if office_data[indicator].get('plan'):
                            worksheet_c.write_number(row, column + 1,
                                                     float(office_data[indicator]['plan']['rounded_value']))
                        else:
                            worksheet_c.write_number(row, column + 1, 0)

                        if office_data[indicator].get('fact'):
                            worksheet_c.write_number(row, column + 2,
                                                     float(office_data[indicator]['fact']['rounded_value']))
                        else:
                            worksheet_c.write_number(row, column + 2, 0)

                        if office_data[indicator].get('to_plan'):
                            worksheet_c.write_number(row, column + 3, float(office_data[indicator]['to_plan']))
                        else:
                            worksheet_c.write_number(row, column + 3, 0)
                    else:
                        worksheet_c.write_number(row, column + 1, 0)
                        worksheet_c.write_number(row, column + 2, 0)
                        worksheet_c.write_number(row, column + 3, 0)
                    column += 4
                row += 1
        workbook.close()

        result = base64.b64encode(output.getvalue())
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create(
            {'name': "forecast", 'datas': result})
        download_url = '/web/content/' + str(attachment_id.id) + '?download=true'

        return {
            "type": "ir.actions.act_url",
            "url": str(base_url) + str(download_url),
            "target": "new",
        }
