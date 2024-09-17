To configure this module, you neet to go to Invoicing > Reporting > Belgium Annual Account
and create a report instance according to the desired accounting time period.

You need to specify two MIS Builder templates, the first one for the Balance Sheet
and the second one for the Profit & Loss, provided by this module :

- Micro model company with capital [m07-f]
- Abbreviated model company with capital [m01-f]
- Full model company with capital [m02-f]
- Micro model company without capital [m87-f]
- Abbreviated model company without capital [m81-f]
- Full model company without capital [m82-f]
- Micro schema non-profit institution [m08-f]
- Abbreviated schema non-profit institution [m04-f]
- Full schema non-profit institution [m05-f]

The prefixes in square brackets are the prefixes given by the National Bank of Belgium.

You will need to edit those templates to add the json data file and the json calculation file.
Those files are located in l10n_be_mis_report/script/calc and l10n_be_mis_report/script/data.

Pay attention to add the json files with the same prefix present in the template name.

After completing the report, you can confirm it. Some verifications will be made and exceptions
will be thrown if information is missing or if it does not correspond to the expected format.

When the report is confirmed, you are able to download the XBRL file containing the data of the report.

If you need to make some modifications, the report must be in state draft.
