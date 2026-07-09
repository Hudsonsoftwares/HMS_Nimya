# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date

class DoctorDashboard(models.TransientModel):
    _name = 'doctor.dashboard'
    _description = 'Doctor Consultation Dashboard'

    doctor_id = fields.Many2one('hr.employee', string="Doctor", compute='_compute_doctor_info')
    department_id = fields.Many2one('hr.department', string="Department", related='doctor_id.department_id')
    date = fields.Date(string="Date", default=fields.Date.context_today)

    today_patients = fields.Integer(string="Today's Patients", compute='_compute_stats')
    waiting_count = fields.Integer(string="Waiting", compute='_compute_stats')
    consultation_count = fields.Integer(string="In Consultation", compute='_compute_stats')
    completed_count = fields.Integer(string="Completed", compute='_compute_stats')

    queue_ids = fields.Many2many(
        comodel_name='hospital.consultation',
        relation='doctor_dashboard_queue_rel',
        column1='dashboard_id',
        column2='consultation_id',
        string="Today's Queue",
        compute='_compute_queue'
    )

    def _compute_doctor_info(self):
        doctor = self.env['hr.employee'].search([
            ('user_id', '=', self.env.user.id),
            ('name', 'not like', 'Admin')
        ], limit=1)
        if not doctor:
            # Fallback for Administrators: map to the sample doctor 'Dr. John Mathew'
            doctor = self.env['hr.employee'].search([('name', 'like', 'John')], limit=1)
            if not doctor:
                doctor = self.env['hr.employee'].search([], limit=1)
        for rec in self:
            rec.doctor_id = doctor.id if doctor else False

    def _compute_stats(self):
        today = date.today()
        for rec in self:
            doctor = rec.doctor_id
            if doctor:
                all_today = self.env['hospital.consultation'].search([
                    ('doctor_id', '=', doctor.id),
                    ('visit_date', '=', today)
                ])
                rec.today_patients = len(all_today)
                rec.waiting_count = len(all_today.filtered(lambda c: c.state == 'draft'))
                rec.consultation_count = len(all_today.filtered(lambda c: c.state == 'consultation'))
                rec.completed_count = len(all_today.filtered(lambda c: c.state == 'completed'))
            else:
                rec.today_patients = 0
                rec.waiting_count = 0
                rec.consultation_count = 0
                rec.completed_count = 0

    def _compute_queue(self):
        today = date.today()
        for rec in self:
            doctor = rec.doctor_id
            if doctor:
                queue = self.env['hospital.consultation'].search([
                    ('doctor_id', '=', doctor.id),
                    ('visit_date', '=', today),
                    ('state', 'in', ('draft', 'consultation'))
                ], order='token_number asc')
                rec.queue_ids = [(6, 0, queue.ids)]
            else:
                rec.queue_ids = [(6, 0, [])]

    def action_open_consultations(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Today Queue',
            'res_model': 'hospital.consultation',
            'view_mode': 'list,form',
            'target': 'current',
        }

    @api.model
    def action_open_dashboard(self):
        dashboard_rec = self.create({})
        return {
            'name': 'Doctor Dashboard',
            'type': 'ir.actions.act_window',
            'res_model': 'doctor.dashboard',
            'res_id': dashboard_rec.id,
            'view_mode': 'form',
            'target': 'current',
        }
