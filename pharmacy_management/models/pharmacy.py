from odoo import models, fields


class HospitalPharmacy(models.Model):
    _name = "hospital.pharmacy"
    _description = "Hospital Pharmacy"

    name = fields.Char(string="Prescription Number")