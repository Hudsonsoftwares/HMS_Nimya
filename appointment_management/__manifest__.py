{
    'name': 'Appointment Management',
    'version': '1.0',
    'summary': 'Hospital Appointment Management Module',
    'description': """
Hospital Appointment Management
==============================

Manage patient appointments, doctor schedules,
token generation and appointment workflow.
""",
    'author': 'Hudson Software Solutions',
    'website': 'https://hudsonsoftwares.com',
    'category': 'Healthcare',
    'depends': [
        'base',
        'mail',
        'contacts',
        'hr',
        'Clinic_master',
        'insurance',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/appointment_sequence.xml',
        'views/dashboard_views.xml',
        'views/appointment_views.xml',
        'views/doctor_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}