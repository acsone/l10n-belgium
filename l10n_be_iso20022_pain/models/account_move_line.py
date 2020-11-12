# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _prepare_payment_line_vals(self, payment_order):
        self.ensure_one()
        vals = super()._prepare_payment_line_vals(payment_order)
        invoice_journal = self.move_id.journal_id
        if (
            "communication" in vals
            and invoice_journal.invoice_reference_type != "none"
            and invoice_journal.invoice_reference_model == "be"
        ):
            vals["communication"] = self.move_id.ref.replace("+", "").replace("/", "")
        return vals
