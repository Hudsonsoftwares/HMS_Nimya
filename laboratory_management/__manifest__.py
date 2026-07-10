{
    'name': 'Laboratory Management',
    'version': '1.0',
    'summary': 'Hospital Laboratory Module',
    'author': 'Hudson Software Solutions',
    'category': 'Healthcare',
    'license': 'LGPL-3',

    'depends': [
        'base',
        'mail',
        'contacts',
        'Clinic_master',
        'hr',
        'product',
        'maintenance',
    ],

    'data': [
        'security/ir.model.access.csv',
        'data/laboratory_sequence.xml',
        'report/laboratory_report_templates.xml',
        'views/laboratory_views.xml',
    ],

    'installable': True,
    'application': True,
}