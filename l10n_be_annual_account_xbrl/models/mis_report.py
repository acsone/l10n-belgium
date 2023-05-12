from odoo import fields, models


class MisReport(models.Model):

    _inherit = "mis.report"

    json_data_file = fields.Binary(string="JSON Data File")
    json_data_filename = fields.Char(string="JSON Data Filename")
    json_calc_file = fields.Binary(string="JSON Calculation File")
    json_calc_filename = fields.Char(string="JSON Calculation Filename")
