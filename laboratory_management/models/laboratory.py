from odoo import models, fields


class HospitalLaboratory(models.Model):
    _name = "hospital.laboratory"
    _description = "Hospital Laboratory"

    name = fields.Char(string="Lab Request Number")