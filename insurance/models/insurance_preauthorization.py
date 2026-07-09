# -*- coding: utf-8 -*-
from odoo import models, fields, api

class InsurancePreauthorization(models.Model):
    _name = 'insurance.preauthorization'
    _description = 'Insurance Pre-Authorization Request'
    _order = 'name desc, id desc'

    name = fields.Char(
        string='Request Number',
        required=True,
        readonly=True,
        default='/',
        copy=False,
    )
    case_id = fields.Many2one(
        comodel_name='insurance.case',
        string='Insurance Case',
        required=True,
        ondelete='cascade',
    )
    patient_id = fields.Many2one(
        comodel_name='clinic.patient',
        string='Patient',
        related='case_id.patient_id',
        store=True,
        readonly=True,
    )
    provider_id = fields.Many2one(
        comodel_name='clinic.insurance.provider',
        string='Insurance Provider',
        related='case_id.provider_id',
        store=True,
        readonly=True,
    )
    requested_service = fields.Char(
        string='Requested Service',
        required=True,
    )
    department = fields.Char(
        string='Department',
    )
    request_type = fields.Selection([
        ('consultation', 'Consultation'),
        ('laboratory', 'Laboratory'),
        ('radiology', 'Radiology'),
        ('procedure', 'Procedure'),
        ('surgery', 'Surgery'),
        ('medicine', 'Medicine'),
        ('other', 'Other'),
    ], string='Request Type', required=True, default='consultation')
    requested_by = fields.Many2one(
        comodel_name='res.users',
        string='Requested By (Doctor)',
        default=lambda self: self.env.user,
    )
    request_date = fields.Date(
        string='Request Date',
        default=fields.Date.context_today,
        required=True,
    )
    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('emergency', 'Emergency'),
    ], string='Priority', default='normal', required=True)

    # Approval Information
    approval_status = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Approval Status', default='draft', required=True)
    approval_number = fields.Char(
        string='Approval Number',
    )
    approval_date = fields.Date(
        string='Approval Date',
    )
    approval_expiry_date = fields.Date(
        string='Approval Expiry Date',
    )
    approved_by = fields.Many2one(
        comodel_name='res.users',
        string='Approved By',
    )

    # Communication
    submission_method = fields.Selection([
        ('portal', 'Portal'),
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('manual', 'Manual'),
        ('api', 'API'),
    ], string='Submission Method', default='portal')
    submission_date = fields.Date(
        string='Submission Date',
    )
    reference_number = fields.Char(
        string='Reference Number',
    )

    # Documents
    attachment_approval = fields.Binary(string='Approval Letter')
    attachment_approval_filename = fields.Char(string='Approval Letter Filename')
    attachment_email = fields.Binary(string='Insurance Email Reply')
    attachment_email_filename = fields.Char(string='Email Reply Filename')
    attachment_support = fields.Binary(string='Supporting Documents')
    attachment_support_filename = fields.Char(string='Supporting Documents Filename')
    attachment_report = fields.Binary(string='Medical Report')
    attachment_report_filename = fields.Char(string='Medical Report Filename')

    # Notes
    notes = fields.Text(
        string='Internal Notes',
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('insurance.preauthorization.seq') or '/'
        return super(InsurancePreauthorization, self).create(vals_list)

    def action_submit(self):
        self.write({
            'approval_status': 'pending',
            'submission_date': fields.Date.context_today(self)
        })

    def action_approve(self):
        self.write({
            'approval_status': 'approved',
            'approval_date': fields.Date.context_today(self),
            'approved_by': self.env.user.id
        })

    def action_reject(self):
        self.write({
            'approval_status': 'rejected'
        })
