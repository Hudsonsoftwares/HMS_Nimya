# -*- coding: utf-8 -*-
from odoo import models, fields

class ClinicPatientDocument(models.Model):
    _name = 'clinic.patient.document'
    _description = 'Patient Document'
    _order = 'date_uploaded desc, id desc'

    name = fields.Char(
        string='Document Name',
        required=True,
    )
    patient_id = fields.Many2one(
        comodel_name='clinic.patient',
        string='Patient',
        required=True,
        ondelete='cascade',
    )
    document = fields.Binary(
        string='Document File',
        required=True,
    )
    filename = fields.Char(
        string='Filename',
    )
    date_uploaded = fields.Date(
        string='Date Uploaded',
        readonly=True,
        default=fields.Date.today,
    )
    description = fields.Text(
        string='Description',
    )
