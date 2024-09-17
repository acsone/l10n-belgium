# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class Partner(models.Model):
    _name = "res.partner"
    _inherit = "res.partner"

    kind_of_address = fields.Selection(
        selection=[
            ("atc:m002", "Address of the business unit"),
            ("atc:m001", "Address of the head office"),
            ("atc:m003", "Branch of a foreign company"),
            ("other", "Other"),
        ],
        string="Kind of Address",
    )
    other_kind_of_address = fields.Char(string="Other Kind Of Address")
    kind_of_entity_number_list = fields.Char(
        compute="_compute_kind_of_entity_number_list"
    )
    entity_number = fields.Char(compute="_compute_entity_number")
    member_number = fields.Char(compute="_compute_member_number")
    street_name = fields.Char(compute="_compute_street_name")
    street_number = fields.Char(compute="_compute_street_number")
    street_box = fields.Char(compute="_compute_street_box")
    country_list = fields.Char(compute="_compute_country")

    @api.onchange("kind_of_address")
    def _onchange_kind_of_address(self):
        self.other_kind_of_address = False

    @api.constrains("kind_of_address", "other_kind_of_address")
    def _check_other_kind_of_address(self):
        if any(
            rec.kind_of_address == "other" and not rec.other_kind_of_address
            for rec in self
        ):
            raise ValidationError(_("Other Kind Of Address cannot be empty"))

    @api.depends("id_numbers")
    def _compute_kind_of_entity_number_list(self):
        for rec in self:
            rec.kind_of_entity_number_list = False
            for id_number in rec.id_numbers:
                if id_number.category_id.code == "nmt:m1":
                    rec.kind_of_entity_number_list = id_number.category_id.code

    @api.depends("id_numbers")
    def _compute_entity_number(self):
        for rec in self:
            rec.entity_number = False
            for id_number in rec.id_numbers:
                if id_number.category_id.code == "nmt:m1":
                    rec.entity_number = id_number.name

    @api.depends("id_numbers")
    def _compute_member_number(self):
        for rec in self:
            rec.member_number = False
            for id_number in rec.id_numbers:
                if id_number.category_id.code == "member_number":
                    rec.member_number = id_number.name

    def _get_matched_street(self, street):
        """Returns a match object containing 3 subgroups (street number, street box
        and street name), if street matches the regular expression
        """
        return re.match(
            r"(?P<number>\d+[a-zA-Z]*)\s*\/*\s*(?P<box>\w*)\s*,\s*(?P<street>.+)",
            street,
        )

    @api.depends("street")
    def _compute_street_name(self):
        for rec in self:
            rec.street_name = False
            matched_street = self._get_matched_street(rec.street)
            if matched_street:
                rec.street_name = matched_street.group("street")

    @api.depends("street")
    def _compute_street_number(self):
        for rec in self:
            rec.street_number = False
            matched_street = self._get_matched_street(rec.street)
            if matched_street:
                rec.street_number = matched_street.group("number")

    @api.depends("street")
    def _compute_street_box(self):
        for rec in self:
            rec.street_box = False
            matched_street = self._get_matched_street(rec.street)
            if matched_street:
                rec.street_box = matched_street.group("box")

    @api.depends("country_id")
    def _compute_country(self):
        for rec in self:
            rec.country_list = f"cty:m{rec.country_id.code}"

    def get_kind_of_number(self):
        return {
            "nmt:m1": "entity_number",
            "other_id_number": "Other Identification Number",
        }

    def get_member_number(self):
        self.ensure_one()
        for id_number in self.id_numbers:
            if id_number.category_id.code == "member_number":
                return id_number.name
        return None

    # flake8: noqa: B950
    def _get_admin_id_mapping(self):
        """Returns a dictionary of mapping dictionaries where the key is the XBRL fact id and the
        value is its corresponding field, for each type of administrator (legal and natural person)
        """
        return {
            # Administratror : legal person
            "company": {
                "nmt-enum:list1#dim:anlp=#dim:bas=bas:m26#dim:dcl=dcl:m7#dim:part=part:m2#dim:psn=psn:m10": "kind_of_entity_number_list",  # Kind of entity number (list) id_numbers.category_id.code"
                "met:str2#dim:anlp=#dim:bas=bas:m26#dim:part=part:m2#dim:psn=psn:m10#dim:qlt=qlt:m1": "entity_number",  # Kind of entity number (value)  ????? id_numbers.name
                "atc-enum:list1#dim:anlp=#dim:bas=bas:m31#dim:dcl=dcl:m7#dim:part=part:m2#dim:psn=psn:m10": "kind_of_address",  # Kind of address (list)
                "met:str2#dim:anlp=#dim:bas=bas:m31#dim:dcl=dcl:m7#dim:part=part:m2#dim:psn=psn:m10": "kind_of_address",  # Kind of address (other)
                "met:str2#dim:anlp=#dim:bas=bas:m31#dim:ctc=ctc:m1#dim:part=part:m2#dim:psn=psn:m10": "street_name",  # Street name but same field
                "met:str2#dim:anlp=#dim:bas=bas:m31#dim:ctc=ctc:m2#dim:part=part:m2#dim:psn=psn:m10": "street_number",  # Street number but same field
                "met:str2#dim:anlp=#dim:bas=bas:m31#dim:ctc=ctc:m3#dim:part=part:m2#dim:psn=psn:m10": "street_box",  # Street box
                "pcd-enum:list1#dim:anlp=#dim:bas=bas:m31#dim:ctc=ctc:m4#dim:part=part:m2#dim:psn=psn:m10": "zip",  # Postal code and city (list)
                "met:str2#dim:anlp=#dim:bas=bas:m31#dim:ctc=ctc:m4#dim:part=part:m2#dim:psn=psn:m10": "zip",  # Postal code (other)
                "met:str2#dim:anlp=#dim:bas=bas:m31#dim:ctc=ctc:m5#dim:part=part:m2#dim:psn=psn:m10": "city",  # City (other)
                "cty-enum:list1#dim:anlp=#dim:bas=bas:m31#dim:ctc=ctc:m6#dim:part=part:m2#dim:psn=psn:m10": "country_list",  # Country name (list)
            },
            # Administrator : natural person
            "person": {
                "met:str2#dim:afnp=#dim:annp=#dim:bas=bas:m28#dim:dcl=dcl:m27#dim:part=part:m2#dim:psn=psn:m12": "function",  # Profession
                "atc-enum:list1#dim:afnp=#dim:annp=#dim:bas=bas:m31#dim:dcl=dcl:m7#dim:part=part:m2#dim:psn=psn:m12": "kind_of_address",  # Kind of address (list)
                "met:str2#dim:afnp=#dim:annp=#dim:bas=bas:m31#dim:dcl=dcl:m7#dim:part=part:m2#dim:psn=psn:m12": "other_kind_of_address",  # Kind of address (other)
                "met:str2#dim:afnp=#dim:annp=#dim:bas=bas:m31#dim:ctc=ctc:m1#dim:part=part:m2#dim:psn=psn:m12": "street_name",  # Street name
                "met:str2#dim:afnp=#dim:annp=#dim:bas=bas:m31#dim:ctc=ctc:m2#dim:part=part:m2#dim:psn=psn:m12": "street_number",  # Street number
                "met:str2#dim:afnp=#dim:annp=#dim:bas=bas:m31#dim:ctc=ctc:m3#dim:part=part:m2#dim:psn=psn:m12": "street_box",  # Street box
                "pcd-enum:list1#dim:afnp=#dim:annp=#dim:bas=bas:m31#dim:ctc=ctc:m4#dim:part=part:m2#dim:psn=psn:m12": "zip",  # Postal code and city (list)
                "met:str2#dim:afnp=#dim:annp=#dim:bas=bas:m31#dim:ctc=ctc:m4#dim:part=part:m2#dim:psn=psn:m12": "zip",  # Postal code (other)
                "met:str2#dim:afnp=#dim:annp=#dim:bas=bas:m31#dim:ctc=ctc:m5#dim:part=part:m2#dim:psn=psn:m12": "city",  # City (other)
                "cty-enum:list1#dim:afnp=#dim:annp=#dim:bas=bas:m31#dim:ctc=ctc:m6#dim:part=part:m2#dim:psn=psn:m12": "country_list",  # Country name (list)
            },
        }

    # flake8: noqa: B950
    def _get_accountant_id_mapping(self):
        return {
            """Returns a dictionary of mapping dictionaries where the key is the XBRL fact id and the
            value is its corresponding field, for each type of administrator (legal and natural person)
            """
            # Accountant : legal person
            "company": {
                "nmt-enum:list1#dim:aclp=#dim:bas=bas:m26#dim:dcl=dcl:m7#dim:part=part:m2#dim:psn=psn:m13": "kind_of_entity_number_list",  # Kind of entity number (list)
                "met:str2#dim:aclp=#dim:bas=bas:m26#dim:part=part:m2#dim:psn=psn:m13#dim:qlt=qlt:m1": "entity_number",  # Kind of entity number (value)
                "met:str2#dim:aclp=#dim:bas=bas:m34#dim:part=part:m2#dim:psn=psn:m13#dim:qlt=qlt:m5": "member_number",  # Member number
                "atc-enum:list1#dim:aclp=#dim:bas=bas:m31#dim:dcl=dcl:m7#dim:part=part:m2#dim:psn=psn:m13": "kind_of_address",  # Kind of address (list)
                "met:str2#dim:aclp=#dim:bas=bas:m31#dim:dcl=dcl:m7#dim:part=part:m2#dim:psn=psn:m13": "kind_of_address",  # Kind of address (other)
                "met:str2#dim:aclp=#dim:bas=bas:m31#dim:ctc=ctc:m1#dim:part=part:m2#dim:psn=psn:m13": "street_name",  # Street name
                "met:str2#dim:aclp=#dim:bas=bas:m31#dim:ctc=ctc:m2#dim:part=part:m2#dim:psn=psn:m13": "street_number",  # Street number
                "met:str2#dim:aclp=#dim:bas=bas:m31#dim:ctc=ctc:m3#dim:part=part:m2#dim:psn=psn:m13": "street_box",  # Street box
                "pcd-enum:list1#dim:aclp=#dim:bas=bas:m31#dim:ctc=ctc:m4#dim:part=part:m2#dim:psn=psn:m13": "zip",  # Postal code and city (list)
                "met:str2#dim:aclp=#dim:bas=bas:m31#dim:ctc=ctc:m4#dim:part=part:m2#dim:psn=psn:m13": "zip",  # Postal code (other)
                "met:str2#dim:aclp=#dim:bas=bas:m31#dim:ctc=ctc:m5#dim:part=part:m2#dim:psn=psn:m13": "city",  # City (other)
                "cty-enum:list1#dim:aclp=#dim:bas=bas:m31#dim:ctc=ctc:m6#dim:part=part:m2#dim:psn=psn:m13": "country_list",  # Country name (list)
            },
            # Accountant : natural person
            "person": {
                "met:str2#dim:acfn=#dim:acnp=#dim:bas=bas:m28#dim:dcl=dcl:m27#dim:part=part:m2#dim:psn=psn:m15": "function",  # Profession
                "met:str2#dim:acfn=#dim:acnp=#dim:bas=bas:m34#dim:part=part:m2#dim:psn=psn:m15#dim:qlt=qlt:m5": "member_number",  # Member number
                "atc-enum:list1#dim:acfn=#dim:acnp=#dim:bas=bas:m31#dim:dcl=dcl:m7#dim:part=part:m2#dim:psn=psn:m15": "kind_of_address",  # Kind of address (list)
                "met:str2#dim:acfn=#dim:acnp=#dim:bas=bas:m31#dim:dcl=dcl:m7#dim:part=part:m2#dim:psn=psn:m15": "other_kind_of_address",  # Kind of address (other)
                "met:str2#dim:acfn=#dim:acnp=#dim:bas=bas:m31#dim:ctc=ctc:m1#dim:part=part:m2#dim:psn=psn:m15": "street_name",  # Street name
                "met:str2#dim:acfn=#dim:acnp=#dim:bas=bas:m31#dim:ctc=ctc:m2#dim:part=part:m2#dim:psn=psn:m15": "street_number",  # Street number
                "met:str2#dim:acfn=#dim:acnp=#dim:bas=bas:m31#dim:ctc=ctc:m3#dim:part=part:m2#dim:psn=psn:m15": "street_box",  # Street box
                "pcd-enum:list1#dim:acfn=#dim:acnp=#dim:bas=bas:m31#dim:ctc=ctc:m4#dim:part=part:m2#dim:psn=psn:m15": "zip",  # Postal code and city (list)
                "met:str2#dim:acfn=#dim:acnp=#dim:bas=bas:m31#dim:ctc=ctc:m4#dim:part=part:m2#dim:psn=psn:m15": "zip",  # Postal code (other)
                "met:str2#dim:acfn=#dim:acnp=#dim:bas=bas:m31#dim:ctc=ctc:m5#dim:part=part:m2#dim:psn=psn:m15": "city",  # City (other)
                "cty-enum:list1#dim:acfn=#dim:acnp=#dim:bas=bas:m31#dim:ctc=ctc:m6#dim:part=part:m2#dim:psn=psn:m15": "country_list",  # Country name (list)
            },
        }
