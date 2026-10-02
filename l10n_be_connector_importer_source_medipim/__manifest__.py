# Copyright 2026 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "L10n Be Connector Importer Product Medipim",
    "summary": """This module allows to import products from Belgian Medipim API""",
    "version": "18.0.1.0.0",
    "license": "LGPL-3",
    "maintainers": ["rousseldenis"],
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-belgium",
    "depends": [
        "connector_importer_product",
        "connector_importer_api",
        "l10n_be_product_cnk",
        "product_state",
    ],
    "data": [
        "security/security.xml",
        "data/source_medipim.xml",
        "data/import_type_product_product.xml",
        "data/import_backend.xml",
        "data/import_recordset.xml",
        "views/product_product.xml",
    ],
}
