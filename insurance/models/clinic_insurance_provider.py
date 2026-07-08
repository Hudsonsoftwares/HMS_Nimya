# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ClinicInsuranceProvider(models.Model):
    _inherit = 'clinic.insurance.provider'

    code = fields.Char(
        string='Provider Code',
        required=True,
    )
    company_type = fields.Selection([
        ('insurance', 'Insurance Company'),
        ('tpa', 'Third Party Administrator (TPA)'),
    ], string='Company Type', required=True, default='insurance')

    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ], string='Status', default='active', compute='_compute_status', inverse='_inverse_status', store=True, readonly=False)

    # Contact Details
    contact_person = fields.Char(string='Contact Person')
    designation = fields.Char(string='Designation')
    mobile = fields.Char(string='Mobile')
    website = fields.Char(string='Website')

    # Address Details
    building = fields.Char(string='Building')
    street = fields.Char(string='Street')
    city = fields.Char(string='City')
    state = fields.Char(string='State')
    country_id = fields.Many2one('res.country', string='Country')
    postal_code = fields.Char(string='Postal Code')
    
    address = fields.Text(
        string='Address',
        compute='_compute_address',
        store=True,
    )

    # Business Details
    registration_number = fields.Char(string='Registration Number')
    tax_number = fields.Char(string='Tax Number')
    contract_start_date = fields.Date(string='Contract Start Date')
    contract_end_date = fields.Date(string='Contract End Date')
    currency_id = fields.Many2one('res.currency', string='Default Currency')

    # Claim & Authorization Details
    requires_pre_auth = fields.Boolean(string='Requires Pre-Authorization', default=False)
    pre_auth_email = fields.Char(string='Pre-Authorization Email')
    claims_email = fields.Char(string='Claims Email')
    claims_portal_url = fields.Char(string='Claims Portal URL')
    customer_support_number = fields.Char(string='Customer Support Number')

    # Notes
    internal_notes = fields.Text(string='Internal Notes')

    @api.depends('active')
    def _compute_status(self):
        for record in self:
            record.status = 'active' if record.active else 'inactive'

    def _inverse_status(self):
        for record in self:
            record.active = (record.status == 'active')

    @api.depends('building', 'street', 'city', 'state', 'country_id', 'postal_code')
    def _compute_address(self):
        for record in self:
            parts = []
            if record.building:
                parts.append(record.building)
            if record.street:
                parts.append(record.street)
            if record.city:
                parts.append(record.city)
            if record.state:
                parts.append(record.state)
            if record.country_id:
                parts.append(record.country_id.name)
            if record.postal_code:
                parts.append(record.postal_code)
            record.address = ', '.join(parts) if parts else ''
