# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductBfciCategory(models.Model):
    _name = "product.bfci.category"
    _description = "Product Bfci Category"

    name = fields.Char(
        translate=True,
    )
    bfci_id = fields.Char(
        help="This is a technical field to represent id in CBIP/BFCI database."
    )
    parent_id = fields.Many2one(
        comodel_name="product.bfci.category",
        ondelete="cascade",
        index=True,
        domain="[('id', '!=', id)]",
    )
