# -*- coding: utf-8 -*-
#
##############################################################################
#
#    Authors: Adrien Peiffer
#    Copyright (c) 2014 Acsone SA/NV (http://www.acsone.eu)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api, models, fields
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

BelgiumBaseTaxCodesIn = ['81', '82', '83', '84', '85', '86', '87', '88']
BelgiumBaseTaxCodesOut = ['00', '01', '02', '03', '44', '45', '46', '46L',
                          '46T', '47', '48', '48s44', '48s46L', '48s46T', '49']
BelgiumBaseTaxCodes = BelgiumBaseTaxCodesIn + BelgiumBaseTaxCodesOut


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    discount_percent = fields.Float(string='Discount Percent')
    discount_delay = fields.Integer(string='Discount Delay (days)')

    @api.one
    @api.onchange('discount_percent')
    def discount_percent_change(self):
        discount = self.amount_untaxed * (0.0 + self.discount_percent/100)
        self.discount_amount = discount
        return

    @api.one
    @api.onchange('discount_delay', 'date_invoice')
    def discount_delay_change(self):
        if self.date_invoice:
            date_invoice = self.date_invoice
            date_invoice = datetime.strptime(date_invoice,
                                             DEFAULT_SERVER_DATE_FORMAT)
        else:
            date_invoice = datetime.now()
        due_date = date_invoice + timedelta(days=self.discount_delay)
        self.discount_due_date = due_date.date()


class account_invoice_tax(models.Model):
    _inherit = 'account.invoice.tax'

    def compute(self, invoice):
        tax_grouped = super(account_invoice_tax, self).compute(invoice)
        currency = invoice.currency_id\
            .with_context(date=invoice.date_invoice or
                          fields.Date.context_today(invoice))
        pct = invoice.discount_percent
        if pct:
            multiplier = 1-pct/100
            atc_obj = self.env['account.tax.code']
            belgium_btc = atc_obj.search([('code', 'in',
                                          BelgiumBaseTaxCodes)])
            for t in tax_grouped.values():
                if t['base_code_id'] in belgium_btc.ids:
                    t['base'] = currency.round(t['base'] * multiplier)
                    t['amount'] = currency.round(t['amount'] * multiplier)
                    t['base_amount'] = currency.round(t['base_amount'] *
                                                      multiplier)
                    t['tax_amount'] = currency.round(t['tax_amount'] *
                                                     multiplier)
        return tax_grouped
