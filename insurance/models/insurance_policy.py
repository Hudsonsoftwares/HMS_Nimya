# -*- coding: utf-8 -*-
from odoo import models, fields, api

class InsurancePolicy(models.Model):
    _name = 'insurance.policy'
    _description = 'Insurance Policy'
    _order = 'name'

    name = fields.Char(
        string='Policy Name',
        required=True,
    )
    provider_id = fields.Many2one(
        comodel_name='clinic.insurance.provider',
        string='Insurance Provider',
        required=True,
        ondelete='restrict',
    )
    code = fields.Char(
        string='Policy Code',
    )
    policy_type = fields.Selection([
        ('individual', 'Individual'),
        ('family', 'Family'),
        ('corporate', 'Corporate'),
        ('government', 'Government'),
    ], string='Policy Type', default='individual')

    coverage_type = fields.Selection([
        ('full', 'Full Coverage'),
        ('partial', 'Partial Coverage'),
        ('op_only', 'OP Only'),
        ('ip_only', 'IP Only'),
    ], string='Coverage Type', default='full')

    policy_number_format = fields.Char(
        string='Policy Number Format',
        help='Pattern or format description for validation (e.g. POL-######)',
    )
    description = fields.Text(
        string='Description',
    )
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ], string='Status', default='active', compute='_compute_status', inverse='_inverse_status', store=True, readonly=False)

    active = fields.Boolean(
        default=True,
    )

    valid_from = fields.Date(
        string='Valid From',
    )
    valid_until = fields.Date(
        string='Valid Until',
    )
    requires_pre_auth = fields.Boolean(
        string='Pre-Authorization Required',
        default=False,
    )
    verification_method = fields.Selection([
        ('portal', 'Portal'),
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('manual', 'Manual'),
        ('api', 'API'),
    ], string='Verification Method')

    copay_percentage = fields.Float(
        string='Default Copayment Percentage',
        default=0.0,
    )
    annual_limit = fields.Float(
        string='Annual Coverage Limit',
        default=0.0,
    )
    remarks = fields.Text(
        string='Remarks',
    )

    @api.depends('active')
    def _compute_status(self):
        for record in self:
            record.status = 'active' if record.active else 'inactive'

    def _inverse_status(self):
        for record in self:
            record.active = (record.status == 'active')

    @api.onchange('provider_id')
    def _onchange_provider_id(self):
        if self.provider_id:
            # Safely copy values from the provider model if configured
            if hasattr(self.provider_id, 'verification_method') and self.provider_id.verification_method:
                self.verification_method = self.provider_id.verification_method
            if hasattr(self.provider_id, 'requires_pre_auth'):
                self.requires_pre_auth = self.provider_id.requires_pre_auth
