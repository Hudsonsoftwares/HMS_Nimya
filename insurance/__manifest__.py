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
        'data/insurance_sequence.xml',
        'views/clinic_insurance_provider_views.xml',
        'views/insurance_menu.xml',
    ],

    'installable': True,
    'application': True,
}