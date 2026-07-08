# -*- coding: utf-8 -*-
from odoo import models, fields

class ClinicPatientCategory(models.Model):
    _name = 'clinic.patient.category'
    _description = 'Patient Category'
    _order = 'name'

    name = fields.Char(
        string='Category Name',
        required=True,
    )
    active = fields.Boolean(
        default=True,
    )
