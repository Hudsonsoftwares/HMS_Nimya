# -*- coding: utf-8 -*-
from datetime import datetime, time, timedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HospitalAppointment(models.Model):
    _name = 'hospital.appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Hospital Appointment'
    _order = 'appointment_date desc, appointment_time desc, id desc'

    @api.model
    def _default_doctor_id(self):
        # Default to the hr.employee record linked to current user
        return self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)

    name = fields.Char(
        string='Appointment ID',
        required=True,
        readonly=True,
        default='/',
        copy=False,
        tracking=True,
    )
    
    # Patient Information (Auto-loaded via related fields)
    patient_id = fields.Many2one(
        comodel_name='clinic.patient',
        string='Patient',
        required=True,
        tracking=True,
        ondelete='restrict',
    )
    patient_id_ref = fields.Char(
        string='Patient ID',
        related='patient_id.patient_id',
        readonly=True,
        store=True,
    )
    patient_name = fields.Char(
        string='Patient Name',
        related='patient_id.name',
        readonly=True,
    )
    patient_age = fields.Integer(
        string='Age',
        related='patient_id.age',
        readonly=True,
    )
    patient_gender = fields.Selection(
        string='Gender',
        related='patient_id.gender',
        readonly=True,
    )
    patient_dob = fields.Date(
        string='Date of Birth',
        related='patient_id.date_of_birth',
        readonly=True,
    )
    patient_blood_group = fields.Selection(
        string='Blood Group',
        related='patient_id.blood_group',
        readonly=True,
    )
    patient_phone = fields.Char(
        string='Phone Number',
        related='patient_id.mobile',
        readonly=True,
    )
    
    # Insurance Information (Auto-loaded via related fields)
    has_insurance = fields.Boolean(
        string='Insurance Status',
        related='patient_id.has_insurance',
        readonly=True,
    )
    insurance_provider_id = fields.Many2one(
        comodel_name='clinic.insurance.provider',
        string='Insurance Provider',
        related='patient_id.insurance_provider_id',
        readonly=True,
    )
    policy_number = fields.Char(
        string='Policy Number',
        related='patient_id.policy_number',
        readonly=True,
    )
    insurance_expiry_date = fields.Date(
        string='Insurance Expiry',
        related='patient_id.insurance_expiry_date',
        readonly=True,
    )
    
    # Visit Specifications
    previous_visit_date = fields.Date(
        string='Previous Visit Date',
        compute='_compute_previous_visit_date',
        store=True,
    )
    doctor_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Doctor',
        required=True,
        tracking=True,
        default=_default_doctor_id,
    )
    department_id = fields.Many2one(
        comodel_name='hr.department',
        string='Department',
        related='doctor_id.department_id',
        store=True,
        readonly=True,
    )
    appointment_date = fields.Date(
        string='Appointment Date',
        default=fields.Date.today,
        required=True,
        tracking=True,
    )
    appointment_time = fields.Float(
        string='Appointment Time',
        default=9.0,
        required=True,
        tracking=True,
    )
    visit_type = fields.Selection(
        selection=[
            ('new', 'New Visit'),
            ('followup', 'Follow-up'),
            ('emergency', 'Emergency'),
            ('walkin', 'Walk-in'),
        ],
        string='Visit Type',
        default='new',
        required=True,
        tracking=True,
    )
    priority = fields.Selection(
        selection=[
            ('normal', 'Normal'),
            ('urgent', 'Urgent'),
            ('emergency', 'Emergency'),
        ],
        string='Priority',
        default='normal',
        required=True,
        tracking=True,
    )
    payment_type = fields.Selection(
        selection=[
            ('cash', 'Cash'),
            ('insurance', 'Insurance'),
            ('card', 'Card'),
        ],
        string='Payment Type',
        default='cash',
        required=True,
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('waiting', 'Waiting'),
            ('consultation', 'In Consultation'),
            ('done', 'Completed'),
            ('cancel', 'Cancelled'),
            ('noshow', 'No Show'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
    )
    
    # Token & Queue tracking
    token_number = fields.Integer(
        string='Token Number',
        readonly=True,
        copy=False,
        tracking=True,
    )
    is_on_hold = fields.Boolean(
        string='On Hold',
        default=False,
        tracking=True,
    )
    arrival_time = fields.Datetime(
        string='Arrival Time',
        readonly=True,
    )
    consultation_start_time = fields.Datetime(
        string='Consultation Start Time',
        readonly=True,
    )
    waiting_time_str = fields.Char(
        string='Waiting Time',
        compute='_compute_waiting_time_str',
    )
    estimated_consultation_time = fields.Datetime(
        string='Est. Consultation Time',
        compute='_compute_est_consultation_time',
    )
    
    # Integrations
    insurance_case_id = fields.Many2one(
        comodel_name='insurance.case',
        string='Insurance Case',
        domain="[('patient_id', '=', patient_id), ('verification_status', '=', 'verified')]",
        readonly=False,
    )
    insurance_summary = fields.Text(
        string='Insurance Summary',
        related='insurance_case_id.verification_summary',
        readonly=True,
    )
    appointment_datetime = fields.Datetime(
        string='Appointment Date/Time',
        compute='_compute_appointment_datetime',
        store=True,
    )
    consultation_fees = fields.Float(
        string='Consultation Fees',
        compute='_compute_consultation_fees',
        store=True,
        readonly=False,
        tracking=True,
    )

    @api.depends('doctor_id')
    def _compute_consultation_fees(self):
        for rec in self:
            if rec.doctor_id:
                schedule = self.env['doctor.schedule'].search([('doctor_id', '=', rec.doctor_id.id)], limit=1)
                rec.consultation_fees = schedule.consultation_fees if schedule else 0.0
            else:
                rec.consultation_fees = 0.0
    
    # Notes/Clinical Info
    chief_complaint = fields.Char(string='Chief Complaint')
    symptoms = fields.Text(string='Symptoms')
    notes = fields.Text(string='Notes')
    
    # Audit info
    created_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Created By',
        default=lambda self: self.env.user,
        readonly=True,
    )
    created_date = fields.Datetime(
        string='Created Date',
        default=fields.Datetime.now,
        readonly=True,
    )

    @api.depends('appointment_date', 'appointment_time')
    def _compute_appointment_datetime(self):
        for rec in self:
            if rec.appointment_date:
                hours = int(rec.appointment_time)
                minutes = int(round((rec.appointment_time - hours) * 60))
                dt_naive = datetime.combine(rec.appointment_date, time(hours, minutes))
                rec.appointment_datetime = dt_naive
            else:
                rec.appointment_datetime = False

    @api.depends('patient_id', 'appointment_date')
    def _compute_previous_visit_date(self):
        for rec in self:
            if rec.patient_id and rec.appointment_date:
                last_appt = self.search([
                    ('patient_id', '=', rec.patient_id.id),
                    ('state', '=', 'done'),
                    ('appointment_date', '<', rec.appointment_date),
                    ('id', '!=', rec.id or 0)
                ], order='appointment_date desc', limit=1)
                rec.previous_visit_date = last_appt.appointment_date if last_appt else False
            else:
                rec.previous_visit_date = False

    @api.depends('arrival_time', 'consultation_start_time', 'state')
    def _compute_waiting_time_str(self):
        for rec in self:
            if rec.arrival_time:
                end_time = rec.consultation_start_time or fields.Datetime.now()
                diff = end_time - rec.arrival_time
                diff_mins = int(diff.total_seconds() / 60)
                rec.waiting_time_str = f"{diff_mins} mins"
            else:
                rec.waiting_time_str = "0 mins"

    @api.depends('doctor_id', 'appointment_date', 'state', 'token_number')
    def _compute_est_consultation_time(self):
        for rec in self:
            if rec.state in ('draft', 'cancel', 'done', 'noshow') or not rec.doctor_id or not rec.appointment_date:
                rec.estimated_consultation_time = False
                continue
            
            schedule = self.env['doctor.schedule'].search([('doctor_id', '=', rec.doctor_id.id)], limit=1)
            duration = schedule.consultation_duration or 15
            
            # Count how many patients are waiting ahead of this patient today
            domain = [
                ('doctor_id', '=', rec.doctor_id.id),
                ('appointment_date', '=', rec.appointment_date),
                ('state', '=', 'waiting'),
                ('token_number', '<', rec.token_number or 999999),
            ]
            patients_ahead = self.search_count(domain)
            
            # Include patient currently in consultation
            in_consult = self.search_count([
                ('doctor_id', '=', rec.doctor_id.id),
                ('appointment_date', '=', rec.appointment_date),
                ('state', '=', 'consultation')
            ])
            
            total_wait_mins = (patients_ahead + in_consult) * duration
            rec.estimated_consultation_time = fields.Datetime.now() + timedelta(minutes=total_wait_mins)

    # Double Booking Constraints
    @api.constrains('doctor_id', 'appointment_date', 'appointment_time')
    def _check_doctor_availability(self):
        for rec in self:
            if not rec.doctor_id or not rec.appointment_date:
                continue
                
            # 1. Check working days (convert weekday to name: mon, tue...)
            weekday_num = rec.appointment_date.weekday()
            weekdays = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
            weekday_name = weekdays[weekday_num]
            
            schedule = self.env['doctor.schedule'].search([('doctor_id', '=', rec.doctor_id.id)], limit=1)
            if not schedule:
                raise ValidationError(f"No working schedule found for Doctor {rec.doctor_id.name}!")
                
            if not getattr(schedule, weekday_name):
                raise ValidationError(f"Doctor {rec.doctor_id.name} does not work on {rec.appointment_date.strftime('%A')}s!")
                
            # 2. Check unavailability / leaves
            leave = self.env['doctor.unavailability'].search([
                ('doctor_id', '=', rec.doctor_id.id),
                ('start_date', '<=', rec.appointment_date),
                ('end_date', '>=', rec.appointment_date)
            ], limit=1)
            if leave:
                raise ValidationError(f"Doctor {rec.doctor_id.name} is unavailable on {rec.appointment_date} due to: {leave.reason or 'Leave'}.")
                
            # 3. Check daily maximum patients
            daily_count = self.search_count([
                ('doctor_id', '=', rec.doctor_id.id),
                ('appointment_date', '=', rec.appointment_date),
                ('id', '!=', rec.id or 0),
                ('state', 'not in', ['cancel', 'noshow'])
            ])
            if daily_count >= schedule.max_patients:
                raise ValidationError(f"Doctor {rec.doctor_id.name} has reached the maximum patient limit of {schedule.max_patients} for {rec.appointment_date}!")
                
            # 4. Check time overlap
            duration_hours = (schedule.consultation_duration or 15) / 60.0
            
            # Check if appointment time is within working hours
            if rec.appointment_time < schedule.work_start_time or (rec.appointment_time + duration_hours) > schedule.work_end_time:
                raise ValidationError(f"Appointment time must be within working hours: {self._float_time_to_str(schedule.work_start_time)} to {self._float_time_to_str(schedule.work_end_time)}.")
                
            # Check if appointment time falls within break hours
            if rec.appointment_time >= schedule.break_start_time and rec.appointment_time < schedule.break_end_time:
                raise ValidationError(f"Appointment time falls during the doctor's break: {self._float_time_to_str(schedule.break_start_time)} to {self._float_time_to_str(schedule.break_end_time)}.")

            # Check if there is an overlapping appointment
            overlapping = self.search([
                ('doctor_id', '=', rec.doctor_id.id),
                ('appointment_date', '=', rec.appointment_date),
                ('id', '!=', rec.id or 0),
                ('state', 'not in', ['cancel', 'noshow']),
                ('appointment_time', '>=', rec.appointment_time - duration_hours + 0.001),
                ('appointment_time', '<=', rec.appointment_time + duration_hours - 0.001)
            ], limit=1)
            if overlapping:
                overlap_time_str = self._float_time_to_str(overlapping.appointment_time)
                raise ValidationError(f"This time slot overlaps with another appointment at {overlap_time_str} for Doctor {rec.doctor_id.name}!")

    def _float_time_to_str(self, float_time):
        hours = int(float_time)
        minutes = int(round((float_time - hours) * 60))
        return f"{hours:02d}:{minutes:02d}"

    # Token recalculation helpers
    def _get_next_token(self, doctor_id, appt_date):
        domain = [
            ('doctor_id', '=', doctor_id),
            ('appointment_date', '=', appt_date),
            ('token_number', '>', 0)
        ]
        max_token_appt = self.search(domain, order='token_number desc', limit=1)
        return (max_token_appt.token_number or 0) + 1

    # Insurance Case Auto-Integration
    def _create_insurance_case(self):
        for rec in self:
            if rec.payment_type == 'insurance' and rec.has_insurance and not rec.insurance_case_id:
                provider = rec.insurance_provider_id
                method = provider.verification_method if provider else False
                requires_pre_auth = provider.requires_pre_auth if provider else False
                
                case = self.env['insurance.case'].create({
                    'patient_id': rec.patient_id.id,
                    'verification_status': 'draft',
                    'visit_date': rec.appointment_date,
                    'verification_method': method,
                    'requires_pre_auth': requires_pre_auth,
                })
                rec.insurance_case_id = case.id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('hospital.appointment') or '/'
            
            # Generate token number automatically if not set
            if not vals.get('token_number') and vals.get('doctor_id') and vals.get('appointment_date'):
                vals['token_number'] = self._get_next_token(vals['doctor_id'], vals['appointment_date'])
        
        records = super(HospitalAppointment, self).create(vals_list)
        # Create insurance case if confirmed during create
        for rec in records:
            if rec.state in ('confirmed', 'waiting'):
                rec._create_insurance_case()
        return records

    def write(self, vals):
        # Cache doctor and date to check if token needs recalculation
        check_recalc = 'doctor_id' in vals or 'appointment_date' in vals
        
        res = super(HospitalAppointment, self).write(vals)
        
        if check_recalc:
            for rec in self:
                rec.token_number = rec._get_next_token(rec.doctor_id.id, rec.appointment_date)
        
        # Check if state shifted to confirmed/waiting or payment type changed to insurance
        if 'state' in vals or 'payment_type' in vals:
            for rec in self:
                if rec.state in ('confirmed', 'waiting'):
                    rec._create_insurance_case()
        return res

    # Queue Actions
    def action_confirm(self):
        for rec in self:
            if rec.state == 'draft':
                rec.write({'state': 'confirmed'})

    def action_arrive(self):
        for rec in self:
            if rec.state in ('draft', 'confirmed'):
                rec.write({
                    'state': 'waiting',
                    'arrival_time': fields.Datetime.now()
                })

    def action_start_consultation(self):
        for rec in self:
            if rec.state == 'waiting':
                rec.write({
                    'state': 'consultation',
                    'consultation_start_time': fields.Datetime.now()
                })

    def action_complete(self):
        for rec in self:
            if rec.state == 'consultation':
                rec.write({'state': 'done'})

    def action_no_show(self):
        for rec in self:
            if rec.state in ('draft', 'confirmed', 'waiting'):
                rec.write({'state': 'noshow'})

    def action_cancel(self):
        for rec in self:
            rec.write({'state': 'cancel'})

    def action_draft(self):
        for rec in self:
            rec.write({
                'state': 'draft',
                'arrival_time': False,
                'consultation_start_time': False,
                'is_on_hold': False,
            })

    def action_hold(self):
        for rec in self:
            rec.write({'is_on_hold': True})

    def action_resume(self):
        for rec in self:
            rec.write({'is_on_hold': False})

    def action_call_next(self):
        today = fields.Date.today()
        for rec in self:
            next_appt = self.search([
                ('doctor_id', '=', rec.doctor_id.id),
                ('appointment_date', '=', today),
                ('state', '=', 'waiting'),
                ('is_on_hold', '=', False),
            ], order='token_number asc', limit=1)
            
            if next_appt:
                # Complete the current active consultation for this doctor if exists
                active_consultations = self.search([
                    ('doctor_id', '=', rec.doctor_id.id),
                    ('appointment_date', '=', today),
                    ('state', '=', 'consultation')
                ])
                for ac in active_consultations:
                    ac.action_complete()
                
                next_appt.action_start_consultation()

    def action_view_patient_profile(self):
        self.ensure_one()
        return {
            'name': 'Patient Profile',
            'type': 'ir.actions.act_window',
            'res_model': 'clinic.patient',
            'res_id': self.patient_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_insurance_case(self):
        self.ensure_one()
        return {
            'name': 'Insurance Case',
            'type': 'ir.actions.act_window',
            'res_model': 'insurance.case',
            'res_id': self.insurance_case_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.onchange('patient_id', 'payment_type')
    def _onchange_patient_id_insurance(self):
        if self.patient_id and self.payment_type == 'insurance':
            verified_case = self.env['insurance.case'].search([
                ('patient_id', '=', self.patient_id.id),
                ('verification_status', '=', 'verified')
            ], order='id desc', limit=1)
            if verified_case:
                self.insurance_case_id = verified_case.id
            else:
                self.insurance_case_id = False
        else:
            self.insurance_case_id = False
