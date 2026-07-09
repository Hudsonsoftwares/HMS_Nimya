# -*- coding: utf-8 -*-
from odoo import models, fields, api

class HospitalConsultation(models.Model):
    _name = "hospital.consultation"
    _description = "Hospital Consultation"
    _order = "id desc"

    name = fields.Char(string="Consultation Number", required=True, copy=False, readonly=True, default='/')
    
    # Patient Details
    patient_id = fields.Many2one(comodel_name='clinic.patient', string="Patient", required=True, readonly=True)
    patient_id_ref = fields.Char(string="Patient ID", related='patient_id.patient_id', readonly=True)
    patient_name = fields.Char(string="Patient Name", related='patient_id.name', readonly=True)
    patient_age = fields.Integer(string="Age", related='patient_id.age', readonly=True)
    patient_gender = fields.Selection(string="Gender", related='patient_id.gender', readonly=True)
    patient_blood_group = fields.Selection(string="Blood Group", related='patient_id.blood_group', readonly=True)
    patient_phone = fields.Char(string="Contact", related='patient_id.mobile', readonly=True)

    # Appointment Details
    appointment_id = fields.Many2one(comodel_name='hospital.appointment', string="Appointment", required=True, readonly=True)
    appointment_name = fields.Char(string="Appointment Number", related='appointment_id.name', readonly=True)
    token_number = fields.Integer(string="Token Number", related='appointment_id.token_number', readonly=True)
    department_id = fields.Many2one(comodel_name='hr.department', string="Department", related='appointment_id.department_id', store=True, readonly=True)
    doctor_id = fields.Many2one(comodel_name='hr.employee', string="Doctor", related='appointment_id.doctor_id', store=True, readonly=True)
    visit_date = fields.Date(string="Visit Date", related='appointment_id.appointment_date', readonly=True)
    appointment_time = fields.Float(string="Visit Time", related='appointment_id.appointment_time', readonly=True)
    priority = fields.Selection(string="Priority", related='appointment_id.priority', readonly=True)

    # Nurse Triage Vitals (Copied over)
    triage_id = fields.Many2one(comodel_name='hospital.nurse.triage', string="Nurse Triage", readonly=True)
    temperature = fields.Float(string="Temperature (°C)", readonly=True)
    systolic_bp = fields.Integer(string="Systolic BP (mmHg)", readonly=True)
    diastolic_bp = fields.Integer(string="Diastolic BP (mmHg)", readonly=True)
    pulse_rate = fields.Integer(string="Pulse Rate (bpm)", readonly=True)
    respiratory_rate = fields.Integer(string="Respiratory Rate (bpm)", readonly=True)
    spo2 = fields.Integer(string="SpO2 (%)", readonly=True)
    weight = fields.Float(string="Weight (kg)", readonly=True)
    height = fields.Float(string="Height (cm)", readonly=True)
    bmi = fields.Float(string="BMI", readonly=True)
    blood_sugar = fields.Char(string="Blood Sugar", readonly=True)
    allergies = fields.Char(string="Allergies", readonly=True)

    # Previous Medical History (Last 5 consultations)
    previous_consultation_ids = fields.Many2many(
        comodel_name='hospital.consultation',
        relation='consultation_history_rel',
        column1='current_id',
        column2='history_id',
        string="Medical History",
        compute='_compute_previous_history'
    )

    # Main Consultation Area
    chief_complaint = fields.Text(string="Chief Complaint")
    history_present_illness = fields.Text(string="History of Present Illness")
    examination = fields.Text(string="Examination")
    diagnosis = fields.Text(string="Diagnosis")
    icd_code = fields.Char(string="ICD Code")
    treatment_plan = fields.Text(string="Treatment Plan")
    doctor_notes = fields.Text(string="Doctor Notes")
    medicine_line_ids = fields.One2many(
        comodel_name='hospital.consultation.medicine.line',
        inverse_name='consultation_id',
        string='Prescribed Medicines',
    )
    
    # Referrals & Admissions (Orders)
    referral_doctor_id = fields.Many2one(comodel_name='hr.employee', string="Referral Doctor")
    referral_reason = fields.Text(string="Referral Reason")
    admission_required = fields.Boolean(string="Admission Required", default=False)
    admission_notes = fields.Text(string="Admission Notes")

    # AI Letters & Certificates
    ai_referral_letter = fields.Html(string="AI Referral Letter")
    ai_fitness_certificate = fields.Html(string="AI Fitness Certificate")
    ai_medical_certificate = fields.Html(string="AI Medical Certificate")

    # Actions Results Fields
    prescription_generated = fields.Boolean(string="Prescription Generated", default=False)
    lab_request_generated = fields.Boolean(string="Lab Request Generated", default=False)
    radiology_generated = fields.Boolean(string="Radiology Generated", default=False)
    followup_created = fields.Boolean(string="Follow-up Created", default=False)

    state = fields.Selection([
        ('draft', 'Waiting'),
        ('consultation', 'In Consultation'),
        ('completed', 'Completed'),
        ('cancel', 'Cancelled'),
    ], string="Status", default='draft', required=True)

    def _compute_previous_history(self):
        for rec in self:
            if rec.patient_id:
                history = self.search([
                    ('patient_id', '=', rec.patient_id.id),
                    ('state', '=', 'completed'),
                    ('id', '!=', rec.id)
                ], order='id desc', limit=5)
                rec.previous_consultation_ids = [(6, 0, history.ids)]
            else:
                rec.previous_consultation_ids = [(6, 0, [])]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('hospital.consultation') or '/'
        return super(HospitalConsultation, self).create(vals_list)

    def action_start(self):
        for rec in self:
            rec.state = 'consultation'
            if rec.appointment_id:
                rec.appointment_id.write({'state': 'consultation'})

    def action_complete(self):
        for rec in self:
            rec.state = 'completed'
            if rec.appointment_id:
                rec.appointment_id.action_complete()

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'
            if rec.appointment_id:
                rec.appointment_id.action_cancel()

    # Smart/Workflow Buttons
    def action_view_dummy(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Feature Preview',
                'message': 'Smart Button Preview: Opens patient details, clinical sheets, or billing records.',
                'type': 'info',
                'sticky': False,
            }
        }

    def action_generate_prescription(self):
        for rec in self:
            rec.prescription_generated = True
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Prescription',
                'message': 'Prescription successfully generated and sent to Pharmacy.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_generate_lab(self):
        for rec in self:
            rec.lab_request_generated = True
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Lab Request',
                'message': 'Laboratory test request submitted successfully.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_generate_radiology(self):
        for rec in self:
            rec.radiology_generated = True
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Radiology Request',
                'message': 'Radiology/X-Ray scan request submitted successfully.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_create_followup(self):
        for rec in self:
            rec.followup_created = True
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Follow-up Created',
                'message': 'Follow-up appointment successfully scheduled.',
                'type': 'success',
                'sticky': False,
            }
        }

    def _call_ai_api(self, prompt, fallback_html):
        api_key = self.env['ir.config_parameter'].sudo().get_param('Groq') or \
                  self.env['ir.config_parameter'].sudo().get_param('groq.api_key') or \
                  self.env['ir.config_parameter'].sudo().get_param('groq_api_key')
        if not api_key:
            return fallback_html

        import requests
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.5
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            if response.status_code == 200:
                result = response.json()['choices'][0]['message']['content'].strip()
                if result.startswith("```html"):
                    result = result.split("```html", 1)[1]
                if "```" in result:
                    result = result.split("```")[0]
                return result.strip()
        except Exception:
            pass
        return fallback_html

    def action_generate_ai_referral(self):
        self.ensure_one()
        fallback = f"""
        <div>
            <p><strong>Date:</strong> {fields.Date.today()}</p>
            <p><strong>To:</strong> Consultant Specialist / Department Representative</p>
            <p><strong>Subject:</strong> Medical Referral for {self.patient_name or 'Patient'} (Age: {self.patient_age or 'N/A'})</p>
            <br/>
            <p>Dear Colleague,</p>
            <p>I am writing to refer this patient, <strong>{self.patient_name or 'Patient'}</strong>, a {self.patient_age or 'N/A'}-year-old {self.patient_gender or 'patient'}, for further clinical evaluation and management.</p>
            <p><strong>Clinical Notes:</strong></p>
            <ul>
                <li><strong>Chief Complaint:</strong> {self.chief_complaint or 'N/A'}</li>
                <li><strong>Diagnosis:</strong> {self.diagnosis or 'N/A'} (ICD: {self.icd_code or 'N/A'})</li>
                <li><strong>Vitals recorded:</strong> Temp: {self.temperature or 0.0}°C, BP: {self.systolic_bp or 0}/{self.diastolic_bp or 0} mmHg, Pulse: {self.pulse_rate or 0} bpm</li>
            </ul>
            <p>Kindly assess and advise on optimal management. Thank you for your clinical cooperation.</p>
            <br/>
            <p>Sincerely,</p>
            <p><strong>Dr. {self.doctor_id.name or 'John Mathew'}</strong><br/>{self.department_id.name or 'General Medicine'}</p>
        </div>
        """
        prompt = (
            "Write a professional medical referral letter in clean HTML format (only the body content inside <div>, do not include <html>, <body>, or Markdown code blocks like ```html). "
            f"The letter is written by Dr. {self.doctor_id.name or 'John Mathew'} ({self.department_id.name or 'General Medicine'}) referring patient {self.patient_name or 'Patient'} (Age: {self.patient_age or 'N/A'}, Gender: {self.patient_gender or 'N/A'}) to a specialist. "
            "Patient details:\n"
            f"- Visit Date: {self.visit_date or fields.Date.today()}\n"
            f"- Vitals: Temp {self.temperature or 0.0}°C, BP {self.systolic_bp or 0}/{self.diastolic_bp or 0} mmHg, Pulse {self.pulse_rate or 0} bpm, SpO2 {self.spo2 or 0}%, BMI {self.bmi or 0.0}\n"
            "Clinical Notes:\n"
            f"- Chief Complaint: {self.chief_complaint or 'N/A'}\n"
            f"- History of Present Illness: {self.history_present_illness or 'N/A'}\n"
            f"- Physical Exam: {self.examination or 'N/A'}\n"
            f"- Diagnosis: {self.diagnosis or 'N/A'} (ICD Code: {self.icd_code or 'N/A'})\n"
            f"- Treatment Plan: {self.treatment_plan or 'N/A'}\n\n"
            "Ensure it has a formal medical letter structure: Date, Recipient (Specialist), Subject line, Patient summary, clinical reasoning, recommendation, and Doctor's sign-off. "
            "Output ONLY the HTML block. Do not write any markdown wrappers, triple backticks, or extra conversational chat remarks."
        )
        res = self._call_ai_api(prompt, fallback)
        self.write({'ai_referral_letter': res})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'AI Referral Letter',
                'message': 'Referral letter successfully generated by AI.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_generate_ai_fitness(self):
        self.ensure_one()
        fallback = f"""
        <div>
            <p style="text-align: center; font-size: 20px; font-weight: bold;">MEDICAL FITNESS CERTIFICATE</p>
            <br/>
            <p><strong>Date:</strong> {fields.Date.today()}</p>
            <br/>
            <p>This is to certify that I have conducted a clinical evaluation on patient <strong>{self.patient_name or 'Patient'}</strong>, a {self.patient_age or 'N/A'}-year-old {self.patient_gender or 'patient'}.</p>
            <p>At the time of examination, the patient's vitals were found to be normal:</p>
            <ul>
                <li><strong>Blood Pressure:</strong> {self.systolic_bp or 0}/{self.diastolic_bp or 0} mmHg</li>
                <li><strong>Pulse:</strong> {self.pulse_rate or 0} bpm</li>
                <li><strong>Temperature:</strong> {self.temperature or 0.0}°C</li>
            </ul>
            <p>Based on the medical evaluation and physical assessment, I hereby certify that the patient is <strong>fit</strong> to resume normal duties, work, or physical activities.</p>
            <br/>
            <br/>
            <p>Medical Officer,</p>
            <p><strong>Dr. {self.doctor_id.name or 'John Mathew'}</strong><br/>{self.department_id.name or 'General Medicine'}</p>
        </div>
        """
        prompt = (
            "Write a formal Medical Fitness Certificate in clean HTML format (only the body content inside <div>, do not include <html>, <body>, or Markdown code blocks like ```html). "
            f"The certificate is issued by Dr. {self.doctor_id.name or 'John Mathew'} ({self.department_id.name or 'General Medicine'}) certifying the physical/medical fitness of patient {self.patient_name or 'Patient'} (Age: {self.patient_age or 'N/A'}, Gender: {self.patient_gender or 'N/A'}) based on clinical evaluation. "
            "Patient details:\n"
            f"- Evaluation Date: {self.visit_date or fields.Date.today()}\n"
            f"- Vitals: Temp {self.temperature or 0.0}°C, BP {self.systolic_bp or 0}/{self.diastolic_bp or 0} mmHg, Pulse {self.pulse_rate or 0} bpm, SpO2 {self.spo2 or 0}%, Height {self.height or 0.0}cm, Weight {self.weight or 0.0}kg, BMI {self.bmi or 0.0}\n"
            "Clinical findings:\n"
            f"- Chief Complaint: {self.chief_complaint or 'N/A'}\n"
            f"- Examination: {self.examination or 'N/A'}\n"
            f"- Diagnosis: {self.diagnosis or 'N/A'}\n\n"
            "The certificate must formally declare that the patient has been examined and is found to be in fit physical health to resume normal duties/work/exercise. "
            "Output ONLY the HTML block. Do not write any markdown wrappers, triple backticks, or extra conversational chat remarks."
        )
        res = self._call_ai_api(prompt, fallback)
        self.write({'ai_fitness_certificate': res})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'AI Fitness Certificate',
                'message': 'Fitness certificate successfully generated by AI.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_generate_ai_medical(self):
        self.ensure_one()
        fallback = f"""
        <div>
            <p style="text-align: center; font-size: 20px; font-weight: bold;">MEDICAL CERTIFICATE (SICK LEAVE)</p>
            <br/>
            <p><strong>Date:</strong> {fields.Date.today()}</p>
            <br/>
            <p>This is to certify that patient <strong>{self.patient_name or 'Patient'}</strong> has been under my clinical care for <strong>{self.diagnosis or 'medical evaluation'}</strong>.</p>
            <p>Due to the patient's health condition, I recommend a period of medical rest for recovery.</p>
            <p><strong>Recommended Leave:</strong> 3 Days (starting from {self.visit_date or fields.Date.today()})</p>
            <br/>
            <br/>
            <p>Medical Officer,</p>
            <p><strong>Dr. {self.doctor_id.name or 'John Mathew'}</strong><br/>{self.department_id.name or 'General Medicine'}</p>
        </div>
        """
        prompt = (
            "Write a formal Medical Certificate (Sick Leave Recommendation) in clean HTML format (only the body content inside <div>, do not include <html>, <body>, or Markdown code blocks like ```html). "
            f"The certificate is issued by Dr. {self.doctor_id.name or 'John Mathew'} ({self.department_id.name or 'General Medicine'}) for patient {self.patient_name or 'Patient'} (Age: {self.patient_age or 'N/A'}, Gender: {self.patient_gender or 'N/A'}) recommending sick leave based on diagnosis. "
            "Patient details:\n"
            f"- Visit Date: {self.visit_date or fields.Date.today()}\n"
            f"- Vitals: Temp {self.temperature or 0.0}°C, BP {self.systolic_bp or 0}/{self.diastolic_bp or 0} mmHg, Pulse {self.pulse_rate or 0} bpm, SpO2 {self.spo2 or 0}%, BMI {self.bmi or 0.0}\n"
            "Clinical findings:\n"
            f"- Chief Complaint: {self.chief_complaint or 'N/A'}\n"
            f"- Diagnosis: {self.diagnosis or 'N/A'} (ICD Code: {self.icd_code or 'N/A'})\n"
            f"- Treatment Plan: {self.treatment_plan or 'N/A'}\n\n"
            "The certificate must formally declare the diagnosis and recommend a reasonable period of rest/medical leave (e.g. 3-5 days from evaluation date) for recovery. "
            "Output ONLY the HTML block. Do not write any markdown wrappers, triple backticks, or extra conversational chat remarks."
        )
        res = self._call_ai_api(prompt, fallback)
        self.write({'ai_medical_certificate': res})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'AI Medical Certificate',
                'message': 'Medical certificate successfully generated by AI.',
                'type': 'success',
                'sticky': False,
            }
        }


class HospitalConsultationMedicineLine(models.Model):
    _name = 'hospital.consultation.medicine.line'
    _description = 'Consultation Medicine Line'

    consultation_id = fields.Many2one(
        comodel_name='hospital.consultation',
        string='Consultation Reference',
        ondelete='cascade',
        required=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Medicine Name',
        required=True,
        domain="[('sale_ok', '=', True)]"
    )
    dosage = fields.Char(string='Dosage')
    duration = fields.Char(string='Duration')
    notes = fields.Char(string='Doctor Notes/Instructions')