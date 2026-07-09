# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PatientInsuranceDocument(models.Model):
    _name = 'patient.insurance.document'
    _description = 'Patient Insurance Document'
    _order = 'upload_date desc, id desc'

    patient_id = fields.Many2one(
        comodel_name='clinic.patient',
        string='Patient',
        ondelete='cascade',
        required=True,
    )
    document_type = fields.Selection([
        ('insurance_card', 'Insurance Card'),
        ('policy_document', 'Policy Document'),
        ('membership_card', 'Membership Card'),
        ('health_card', 'Health Card'),
        ('referral_letter', 'Referral Letter'),
        ('previous_approval', 'Previous Approval Letter'),
        ('claim_form', 'Claim Form'),
        ('other', 'Other'),
    ], string='Document Type', required=True)

    name = fields.Char(
        string='Document Name',
        required=True,
    )
    attachment = fields.Binary(
        string='Attachment',
        required=True,
    )
    attachment_filename = fields.Char(
        string='Attachment Filename',
    )
    issue_date = fields.Date(
        string='Issue Date',
    )
    expiry_date = fields.Date(
        string='Expiry Date',
    )
    uploaded_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Uploaded By',
        default=lambda self: self.env.user,
        readonly=True,
    )
    upload_date = fields.Date(
        string='Upload Date',
        default=fields.Date.context_today,
        readonly=True,
    )
    remarks = fields.Text(
        string='Remarks',
    )

    @api.constrains('attachment', 'attachment_filename')
    def _check_attachment_type(self):
        for record in self:
            if record.attachment and record.attachment_filename:
                filename = record.attachment_filename.lower()
                allowed_extensions = ('.pdf', '.png', '.jpg', '.jpeg')
                if not filename.endswith(allowed_extensions):
                    raise ValidationError(_("Only PDF, PNG, JPG, and JPEG files are allowed for insurance documents."))
