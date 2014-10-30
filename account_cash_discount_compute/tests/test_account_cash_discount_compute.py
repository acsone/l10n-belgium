# -*- coding: utf-8 -*-
#
##############################################################################
#
#    Authors: Adrien Peiffer
#    Copyright (c) 2014 Acsone SA/NV (http://www.acsone.eu)
#    All Rights Reserved
#
#    WARNING: This program as such is intended to be used by professional
#    programmers who take the whole responsibility of assessing all potential
#    consequences resulting from its eventual inadequacies and bugs.
#    End users who are looking for a ready-to-use solution with commercial
#    guarantees and support are strongly advised to contact a Free Software
#    Service Company.
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

import openerp.tests.common as common
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import logging
_logger = logging.getLogger(__name__)


DB = common.DB
ADMIN_USER_ID = common.ADMIN_USER_ID


def create_simple_invoice(self, date, tax_id):
    journal_id = self.ref('account.sales_journal')
    partner_id = self.ref('base.res_partner_2')
    product_id = self.ref('product.product_product_4')
    return self.env['account.invoice']\
        .create({'partner_id': partner_id,
                 'account_id':
                 self.ref('account.a_recv'),
                 'journal_id':
                 journal_id,
                 'discount_due_date': date,
                 'discount_percent': 10.0,
                 'date_invoice': date,
                 'invoice_line': [(0, 0, {'name': 'test',
                                          'account_id':
                                          self.ref('account.a_sale'),
                                          'price_unit': 2000.00,
                                          'quantity': 1,
                                          'product_id': product_id,
                                          'invoice_line_tax_id': [(4, tax_id)],
                                          }
                                   )
                                  ],
                 })


def create_belgium_tax_code(self, code):
    return self.env['account.tax.code'].create({'name': 'Belgium Tax Code',
                                                'code': code
                                                })


def create_tax(self, name, type_tax_use, compute_type, amount, base_code_id,
               tax_code_id):
    return self.env['account.tax'].create({'name': name,
                                           'type_tax_use': type_tax_use,
                                           'type': compute_type,
                                           'amount': amount,
                                           'base_code_id': base_code_id,
                                           'tax_code_id': tax_code_id,
                                           })


class TestAccountCashDiscountCompute(common.TransactionCase):

    def setUp(self):
        super(TestAccountCashDiscountCompute, self).setUp()
        self.context = self.registry("res.users").context_get(self.cr,
                                                              self.uid)

    def test_invoice_tax_discount(self):
        tax_code = create_belgium_tax_code(self, '48')
        tax = create_tax(self, 'Tax Test 21%', 'sale', 'percent', '0.21',
                         tax_code.id, tax_code.id)
        today = datetime.now()
        date = today.strftime(DEFAULT_SERVER_DATE_FORMAT)
        invoice = create_simple_invoice(self, date, tax.id)
        invoice.button_reset_taxes()
        tax_line = invoice.tax_line
        self.assertEqual(len(tax_line), 1, "Number of tax line isn't correct")
        self.assertAlmostEqual(tax_line.base_amount, 1800, 2,
                               "Tax Base Amoount isn't correct")
