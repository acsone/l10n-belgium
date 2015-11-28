# -*- coding: utf-8 -*-
##############################################################################
#
#     This file is part of l10n_be_coa_multilang_detail, an Odoo module.
#
#     Copyright (c) 2015 ACSONE SA/NV (<http://acsone.eu>)
#
#     l10n_be_coa_multilang_detail is free software: you can redistribute it
#     and/or modify it under the terms of the GNU Affero General Public License
#     as published by the Free Software Foundation, either version 3 of
#     the License, or (at your option) any later version.
#
#     l10n_be_coa_multilang_detail is distributed in the hope that it will be
#     useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Affero General Public License for more details.
#
#     You should have received a copy of the
#     GNU Affero General Public License
#     along with l10n_be_coa_multilang_detail.
#     If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': "l10n_be_coa_multilang_detail",

    'summary': """
        Enable detail in Belgian Balance Sheet and P&L""",

    # 'description': put the module description in README.rst

    'author': "ACSONE SA/NV",
    'website': "http://acsone.eu",

    # Categories can be used to filter modules in modules listing
    # Check http://goo.gl/0TfwzD for the full list
    'category': 'Localization/Account Charts',
    'version': '8.0.1.0.0',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'l10n_be_coa_multilang',
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'account_financial_report.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
