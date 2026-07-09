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
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/laboratory_views.xml',
    ],

    'installable': True,
    'application': True,
}