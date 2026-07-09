# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date

class NurseTriageDashboard(models.TransientModel):
    _name = 'nurse.triage.dashboard'
    _description = 'Nurse Triage Dashboard'

    total_triage = fields.Integer(string="Total Triage Today", compute='_compute_stats')
    pending_triage = fields.Integer(string="Pending Triage", compute='_compute_stats')
    completed_triage = fields.Integer(string="Completed Triage", compute='_compute_stats')
    cancelled_triage = fields.Integer(string="Cancelled Today", compute='_compute_stats')

    pending_queue_ids = fields.Many2many(
        comodel_name='hospital.nurse.triage',
        relation='dashboard_pending_triage_rel',
        column1='dashboard_id',
        column2='triage_id',
        string="Pending Queue",
        compute='_compute_lists'
    )
    completed_queue_ids = fields.Many2many(
        comodel_name='hospital.nurse.triage',
        relation='dashboard_completed_triage_rel',
        column1='dashboard_id',
        column2='triage_id',
        string="Completed Queue",
        compute='_compute_lists'
    )

    def _compute_stats(self):
        Triage = self.env['hospital.nurse.triage']
        today = date.today()
        
        all_today = Triage.search([('visit_date', '=', today)])
        
        for rec in self:
            rec.total_triage = len(all_today)
            rec.pending_triage = len(all_today.filtered(lambda t: t.state == 'draft'))
            rec.completed_triage = len(all_today.filtered(lambda t: t.state == 'completed'))
            rec.cancelled_triage = len(all_today.filtered(lambda t: t.state == 'cancel'))

    def _compute_lists(self):
        Triage = self.env['hospital.nurse.triage']
        today = date.today()
        
        pending = Triage.search([('state', '=', 'draft')], order='id asc')
        completed = Triage.search([('state', '=', 'completed'), ('visit_date', '=', today)], order='write_date desc')
        
        for rec in self:
            rec.pending_queue_ids = [(6, 0, pending.ids)]
            rec.completed_queue_ids = [(6, 0, completed.ids)]

    def action_open_triage(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Patient Queue',
            'res_model': 'hospital.nurse.triage',
            'view_mode': 'list,form',
            'target': 'current',
        }

    @api.model
    def action_open_dashboard(self):
        # Create a transient record for the current session dashboard state
        dashboard_rec = self.create({})
        return {
            'name': 'Triage Dashboard',
            'type': 'ir.actions.act_window',
            'res_model': 'nurse.triage.dashboard',
            'res_id': dashboard_rec.id,
            'view_mode': 'form',
            'target': 'current',
        }
