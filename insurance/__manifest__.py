{
    'name': 'Insurance',
    'version': '18.0.1.0.0',
    'category': 'Healthcare',
    'summary': 'Insurance Management',
    'author': 'Hudson Software Solutions',

    'depends': [
        'base',
        'contacts',
        'mail',
        'Clinic_master',
    ],

    'data': [
        'security/insurance_security.xml',
        'security/ir.model.access.csv',
        'data/insurance_sequence.xml',
        'views/clinic_insurance_provider_views.xml',
        'views/insurance_policy_views.xml',
        'views/insurance_preauthorization_views.xml',
        'views/insurance_case_views.xml',
        'views/clinic_patient_views.xml',
        'views/insurance_menu.xml',
        'views/fetchmail_server_views.xml',
        'views/dashboard_views.xml',
    ],

    'installable': True,
    'application': True,
}