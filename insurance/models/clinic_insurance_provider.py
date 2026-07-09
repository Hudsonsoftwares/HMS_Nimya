# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ClinicInsuranceProvider(models.Model):
    _inherit = 'clinic.insurance.provider'

    logo = fields.Image(
        string='Logo',
        max_width=128,
        max_height=128,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Contact Reference',
        ondelete='restrict',
    )
    code = fields.Char(
        string='Provider Code',
        required=True,
        default='/',
        copy=False,
    )
    company_type = fields.Selection([
        ('insurance', 'Insurance Company'),
        ('tpa', 'Third Party Administrator (TPA)'),
    ], string='Company Type', required=True, default='insurance')

    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ], string='Status', default='active', compute='_compute_status', inverse='_inverse_status', store=True, readonly=False)

    is_preferred = fields.Boolean(
        string='Preferred Insurance Partner',
        default=False,
    )

    # Contact Details
    contact_person = fields.Char(string='Contact Person')
    contact_department = fields.Selection([
        ('claims', 'Claims Department'),
        ('relations', 'Provider Relations'),
        ('support', 'Customer Support'),
        ('others', 'Others'),
    ], string='Contact Department')
    designation = fields.Char(string='Designation')
    mobile = fields.Char(string='Mobile')
    website = fields.Char(string='Website')
    support_hours = fields.Char(string='Support Hours')

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
    network_type = fields.Selection([
        ('local', 'Local Network'),
        ('international', 'International'),
        ('both', 'Both'),
    ], string='Network Type')
    claims_processing_time = fields.Selection([
        ('7_days', '7 Days'),
        ('15_days', '15 Days'),
        ('30_days', '30 Days'),
        ('others', 'Others'),
    ], string='Claims Processing Time')

    # Claim & Authorization Details
    requires_pre_auth = fields.Boolean(string='Requires Pre-Authorization', default=False)
    pre_auth_email = fields.Char(string='Pre-Authorization Email')
    pre_auth_tat = fields.Selection([
        ('immediate', 'Immediate'),
        ('1_hour', 'Within 1 Hour'),
        ('4_hours', 'Within 4 Hours'),
        ('24_hours', 'Within 24 Hours'),
        ('48_hours', 'Within 48 Hours'),
    ], string='Pre-Authorization Turnaround Time')
    pre_auth_notes = fields.Text(string='Pre-Authorization Notes')

    claims_email = fields.Char(string='Claims Email')
    claims_portal_url = fields.Char(string='Claims Portal URL')
    customer_support_number = fields.Char(string='Customer Support Number')
    working_hours = fields.Char(string='Working Hours')
    emergency_contact_number = fields.Char(string='Emergency Contact Number')

    verification_method = fields.Selection([
        ('email', 'Email'),
        ('portal', 'Portal'),
        ('phone', 'Phone'),
        ('manual', 'Manual'),
        ('api', 'API'),
    ], string='Verification Method')

    # Future API Details
    api_available = fields.Boolean(string='API Available', default=False)
    api_doc_url = fields.Char(string='API Documentation URL')
    api_notes = fields.Text(string='API Notes')

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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code') or vals.get('code') == '/':
                vals['code'] = self.env['ir.sequence'].next_by_code('clinic.insurance.provider.seq') or '/'
            
            # Create partner if not present
            if not vals.get('partner_id'):
                partner_vals = {
                    'name': vals.get('name') or 'Insurance Provider',
                    'is_company': True,
                    'phone': vals.get('phone'),
                    'email': vals.get('email'),
                    'website': vals.get('website'),
                    'street': vals.get('building') or vals.get('street'),
                    'city': vals.get('city'),
                    'zip': vals.get('postal_code'),
                    'country_id': vals.get('country_id'),
                }
                partner = self.env['res.partner'].create(partner_vals)
                vals['partner_id'] = partner.id
                
        return super(ClinicInsuranceProvider, self).create(vals_list)

    def write(self, vals):
        res = super(ClinicInsuranceProvider, self).write(vals)
        for rec in self:
            if rec.partner_id:
                partner_vals = {}
                if 'name' in vals:
                    partner_vals['name'] = vals['name']
                if 'phone' in vals:
                    partner_vals['phone'] = vals['phone']
                if 'email' in vals:
                    partner_vals['email'] = vals['email']
                if 'website' in vals:
                    partner_vals['website'] = vals['website']
                if 'street' in vals or 'building' in vals:
                    partner_vals['street'] = rec.building or rec.street
                if 'city' in vals:
                    partner_vals['city'] = vals['city']
                if 'postal_code' in vals:
                    partner_vals['zip'] = vals['postal_code']
                if 'country_id' in vals:
                    partner_vals['country_id'] = vals['country_id']
                
                if partner_vals:
                    rec.partner_id.write(partner_vals)
        return res

    def _init_insurance_provider_partners(self):
        providers = self.search([('partner_id', '=', False)])
        for provider in providers:
            partner = self.env['res.partner'].create({
                'name': provider.name or 'Insurance Provider',
                'is_company': True,
                'phone': provider.phone,
                'email': provider.email,
                'website': provider.website,
                'street': provider.building or provider.street,
                'city': provider.city,
                'zip': provider.postal_code,
                'country_id': provider.country_id.id if provider.country_id else False,
            })
            provider.write({'partner_id': partner.id})

    def _register_hook(self):
        super(ClinicInsuranceProvider, self)._register_hook()
        self.sudo()._init_insurance_provider_partners()
