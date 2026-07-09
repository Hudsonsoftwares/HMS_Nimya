{
    'name': 'Nurse Triage',
    'version': '1.0',
    'summary': 'Hospital Nurse Triage',
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
        'data/nurse_triage_sequence.xml',
        'views/nurse_triage_views.xml',
    ],

    'installable': True,
    'application': True,
}