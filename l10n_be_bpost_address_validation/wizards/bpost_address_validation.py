import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..models.bpost_address import BpostAddress

# Copyright 2023 ACSONE SA/NV


class BpostAddressValidationWizard(models.TransientModel):
    _name = "bpost.address.validation.wizard"
    _description = "Address Validator Using Bpost API"

    partner_id = fields.Many2one("res.partner", readonly=True)
    is_valid = fields.Boolean(compute="_compute_address_validity")
    warning_message = fields.Char(compute="_compute_address_validity")
    suggest_changes = fields.Char(compute="_compute_address_validity")
    bpost_address = fields.Json(compute="_compute_address_validity")

    @api.depends("partner_id", "partner_id.street", "partner_id.city", "partner_id.zip")
    def _compute_address_validity(self):
        for rec in self:
            partner = rec.partner_id
            rec.is_valid = True
            rec.warning_message = ""
            rec.suggest_changes = ""
            rec.bpost_address = {}
            if partner.country_id.code == "BE":
                # This is the JSON that should be sent as input to the API.
                response = self._send_request(partner)
                if response.ok:
                    json = response.json()
                    # Transform the result into a BpostAddress object.
                    rec.bpost_address = BpostAddress(json).toJson()
                    if "error" in rec.bpost_address:
                        rec.is_valid = False
                        if (
                            "street_name" in rec.bpost_address
                            and "postal_code" in rec.bpost_address
                            and "municipality_name" in rec.bpost_address
                            and "street_number" in rec.bpost_address
                        ):
                            rec.warning_message = _(
                                "An error has been detected in the given address. "
                                + "Would you like to keep the suggest change ?"
                            )
                            rec.suggest_changes = self._format_suggest_changes(
                                rec)
                        else:
                            rec.warning_message = _(
                                "The given address is not complete or the address cannot be found."
                            )
                else:
                    raise UserError(
                        _("An error occurred when fetching data from bpost API.")
                    )

    def _format_suggest_changes(self, rec):
        return "{} {} {}, {}".format(
            rec.bpost_address["street_name"],
            rec.bpost_address["street_number"],
            rec.bpost_address["postal_code"],
            rec.bpost_address["municipality_name"],
        )


    def _send_request(self, partner):
        playload = {
            "ValidateAddressesRequest": {
                "AddressToValidateList": {
                    "AddressToValidate": [
                        {
                            "@id": "1",
                            "PostalAddress": {
                                "DeliveryPointLocation": {
                                    "UnstructuredDeliveryPointLocation": partner.street
                                },
                                "PostalCodeMunicipality": {
                                    "UnstructuredPostalCodeMunicipality": partner.zip
                                    + " "
                                    + partner.city
                                },
                            },
                        }
                    ]
                },
                "ValidateAddressOptions": {
                    "IncludeFormatting": "true",
                    "IncludeSuggestions": "true",
                    "IncludeSubmittedAddress": "true",
                    "IncludeListOfBoxes": "true",
                    "IncludeNumberOfBoxes": "true",
                    "IncludeDefaultGeoLocation": "true",
                    "IncludeDefaultGeoLocationForBoxes": "true",
                },
            }
        }
        response = requests.post(
            "https://webservices-pub.bpost.be/ws/"
            + "ExternalMailingAddressProofingCSREST_v1/address/validateAddresses",
            json=playload,
            timeout=10,
            headers={"content-type": "application/json"},
        )

        return response

    def apply_changes(self):
        for rec in self:
            if (
                "street_name" in rec.bpost_address
                and "postal_code" in rec.bpost_address
                and "municipality_name" in rec.bpost_address
                and "street_number" in rec.bpost_address
            ):
                rec.is_valid = True
                partner = rec.partner_id
                partner.street = (
                    rec.bpost_address["street_name"]
                    + " "
                    + rec.bpost_address["street_number"]
                )
                partner.city = rec.bpost_address["municipality_name"]
                partner.zip = rec.bpost_address["postal_code"]
                rec.suggest_changes = ""
