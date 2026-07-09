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
    lab_line_ids = fields.One2many(
        comodel_name='hospital.consultation.lab.line',
        inverse_name='consultation_id',
        string='Laboratory Requests',
    )
    
    # Referrals & Admissions (Orders)
    referral_doctor_id = fields.Many2one(comodel_name='hr.employee', string="Referral Doctor")
    referral_reason = fields.Text(string="Referral Reason")
    admission_required = fields.Boolean(string="Admission Required", default=False)
    admission_notes = fields.Text(string="Admission Notes")

    # AI Letters & Certificates
    ai_referral_letter = fields.Html(string="Referral Letter")
    ai_fitness_certificate = fields.Html(string="Fitness Certificate")
    ai_medical_certificate = fields.Html(string="Medical Certificate")

    document_ids = fields.One2many(
        comodel_name='hospital.patient.document',
        inverse_name='consultation_id',
        string='Generated Documents',
    )

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

    previous_visits_count = fields.Integer(
        string="Previous Visits Count",
        compute="_compute_previous_visits_count",
    )

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

    def _compute_previous_visits_count(self):
        for rec in self:
            if rec.patient_id:
                rec.previous_visits_count = self.search_count([
                    ('patient_id', '=', rec.patient_id.id),
                    ('id', '!=', rec.id)
                ])
            else:
                rec.previous_visits_count = 0

    def action_view_medical_history(self):
        self.ensure_one()
        return {
            'name': 'Patient Medical History',
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.consultation',
            'domain': [('patient_id', '=', self.patient_id.id), ('id', '!=', self.id)],
            'view_mode': 'list,form',
            'target': 'current',
        }

    def action_view_appointment(self):
        self.ensure_one()
        if self.appointment_id:
            return {
                'name': 'Linked Appointment Details',
                'type': 'ir.actions.act_window',
                'res_model': 'hospital.appointment',
                'res_id': self.appointment_id.id,
                'view_mode': 'form',
                'target': 'new',
            }

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
        wiz = self.env['consultation.document.wizard'].create({
            'consultation_id': self.id,
            'document_type': 'referral',
            'document_title': f"Referral Letter - {self.patient_name}",
            'content': res,
            'patient_email': self.patient_id.email or '',
        })
        return {
            'name': 'Send, Print & Save Referral Letter',
            'type': 'ir.actions.act_window',
            'res_model': 'consultation.document.wizard',
            'res_id': wiz.id,
            'view_mode': 'form',
            'target': 'new',
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
        wiz = self.env['consultation.document.wizard'].create({
            'consultation_id': self.id,
            'document_type': 'fitness',
            'document_title': f"Fitness Certificate - {self.patient_name}",
            'content': res,
            'patient_email': self.patient_id.email or '',
        })
        return {
            'name': 'Send, Print & Save Fitness Certificate',
            'type': 'ir.actions.act_window',
            'res_model': 'consultation.document.wizard',
            'res_id': wiz.id,
            'view_mode': 'form',
            'target': 'new',
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
        wiz = self.env['consultation.document.wizard'].create({
            'consultation_id': self.id,
            'document_type': 'medical',
            'document_title': f"Medical Certificate - {self.patient_name}",
            'content': res,
            'patient_email': self.patient_id.email or '',
        })
        return {
            'name': 'Send, Print & Save Medical Certificate',
            'type': 'ir.actions.act_window',
            'res_model': 'consultation.document.wizard',
            'res_id': wiz.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_trigger_speech_rec(self):
        self.ensure_one()
        return {
            'name': 'Speech Translation Wizard',
            'type': 'ir.actions.act_window',
            'res_model': 'consultation.speech.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_consultation_id': self.id,
            }
        }


class ConsultationSpeechWizard(models.TransientModel):
    _name = 'consultation.speech.wizard'
    _description = 'Speech Translation Wizard'

    consultation_id = fields.Many2one(
        comodel_name='hospital.consultation',
        string="Consultation Reference",
        required=True,
        ondelete='cascade',
    )
    speech_language = fields.Selection([
        ('ar-SA', 'Arabic (Saudi Arabia)'),
        ('ar-EG', 'Arabic (Egypt)'),
        ('ar-AE', 'Arabic (UAE)'),
        ('en-US', 'English (US)')
    ], string="Spoken Language", default="ar-SA", required=True)
    raw_transcript = fields.Text(string="Spoken Transcript")
    english_summary = fields.Text(string="Translated & Summarized Text (English)")
    voice_recorder_html = fields.Html(
        string="Recorder Widget",
        compute="_compute_voice_recorder_html",
        sanitize=False,
    )

    def _compute_voice_recorder_html(self):
        for rec in self:
            rec.voice_recorder_html = """
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; text-align: center; margin-bottom: 15px;">
                <div style="font-size: 14px; font-weight: bold; color: #475569; margin-bottom: 10px;">🎙️ Voice Recorder Control</div>
                <button type="button" id="btn_start_rec" class="btn btn-danger" style="margin-right: 10px; font-weight: bold;">🔴 Start Recording</button>
                <button type="button" id="btn_stop_rec" class="btn btn-secondary" style="font-weight: bold;" disabled="true">🛑 Stop</button>
                <div id="rec_status" style="font-size: 13px; font-weight: bold; color: #0284c7; margin-top: 10px; min-height: 18px;">Status: Idle</div>
            </div>
            """

    def action_translate_summarize(self):
        self.ensure_one()
        api_key = self.env['ir.config_parameter'].sudo().get_param('Groq') or \
                  self.env['ir.config_parameter'].sudo().get_param('groq.api_key') or \
                  self.env['ir.config_parameter'].sudo().get_param('groq_api_key')
        
        prompt = (
            "You are a helpful clinical transcription assistant. "
            "Translate the following patient speech transcription from Arabic to English if it is in Arabic. "
            "Then, summarize the transcribed consultation dialog into exactly two or three concise, professional sentences. "
            "Focus only on symptoms, complaints, and diagnosis. "
            "Transcription:\n"
            f"\"{self.raw_transcript}\"\n\n"
            "Output ONLY the final English summary. Do not include any intro, outro, or remarks."
        )
        
        summary = self.raw_transcript or ""
        if api_key and self.raw_transcript:
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
                "temperature": 0.3
            }
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=15)
                if response.status_code == 200:
                    summary = response.json()['choices'][0]['message']['content'].strip()
            except Exception:
                pass
        
        self.write({'english_summary': summary})
        return {
            'name': 'Speech Translation Wizard',
            'type': 'ir.actions.act_window',
            'res_model': 'consultation.speech.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_confirm_insert(self):
        self.ensure_one()
        if self.english_summary:
            current_notes = self.consultation_id.chief_complaint or ""
            new_notes = f"{current_notes}\n\n[Recorded Summary]: {self.english_summary}" if current_notes else f"[Recorded Summary]: {self.english_summary}"
            self.consultation_id.write({
                'chief_complaint': new_notes.strip()
            })
        return {'type': 'ir.actions.act_window_close'}


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


class HospitalConsultationLabLine(models.Model):
    _name = 'hospital.consultation.lab.line'
    _description = 'Consultation Laboratory Request Line'

    consultation_id = fields.Many2one(
        comodel_name='hospital.consultation',
        string='Consultation Reference',
        ondelete='cascade',
        required=True,
    )
    test_name = fields.Char(string='Test Name', required=True)
    instruction = fields.Char(string='Instructions')
    urgency = fields.Selection([
        ('normal', 'Normal'),
        ('urgent', 'Urgent')
    ], string='Urgency', default='normal', required=True)


from odoo import http

class ConsultationPrintController(http.Controller):
    @http.route('/consultation/print_document/<int:doc_id>', type='http', auth='user', website=False)
    def print_document(self, doc_id, **kwargs):
        doc = http.request.env['hospital.patient.document'].browse(doc_id)
        if not doc.exists():
            return "Document not found"
        html_content = f"""
        <!DOCTYPE html>
        <html>
            <head>
                <title>{doc.title}</title>
                <style>
                    body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; margin: 40px; color: #1e293b; line-height: 1.6; background-color: #f8fafc; }}
                    .no-print {{
                        margin-bottom: 20px;
                        padding: 12px;
                        background: #f1f5f9;
                        border-radius: 6px;
                        display: flex;
                        gap: 10px;
                    }}
                    .btn-print {{
                        padding: 8px 18px;
                        background: #0284c7;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                        font-weight: bold;
                        font-size: 14px;
                    }}
                    .btn-print:hover {{ background: #0369a1; }}
                    @media print {{
                        .no-print {{ display: none !important; }}
                        body {{ margin: 0; background-color: white; }}
                        .document-card {{ border: none !important; box-shadow: none !important; padding: 0 !important; }}
                    }}
                </style>
            </head>
            <body>
                <div class="no-print">
                    <button class="btn-print" onclick="window.print()">🖨️ Print Document</button>
                    <button class="btn-print" style="background: #64748b;" onclick="window.close()">❌ Close Preview</button>
                </div>
                <div class="document-card" style="background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 45px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); min-height: 700px;">
                    {doc.content}
                </div>
            </body>
        </html>
        """
        return html_content


class HospitalPatientDocument(models.Model):
    _name = 'hospital.patient.document'
    _description = 'Patient Clinical Document History'
    _order = 'id desc'

    patient_id = fields.Many2one(
        comodel_name='clinic.patient',
        string='Patient',
        required=True,
    )
    consultation_id = fields.Many2one(
        comodel_name='hospital.consultation',
        string='Consultation Reference',
    )
    document_type = fields.Selection([
        ('referral', 'Referral Letter'),
        ('fitness', 'Fitness Certificate'),
        ('medical', 'Medical Certificate')
    ], string='Document Type', required=True)
    date_generated = fields.Date(string='Date Generated', default=fields.Date.context_today)
    title = fields.Char(string='Document Title', required=True)
    content = fields.Html(string='Content', required=True)

    def action_open_document_preview(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/consultation/print_document/{self.id}',
            'target': 'new',
        }


class ConsultationDocumentWizard(models.TransientModel):
    _name = 'consultation.document.wizard'
    _description = 'Consultation Document Wizard'

    consultation_id = fields.Many2one(
        comodel_name='hospital.consultation',
        string='Consultation',
        required=True,
    )
    document_type = fields.Selection([
        ('referral', 'Referral Letter'),
        ('fitness', 'Fitness Certificate'),
        ('medical', 'Medical Certificate')
    ], string='Document Type', required=True)
    document_title = fields.Char(string='Document Title', required=True)
    content = fields.Html(string='Document Content', required=True)
    patient_email = fields.Char(string='Patient Email')

    def action_save(self):
        self.ensure_one()
        self.env['hospital.patient.document'].create({
            'patient_id': self.consultation_id.patient_id.id,
            'consultation_id': self.consultation_id.id,
            'document_type': self.document_type,
            'title': self.document_title,
            'content': self.content,
        })
        if self.document_type == 'referral':
            self.consultation_id.ai_referral_letter = self.content
        elif self.document_type == 'fitness':
            self.consultation_id.ai_fitness_certificate = self.content
        elif self.document_type == 'medical':
            self.consultation_id.ai_medical_certificate = self.content
        return {'type': 'ir.actions.act_window_close'}

    def action_send_email(self):
        self.ensure_one()
        self.action_save()
        if self.patient_email:
            mail_values = {
                'subject': self.document_title,
                'body_html': self.content,
                'email_to': self.patient_email,
            }
            self.env['mail.mail'].sudo().create(mail_values).send()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Email Sent',
                    'message': f'Document successfully sent to {self.patient_email}.',
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No Email',
                    'message': 'No patient email address provided to send the document.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

    def action_print(self):
        self.ensure_one()
        doc = self.env['hospital.patient.document'].create({
            'patient_id': self.consultation_id.patient_id.id,
            'consultation_id': self.consultation_id.id,
            'document_type': self.document_type,
            'title': self.document_title,
            'content': self.content,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/consultation/print_document/{doc.id}',
            'target': 'new',
        }