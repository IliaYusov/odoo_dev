from odoo import models, fields, _
from odoo.exceptions import ValidationError
from datetime import date, timedelta


class currency_rate_update_wizard(models.TransientModel):
    _name = 'currency_rate_update.currency_rate_update_wizard'
    _description = 'Currency rate updater wizard'
    date_start = fields.Date(string='update rates from', default=date.today(), required=True)
    date_end = fields.Date(string='update rates to', default=date.today(), required=True)

    def action_update_rates(self):
        self.ensure_one()

        currencies_not_in_cbr = []
        currencies = self.env['res.currency'].search([('id', 'in', self.env.context['active_ids'])])

        for currency in currencies:
            if not currency.active:
                raise ValidationError(f'Rates are NOT updated. Currency {currency.name} is not active')

        for day in (self.date_start + timedelta(days=x) for x in range((self.date_end - self.date_start).days + 1)):
            rates = self.env['currency_rate_update.currency_rate_update'].get_currency_rates(day)
            for currency in currencies:
                if currency.name in rates:
                    for company in self.env['res.company'].search([]):
                        if self.env['res.currency.rate'].search([
                                                                ('company_id', '=', company.id),
                                                                ('name', '=', day),
                                                                ('currency_id', '=', currency.id),
                                                                ]):
                            self.env['res.currency.rate'].search([
                                                                ('company_id', '=', company.id),
                                                                ('name', '=', day),
                                                                ('currency_id', '=', currency.id)]).sudo().update(
                                {'rate': rates[currency.name]})
                        else:
                            self.env['res.currency.rate'].sudo().create(
                                {'rate': rates[currency.name], 'company_id': company.id, 'name': day,
                                 'currency_id': currency.id})
                else:
                    currencies_not_in_cbr.append(currency.name)

        if currencies_not_in_cbr:
            raise ValidationError(f'{currencies_not_in_cbr} not in CBR rates')
