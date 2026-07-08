# -*- coding: utf-8 -*-
from odoo import models, fields

class ClinicBloodGroup(models.Model):
    _name = 'clinic.blood.group'
    _description = 'Blood Group'
    _order = 'id'

    name = fields.Char(
        string='Blood Group',
        required=True,
    )
