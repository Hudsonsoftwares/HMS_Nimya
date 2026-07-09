# -*- coding: utf-8 -*-
import requests
import json
from odoo import models, fields, api
from odoo.exceptions import UserError

class InsuranceCase(models.Model):
    _name = 'insurance.case'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Insurance Case / Verification'
    _order = 'name desc, id desc'

    name = fields.Char(
        string='Case Number',
        required=True,
        readonly=True,
        default='/',
        copy=False,
    )
    
    # Patient Information
    patient_id = fields.Many2one(
        comodel_name='clinic.patient',
        string='Patient',
        required=True,
        ondelete='restrict',
    )
    patient_id_ref = fields.Char(
        string='Patient ID',
        related='patient_id.patient_id',
        readonly=True,
        store=True,
    )
    visit_date = fields.Date(
        string='Visit Date',
        default=fields.Date.context_today,
        required=True,
    )
    created_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Created By',
        default=lambda self: self.env.user,
        readonly=True,
    )

    # Insurance Information
    provider_id = fields.Many2one(
        comodel_name='clinic.insurance.provider',
        string='Insurance Provider',
        readonly=True,
        store=True,
    )
    policy_number = fields.Char(
        string='Policy Number',
        readonly=True,
        store=True,
    )
    membership_number = fields.Char(
        string='Membership Number',
        readonly=True,
        store=True,
    )
    health_card_number = fields.Char(
        string='Health Card Number',
        readonly=True,
        store=True,
    )
    issue_date = fields.Date(
        string='Issue Date',
        readonly=True,
        store=True,
    )
    expiry_date = fields.Date(
        string='Expiry Date',
        readonly=True,
        store=True,
    )

    # Verification Settings
    verification_method = fields.Selection([
        ('portal', 'Portal'),
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('manual', 'Manual'),
        ('api', 'API'),
    ], string='Verification Method')
    
    verification_status = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ], string='Verification Status', default='draft')
    
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Very High'),
    ], string='Priority', default='1', index=True)
    
    color = fields.Integer(string='Color Index', default=0)
    
    verification_date = fields.Date(
        string='Verification Date',
        readonly=True,
    )
    verified_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Verified By',
        readonly=True,
    )

    # Pre-Authorization
    requires_pre_auth = fields.Boolean(
        string='Requires Pre Authorization',
        default=False,
    )
    preauth_ids = fields.One2many(
        comodel_name='insurance.preauthorization',
        inverse_name='case_id',
        string='Pre-Authorization Requests',
    )

    # Coverage
    coverage_status = fields.Selection([
        ('covered', 'Covered'),
        ('partially', 'Partially Covered'),
        ('not_covered', 'Not Covered'),
    ], string='Coverage Status')
    
    copay_percentage = fields.Float(
        string='Copayment Percentage',
    )
    coverage_notes = fields.Text(
        string='Coverage Notes',
    )
    verification_summary = fields.Text(
        string='Summary',
        readonly=True,
    )

    # Attachments
    attachment_card = fields.Binary(string='Insurance Card')
    attachment_card_filename = fields.Char(string='Insurance Card Filename')
    
    attachment_approval = fields.Binary(string='Approval Letter')
    attachment_approval_filename = fields.Char(string='Approval Letter Filename')
    
    attachment_email = fields.Binary(string='Email Reply')
    attachment_email_filename = fields.Char(string='Email Reply Filename')
    
    attachment_support = fields.Binary(string='Supporting Documents')
    attachment_support_filename = fields.Char(string='Supporting Documents Filename')

    # Patient Insurance Documents
    insurance_document_ids = fields.Many2many(
        comodel_name='patient.insurance.document',
        compute='_compute_insurance_document_ids',
        string='Patient Insurance Documents',
        readonly=True,
    )

    @api.depends('patient_id.insurance_document_ids')
    def _compute_insurance_document_ids(self):
        for case in self:
            case.insurance_document_ids = case.patient_id.insurance_document_ids

    @api.onchange('patient_id')
    def _onchange_patient_id(self):
        if self.patient_id:
            self.provider_id = self.patient_id.insurance_provider_id
            self.policy_number = self.patient_id.policy_number
            self.membership_number = self.patient_id.membership_number
            self.health_card_number = self.patient_id.health_card_number
            self.issue_date = self.patient_id.insurance_issue_date
            self.expiry_date = self.patient_id.insurance_expiry_date
            
            # Default verification and pre-auth from provider
            if self.provider_id:
                self.verification_method = self.provider_id.verification_method
                self.requires_pre_auth = self.provider_id.requires_pre_auth

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('insurance.case.seq') or '/'
            
            # Auto-populate values if patient is set
            if vals.get('patient_id'):
                patient = self.env['clinic.patient'].browse(vals['patient_id'])
                if patient:
                    vals['provider_id'] = patient.insurance_provider_id.id
                    vals['policy_number'] = patient.policy_number
                    vals['membership_number'] = patient.membership_number
                    vals['health_card_number'] = patient.health_card_number
                    vals['issue_date'] = patient.insurance_issue_date
                    vals['expiry_date'] = patient.insurance_expiry_date
                    if not vals.get('verification_method'):
                        vals['verification_method'] = patient.insurance_provider_id.verification_method
                    if 'requires_pre_auth' not in vals:
                        vals['requires_pre_auth'] = patient.insurance_provider_id.requires_pre_auth
        return super(InsuranceCase, self).create(vals_list)

    # Actions / Buttons
    def action_verify_insurance(self):
        self.write({'verification_status': 'pending'})

    def action_send_email(self):
        self.ensure_one()
        api_key = self.env['ir.config_parameter'].sudo().get_param('Groq') or \
                  self.env['ir.config_parameter'].sudo().get_param('groq.api_key') or \
                  self.env['ir.config_parameter'].sudo().get_param('groq_api_key')
        
        subject = f"Insurance Verification Request: {self.patient_id.name}"
        body = (
            f"<p>Dear Claims Department,</p>"
            f"<p>We would like to request insurance verification for the following patient:</p>"
            f"<ul>"
            f"<li><strong>Patient Name:</strong> {self.patient_id.name}</li>"
            f"<li><strong>Policy Number:</strong> {self.policy_number or 'N/A'}</li>"
            f"<li><strong>Membership Number:</strong> {self.membership_number or 'N/A'}</li>"
            f"<li><strong>Health Card/ID:</strong> {self.health_card_number or 'N/A'}</li>"
            f"<li><strong>Visit Date:</strong> {self.visit_date}</li>"
            f"</ul>"
            f"<p>Please confirm their eligibility, coverage details, copayment/deductible, and whether pre-authorization is required.</p>"
            f"<p>Thank you,</p>"
            f"<p>Hospital Administration</p>"
        )
        
        if api_key:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            prompt = (
                "Write a professional email requesting insurance verification for a patient. "
                "Include the following details:\n"
                f"- Patient Name: {self.patient_id.name}\n"
                f"- Policy Number: {self.policy_number or 'N/A'}\n"
                f"- Membership Number: {self.membership_number or 'N/A'}\n"
                f"- Health Card Number: {self.health_card_number or 'N/A'}\n"
                f"- Visit Date: {self.visit_date}\n\n"
                "The email should ask the provider to confirm:\n"
                "1. If the policy is active and covers the visit.\n"
                "2. The copayment percentage.\n"
                "3. Any pre-authorization requirements.\n\n"
                "Generate the subject line (prefixing with 'Subject: ') and the email body (in HTML format) separately. "
                "Output ONLY the generated email. No additional remarks or explanations."
            )
            payload = {
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3
            }
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                if response.status_code == 200:
                    content = response.json()['choices'][0]['message']['content'].strip()
                    if "Subject:" in content:
                        parts = content.split("Subject:", 1)[1].split("\n", 1)
                        subject = parts[0].strip()
                        body = parts[1].strip() if len(parts) > 1 else content
                    else:
                        body = content
            except Exception:
                pass
        
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', raise_if_not_found=False)
        ctx = {
            'default_model': 'insurance.case',
            'default_res_ids': self.ids,
            'default_composition_mode': 'comment',
            'default_email_to': self.provider_id.claims_email or self.provider_id.pre_auth_email or '',
            'default_subject': subject,
            'default_body': body,
            'force_email': True,
        }
        return {
            'name': 'Compose Email',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')] if compose_form else [(False, 'form')],
            'view_id': compose_form.id if compose_form else False,
            'target': 'new',
            'context': ctx,
        }

    def _analyze_chatter_with_ai(self):
        self.ensure_one()
        api_key = self.env['ir.config_parameter'].sudo().get_param('Groq') or \
                  self.env['ir.config_parameter'].sudo().get_param('groq.api_key') or \
                  self.env['ir.config_parameter'].sudo().get_param('groq_api_key')
        if not api_key:
            return
        
        from odoo.tools import html2plaintext
        chatter_history = []
        # Sort messages and limit to the last 5 to keep within token limits
        messages = self.message_ids.sorted(key=lambda m: m.date)
        if len(messages) > 5:
            messages = messages[-5:]
            
        for msg in messages:
            author = msg.author_id.name or "User/System"
            body = html2plaintext(msg.body or '').strip()
            if body:
                # Strip nested reply history to avoid token limits
                for marker in ["On Thu,", "On Fri,", "On Sat,", "On Sun,", "On Mon,", "On Tue,", "On Wed,", "-----Original Message-----", "From:"]:
                    if marker in body:
                        body = body.split(marker)[0].strip()
                if body:
                    chatter_history.append(f"{author}: {body}")
        
        if not chatter_history:
            return
        
        history_text = "\n".join(chatter_history)
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        prompt = (
            "Analyze the following communication history for an insurance verification case.\n"
            "Provide a highly detailed, structured summary of the insurance coverage status. "
            "You MUST extract and list every single laboratory test and medicine mentioned in the communication, showing their specific coverage status and limits.\n\n"
            "Format your response EXACTLY using the following markdown sections:\n\n"
            "### 1. Overall Status & Consultation\n"
            "- **Status**: (e.g. Approved / Pending / Excluded)\n"
            "- **Copayment**: (e.g. 20% payable by member)\n"
            "- **Consultation**: (Details of General Physician / Specialist coverage)\n\n"
            "### 2. Detailed Laboratory Tests Coverage\n"
            "List every laboratory test mentioned in the email (e.g., CBC, Blood Sugar, HbA1c, Lipid Profile, Liver/Kidney tests, Vitamin D, Vitamin B12, Iron Profile, etc.) with its specific coverage and conditions/frequency limits:\n"
            "- **[Test Name]**: (Covered / Not Covered) - [Specific conditions/frequency limits/exclusions]\n\n"
            "### 3. Detailed Pharmacy & Medicines Coverage\n"
            "List every medicine category and quantity limits mentioned in the email:\n"
            "- **[Medicine Category/Name]**: (Covered / Not Covered) - [Limits/frequency/restrictions]\n\n"
            "### 4. Radiology & Other Services\n"
            "- **[Service/Investigation]**: (Covered / Not Covered) - [Approval/Authorisation requirements]\n\n"
            "### 5. Pre-Authorization & Exclusions\n"
            "- **Pre-Authorization Required**: [List of services requiring prior approval]\n"
            "- **Exclusions**: [List of excluded services/network conditions]\n\n"
            "Do not omit any details or group tests/medicines together. Keep the listing highly specific as provided in the email reply.\n\n"
            f"Communication History:\n{history_text}"
        )
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                summary = data['choices'][0]['message']['content'].strip()
                self.write({'verification_summary': summary})
        except Exception:
            pass

    def message_post(self, **kwargs):
        message = super(InsuranceCase, self).message_post(**kwargs)
        if not self.env.context.get('skip_ai_analysis'):
            self.with_context(skip_ai_analysis=True)._analyze_chatter_with_ai()
        return message

    def action_open_portal(self):
        self.ensure_one()
        if self.provider_id and self.provider_id.claims_portal_url:
            return {
                'type': 'ir.actions.act_url',
                'url': self.provider_id.claims_portal_url,
                'target': 'new',
            }
        else:
            raise UserError("No claims portal URL defined for this insurance provider.")

    def action_mark_verified(self):
        self.write({
            'verification_status': 'verified',
            'verification_date': fields.Date.context_today(self),
            'verified_by_id': self.env.user.id
        })

    def action_reject(self):
        self.write({'verification_status': 'rejected'})

    # Smart Buttons Redirection
    def action_view_patient(self):
        self.ensure_one()
        return {
            'name': 'Patient Profile',
            'type': 'ir.actions.act_window',
            'res_model': 'clinic.patient',
            'view_mode': 'form',
            'res_id': self.patient_id.id,
            'target': 'current',
        }

    def action_view_dummy(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Feature Preview',
                'message': 'This link redirects to patient records in the billing/clinical modules.',
                'type': 'info',
                'sticky': False,
            }
        }
