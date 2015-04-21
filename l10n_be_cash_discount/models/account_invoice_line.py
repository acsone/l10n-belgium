# -*- coding: utf-8 -*-
#
##############################################################################
#
#     Authors: Adrien Peiffer
#    Copyright (c) 2015 Acsone SA/NV (http://www.acsone.eu)
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

from openerp import models, api, fields
from openerp.addons.l10n_be_cash_discount.models.account_invoice_tax \
    import BelgiumBaseTaxCodes


class account_invoice_line(models.Model):
    _inherit = 'account.invoice.line'

    @api.model
    def _move_line_get_discount(self, invoice_id, aml):
        invoice = self.env['account.invoice'].browse(invoice_id)
        pct = invoice.discount_percent
        if not pct and invoice.discount_amount:
            pct = (1 - (invoice.discount_amount / invoice.amount_total)) * 100
        if pct:
            currency = invoice.currency_id\
                .with_context(date=invoice.date_invoice or
                              fields.Date.context_today(invoice))
            multiplier = 1-pct/100
            atc_obj = self.env['account.tax.code']
            belgium_btc = atc_obj.search([('code', 'in', BelgiumBaseTaxCodes)])
            for tax in aml:
                if tax['tax_code_id'] in belgium_btc.ids:
                    tax['tax_amount'] = \
                        currency.round(tax['tax_amount'] * multiplier)

    @api.model
    def move_line_get(self, invoice_id):
        aml = super(account_invoice_line, self).move_line_get(invoice_id)
        self._move_line_get_discount(invoice_id, aml)
        return aml
