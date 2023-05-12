# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import json
import re
import tempfile
from datetime import datetime

from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class L10nBeAnnualAccountXbrl(models.Model):
    _name = "l10n.be.annual.account.xbrl"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Belgium Annual Account"
    _order = "date_from desc"
    _rec_name = "report_name"

    @api.model
    def _get_default_company_id(self):
        return self.env.company

    report_name = fields.Char(string="Report Name", required=True)
    bs_mis_report_template_id = fields.Many2one(
        comodel_name="mis.report",
        string="Balance Sheet",
        domain=[("json_data_file", "!=", False), ("json_calc_file", "!=", False)],
    )
    pl_mis_report_template_id = fields.Many2one(
        comodel_name="mis.report",
        string="Profit & Loss",
        domain=[("json_data_file", "!=", False), ("json_calc_file", "!=", False)],
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=_get_default_company_id,
    )
    company_category = fields.Selection(
        string="Company Category",
        selection=[
            ("m01-f", "companies with capital"),
            ("m81-f", "companies without capital"),
            ("m04-f", "Non-profit institution"),
        ],
    )
    company_registry = fields.Char(
        string="Company Registry",
        related="company_id.company_registry",
        required=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("published", "Published"),
        ],
        default="draft",
        string="Status",
    )
    date_range_id = fields.Many2one(comodel_name="date.range", string="Date Range")
    date_from = fields.Date(string="From", required=True)
    date_to = fields.Date(string="To", required=True)
    administrator_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="annual_account_xbrl_administrators",
        string="Administrators",
    )
    accountant_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="annual_account_xbrl_accountants",
        string="Accountants",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    schema_ref = fields.Char(string="Schema")
    legal_form = fields.Selection(
        string="Legal Status",
        selection=[
            ("lgf:m418", "Autonomous municipal company"),
            ("lgf:m706", "Cooperative society"),
            ("lgf:m716", "Cooperative society governed by public law"),
            (
                "lgf:m265",
                "Europ. Econ. assoc wo reg.seat but with est. unit in Belgium",
            ),
            ("lgf:m027", "European company (Societas Europaea)"),
            ("lgf:m001", "European cooperative society"),
            ("lgf:m065", "European economic assoc with registered seat in Belgium"),
            ("lgf:m030", "Foreign company"),
            ("lgf:m011", "General partnership"),
            ("lgf:m125", "International non-profit organization"),
            ("lgf:m612", "Limited partnership"),
            ("lgf:m017", "Non-profit organization"),
            ("lgf:m026", "Private foundation"),
            ("lgf:m610", "Private limited company"),
            ("lgf:m616", "Private limited company governed by public law"),
            ("lgf:m021", "Private mutual insurance fund"),
            ("lgf:m014", "Public limited company"),
            ("lgf:m029", "Public utility foundation"),
        ],
    )
    active = fields.Boolean(
        default=True,
    )
    commercial_court = fields.Selection(
        string="Commercial Court",
        selection=[
            ("cct:m03", "Antwerp, division Antwerp"),
            ("cct:m10", "Antwerp, division Hasselt"),
            ("cct:m17", "Antwerp, division Mechelen"),
            ("cct:m25", "Antwerp, division Tongeren"),
            ("cct:m27", "Antwerp, division Turnhout"),
            ("cct:m32", "Brussels, Dutch speaking"),
            ("cct:m31", "Brussels, French speaking"),
            ("cct:m30", "Eupen"),
            ("cct:m05", "Ghent, division Bruges"),
            ("cct:m07", "Ghent, division Dendermonde"),
            ("cct:m09", "Ghent, division Ghent"),
            ("cct:m12", "Ghent, division Ieper"),
            ("cct:m13", "Ghent, division Kortrijk"),
            ("cct:m22", "Ghent, division Ostend"),
            ("cct:m23", "Ghent, division Oudenaarde"),
            ("cct:m29", "Ghent, division Veurne"),
            ("cct:m06", "Hainaut, division Charleroi"),
            ("cct:m18", "Hainaut, division Mons"),
            ("cct:m26", "Hainaut, division Tournai"),
            ("cct:m14", "Leuven"),
            ("cct:m04", "Liège, division Arlon"),
            ("cct:m08", "Liège, division Dinant"),
            ("cct:m11", "Liège, division Huy"),
            ("cct:m16", "Liège, division Marche-en-Famenne"),
            ("cct:m19", "Liège, division Namur"),
            ("cct:m20", "Liège, division Neufchâteau"),
            ("cct:m28", "Liège, division Verviers"),
            ("cct:m21", "Walloon Brabant"),
        ],
    )
    date_recent_filing = fields.Date(
        string="Last filing date",
        help="Date of filing the most recent document mentioning the date of "
        "publication of the deed of incorporation and of the deed of amendment "
        "of the articles of association",
    )
    date_general_assembly = fields.Date(
        string="General Assembly",
        help="Date of the general assembly where the accounts were approved",
    )
    date_last_xbrl_generation = fields.Date(
        string="Last XBRL Generation Date", tracking=True
    )

    # flake8: noqa: B950
    def get_mapping_dict(self):
        """Returns a mapping dictionary where the key is the XBRL fact id
        and the value is its corresponding field
        """
        return {
            "met:str2#dim:bas=bas:m26#dim:part=part:m2#dim:psn=psn:m1#dim:qlt=qlt:m1": "company_registry",
            "met:dte1#dim:bas=bas:m27#dim:evt=evt:m1#dim:part=part:m2": "date_general_assembly",
            "met:dte1#dim:bas=bas:m27#dim:mmt=mmt:m1#dim:part=part:m2#dim:prd=prd:m1": "date_from",
            "met:dte1#dim:bas=bas:m27#dim:mmt=mmt:m2#dim:part=part:m2#dim:prd=prd:m1": "date_to",
            "lgf-enum:list2#dim:bas=bas:m30#dim:part=part:m2#dim:psn=psn:m1": "legal_form",
            "cct-enum:list1#dim:bas=bas:m32#dim:part=part:m2": "commercial_court",
            "met:dte1#dim:bas=bas:m27#dim:evt=evt:m2#dim:part=part:m2": "date_recent_filing",
        }

    def action_confirmed(self):
        self.state = "confirmed"

    def action_draft(self):
        self.state = "draft"

    def action_published(self):
        self.state = "published"
        self.active = False

    @api.constrains(
        "state",
        "company_category",
        "schema_ref",
        "commercial_court",
        "date_recent_filing",
        "legal_form",
        "date_from",
        "date_to",
    )
    def _check_confirmed(self):
        for record in self:
            if record.state != "draft":
                if not record.company_category:
                    raise ValidationError(_("Company Category cannot be empty"))
                if not record.schema_ref:
                    raise ValidationError(_("Schema cannot be empty"))
                if not record.commercial_court:
                    raise ValidationError(_("Commercial Court cannot be empty"))
                if not record.date_recent_filing:
                    raise ValidationError(_("Last filing date cannot be empty"))
                if not record.legal_form:
                    raise ValidationError(_("Legal Status cannot be empty"))
                if not record.date_from:
                    raise ValidationError(_("Date From cannot be empty"))
                if not record.date_to:
                    raise ValidationError(_("Date To cannot be empty"))
                if not record.bs_mis_report_template_id:
                    raise ValidationError(_("Balance Sheet cannot be empty"))
                if not record.pl_mis_report_template_id:
                    raise ValidationError(_("Profit & Loss cannot be empty"))
                self._check_administrators()
                if record.date_general_assembly < record.date_to:
                    raise UserError(
                        _(
                            "The closing date of the financial year must be earlier than"
                            " or equal to the date of approval by the general meeting"
                        )
                    )

    @api.constrains("state", "date_recent_filing")
    def _check_date_recent_filing(self):
        for record in self:
            if record.state != "draft":
                if record.date_recent_filing > fields.Date.today():
                    raise ValidationError(_("Last filing date cannot be in the future"))

    @api.onchange("date_range_id")
    def _onchange_date_range(self):
        if self.date_range_id:
            self.date_from = self.date_range_id.date_start
            self.date_to = self.date_range_id.date_end

    @api.onchange("date_from", "date_to")
    def _onchange_dates(self):
        if self.date_range_id:
            if (
                self.date_from != self.date_range_id.date_start
                or self.date_to != self.date_range_id.date_end
            ):
                self.date_range_id = False

    @api.onchange("company_category")
    def _onchange_schema(self):
        if self.company_category == "m01-f":
            self.schema_ref = "http://www.nbb.be/be/fr/cbso/fws/22.19/mod/m01/m01-f.xsd"
        elif self.company_category == "m81-f":
            self.schema_ref = "http://www.nbb.be/be/fr/cbso/fws/22.19/mod/m81/m81-f.xsd"
        elif self.company_category == "m04-f":
            self.schema_ref = "http://www.nbb.be/be/fr/cbso/fws/22.19/mod/m04/m04-f.xsd"

    @api.constrains("bs_mis_report_template_id")
    def _check_balance_sheet(self):
        if self.bs_mis_report_template_id:
            if not self.bs_mis_report_template_id.json_data_file:
                raise ValidationError(
                    _(
                        "JSON Data file cannot be empty, "
                        "edit the balance sheet to add one"
                    )
                )
            if not self.bs_mis_report_template_id.json_calc_file:
                raise ValidationError(
                    _(
                        "JSON Calculation file cannot be empty, "
                        "edit the balance sheet to add one"
                    )
                )

    @api.constrains("pl_mis_report_template_id")
    def _check_profit_loss(self):
        if self.pl_mis_report_template_id:
            if not self.pl_mis_report_template_id.json_data_file:
                raise ValidationError(
                    _(
                        "JSON Data file cannot be empty, "
                        "edit the profit & loss to add one"
                    )
                )
            if not self.pl_mis_report_template_id.json_calc_file:
                raise ValidationError(
                    _(
                        "JSON Calculation file cannot be empty, "
                        "edit the profit & loss to add one"
                    )
                )

    def _check_administrators(self):
        for record in self:
            for admin in record.administrator_ids:
                self._check_admin_address(admin)
                self._check_entity_number(admin)
            for accountant in record.accountant_ids:
                self._check_admin_address(accountant)
                self._check_entity_number(accountant)
                self._check_member_number(accountant)

    def _check_admin_address(self, admin):
        if not admin.kind_of_address:
            raise UserError(
                _(
                    f"Kind of Address field for Administrator {admin.name} cannot be empty"
                )
            )
        matched_street = re.match(
            r"(?P<number>\d+[a-zA-Z]*)\s*\/*\s*(?P<box>\w*)\s*,\s*(?P<street>.+)",
            admin.street,
        )
        if not matched_street:
            raise UserError(
                f"Address of {admin.name} should be like : "
                f"STREET_NUMBER/STREET_BOX(optional), STREET_NAME."
                " Example : 718A(/14), Pink Road"
            )

    def _check_entity_number(self, admin):
        nb_entity_number = 0
        for id_number in admin.id_numbers:
            if id_number.category_id.code == "nmt:m1":
                nb_entity_number += 1
        if nb_entity_number != 1 and admin.company_type == "company":
            raise UserError(
                _(
                    f"Administrator {admin.name} must have "
                    f"only one Entity Number (in ID Numbers)"
                )
            )

    def _check_member_number(self, admin):
        nb_member_number = 0
        for id_number in admin.id_numbers:
            if id_number.category_id.code == "member_number":
                nb_member_number += 1
        if nb_member_number != 1:
            raise UserError(
                _(
                    f"Accountant {admin.name} must have only one Member Number (in ID Numbers)"
                )
            )

    def action_download_xbrl(self):
        """Downloads the xbrl balance sheet"""
        tmp = tempfile.mkdtemp()
        report_name = self.report_name.strip()
        report_name = report_name.replace(" ", "_")
        result_file_path = f"{tmp}/{report_name}.xbrl"
        self._write_xbrl_report(result_file_path)
        with open(result_file_path, "rb") as file:
            attachment_model = self.env["ir.attachment"].sudo()
            attachment = attachment_model.create(
                {
                    "name": f"{report_name}.xbrl",
                    "datas": base64.b64encode(file.read()),
                    "type": "binary",
                    "mimetype": "application/xml",
                }
            )
        url = f"web/content/{attachment.id}?download=true"
        self.date_last_xbrl_generation = datetime.today()
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
        }

    def _write_xbrl_report(self, result_file_path):
        """Writes the information of the balance sheet for the selected
        accounting period in the file result_file_path
        :param result_file_path: the path of the xbrl file
        """
        balance_sheet_kpis_dict = self._evaluate_kpis(self.bs_mis_report_template_id)
        profit_loss_kpis_dict = self._evaluate_kpis(self.pl_mis_report_template_id)
        json_file = base64.standard_b64decode(
            self.bs_mis_report_template_id.json_data_file
        )
        json_data_dict = json.loads(json_file)
        fact_prototypes = json_data_dict["internalModels"][0]["factPrototypes"]
        rubcode_list = self._get_rubcode_list(fact_prototypes)
        rubcodes = []
        rubcodes = self._get_rubcodes(balance_sheet_kpis_dict, rubcodes)
        rubcodes = self._get_rubcodes(profit_loss_kpis_dict, rubcodes)
        ns_list = self._get_xbrl_namespaces(json_data_dict, rubcode_list, rubcodes)
        namespaces_dict = json_data_dict["internalModels"][0]["namespacesByPrefix"]
        NSMAP = self._set_nsmap(ns_list, namespaces_dict)
        root = etree.Element("xbrl", nsmap=NSMAP)
        link = etree.SubElement(root, "{http://www.xbrl.org/2003/linkbase}schemaRef")
        link.set("{http://www.w3.org/1999/xlink}type", "simple")
        link.set("{http://www.w3.org/1999/xlink}href", self.schema_ref)
        root = self._write_identifying_data(root, json_data_dict)
        administrators_list = json_data_dict["internalModels"][0]["editorModel"][
            "sectionsOrTables"
        ][1]["section"]["sectionsOrTables"][0]["section"]["sectionsOrTables"][0][
            "section"
        ][
            "sectionsOrTables"
        ]
        root = self._write_administrators(
            root,
            json_data_dict,
            self.administrator_ids,
            administrators_list,
            "administrator",
        )
        accountants_list = json_data_dict["internalModels"][0]["editorModel"][
            "sectionsOrTables"
        ][1]["section"]["sectionsOrTables"][0]["section"]["sectionsOrTables"][1][
            "section"
        ][
            "sectionsOrTables"
        ]
        root = self._write_administrators(
            root, json_data_dict, self.accountant_ids, accountants_list, "accountant"
        )
        root = self._write_kpis(root, rubcode_list, balance_sheet_kpis_dict)
        root = self._write_kpis(root, rubcode_list, profit_loss_kpis_dict)
        root = self._write_units(root)
        prev_root_length = len(root)
        id_data_dict = {
            "l10n_be": self.get_mapping_dict(),
            "company_id": self.company_id.get_mapping_dict(),
        }
        root = self._write_identifying_data_values(
            root, id_data_dict, NSMAP, len(root) - prev_root_length + 1, json_data_dict
        )
        index = len(root) - prev_root_length + 1
        root = self._write_admin_list_values(json_data_dict, root, index, NSMAP)
        index = len(root) - prev_root_length + 1
        kpis_dict = dict(balance_sheet_kpis_dict, **profit_loss_kpis_dict)
        root = self._write_rubric_values(
            json_data_dict, kpis_dict, rubcodes, root, index
        )
        self._write_report_in_file(result_file_path, root)

    def _write_units(self, root):
        """Writes the needed units in the XBRL document"""
        unit_eur = etree.SubElement(root, "unit", id="EUR")
        measure_eur = etree.SubElement(unit_eur, "measure")
        measure_eur.text = "iso4217:EUR"
        unit_pure = etree.SubElement(root, "unit", id="pure")
        measure_pure = etree.SubElement(unit_pure, "measure")
        measure_pure.text = "pure"
        return root

    def _write_rubric_values(self, json_data_dict, kpis_dict, rubcodes, root, index):
        """Writes the values regarding the rubric codes in the XBRL document
        :param json_data_dict: Data dictionary containing data from the NBB taxonomy
        :param kpis_dict: Dictionary containing the evaluation of mis report
                          templates over a time period
        :param rubcodes: The list of all the rubric codes present in the json data dictionary
        :param root: Root tag of the XBRL document
        :param index: The index of the XBRL context
        """
        for rubcode_name, kpi_value in kpis_dict.items():
            split_rubcode = rubcode_name.split("_")
            sanitized_rubcode = ""
            if len(split_rubcode) == 2:
                sanitized_rubcode = split_rubcode[-1]
            elif len(split_rubcode) == 3:
                sanitized_rubcode = f"{split_rubcode[-2]}/{split_rubcode[-1]}"
            if sanitized_rubcode not in rubcodes or not kpi_value:
                continue
            rubcode_fact_prototype = self._get_rub_fact_prototype(
                sanitized_rubcode, json_data_dict
            )
            value = etree.SubElement(
                root,
                "{http://www.nbb.be/be/fr/cbso/dict/met}%s"
                % rubcode_fact_prototype.get("qname").split(":")[1],
                contextRef=f"c{index}",
                decimals="INF",
                unitRef="EUR",
            )
            kpi_value = self.company_id.currency_id.round(kpi_value)
            # In some cases currency_id.round returns more than two decimals
            value.text = str(round(kpi_value, 2))
            index += 1
        return root

    def _get_rub_fact_prototype(self, rubcode_name, json_data_dict):
        """Returns the fact prototype present in the json data dictionary
        which correspond to the rubric code rubcode_name
        :param rubcode_name: The rubric code
        :param json_data_dict: Data dictionary containing data from the NBB taxonomy
        """
        fact_prototypes = json_data_dict["internalModels"][0]["factPrototypes"]
        for fact_prototype in fact_prototypes:
            if fact_prototype.get("rubCode"):
                if fact_prototype["rubCode"] == rubcode_name:
                    return fact_prototype

    def _write_report_in_file(self, file_path, root):
        """Writes pretty printed root in the XBRL file"""
        with open(file_path, "wb") as file:
            file.write(
                etree.tostring(
                    element_or_tree=root,
                    xml_declaration=True,
                    encoding="UTF-8",
                    pretty_print=True,
                )
            )

    def _get_rubcodes(self, mis_report_template_kpis, rubcodes_list):
        """Returns the list of the rubric codes present in mis_report_template_kpis
        :param mis_report_template_kpis: Dictionary containing the evaluation of the
                                         mis report template over a time period
        :param rubcodes_list: The list of all the rubric codes from the json data file
        """
        for key in mis_report_template_kpis.keys():
            if key.startswith("rub"):
                split_acc_name = key.split("_")
                sanitized_acc_name = ""
                if len(split_acc_name) == 2:
                    sanitized_acc_name = split_acc_name[-1]
                elif len(split_acc_name) == 3:
                    sanitized_acc_name = f"{split_acc_name[-2]}/{split_acc_name[-1]}"
                if sanitized_acc_name not in rubcodes_list:
                    rubcodes_list.append(sanitized_acc_name)
        return rubcodes_list

    def _set_nsmap(self, ns_list, namespaces_dict):
        """Set the namespaces mapping dictionary used in the XBRL file"""
        etree.register_namespace("link", "http://www.xbrl.org/2003/linkbase")
        etree.register_namespace("xlink", "http://www.w3.org/1999/xlink")
        NSMAP = {
            None: "http://www.xbrl.org/2003/instance",
            "xbrldi": "http://xbrl.org/2006/xbrldi",
            "link": "http://www.xbrl.org/2003/linkbase",
            "xlink": "http://www.w3.org/1999/xlink",
            "iso4217": "http://www.xbrl.org/2003/iso4217",
        }
        if self.accountant_ids or self.administrator_ids:
            NSMAP["open"] = "http://www.nbb.be/be/fr/cbso/dict/dom/open"
        for namespace in ns_list:
            if namespace.startswith("dim:"):
                namespace = namespace.split(":")[1]
            if namespaces_dict.get(namespace):
                etree.register_namespace(namespace, namespaces_dict.get(namespace))
                NSMAP[namespace] = namespaces_dict.get(namespace)
        return NSMAP

    def _write_identifying_data(self, root, json_data_dict):
        """Writes the identifying data contexts in the XBRL file"""
        id_data_dict = {
            "l10n_be": self.get_mapping_dict(),
            "company_id": self.company_id.get_mapping_dict(),
        }
        added_fact_list = []
        for module_name, mapping_dict in id_data_dict.items():
            for fact_id, field_name in mapping_dict.items():
                matched_dims = re.match(r"[^#]+#(?P<dimensions>.+)", fact_id)
                if matched_dims.group("dimensions") in added_fact_list:
                    continue
                fact_prototypes = json_data_dict["internalModels"][0]["factPrototypes"]
                for fact_prototype in fact_prototypes:
                    class_instance = (
                        self if module_name == "l10n_be" else self.company_id
                    )
                    if (
                        fact_prototype.get("id") == fact_id
                        and class_instance[field_name]
                    ):
                        context = etree.Element("context", id=f"c{len(root)}")
                        entity = etree.Element("entity")
                        identifier = etree.Element(
                            "identifier", scheme="http://fgov.be"
                        )
                        identifier.text = self.company_registry
                        entity.append(identifier)
                        context.append(entity)
                        period = etree.Element("period")
                        instant = etree.Element("instant")
                        instant.text = self.date_to.strftime(format="%Y-%m-%d")
                        period.append(instant)
                        context.append(period)
                        scenario = etree.Element("scenario")
                        for dimension in fact_prototype.get("dims"):
                            xbrldi = etree.SubElement(
                                scenario,
                                "{http://xbrl.org/2006/xbrldi}explicitMember",
                                dimension=dimension["dimQname"],
                            )
                            xbrldi.text = dimension["memberQname"]
                            context.append(scenario)
                            root.append(context)
                            if matched_dims:
                                added_fact_list.append(matched_dims.group("dimensions"))
                                if field_name == "zip":
                                    zip_code = (
                                        self._parse_zip(
                                            class_instance[field_name], json_data_dict
                                        )
                                        if field_name == "zip"
                                        else None
                                    )
                                    if zip_code:
                                        added_fact_list.append(
                                            "dim:bas=bas:m31#dim:ctc=ctc:m5#"
                                            "dim:part=part:m2#dim:psn=psn:m1"
                                        )
        return root

    def _write_identifying_data_values(
        self, root, id_data_dict, ns_map, index, json_data_dict
    ):
        """Writes the identifying data value, for each context in the XBRL file
        :param root: Root tag of the XBRL document
        :param id_data_dict: A dictionary of dictionaries containing the name of the
                             field corresponding to an XBRL fact id, for
                             l10n_be_annual_account_xbrl and res_company models
        :param ns_map: The namespaces mapping dictionary
        :param index: The index of the XBRL context
        :param json_data_dict: Data dictionary containing data from the NBB taxonomy
        """
        values_list = []
        for module_name, mapping_dict in id_data_dict.items():
            for fact_id, field_name in mapping_dict.items():
                if field_name in values_list:
                    continue
                class_instance = self if module_name == "l10n_be" else self.company_id
                ns = fact_id.split("#")[0]
                if field_name == "zip" or field_name == "city":
                    zip_code = (
                        self._parse_zip(class_instance[field_name], json_data_dict)
                        if field_name == "zip"
                        else None
                    )
                    if zip_code:
                        if "pcd-enum:list1" in fact_id:
                            root = self._write_fact_value(
                                root,
                                ns_map[ns.split(":")[0]],
                                ns.split(":")[1],
                                index,
                                zip_code,
                            )
                            values_list.append(field_name)
                            values_list.append("city")
                            index += 1
                    else:
                        if "pcd-enum:list1" not in fact_id:
                            root = self._write_fact_value(
                                root,
                                ns_map[ns.split(":")[0]],
                                ns.split(":")[1],
                                index,
                                class_instance[field_name],
                            )
                            values_list.append(field_name)
                            index += 1
                else:
                    if class_instance[field_name]:
                        root = self._write_fact_value(
                            root,
                            ns_map[ns.split(":")[0]],
                            ns.split(":")[1],
                            index,
                            class_instance[field_name],
                        )
                        values_list.append(field_name)
                        index += 1
        return root

    def _write_kpis(self, root, rubcode_list, mis_report_template_kpis):
        """Writes the contexts for each rubric code of a mis report template
        in the XBRL file
        :param root: Root tag of the XBRL document
        :param rubcode_list: The list of all the rubric codes from the json data dictionary
        :param mis_report_template_kpis: A dictionary containing the evaluation of the
                                         mis report template over a time period
        """
        if mis_report_template_kpis:
            for rubric, value in mis_report_template_kpis.items():
                # Check if it is an account
                if rubric.startswith("rub"):
                    if value:
                        context = etree.Element("context", id=f"c{len(root)}")
                        entity = etree.Element("entity")
                        identifier = etree.Element(
                            "identifier", scheme="http://fgov.be"
                        )
                        identifier.text = self.company_registry
                        entity.append(identifier)
                        context.append(entity)
                        period = etree.Element("period")
                        instant = etree.Element("instant")
                        instant.text = self.date_to.strftime(format="%Y-%m-%d")
                        period.append(instant)
                        context.append(period)
                        scenario = etree.Element("scenario")
                        scenario = self._write_rubric_dimensions(
                            scenario, rubric, rubcode_list
                        )
                        context.append(scenario)
                        root.append(context)
        return root

    def _write_rubric_dimensions(self, scenario, account_name, rubcode_list):
        """Writes the dimensions of a rubric in the XBRL file
        :param scenario: The scenario tag of a context
        :param account_name: The name of the rubric
        :param rubcode_list: The list of all the rubric codes from the json data dictionary
        :return:
        """
        split_acc_name = account_name.split("_")
        sanitized_acc_name = ""
        if len(split_acc_name) == 2:
            sanitized_acc_name = split_acc_name[-1]
        elif len(split_acc_name) == 3:
            sanitized_acc_name = f"{split_acc_name[-2]}/{split_acc_name[-1]}"
        for fact_prototype in rubcode_list:
            if fact_prototype.get("rubCode") and fact_prototype.get("period") == "N":
                if (
                    "rubCode" in fact_prototype
                    and fact_prototype["rubCode"] == sanitized_acc_name
                ):
                    for dim in fact_prototype["dims"]:
                        xbrldi = etree.Element(
                            "{http://xbrl.org/2006/xbrldi}explicitMember",
                            dimension=dim.get("dimQname"),
                        )
                        xbrldi.text = dim.get("memberQname")
                        scenario.append(xbrldi)
                    break
        return scenario

    def _get_rubcode_list(self, fact_prototypes):
        """Get the list of all the rubric codes of the json data file"""
        rubcode_list = []
        rubcodes = []
        for fact_prototype in fact_prototypes:
            if fact_prototype.get("rubCode") and fact_prototype.get("period") == "N":
                if fact_prototype.get("rubCode") not in rubcodes:
                    rubcodes.append(fact_prototype.get("rubCode"))
                    rubcode_list.append(fact_prototype)
        return rubcode_list

    def _get_xbrl_namespaces(self, json_data_dict, rubcode_list, rubcodes):
        """Returns the list of the namespaces needed for the XBRL facts that
        will be written in the XBRL report
        """
        fact_ids_list = self._get_fact_ids(json_data_dict, rubcode_list, rubcodes)
        ns_list = []
        fact_prototypes = json_data_dict["internalModels"][0]["factPrototypes"]
        for fact_id in fact_ids_list:
            for fact_prototype in fact_prototypes:
                if fact_prototype.get("id") != fact_id:
                    continue
                for dimension in fact_prototype.get("dims"):
                    dimension_names = dimension.get("dimQname").split(":")
                    for dimension_name in dimension_names:
                        if dimension_name not in ns_list:
                            ns_list.append(dimension_name)
                if fact_prototype.get("qname"):
                    if "-" in fact_prototype["qname"]:
                        dimension_name = (
                            fact_prototype["qname"].split(":")[0].split("-")[0]
                        )
                        if dimension_name not in ns_list:
                            ns_list.append(dimension_name)
                    dimension_name = fact_prototype["qname"].split(":")[0]
                    if dimension_name not in ns_list:
                        ns_list.append(dimension_name)
                break
        return ns_list

    def _get_fact_ids(self, json_data_dict, rubcode_list, rubcodes):
        """Returns the list of all the ids of the XBRL facts that will be
        written in the XBRL report
        :param json_data_dict: Data dictionary containing data from the NBB taxonomy
        :param rubcode_list: The list of all the rubric codes from the json data dictionary
        :param rubcodes: The list of the rubcodes present in the balance sheet and
                         the profit & loss
        """

        # l10n_be_annual_account_xbrl fact ids
        fact_ids_list = [
            fact_id
            for fact_id in self.get_mapping_dict().keys()
            if self._fact_has_value(
                fact_id, self, self.get_mapping_dict(), json_data_dict
            )
        ]
        # Company fact ids
        fact_ids_list += [
            fact_id
            for fact_id in self.company_id.get_mapping_dict().keys()
            if self._fact_has_value(
                fact_id,
                self.company_id,
                self.company_id.get_mapping_dict(),
                json_data_dict,
            )
            and fact_id not in fact_ids_list
        ]
        # Administrators fact ids
        for admin in self.administrator_ids:
            fact_ids_list += [
                fact_id
                for fact_id in admin._get_admin_id_mapping()[admin.company_type].keys()
                if self._fact_has_value(
                    fact_id,
                    admin,
                    admin._get_admin_id_mapping()[admin.company_type],
                    json_data_dict,
                )
                and fact_id not in fact_ids_list
            ]
        # Accountants fact ids
        for accountant in self.accountant_ids:
            fact_ids_list += [
                fact_id
                for fact_id in accountant._get_accountant_id_mapping()[
                    accountant.company_type
                ].keys()
                if self._fact_has_value(
                    fact_id,
                    accountant,
                    accountant._get_accountant_id_mapping()[accountant.company_type],
                    json_data_dict,
                )
                and fact_id not in fact_ids_list
            ]
        # Rubcodes fact ids
        kpi_dict = dict(
            self._evaluate_kpis(self.bs_mis_report_template_id),
            **self._evaluate_kpis(self.pl_mis_report_template_id),
        )
        for fact_prototype in rubcode_list:
            rubcode = fact_prototype.get("rubCode")
            acc_name = ""
            if rubcode in rubcodes:
                if "/" in rubcode:
                    acc_name = rubcode.split("/")
                    acc_name = f"rub_{acc_name[0]}_{acc_name[1]}"
                else:
                    acc_name = f"rub_{rubcode}"
            if kpi_dict.get(acc_name):
                fact_ids_list.append(fact_prototype.get("id"))
        return fact_ids_list

    def _evaluate_kpis(self, mis_report_template):
        """evaluate the mis report template over a time period,
        from date_from to date_to
        """
        aep = mis_report_template._prepare_aep(companies=self.company_id)
        return mis_report_template.evaluate(
            aep=aep,
            date_from=self.date_from,
            date_to=self.date_to,
        )

    def _write_administrators(
        self, root, json_data_dict, admin_list, admin_data_list, admin_type
    ):
        """Writes the information regarding the administrators or the
        accountants in the XBRL file
        :param root: Root tag of the XBRL document
        :param json_data_dict: Data dictionary containing data from the NBB taxonomy
        :param admin_list: The list of the administrators or the accountants of the company
        :param admin_data_list: A list of res_partner who are the administrators or
                                the accountants of a company
        :param admin_type: The function of the res_partner , administrator or accountant
        """
        for admin in admin_list:
            facts_list = []
            if admin.company_type == "person":
                admin_rows = (
                    admin_data_list[1]["section"]["sectionsOrTables"][0]
                    .get("table")
                    .get("rows")
                )
            else:
                admin_rows = (
                    admin_data_list[0]["section"]["sectionsOrTables"][0]
                    .get("table")
                    .get("rows")
                )
            open_dim_q_names = self._find_open_dim_q_names(admin_rows)
            for row in admin_rows:
                for col in row.get("cols"):
                    if col.get("fp"):
                        dimensions = self._find_xbrl_fact_by_id(
                            json_data_dict["internalModels"][0]["factPrototypes"],
                            col["fp"].get("id"),
                        ).get("dims")
                        if not self._is_fact_written(dimensions, facts_list):
                            if admin_type == "administrator":
                                id_mapping_list = admin._get_admin_id_mapping()[
                                    admin.company_type
                                ]
                            else:
                                id_mapping_list = admin._get_accountant_id_mapping()[
                                    admin.company_type
                                ]
                            if self._fact_has_value(
                                col["fp"].get("id"),
                                admin,
                                id_mapping_list,
                                json_data_dict,
                            ):
                                context = etree.Element("context", id=f"c{len(root)}")
                                entity = etree.Element("entity")
                                identifier = etree.Element(
                                    "identifier", scheme="http://fgov.be"
                                )
                                identifier.text = self.company_registry
                                entity.append(identifier)
                                context.append(entity)
                                period = etree.Element("period")
                                instant = etree.Element("instant")
                                instant.text = self.date_to.strftime(format="%Y-%m-%d")
                                period.append(instant)
                                context.append(period)
                                scenario = etree.Element("scenario")
                                open_dim_q_names_dict = dict()
                                if len(open_dim_q_names) == 1:
                                    open_dim_q_names_dict = {
                                        open_dim_q_names[0]: admin.name
                                    }
                                elif len(open_dim_q_names) == 2:
                                    open_dim_q_names_dict = {
                                        open_dim_q_names[0]: admin.firstname,
                                        open_dim_q_names[1]: admin.lastname,
                                    }
                                scenario = self._write_admin_dimensions(
                                    scenario,
                                    col["fp"].get("id"),
                                    open_dim_q_names_dict,
                                    json_data_dict,
                                )
                                context.append(scenario)
                                root.append(context)
                                facts_list.append(self._concat_dims(dimensions))
        return root

    def _fact_has_value(self, fact_id, class_instance, id_mapping_list, json_data_dict):
        """Returns true if the XBRL fact has a value
        :param fact_id: The id of the XBRL fact
        :param class_instance: an instance of res_partner (administrator or accountant)
        :param id_mapping_list: A dictionary of mapping dictionaries where the key is
                                the XBRL fact id and the value is its corresponding field,
                                for each type of administrator (legal and natural person)
        :param json_data_dict: Data dictionary containing data from the NBB taxonomy
        """
        fact_value = None
        if fact_id in id_mapping_list:
            field_name = id_mapping_list.get(fact_id)
            if "id_numbers" in field_name:
                for id_number in class_instance.id_numbers:
                    if field_name == "id_numbers.category_id":
                        if id_number.category_id.code == "nmt:m1":
                            fact_value = id_number.category_id.code
                    elif field_name == "id_numbers.member_number":
                        fact_value = class_instance.get_member_number()
                    else:
                        fact_value = id_number.name
            elif "street" in field_name:
                street_dict = self._parse_street(class_instance.street)
                fact_value = street_dict[field_name]
                if len(fact_value) == 0:
                    fact_value = None
            elif "zip" in field_name or "city" in field_name:
                zip_value = self._parse_zip(class_instance["zip"], json_data_dict)
                if zip_value:
                    if "pcd-enum" in fact_id:
                        fact_value = zip_value
                else:
                    fact_value = class_instance[field_name]
            else:
                fact_value = class_instance[field_name]
        return fact_value is not None and fact_value is not False

    def _find_open_dim_q_names(self, admin_rows):
        """Returns a list of the open dimensions of an administrator"""
        open_dim_q_names = []
        for row in admin_rows:
            if len(open_dim_q_names) <= 0:
                for col in row.get("cols"):
                    if col.get("fp"):
                        if col["fp"].get("openDimQNames"):
                            for open_dim_q_name in col["fp"]["openDimQNames"]:
                                open_dim_q_names.append(open_dim_q_name)
        return open_dim_q_names

    def _is_fact_written(self, dimensions, facts_list):
        return self._concat_dims(dimensions) in facts_list

    def _concat_dims(self, dimensions):
        concat_dim = ""
        for dim in dimensions:
            if dim.get("memberQname"):
                concat_dim += f"{dim.get('dimQname')}={dim.get('memberQname')}#"
        return concat_dim

    def _write_admin_dimensions(
        self, scenario, xbrl_fact_id, open_dim_q_names_dict, json_data_dict
    ):
        """Add the dimension to the scenario tag for the administrators
        or the accountants in the XBRL file
        :param scenario: The scenario tag of a context
        :param xbrl_fact_id: The id of the XBRL fact
        :param open_dim_q_names_dict: A dictionary containing the open dimensions
        :param json_data_dict: Data dictionary containing data from the NBB taxonomy
        """
        dimensions = self._find_xbrl_fact_by_id(
            json_data_dict["internalModels"][0]["factPrototypes"], xbrl_fact_id
        ).get("dims")
        for key, value in open_dim_q_names_dict.items():
            xbrldi = etree.SubElement(
                scenario,
                "{http://xbrl.org/2006/xbrldi}typedMember",
                dimension=key,
            )
            openstr = etree.SubElement(
                xbrldi, "{http://www.nbb.be/be/fr/cbso/dict/dom/open}str"
            )
            openstr.text = value
        for dim in dimensions:
            if dim.get("memberQname"):
                xbrldi = etree.SubElement(
                    scenario,
                    "{http://xbrl.org/2006/xbrldi}explicitMember",
                    dimension=dim.get("dimQname"),
                )
                xbrldi.text = dim.get("memberQname")
        return scenario

    def _find_xbrl_fact_by_id(self, fact_prototypes, xbrl_fact_id):
        for fact_prototype in fact_prototypes:
            if fact_prototype.get("id") == xbrl_fact_id:
                return fact_prototype
        return None

    def _write_admin_list_values(self, json_data_dict, root, index, ns_map):
        """Write the values of the XBRL facts regarding the administrators
        and the accountants
        :param json_data_dict: Data dictionary containing data from the NBB taxonomy
        :param root: Root tag of the XBRL document
        :param index: The index of the XBRL context
        :param ns_map: The namespaces mapping dictionary
        """
        prev_root_length = len(root)
        for administrator_id in self.administrator_ids:
            admin_mapping_dict = administrator_id._get_admin_id_mapping()[
                administrator_id.company_type
            ]
            root = self._write_admin_and_accounting_values(
                json_data_dict,
                root,
                index,
                ns_map,
                admin_mapping_dict,
                administrator_id,
            )
            index += len(root) - prev_root_length
            prev_root_length = len(root)
        for accountant_id in self.accountant_ids:
            acc_mapping_dict = accountant_id._get_accountant_id_mapping()[
                accountant_id.company_type
            ]
            root = self._write_admin_and_accounting_values(
                json_data_dict, root, index, ns_map, acc_mapping_dict, accountant_id
            )
            index += len(root) - prev_root_length
            prev_root_length = len(root)
        return root

    def _write_admin_and_accounting_values(
        self, json_data_dict, root, index, ns_map, mapping_dict, admin
    ):
        """Writes the values of the XBRL facts regarding an administrator or an accountant
        :param json_data_dict: Data dictionary containing data from the NBB taxonomy
        :param root: Root tag of the XBRL document
        :param index: The index of the XBRL context
        :param ns_map: The namespaces mapping dictionary
        :param mapping_dict: A dictionary of mapping dictionaries where the key is the
                             XBRL fact id and the value is its corresponding field,
                             for each type of administrator (legal and natural person)
        :param admin: A res_partner instance (administrator or accountant)
        """
        values_list = []

        for key, value in mapping_dict.items():
            if value in values_list:
                continue
            if not self._fact_has_value(key, admin, mapping_dict, json_data_dict):
                continue
            ns = key.split("#")[0]
            if value == "zip" or value == "city":
                zip_code = (
                    self._parse_zip(admin.mapped(value)[0], json_data_dict)
                    if value == "zip"
                    else None
                )
                if zip_code:
                    if "pcd-enum:list1" in key:
                        root = self._write_fact_value(
                            root,
                            ns_map[ns.split(":")[0]],
                            ns.split(":")[1],
                            index,
                            zip_code,
                        )
                        values_list.append(value)
                        index += 1
                else:
                    if "pcd-enum:list1" not in key:
                        root = self._write_fact_value(
                            root,
                            ns_map[ns.split(":")[0]],
                            ns.split(":")[1],
                            index,
                            admin.mapped(value)[0],
                        )
                        values_list.append(value)
                        index += 1
            else:
                if admin[value]:
                    root = self._write_fact_value(
                        root,
                        ns_map[ns.split(":")[0]],
                        ns.split(":")[1],
                        index,
                        admin[value],
                    )
                    values_list.append(value)
                    index += 1
        return root

    def _parse_street(self, street):
        """Returns a dictionary containing the street name, the street
        number and the street box, if street follows the correct format"""
        matched_street = re.match(
            r"(?P<number>\d+[a-zA-Z]*)\s*\/*\s*(?P<box>\w*)\s*,\s*(?P<street>.+)",
            street,
        )
        if not matched_street:
            raise UserError(
                _(
                    "Contact address should be like : "
                    "STREET_NUMBER/STREET_BOX(optional), STREET_NAME. "
                    "Example : 718A(/14), Pink Road"
                )
            )
        else:
            return {
                "street_name": matched_street.group("street"),
                "street_number": matched_street.group("number"),
                "street_box": matched_street.group("box"),
            }

    def _parse_zip(self, zip_value, json_data_dict):
        """Checks if the zip code is in zip code list of the json dictionary
        :param zip_value: The zip code
        :param json_data_dict: Data dictionary containing data from the NBB taxonomy
        """
        for pcd_enum in json_data_dict["internalModels"][0]["editorModel"][
            "codeListsMap"
        ]["pcd-enum:list1"]:
            code = pcd_enum.get("code")
            if not pcd_enum:
                continue
            if code == f"pcd:m{zip_value}":
                return code if len(code) > 0 else None

    def _write_fact_value(self, root, ns_map, ns, index, value):
        """Add the value of an XBRL fact as a child of root
        :param root: The root tag of the XBRL document
        :param ns_map: The namespaces mapping dictionary
        :param ns: The namespace
        :param index: The index of the XBRL context to reference
        :param value: The value of the XBRL fact
        """
        fact_value = etree.SubElement(
            root, "{" + ns_map + "}" + ns, contextRef=f"c{index}"
        )
        fact_value.text = str(value)
        return root
