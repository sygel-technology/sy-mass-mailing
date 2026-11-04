# Copyright 2026 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'Mailing List Reference',
    'summary': 'Add the reference field to mailing lists',
    'version': '18.0.1.0.0',
    "category": "Marketing",
    'website': 'https://sygel.es',
    'author': 'Sygel',
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'mass_mailing',
    ],
    'data': [
        "views/mailing_list_views.xml"
    ],
}
