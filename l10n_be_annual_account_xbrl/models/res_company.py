# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import re

from odoo import api, fields, models


class ResCompany(models.Model):
    _name = "res.company"
    _inherit = "res.company"

    street_name = fields.Char(compute="_compute_street_name")
    street_number = fields.Char(compute="_compute_street_number")
    street_box = fields.Char(compute="_compute_street_box")
    country_list = fields.Char(compute="_compute_country")

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

    # flake8: noqa: B950
    def get_mapping_dict(self):
        """Returns a mapping dictionary where the key is the XBRL fact id
        and the value is its corresponding field
        """
        return {
            "met:str2#dim:bas=bas:m29#dim:part=part:m2#dim:psn=psn:m1": "name",
            "met:str2#dim:bas=bas:m31#dim:ctc=ctc:m1#dim:part=part:m2#dim:psn=psn:m1": "street_name",
            "met:str2#dim:bas=bas:m31#dim:ctc=ctc:m2#dim:part=part:m2#dim:psn=psn:m1": "street_number",
            "met:str2#dim:bas=bas:m31#dim:ctc=ctc:m3#dim:part=part:m2#dim:psn=psn:m1": "street_box",
            "pcd-enum:list1#dim:bas=bas:m31#dim:ctc=ctc:m4#dim:part=part:m2#dim:psn=psn:m1": "zip",
            "met:str2#dim:bas=bas:m31#dim:ctc=ctc:m4#dim:part=part:m2#dim:psn=psn:m1": "zip",
            "met:str2#dim:bas=bas:m31#dim:ctc=ctc:m5#dim:part=part:m2#dim:psn=psn:m1": "city",
            "cty-enum:list1#dim:bas=bas:m31#dim:ctc=ctc:m6#dim:part=part:m2#dim:psn=psn:m1": "country_list",
            "met:str2#dim:bas=bas:m31#dim:ctc=ctc:m7#dim:part=part:m2#dim:psn=psn:m1": "email",
            "met:str2#dim:bas=bas:m31#dim:ctc=ctc:m8#dim:part=part:m2#dim:psn=psn:m21": "website",
        }

    def _get_matched_street(self, street):
        """Returns a match object containing 3 subgroups (street number, street box
        and street name), if street matches the regular expression
        """
        return re.match(
            r"(?P<number>\d+[a-zA-Z]*)\s*\/*\s*(?P<box>\w*)\s*,\s*(?P<street>.+)",
            street,
        )
