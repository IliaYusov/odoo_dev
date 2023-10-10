from odoo import _, models, fields, api
from zeep import Client
from datetime import date, timedelta, datetime
import pytz

class currency_rate_update(models.Model):
    _name = 'currency_rate_update.currency_rate_update'
    _description = "updater for currency rates"
    _check_company_auto = True

    def get_currency_rates(self, day):
        clt = Client("http://www.cbr.ru/DailyInfoWebServ/DailyInfo.asmx?WSDL").service.GetCursOnDate(day)
        rates = {}
        for cl in clt['_value_1']['_value_1']:
            rates[cl['ValuteCursOnDate']['VchCode']] = 1 / cl['ValuteCursOnDate']['VunitRate']
        return rates

    def auto_rate_update(self):
        currencies = self.env['res.currency'].search([('active', '=', True)])
        tomorrow = date.today() + timedelta(days=1)
        rates = self.env['currency_rate_update.currency_rate_update'].get_currency_rates(tomorrow)
        for currency in currencies:
            if currency.name in rates:
                for company in self.env['res.company'].search([('auto_currency_update', '=', True)]):
                    check_rate = self.env['res.currency.rate'].search([
                                                            ('company_id', '=', company.id),
                                                            ('name', '=', tomorrow),
                                                            ('currency_id', '=', currency.id),
                                                            ])
                    if check_rate:
                        check_rate.sudo().update({'rate': rates[currency.name]})
                    else:
                        self.env['res.currency.rate'].sudo().create(
                            {'rate': rates[currency.name], 'company_id': company.id, 'name': tomorrow,
                             'currency_id': currency.id})
