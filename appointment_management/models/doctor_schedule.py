# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class DoctorSchedule(models.Model):
    _name = 'doctor.schedule'
    _description = 'Doctor Working Schedule'
    _rec_name = 'doctor_id'

    doctor_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Doctor',
        required=True,
    )
    
    # Working Days
    mon = fields.Boolean(string='Monday', default=True)
    tue = fields.Boolean(string='Tuesday', default=True)
    wed = fields.Boolean(string='Wednesday', default=True)
    thu = fields.Boolean(string='Thursday', default=True)
    fri = fields.Boolean(string='Friday', default=True)
    sat = fields.Boolean(string='Saturday', default=False)
    sun = fields.Boolean(string='Sunday', default=False)

    # Working Hours
    work_start_time = fields.Float(string='Working Hours Start', default=9.0)
    work_end_time = fields.Float(string='Working Hours End', default=17.0)
    
    # Break Time
    break_start_time = fields.Float(string='Break Start', default=13.0)
    break_end_time = fields.Float(string='Break End', default=14.0)

    # Patient Limits
    max_patients = fields.Integer(string='Maximum Patients Per Day', default=25)
    consultation_duration = fields.Integer(string='Consultation Duration (mins)', default=15)
    consultation_fees = fields.Float(string='Consultation Fees', default=0.0)

    _sql_constraints = [
        ('doctor_uniq', 'unique(doctor_id)', 'A working schedule already exists for this doctor!')
    ]

    @api.constrains('work_start_time', 'work_end_time', 'break_start_time', 'break_end_time')
    def _check_times(self):
        for rec in self:
            if rec.work_start_time >= rec.work_end_time:
                raise ValidationError("Work start time must be before work end time.")
            if rec.break_start_time >= rec.break_end_time:
                raise ValidationError("Break start time must be before break end time.")
            if rec.break_start_time < rec.work_start_time or rec.break_end_time > rec.work_end_time:
                raise ValidationError("Break times must fall within working hours.")


class DoctorUnavailability(models.Model):
    _name = 'doctor.unavailability'
    _description = 'Doctor Leave / Unavailability'
    _rec_name = 'doctor_id'

    doctor_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Doctor',
        required=True,
    )
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    reason = fields.Char(string='Reason')

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.start_date > rec.end_date:
                raise ValidationError("The start date of unavailability must be before or equal to the end date.")
