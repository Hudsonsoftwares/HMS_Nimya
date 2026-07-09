{
    'name': 'Consultation Management',
    'version': '1.0',
    'summary': 'Hospital Consultation Module',
    'author': 'Hudson Software Solutions',
    'category': 'Healthcare',
    'license': 'LGPL-3',

    'depends': [
        'base',
        'mail',
        'contacts',
        'Clinic_master',
        'appointment_management',
        'nurse_triage',
        'product',
    ],

    'data': [
        'security/ir.model.access.csv',
        'data/consultation_sequence.xml',
        'views/consultation_views.xml',
    ],

    'installable': True,
    'application': True,
    'assets': {
        'web.assets_backend': [
            'consultation_management/static/src/js/speech_recognition.js',
        ],
    },
}