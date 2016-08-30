# -*- coding: utf-8 -*-
# Copyright 2016 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re
from openerp import api, fields, models, _
from openerp.exceptions import ValidationError


class AccountPaymentLine(models.Model):

    _inherit = 'account.payment.line'

    def _get_communication_type(self):
        """Add BBA Structured Communication Type"""
        return[('normal', 'Free Communication'),
               ('bba', 'BBA Structured Communication')]

    communication_type = fields.Selection(
        selection=_get_communication_type)

    def check_bbacomm(self, val):
        supported_chars = '0-9'
        pattern = re.compile('[^' + supported_chars + ']')
        if pattern.findall(val or ''):
            return False
        if len(val) == 12:
            base = int(val[:10])
            mod = base % 97 or 97
            if mod == int(val[-2:]):
                return True
        return False

    @api.constrains('communication', 'communication_type')
    def _check_communication(self):
        for rec in self:
            if rec.communication_type == 'bba':
                if not self.check_bbacomm(rec.communication):
                    raise ValidationError(_(
                        "Invalid BBA Structured Communication !"))

    def invoice_reference_type2communication_type(self):
        res = super(AccountPaymentLine, self)\
            .invoice_reference_type2communication_type()
        res['bba'] = 'bba'
        return res
