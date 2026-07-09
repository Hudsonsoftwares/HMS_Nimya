# -*- coding: utf-8 -*-
from odoo import models, fields, api

class InsuranceDashboard(models.TransientModel):
    _name = 'insurance.dashboard'
    _description = 'Insurance Case Verification Dashboard'

    # KPIs
    total_cases = fields.Integer(string="Total Cases", compute='_compute_stats')
    draft_cases = fields.Integer(string="Draft Cases", compute='_compute_stats')
    pending_cases = fields.Integer(string="Pending Cases", compute='_compute_stats')
    verified_cases = fields.Integer(string="Verified Cases", compute='_compute_stats')
    rejected_cases = fields.Integer(string="Rejected Cases", compute='_compute_stats')
    expired_cases = fields.Integer(string="Expired Cases", compute='_compute_stats')
    
    total_preauths = fields.Integer(string="Total Pre-Auths", compute='_compute_stats')
    pending_preauths = fields.Integer(string="Pending Pre-Auths", compute='_compute_stats')
    approved_preauths = fields.Integer(string="Approved Pre-Auths", compute='_compute_stats')
    
    total_providers = fields.Integer(string="Total Providers", compute='_compute_stats')

    # Lists
    pending_case_ids = fields.Many2many(
        comodel_name='insurance.case',
        relation='dashboard_pending_cases_rel',
        column1='dashboard_id',
        column2='case_id',
        string="Cases Pending Verification",
        compute='_compute_lists'
    )
    recent_case_ids = fields.Many2many(
        comodel_name='insurance.case',
        relation='dashboard_recent_cases_rel',
        column1='dashboard_id',
        column2='case_id',
        string="Recent Cases",
        compute='_compute_lists'
    )
    pending_preauth_ids = fields.Many2many(
        comodel_name='insurance.preauthorization',
        relation='dashboard_pending_preauth_rel',
        column1='dashboard_id',
        column2='preauth_id',
        string="Pending Pre-Authorizations",
        compute='_compute_lists'
    )

    def _compute_stats(self):
        Case = self.env['insurance.case']
        Preauth = self.env['insurance.preauthorization']
        Provider = self.env['clinic.insurance.provider']
        
        all_cases = Case.search([])
        all_preauths = Preauth.search([])
        all_providers = Provider.search([])
        
        for rec in self:
            rec.total_cases = len(all_cases)
            rec.draft_cases = len(all_cases.filtered(lambda c: c.verification_status == 'draft'))
            rec.pending_cases = len(all_cases.filtered(lambda c: c.verification_status == 'pending'))
            rec.verified_cases = len(all_cases.filtered(lambda c: c.verification_status == 'verified'))
            rec.rejected_cases = len(all_cases.filtered(lambda c: c.verification_status == 'rejected'))
            rec.expired_cases = len(all_cases.filtered(lambda c: c.verification_status == 'expired'))
            
            rec.total_preauths = len(all_preauths)
            rec.pending_preauths = len(all_preauths.filtered(lambda p: p.approval_status == 'pending'))
            rec.approved_preauths = len(all_preauths.filtered(lambda p: p.approval_status == 'approved'))
            
            rec.total_providers = len(all_providers)

    def _compute_lists(self):
        Case = self.env['insurance.case']
        Preauth = self.env['insurance.preauthorization']
        
        pending_cases = Case.search([('verification_status', '=', 'pending')], order='visit_date asc')
        recent_cases = Case.search([], order='write_date desc', limit=10)
        pending_preauths = Preauth.search([('approval_status', '=', 'pending')], order='request_date asc')
        
        for rec in self:
            rec.pending_case_ids = [(6, 0, pending_cases.ids)]
            rec.recent_case_ids = [(6, 0, recent_cases.ids)]
            rec.pending_preauth_ids = [(6, 0, pending_preauths.ids)]

    def action_open_cases(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Insurance Cases',
            'res_model': 'insurance.case',
            'view_mode': 'list,form',
            'target': 'current',
        }

    @api.model
    def action_open_dashboard(self):
        # Create a transient record for the current session dashboard state
        dashboard_rec = self.create({})
        return {
            'name': 'Insurance Dashboard',
            'type': 'ir.actions.act_window',
            'res_model': 'insurance.dashboard',
            'res_id': dashboard_rec.id,
            'view_mode': 'form',
            'target': 'current',
        }
