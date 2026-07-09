{
    'name': 'Billing & Payment',
    'version': '1.0',
    'summary': 'Hospital Billing and Payment',
    'author': 'Hudson Software Solutions',
    'category': 'Healthcare',
    'license': 'LGPL-3',

    'depends': [
        'base',
        'mail',
        'contacts',
        'Clinic_master',
        'appointment_management',
    ],

    'data': [
        'security/ir.model.access.csv',
        'data/billing_sequence.xml',
        'report/billing_templates.xml',
        'report/billing_report.xml',
        'data/billing_email_template.xml',
        'views/billing_views.xml',
    ],

    'installable': True,
    'application': True,
}
