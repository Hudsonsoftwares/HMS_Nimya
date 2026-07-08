# -*- coding: utf-8 -*-
from odoo import models, fields

class ClinicInsuranceProvider(models.Model):
    _name = 'clinic.insurance.provider'
    _description = 'Insurance Provider'
    _order = 'name'

    name = fields.Char(
        string='Insurance Provider Name',
        required=True,
    )
    phone = fields.Char(
        string='Phone',
    )
    email = fields.Char(
        string='Email',
    )
    active = fields.Boolean(
        default=True,
    )
