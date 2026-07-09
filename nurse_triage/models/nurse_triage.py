# -*- coding: utf-8 -*-
from odoo import models, fields, api

class HospitalNurseTriage(models.Model):
    _name = "hospital.nurse.triage"
    _description = "Hospital Nurse Triage"
    _order = "id desc"

    name = fields.Char(string="Triage Number", required=True, copy=False, readonly=True, default='/')
    patient_id = fields.Many2one(comodel_name='clinic.patient', string="Patient", required=True)
    appointment_id = fields.Many2one(comodel_name='hospital.appointment', string="Appointment", required=True)
    doctor_id = fields.Many2one(comodel_name='hr.employee', string="Doctor", related='appointment_id.doctor_id', store=True, readonly=True)
    
    visit_date = fields.Date(string="Visit Date", default=fields.Date.context_today)
    
    # Vitals
    temperature = fields.Float(string="Temperature (°C)")
    systolic_bp = fields.Integer(string="Systolic BP (mmHg)")
    diastolic_bp = fields.Integer(string="Diastolic BP (mmHg)")
    pulse_rate = fields.Integer(string="Pulse Rate (bpm)")
    respiratory_rate = fields.Integer(string="Respiratory Rate (bpm)")
    spo2 = fields.Integer(string="SpO2 (%)")
    
    # Physical Measurements
    weight = fields.Float(string="Weight (kg)")
    height = fields.Float(string="Height (cm)")
    bmi = fields.Float(string="BMI", compute="_compute_bmi", store=True)
    
    nursing_notes = fields.Text(string="Nursing Notes / Complaint")
    
    state = fields.Selection([
        ('draft', 'Pending Triage'),
        ('completed', 'Triage Completed'),
        ('cancel', 'Cancelled'),
    ], string="Status", default='draft', required=True)
    sent_to_doctor = fields.Boolean(string="Sent to Doctor", default=False, copy=False)

    @api.depends('weight', 'height')
    def _compute_bmi(self):
        for rec in self:
            if rec.weight > 0 and rec.height > 0:
                # height in meters
                height_m = rec.height / 100.0
                rec.bmi = rec.weight / (height_m * height_m)
            else:
                rec.bmi = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('hospital.nurse.triage') or '/'
        return super(HospitalNurseTriage, self).create(vals_list)

    def action_complete(self):
        for rec in self:
            rec.state = 'completed'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def action_send_to_doctor(self):
        for rec in self:
            if not rec.sent_to_doctor:
                self.env['hospital.consultation'].create({
                    'patient_id': rec.patient_id.id,
                    'appointment_id': rec.appointment_id.id,
                    'triage_id': rec.id,
                    'state': 'draft',
                    'temperature': rec.temperature,
                    'systolic_bp': rec.systolic_bp,
                    'diastolic_bp': rec.diastolic_bp,
                    'pulse_rate': rec.pulse_rate,
                    'respiratory_rate': rec.respiratory_rate,
                    'spo2': rec.spo2,
                    'weight': rec.weight,
                    'height': rec.height,
                    'bmi': rec.bmi,
                })
                rec.sent_to_doctor = True