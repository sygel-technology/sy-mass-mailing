# Copyright 2026 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Mass Mailing Partner Import",
    "summary": "Imports partners from mass mailing lists",
    "version": "18.0.1.0.0",
    "category": "Marketing",
    "website": "https://github.com/sygel-technology/sy-mass-mailing",
    "author": "Sygel",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["mass_mailing"],
    "data": [
        "security/ir.model.access.csv",
        "views/mailing_contact_views.xml",
        "views/res_partner_views.xml",
        "wizard/partner_mail_list_wizard_views.xml",
        "wizard/mailing_contact_import_views.xml",
    ],
}
