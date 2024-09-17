# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "L10n Be Annual Account Xbrl",
    "summary": """
        generates the xbrl report of belgium annual account""",
    "version": "14.0.1.0.0",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-belgium",
    "depends": [
        "l10n_be_mis_reports",
        "contacts",
        "partner_firstname",
        "partner_identification",
    ],
    "data": [
        "data/partner_id_numbers_data.xml",
        "security/acl_l10n_be_annual_account_xbrl.xml",
        "security/acl_rule_l10n_be_annual_account_xbrl.xml",
        "views/l10n_be_annual_account_xbrl.xml",
        "views/mis_report.xml",
        "views/res_partner.xml",
    ],
    "demo": [],
}
