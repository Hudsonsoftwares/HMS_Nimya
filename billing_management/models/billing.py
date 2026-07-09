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
            ('paid', 'Paid'),
            ('cancel', 'Cancelled'),
        ],
        default='draft',
        string="Status",
    )

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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('hospital.billing') or '/'
        return super(HospitalBilling, self).create(vals_list)

    def action_pay(self):
        for rec in self:
            rec.state = 'paid'

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



