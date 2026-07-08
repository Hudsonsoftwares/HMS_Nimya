# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date, datetime

class AppointmentDashboard(models.TransientModel):
    _name = 'appointment.dashboard'
    _description = 'Appointment Management Dashboard'

    # KPIs
    today_appointments = fields.Integer(string="Today's Appointments", compute='_compute_kpi_stats')
    waiting_patients = fields.Integer(string="Waiting Patients", compute='_compute_kpi_stats')
    consultation_patients = fields.Integer(string="Patients in Consultation", compute='_compute_kpi_stats')
    completed_appointments = fields.Integer(string="Completed Appointments", compute='_compute_kpi_stats')
    cancelled_appointments = fields.Integer(string="Cancelled/No-Show", compute='_compute_kpi_stats')
    available_doctors = fields.Integer(string="Doctors Available", compute='_compute_kpi_stats')
    avg_waiting_time = fields.Char(string="Average Waiting Time", compute='_compute_kpi_stats')
    followup_appointments = fields.Integer(string="Follow-up Appointments", compute='_compute_kpi_stats')
    emergency_appointments = fields.Integer(string="Emergency Appointments", compute='_compute_kpi_stats')

    # Tables/Lists
    today_queue_ids = fields.Many2many(
        comodel_name='hospital.appointment',
        relation='dashboard_today_queue_rel',
        column1='dashboard_id',
        column2='appointment_id',
        string="Today's Queue",
        compute='_compute_lists'
    )
    upcoming_appointment_ids = fields.Many2many(
        comodel_name='hospital.appointment',
        relation='dashboard_upcoming_appt_rel',
        column1='dashboard_id',
        column2='appointment_id',
        string="Upcoming Appointments",
        compute='_compute_lists'
    )
    recent_appointment_ids = fields.Many2many(
        comodel_name='hospital.appointment',
        relation='dashboard_recent_appt_rel',
        column1='dashboard_id',
        column2='appointment_id',
        string="Recent Appointments",
        compute='_compute_lists'
    )

    def _compute_kpi_stats(self):
        today = date.today()
        Appointment = self.env['hospital.appointment']
        
        # Today's appointments count
        today_appts = Appointment.search([('appointment_date', '=', today)])
        
        # Doctors working today
        weekday = today.strftime('%a').lower()  # mon, tue, wed, etc.
        working_schedules = self.env['doctor.schedule'].search([(weekday, '=', True)])
        active_leaves = self.env['doctor.unavailability'].search([
            ('start_date', '<=', today),
            ('end_date', '>=', today)
        ])
        working_doctor_ids = working_schedules.mapped('doctor_id').ids
        on_leave_doctor_ids = active_leaves.mapped('doctor_id').ids
        avail_doctors_count = len(set(working_doctor_ids) - set(on_leave_doctor_ids))

        # Calculate average waiting time
        completed_today = today_appts.filtered(lambda a: a.state == 'done' and a.arrival_time and a.consultation_start_time)
        avg_wait = "0 mins"
        if completed_today:
            total_wait_secs = 0
            for appt in completed_today:
                diff = appt.consultation_start_time - appt.arrival_time
                total_wait_secs += diff.total_seconds()
            avg_mins = int((total_wait_secs / len(completed_today)) / 60)
            avg_wait = f"{avg_mins} mins"
        else:
            avg_wait = "10 mins"  # Default fallback if no appointments completed today

        for rec in self:
            rec.today_appointments = len(today_appts)
            rec.waiting_patients = len(today_appts.filtered(lambda a: a.state == 'waiting'))
            rec.consultation_patients = len(today_appts.filtered(lambda a: a.state == 'consultation'))
            rec.completed_appointments = len(today_appts.filtered(lambda a: a.state == 'done'))
            rec.cancelled_appointments = len(today_appts.filtered(lambda a: a.state in ('cancel', 'noshow')))
            rec.available_doctors = avail_doctors_count
            rec.avg_waiting_time = avg_wait
            rec.followup_appointments = len(today_appts.filtered(lambda a: a.visit_type == 'followup'))
            rec.emergency_appointments = len(today_appts.filtered(lambda a: a.visit_type == 'emergency'))

    def _compute_lists(self):
        today = date.today()
        Appointment = self.env['hospital.appointment']
        
        today_queue = Appointment.search([
            ('appointment_date', '=', today),
            ('state', 'in', ['waiting', 'consultation'])
        ], order='token_number asc')
        
        upcoming = Appointment.search([
            ('appointment_date', '>=', today),
            ('state', 'in', ['draft', 'confirmed'])
        ], order='appointment_date asc, appointment_time asc', limit=10)
        
        recent = Appointment.search([
            ('state', 'in', ['done', 'cancel', 'noshow'])
        ], order='write_date desc', limit=10)

        for rec in self:
            rec.today_queue_ids = [(6, 0, today_queue.ids)]
            rec.upcoming_appointment_ids = [(6, 0, upcoming.ids)]
            rec.recent_appointment_ids = [(6, 0, recent.ids)]
            
    def action_open_appointments(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Appointments',
            'res_model': 'hospital.appointment',
            'view_mode': 'list,form',
            'target': 'current',
        }

    @api.model
    def action_open_dashboard(self):
        # Create a transient record for the current session dashboard state
        dashboard_rec = self.create({})
        return {
            'name': 'Clinic Dashboard',
            'type': 'ir.actions.act_window',
            'res_model': 'appointment.dashboard',
            'res_id': dashboard_rec.id,
            'view_mode': 'form',
            'target': 'current',
        }
