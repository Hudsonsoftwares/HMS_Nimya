# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ClinicPatient(models.Model):
    _inherit = 'clinic.patient'

    insurance_document_ids = fields.One2many(
        comodel_name='patient.insurance.document',
        inverse_name='patient_id',
        string='Insurance Documents',
    )

    @api.model_create_multi
    def create(self, vals_list):
        patients = super(ClinicPatient, self).create(vals_list)
        for patient in patients:
            if patient.has_insurance:
                method = False
                requires_pre_auth = False
                if patient.insurance_provider_id:
                    method = patient.insurance_provider_id.verification_method
                    requires_pre_auth = patient.insurance_provider_id.requires_pre_auth
                
                self.env['insurance.case'].create({
                    'patient_id': patient.id,
                    'verification_status': 'draft',
                    'visit_date': fields.Date.context_today(self),
                    'verification_method': method,
                    'requires_pre_auth': requires_pre_auth,
                })
        return patients

    def write(self, vals):
        res = super(ClinicPatient, self).write(vals)
        if 'has_insurance' in vals and vals['has_insurance']:
            for patient in self:
                existing_case = self.env['insurance.case'].search([
                    ('patient_id', '=', patient.id),
                    ('verification_status', 'in', ['draft', 'pending'])
                ], limit=1)
                if not existing_case:
                    method = False
                    requires_pre_auth = False
                    if patient.insurance_provider_id:
                        method = patient.insurance_provider_id.verification_method
                        requires_pre_auth = patient.insurance_provider_id.requires_pre_auth
                    
                    self.env['insurance.case'].create({
                        'patient_id': patient.id,
                        'verification_status': 'draft',
                        'visit_date': fields.Date.context_today(self),
                        'verification_method': method,
                        'requires_pre_auth': requires_pre_auth,
                    })
        return res
