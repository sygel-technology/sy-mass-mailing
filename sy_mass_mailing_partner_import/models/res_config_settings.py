# Copyright 2026 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    mailing_import_type = fields.Selection(
        selection=[
            ("email", "Email Addresses"),
            ("partner", "Odoo Contacts"),
        ],
        string="Default Mailing Import Type",
        config_parameter="sy_mass_mailing_partner_import.mailing_import_type",
        default="email",
    )
