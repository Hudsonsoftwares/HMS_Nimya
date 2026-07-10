# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date, datetime

class LaboratoryTest(models.Model):
    _name = 'laboratory.test'
    _description = 'Laboratory Test Catalog'
    _order = 'name asc'

    code = fields.Char(string='Test Code', required=True, copy=False)
    name = fields.Char(string='Test Name', required=True)
    category = fields.Selection([
        ('hematology', 'Hematology'),
        ('biochemistry', 'Biochemistry'),
        ('microbiology', 'Microbiology'),
        ('immunology', 'Immunology'),
        ('urinalysis', 'Urinalysis'),
        ('other', 'Other')
    ], string='Category', default='biochemistry', required=True)
    description = fields.Text(string='Description')
    normal_range = fields.Char(string='Normal Reference Range')
    unit = fields.Char(string='Unit')
    cost = fields.Float(string='Cost', default=0.0)
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('uniq_code', 'unique(code)', 'The test code must be unique!')
    ]


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    is_lab_equipment = fields.Boolean(string="Is Laboratory Equipment", default=True)


class HospitalLaboratory(models.Model):
    _name = "hospital.laboratory"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Laboratory Request"
    _order = "name desc, id desc"

    name = fields.Char(string="Request ID", required=True, readonly=True, default='/', copy=False)
    patient_id = fields.Many2one('clinic.patient', string='Patient', required=True, tracking=True)
    patient_ref = fields.Char(string='Patient ID', related='patient_id.patient_id', readonly=True)
    doctor_id = fields.Many2one('hr.employee', string='Prescribing Doctor', tracking=True)
    request_date = fields.Date(string='Request Date', default=fields.Date.today, required=True, tracking=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('sample_collected', 'Sample Collected'),
        ('testing', 'Testing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True)
    
    test_ids = fields.Many2many('laboratory.test', 'lab_request_test_rel', 'request_id', 'test_id', string='Tests to Perform', required=True, tracking=True)
    sample_ids = fields.One2many('laboratory.sample', 'request_id', string='Samples')
    result_ids = fields.One2many('laboratory.result', 'request_id', string='Results')
    notes = fields.Text(string='Notes')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('hospital.laboratory') or '/'
        records = super(HospitalLaboratory, self).create(vals_list)
        for record in records:
            record._sync_result_lines()
        return records

    def write(self, vals):
        res = super(HospitalLaboratory, self).write(vals)
        if 'test_ids' in vals:
            for record in self:
                record._sync_result_lines()
        return res

    def _sync_result_lines(self):
        for rec in self:
            existing_tests = rec.result_ids.mapped('test_id')
            # Add new results
            for test in rec.test_ids:
                if test not in existing_tests:
                    self.env['laboratory.result'].create({
                        'request_id': rec.id,
                        'test_id': test.id,
                        'state': 'draft',
                    })
            # Remove deleted tests
            for result in rec.result_ids:
                if result.test_id not in rec.test_ids:
                    result.unlink()

    def action_request(self):
        self.write({'state': 'requested'})

    def action_collect_sample(self):
        # Auto-create sample records based on category of requested tests
        for rec in self:
            categories = rec.test_ids.mapped('category')
            # Map test categories to sample types
            sample_types = set()
            for cat in categories:
                if cat in ('hematology', 'biochemistry', 'immunology'):
                    sample_types.add('blood')
                elif cat == 'urinalysis':
                    sample_types.add('urine')
                elif cat == 'microbiology':
                    sample_types.add('swab')
                else:
                    sample_types.add('other')

            for s_type in sample_types:
                # Check if sample of this type already exists for this request
                existing_sample = rec.sample_ids.filtered(lambda s: s.sample_type == s_type)
                if not existing_sample:
                    tests_for_sample = rec.test_ids.filtered(lambda t: (
                        (s_type == 'blood' and t.category in ('hematology', 'biochemistry', 'immunology')) or
                        (s_type == 'urine' and t.category == 'urinalysis') or
                        (s_type == 'swab' and t.category == 'microbiology') or
                        (s_type == 'other' and t.category == 'other')
                    ))
                    self.env['laboratory.sample'].create({
                        'request_id': rec.id,
                        'sample_type': s_type,
                        'test_ids': [(6, 0, tests_for_sample.ids)],
                        'state': 'pending'
                    })
        self.write({'state': 'sample_collected'})

    def action_start_testing(self):
        # Make sure samples are processed/collected before testing starts
        for rec in self:
            if not rec.sample_ids:
                raise ValidationError(_("No samples collected. Please collect samples first."))
            if any(s.state == 'pending' for s in rec.sample_ids):
                raise ValidationError(_("Some samples are still pending collection. Please process them."))
        self.write({'state': 'testing'})

    def action_complete(self):
        # Ensure all result values are filled in
        for rec in self:
            if not rec.result_ids:
                raise ValidationError(_("No results found. Cannot complete request without test results."))
            if any(not res.result_value for res in rec.result_ids):
                raise ValidationError(_("Please fill in results for all tests before completing."))
            # Auto-verify all draft results when completing
            rec.result_ids.filtered(lambda r: r.state == 'draft').action_verify()
        self.write({'state': 'completed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})


class LaboratorySample(models.Model):
    _name = 'laboratory.sample'
    _description = 'Laboratory Sample'
    _order = 'name desc'

    name = fields.Char(string='Sample ID', required=True, readonly=True, default='/', copy=False)
    request_id = fields.Many2one('hospital.laboratory', string='Lab Request', required=True, ondelete='cascade')
    patient_id = fields.Many2one('clinic.patient', related='request_id.patient_id', string='Patient', store=True, readonly=True)
    test_ids = fields.Many2many('laboratory.test', string='Tests to Perform')
    sample_type = fields.Selection([
        ('blood', 'Blood'),
        ('urine', 'Urine'),
        ('sputum', 'Sputum'),
        ('stool', 'Stool'),
        ('swab', 'Swab'),
        ('other', 'Other')
    ], string='Sample Type', default='blood', required=True)
    collection_date = fields.Datetime(string='Collection Date/Time', default=fields.Datetime.now, required=True)
    collected_by = fields.Many2one('res.users', string='Collected By', default=lambda self: self.env.user)
    state = fields.Selection([
        ('pending', 'Pending Collection'),
        ('collected', 'Collected'),
        ('processed', 'Processed'),
        ('rejected', 'Rejected')
    ], string='Sample Status', default='pending', required=True)
    notes = fields.Text(string='Notes')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('laboratory.sample') or '/'
        return super(LaboratorySample, self).create(vals_list)

    def action_collect(self):
        self.write({'state': 'collected', 'collection_date': fields.Datetime.now()})

    def action_process(self):
        self.write({'state': 'processed'})

    def action_reject(self):
        self.write({'state': 'rejected'})


class LaboratoryResult(models.Model):
    _name = 'laboratory.result'
    _description = 'Laboratory Result'
    _order = 'id asc'

    request_id = fields.Many2one('hospital.laboratory', string='Lab Request', required=True, ondelete='cascade')
    patient_id = fields.Many2one('clinic.patient', related='request_id.patient_id', string='Patient', store=True, readonly=True)
    test_id = fields.Many2one('laboratory.test', string='Test', required=True)
    result_value = fields.Char(string='Result Value')
    normal_range = fields.Char(related='test_id.normal_range', string='Reference Range', readonly=True)
    unit = fields.Char(related='test_id.unit', string='Unit', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('verified', 'Verified')
    ], string='Status', default='draft')
    verified_by = fields.Many2one('res.users', string='Verified By', readonly=True)
    verification_date = fields.Datetime(string='Verification Date/Time', readonly=True)
    remarks = fields.Text(string='Remarks')

    def action_verify(self):
        self.write({
            'state': 'verified',
            'verified_by': self.env.user.id,
            'verification_date': fields.Datetime.now()
        })


class LaboratoryDashboard(models.TransientModel):
    _name = 'laboratory.dashboard'
    _description = 'Laboratory Management Dashboard'

    total_requests = fields.Integer(string="Total Requests Today", compute='_compute_kpi_stats')
    pending_requests = fields.Integer(string="Pending Requests", compute='_compute_kpi_stats')
    sample_collected = fields.Integer(string="Sample Collected", compute='_compute_kpi_stats')
    testing_requests = fields.Integer(string="In Testing", compute='_compute_kpi_stats')
    completed_requests = fields.Integer(string="Completed Today", compute='_compute_kpi_stats')
    cancelled_requests = fields.Integer(string="Cancelled Today", compute='_compute_kpi_stats')
    total_tests = fields.Integer(string="Total Active Tests", compute='_compute_kpi_stats')
    active_equipments = fields.Integer(string="Active Equipments", compute='_compute_kpi_stats')
    maintenance_equipments = fields.Integer(string="Equipments in Maintenance", compute='_compute_kpi_stats')

    recent_request_ids = fields.Many2many(
        comodel_name='hospital.laboratory',
        relation='dashboard_recent_requests_rel',
        column1='dashboard_id',
        column2='request_id',
        string="Recent Requests",
        compute='_compute_lists'
    )
    pending_sample_ids = fields.Many2many(
        comodel_name='laboratory.sample',
        relation='dashboard_pending_samples_rel',
        column1='dashboard_id',
        column2='sample_id',
        string="Pending Sample Collections",
        compute='_compute_lists'
    )
    recent_result_ids = fields.Many2many(
        comodel_name='laboratory.result',
        relation='dashboard_recent_results_rel',
        column1='dashboard_id',
        column2='result_id',
        string="Recent Draft Results",
        compute='_compute_lists'
    )

    def _compute_kpi_stats(self):
        today = date.today()
        LabRequest = self.env['hospital.laboratory']
        LabTest = self.env['laboratory.test']
        Equipment = self.env['maintenance.equipment']

        # Requests today
        requests_today = LabRequest.search([('request_date', '=', today)])
        
        # Test configurations
        active_tests_count = LabTest.search_count([('active', '=', True)])

        # Equipments
        active_eq_count = Equipment.search_count([('is_lab_equipment', '=', True), ('active', '=', True)])
        maint_eq_count = Equipment.search_count([('is_lab_equipment', '=', True), ('active', '=', False)])

        for rec in self:
            rec.total_requests = len(requests_today)
            rec.pending_requests = len(requests_today.filtered(lambda r: r.state == 'requested'))
            rec.sample_collected = len(requests_today.filtered(lambda r: r.state == 'sample_collected'))
            rec.testing_requests = len(requests_today.filtered(lambda r: r.state == 'testing'))
            rec.completed_requests = len(requests_today.filtered(lambda r: r.state == 'completed'))
            rec.cancelled_requests = len(requests_today.filtered(lambda r: r.state == 'cancelled'))
            rec.total_tests = active_tests_count
            rec.active_equipments = active_eq_count
            rec.maintenance_equipments = maint_eq_count

    def _compute_lists(self):
        LabRequest = self.env['hospital.laboratory']
        Sample = self.env['laboratory.sample']
        Result = self.env['laboratory.result']

        recent_requests = LabRequest.search([], order='id desc', limit=10)
        pending_samples = Sample.search([('state', '=', 'pending')], order='id desc', limit=10)
        recent_results = Result.search([('state', '=', 'draft')], order='id desc', limit=10)

        for rec in self:
            rec.recent_request_ids = [(6, 0, recent_requests.ids)]
            rec.pending_sample_ids = [(6, 0, pending_samples.ids)]
            rec.recent_result_ids = [(6, 0, recent_results.ids)]

    @api.model
    def action_open_dashboard(self):
        dashboard_rec = self.create({})
        return {
            'name': 'Laboratory Dashboard',
            'type': 'ir.actions.act_window',
            'res_model': 'laboratory.dashboard',
            'res_id': dashboard_rec.id,
            'view_mode': 'form',
            'target': 'current',
        }