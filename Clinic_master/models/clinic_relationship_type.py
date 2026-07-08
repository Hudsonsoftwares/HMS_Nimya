# -*- coding: utf-8 -*-
from odoo import models, fields

class ClinicRelationshipType(models.Model):
    _name = 'clinic.relationship.type'
    _description = 'Relationship Type'

    name = fields.Char(
        string='Relationship Type',
        required=True,
    )
