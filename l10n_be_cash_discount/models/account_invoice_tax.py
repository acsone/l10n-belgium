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

BelgiumBaseTaxCodesIn = ['81', '82', '83', '84', '85', '86', '87', '88']
BelgiumBaseTaxCodesOut = ['00', '01', '02', '03', '44', '45', '46', '46L',
                          '46T', '47', '48', '48s44', '48s46L', '48s46T', '49']
BelgiumBaseTaxCodes = BelgiumBaseTaxCodesIn + BelgiumBaseTaxCodesOut


class account_invoice_tax(models.Model):
    _inherit = 'account.invoice.tax'

    def _compute_discount_tax_value(self, invoice, tax_grouped):
        """ This method compute taxes values consider discount percent.
        This method is designed to be inherited"""

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

    @api.v8
    def compute(self, invoice):
        tax_grouped = super(account_invoice_tax, self).compute(invoice)
        tax_grouped = self._compute_discount_tax_value(invoice, tax_grouped)
        return tax_grouped
