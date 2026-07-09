# -*- coding: utf-8 -*-
from odoo import models, fields, api

class HospitalBilling(models.Model):
    _name = 'hospital.billing'
    _description = 'Hospital Billing'

    name = fields.Char(
        string="Bill Number",
        required=True,
        readonly=True,
        default='/',
    )
    patient_id = fields.Many2one(
        comodel_name='clinic.patient',
        string="Patient",
    )
    appointment_id = fields.Many2one(
        comodel_name='hospital.appointment',
        string="Appointment",
    )
    bill_date = fields.Date(
        string="Bill Date",
        default=fields.Date.today,
    )
    billing_line_ids = fields.One2many(
        comodel_name='hospital.billing.line',
        inverse_name='billing_id',
        string='Billing Lines',
    )
    amount = fields.Float(
        string="Amount",
        compute='_compute_amount',
        store=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('pending_patient', 'Pending Patient Payment'),
            ('patient_paid', 'Patient Paid'),
            ('pending_insurance', 'Pending Insurance Payment'),
            ('insurance_paid', 'Insurance Paid'),
            ('partially_paid', 'Partially Paid'),
            ('closed', 'Closed'),
            ('cancel', 'Cancelled'),
        ],
        default='draft',
        string="Status",
    )
    
    # Related Patient Information
    patient_id_ref = fields.Char(
        string='Patient ID',
        related='patient_id.patient_id',
        readonly=True,
    )
    doctor_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Doctor',
        related='appointment_id.doctor_id',
        store=True,
        readonly=True,
    )
    department_id = fields.Many2one(
        comodel_name='hr.department',
        string='Department',
        related='appointment_id.department_id',
        store=True,
        readonly=True,
    )
    
    # Related Insurance Information
    insurance_case_id = fields.Many2one(
        comodel_name='insurance.case',
        string='Insurance Case Number',
        related='appointment_id.insurance_case_id',
        store=True,
        readonly=True,
    )
    provider_id = fields.Many2one(
        comodel_name='clinic.insurance.provider',
        string='Insurance Provider',
        related='insurance_case_id.provider_id',
        store=True,
        readonly=True,
    )
    policy_number = fields.Char(
        string='Policy Number',
        related='insurance_case_id.policy_number',
        store=True,
        readonly=True,
    )
    membership_number = fields.Char(
        string='Member ID',
        related='insurance_case_id.membership_number',
        store=True,
        readonly=True,
    )
    verification_status = fields.Selection(
        string='Verification Status',
        related='insurance_case_id.verification_status',
        store=True,
        readonly=True,
    )
    coverage_status = fields.Selection(
        string='Coverage Status',
        related='insurance_case_id.coverage_status',
        store=True,
        readonly=True,
    )
    copay_percentage = fields.Float(
        string='Coverage Percentage',
        related='insurance_case_id.copay_percentage',
        store=True,
        readonly=True,
    )
    expiry_date = fields.Date(
        string='Coverage Expiry Date',
        related='insurance_case_id.expiry_date',
        store=True,
        readonly=True,
    )
    
    # Coverage Calculation
    insurance_amount = fields.Float(
        string="Insurance Pays",
        compute='_compute_insurance_amounts',
        store=True,
    )
    patient_amount = fields.Float(
        string="Patient Pays",
        compute='_compute_insurance_amounts',
        store=True,
    )

    @api.depends('amount', 'insurance_case_id', 'coverage_status', 'copay_percentage', 'appointment_id.payment_type')
    def _compute_insurance_amounts(self):
        for rec in self:
            if rec.appointment_id and rec.appointment_id.payment_type == 'insurance' and rec.insurance_case_id and rec.verification_status == 'verified':
                if rec.coverage_status == 'covered':
                    rec.insurance_amount = rec.amount
                    rec.patient_amount = 0.0
                elif rec.coverage_status == 'partially':
                    copay = rec.copay_percentage or 0.0
                    rec.patient_amount = rec.amount * (copay / 100.0)
                    rec.insurance_amount = rec.amount - rec.patient_amount
                elif rec.coverage_status == 'not_covered':
                    rec.insurance_amount = 0.0
                    rec.patient_amount = rec.amount
                else:
                    rec.insurance_amount = 0.0
                    rec.patient_amount = rec.amount
            else:
                rec.insurance_amount = 0.0
                rec.patient_amount = rec.amount

    @api.depends('billing_line_ids.price_subtotal')
    def _compute_amount(self):
        for rec in self:
            rec.amount = sum(rec.billing_line_ids.mapped('price_subtotal'))

    @api.onchange('appointment_id')
    def _onchange_appointment_id(self):
        if self.appointment_id:
            if not self.patient_id and self.appointment_id.patient_id:
                self.patient_id = self.appointment_id.patient_id.id
            fees = self.appointment_id.consultation_fees
            doctor_name = self.appointment_id.doctor_id.name
            line_name = f"Consultation Fee - Dr. {doctor_name}" if doctor_name else "Consultation Fee"
            existing_line = self.billing_line_ids.filtered(lambda l: "Consultation Fee" in (l.name or ''))
            if existing_line:
                existing_line[0].price_unit = fees
            else:
                new_line_vals = {
                    'name': line_name,
                    'quantity': 1.0,
                    'price_unit': fees,
                }
                self.billing_line_ids = [(0, 0, new_line_vals)]

    def _create_triage_request(self):
        for rec in self:
            if rec.appointment_id:
                # Check if a triage request already exists for this appointment
                existing = self.env['hospital.nurse.triage'].search([('appointment_id', '=', rec.appointment_id.id)], limit=1)
                if not existing:
                    self.env['hospital.nurse.triage'].create({
                        'patient_id': rec.patient_id.id,
                        'appointment_id': rec.appointment_id.id,
                        'state': 'draft',
                    })

    def write(self, vals):
        res = super(HospitalBilling, self).write(vals)
        if 'state' in vals and vals['state'] in ('pending_insurance', 'closed', 'patient_paid'):
            self._create_triage_request()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('hospital.billing') or '/'
        records = super(HospitalBilling, self).create(vals_list)
        for rec in records:
            if rec.state in ('pending_insurance', 'closed', 'patient_paid'):
                rec._create_triage_request()
        return records

    # Workflow Actions / Buttons
    def action_generate_bill(self):
        for rec in self:
            if rec.state == 'draft':
                if rec.appointment_id.payment_type == 'insurance' and rec.insurance_case_id and rec.verification_status == 'verified':
                    if rec.patient_amount == 0:
                        rec.state = 'pending_insurance'
                    else:
                        rec.state = 'pending_patient'
                else:
                    rec.state = 'pending_patient'

    def action_collect_copayment(self):
        for rec in self:
            if rec.state in ('draft', 'pending_patient'):
                if rec.appointment_id.payment_type == 'insurance' and rec.insurance_case_id and rec.verification_status == 'verified':
                    if rec.insurance_amount > 0:
                        rec.state = 'pending_insurance'
                    else:
                        rec.state = 'closed'
                else:
                    rec.state = 'closed'

    def action_submit_insurance_claim(self):
        for rec in self:
            if rec.state in ('draft', 'pending_patient', 'pending_insurance'):
                rec.state = 'pending_insurance'

    def action_receive_insurance_payment(self):
        for rec in self:
            if rec.state in ('pending_insurance', 'partially_paid', 'draft'):
                rec.state = 'insurance_paid'

    def action_close_bill(self):
        for rec in self:
            rec.state = 'closed'

    def action_pay(self):
        for rec in self:
            rec.state = 'closed'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def action_print_bill(self):
        self.ensure_one()
        return self.env.ref('billing_management.action_report_hospital_bill').report_action(self)

    def action_send_email(self):
        self.ensure_one()
        template = self.env.ref('billing_management.email_template_hospital_bill', raise_if_not_found=False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', raise_if_not_found=False)
        ctx = {
            'default_model': 'hospital.billing',
            'default_res_ids': self.ids,
            'default_use_template': bool(template),
            'default_template_id': template.id if template else False,
            'default_composition_mode': 'comment',
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


class HospitalBillingLine(models.Model):
    _name = 'hospital.billing.line'
    _description = 'Hospital Billing Line'

    billing_id = fields.Many2one(
        comodel_name='hospital.billing',
        string='Billing Reference',
        ondelete='cascade',
        required=True,
    )
    name = fields.Char(
        string='Description',
        required=True,
    )
    quantity = fields.Float(
        string='Quantity',
        default=1.0,
    )
    price_unit = fields.Float(
        string='Unit Price',
        required=True,
    )
    price_subtotal = fields.Float(
        string='Subtotal',
        compute='_compute_price_subtotal',
        store=True,
    )

    @api.depends('quantity', 'price_unit')
    def _compute_price_subtotal(self):
        for rec in self:
            rec.price_subtotal = rec.quantity * rec.price_unit


class HospitalAppointment(models.Model):
    _inherit = 'hospital.appointment'

    billing_ids = fields.One2many(
        comodel_name='hospital.billing',
        inverse_name='appointment_id',
        string='Billing & Payments',
    )

    @api.model_create_multi
    def create(self, vals_list):
        appointments = super(HospitalAppointment, self).create(vals_list)
        for appt in appointments:
            self.env['hospital.billing'].create({
                'patient_id': appt.patient_id.id,
                'appointment_id': appt.id,
                'bill_date': appt.appointment_date or fields.Date.today(),
                'state': 'draft',
                'billing_line_ids': [(0, 0, {
                    'name': f"Consultation Fee - Dr. {appt.doctor_id.name}",
                    'quantity': 1.0,
                    'price_unit': appt.consultation_fees,
                })]
            })
        return appointments



