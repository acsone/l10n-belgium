# -*- coding: utf-8 -*-
# Copyright 2016 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tests.common import TransactionCase
from openerp.exceptions import ValidationError


class TestL10nBeIso20022Pain(TransactionCase):

    def setUp(self):
        super(TestL10nBeIso20022Pain, self).setUp()

        # ENVIRONEMENTS
        self.account_invoice = self.env['account.invoice']
        self.account_model = self.env['account.account']
        self.account_invoice_line = self.env['account.invoice.line']
        self.account_payment_line = self.env['account.payment.line']
        self.account_payment_mode = self.env['account.payment.mode']
        self.account_journal = self.env['account.journal']
        self.account_account = self.env['account.account']

        # INSTANCES

        # Instance: Account
        self.invoice_account = self.account_model.search(
            [('user_type_id',
              '=',
              self.env.ref('account.data_account_type_receivable').id
              )], limit=1)
        # Instance: Invoice Line
        self.invoice_line = self.account_invoice_line.create(
            {'name': 'Test invoice line',
             'account_id': self.invoice_account.id,
             'quantity': 2.000,
             'price_unit': 2.99})

        # Instance: Account (sales)
        self.account_sales = self.account_account.create({
            'code': "X1020",
            'name': "Product Sales - (test)",
            'user_type_id': self.env.ref(
                'account.data_account_type_revenue').id
        })

        # Instance: Journal
        self.sales_journal = self.account_journal.create({
            'name': "Sales Journal - (test)",
            'code': "TSAJ",
            'type': "sale",
            'refund_sequence': True,
            'default_debit_account_id': self.account_sales.id,
            'default_credit_account_id': self.account_sales.id,
        })

        # Instance: Payment Mode
        self.payment_mode = self.account_payment_mode.create({
            'name': 'Test payment mode',
            'payment_method_id': self.env.ref(
                'account.account_payment_method_manual_out').id,
            'fixed_journal_id': self.sales_journal.id,
            'bank_account_link': 'fixed'})

        # Instance: Invoice
        self.invoice = self.account_invoice.create({
            'partner_id': self.env.ref('base.res_partner_2').id,
            'account_id': self.invoice_account.id,
            'type': 'in_invoice',
            'invoice_line_ids': [(6, 0, [self.invoice_line.id])],
            'reference_type': 'bba',
            'reference': '+++868/0542/73023+++',
            'state': 'open',
            'payment_mode_id': self.payment_mode.id})

    def test_create_account_payment_line(self):
        # Payment of invoice with BBA communication
        with self.cr.savepoint():
            self.invoice.action_move_create()
            self.invoice.create_account_payment_line()
            pl = self.account_payment_line.search([('move_line_id.invoice_id',
                                                    '=',
                                                    self.invoice.id)])
            self.assertEqual(pl[0].communication, '868054273023', "BBA check")

        # New payment line with invalid BBA communication
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.account_payment_line.create({
                'currency_id': self.env.ref('base.EUR').id,
                'partner_id': self.env.ref('base.res_partner_2').id,
                'communication_type': 'bba',
                'amount_currency': 123.321,
                'communication': '868054273024'})

        # New payment line with invalid BBA communication (too short)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.account_payment_line.create({
                'currency_id': self.env.ref('base.EUR').id,
                'partner_id': self.env.ref('base.res_partner_2').id,
                'communication_type': 'bba',
                'amount_currency': 123.321,
                'communication': '8680542730241'})

        # New payment line with invalid BBA communication (too long)
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.account_payment_line.create({
                'currency_id': self.env.ref('base.EUR').id,
                'partner_id': self.env.ref('base.res_partner_2').id,
                'communication_type': 'bba',
                'amount_currency': 123.321,
                'communication': '86805427302'})

        # New payment line with valid BBA communication
        with self.cr.savepoint():
            self.account_payment_line.create({
                'currency_id': self.env.ref('base.EUR').id,
                'partner_id': self.env.ref('base.res_partner_2').id,
                'communication_type': 'bba',
                'amount_currency': 123.321,
                'communication': '868054273023'})
