# Copyright 2026 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2 import IntegrityError

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase
from odoo.tools import mute_logger


class TestMassMailingPartnerImport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
                "email": "partner@example.com",
                "ref": "TEST001",
            }
        )
        cls.mailing_contact = cls.env["mailing.contact"].create(
            {
                "name": cls.partner.name,
                "email": cls.partner.email,
                "partner_id": cls.partner.id,
            }
        )
        cls.mailing_list_1 = cls.env["mailing.list"].create(
            {"name": "Test Mailing List 1"}
        )
        cls.mailing_list_2 = cls.env["mailing.list"].create(
            {"name": "Test Mailing List 2"}
        )

    def test_mailing_contact_partner(self):
        self.assertEqual(self.mailing_contact.partner_id, self.partner)
        self.assertEqual(self.mailing_contact.partner_ref, "TEST001")

    def test_mailing_contact_unique_partner(self):
        with (
            self.assertRaises(IntegrityError),
            self.cr.savepoint(),
            mute_logger("odoo.sql_db"),
        ):
            self.env["mailing.contact"].create(
                {
                    "name": "Duplicate Contact",
                    "email": "duplicate@example.com",
                    "partner_id": self.partner.id,
                }
            )

    def test_add_to_mailing_lists(self):
        partner = self.env["res.partner"].create(
            {
                "name": "New Partner",
                "email": "newpartner@example.com",
            }
        )

        created_count, subscription_count = partner._add_to_mailing_lists(
            self.mailing_list_1 | self.mailing_list_2
        )
        contact = self.env["mailing.contact"].search([("partner_id", "=", partner.id)])
        self.assertEqual(created_count, 1)
        self.assertEqual(subscription_count, 2)
        self.assertEqual(contact.partner_id, partner)
        self.assertEqual(
            contact.list_ids,
            self.mailing_list_1 | self.mailing_list_2,
        )

    def test_add_to_mailing_lists_existing(self):
        self.partner._add_to_mailing_lists(self.mailing_list_1)
        created_count, subscription_count = self.partner._add_to_mailing_lists(
            self.mailing_list_1 | self.mailing_list_2
        )
        self.assertEqual(created_count, 0)
        self.assertEqual(subscription_count, 1)
        self.assertEqual(
            self.mailing_contact.list_ids,
            self.mailing_list_1 | self.mailing_list_2,
        )
        self.assertEqual(
            self.env["mailing.contact"].search_count(
                [("partner_id", "=", self.partner.id)]
            ),
            1,
        )

    def test_add_to_mailing_lists_opt_out(self):
        self.partner._add_to_mailing_lists(self.mailing_list_1)
        subscription = self.mailing_contact.subscription_ids.filtered(
            lambda sub: sub.list_id == self.mailing_list_1
        )
        subscription.opt_out = True
        created_count, subscription_count = self.partner._add_to_mailing_lists(
            self.mailing_list_1 | self.mailing_list_2
        )
        self.assertEqual(created_count, 0)
        self.assertEqual(subscription_count, 1)
        self.assertTrue(subscription.opt_out)
        self.assertIn(self.mailing_list_2, self.mailing_contact.list_ids)

    def test_partner_mail_list_wizard(self):
        wizard = self.env["partner.mail.list.wizard"].create(
            {
                "partner_ids": [fields.Command.set(self.partner.ids)],
                "mailing_list_ids": [
                    fields.Command.set((self.mailing_list_1 | self.mailing_list_2).ids)
                ],
            }
        )

        action = wizard.action_add_to_mailing_lists()
        self.assertEqual(action["type"], "ir.actions.act_window_close")
        self.assertEqual(
            self.mailing_contact.list_ids,
            self.mailing_list_1 | self.mailing_list_2,
        )

    def test_partner_mail_list_wizard_without_email(self):
        partner = self.env["res.partner"].create({"name": "Partner Without Email"})
        wizard = self.env["partner.mail.list.wizard"].create(
            {
                "partner_ids": [fields.Command.set(partner.ids)],
                "mailing_list_ids": [fields.Command.set(self.mailing_list_1.ids)],
            }
        )
        with self.assertRaises(UserError):
            wizard.action_add_to_mailing_lists()

        self.assertFalse(
            self.env["mailing.contact"].search([("partner_id", "=", partner.id)])
        )

    def test_mailing_contact_import_domain(self):
        wizard = self.env["mailing.contact.import"].create(
            {
                "import_type": "partner",
                "partner_domain": f"[('id', '=', {self.partner.id})]",
                "mailing_list_ids": [fields.Command.set(self.mailing_list_1.ids)],
            }
        )
        action = wizard.action_import()
        self.assertEqual(action["tag"], "display_notification")
        self.assertIn(self.mailing_list_1, self.mailing_contact.list_ids)
        self.assertEqual(
            self.env["mailing.contact"].search_count(
                [("partner_id", "=", self.partner.id)]
            ),
            1,
        )

    def test_mailing_contact_import_without_email(self):
        partner = self.env["res.partner"].create({"name": "Partner Without Email"})
        wizard = self.env["mailing.contact.import"].create(
            {
                "import_type": "partner",
                "partner_domain": f"[('id', '=', {partner.id})]",
                "mailing_list_ids": [fields.Command.set(self.mailing_list_1.ids)],
            }
        )
        with self.assertRaises(UserError):
            wizard.action_import()
        self.assertFalse(
            self.env["mailing.contact"].search([("partner_id", "=", partner.id)])
        )

    def test_mailing_contact_import_email(self):
        wizard = self.env["mailing.contact.import"].create(
            {
                "import_type": "email",
                "contact_list": "standard-import@example.com",
                "mailing_list_ids": [fields.Command.set(self.mailing_list_1.ids)],
            }
        )
        wizard.action_import()
        contact = self.env["mailing.contact"].search(
            [("email", "=", "standard-import@example.com")]
        )
        self.assertTrue(contact)
        self.assertIn(self.mailing_list_1, contact.list_ids)

    def test_partner_merge(self):
        # Crear dos partners con sus respectivos contactos de marketing.
        partner_a = self.env["res.partner"].create(
            {"name": "Partner A", "email": "merge-a@example.com"}
        )
        partner_b = self.env["res.partner"].create(
            {"name": "Partner B", "email": "merge-b@example.com"}
        )
        partner_a._add_to_mailing_lists(self.mailing_list_1)
        partner_b._add_to_mailing_lists(self.mailing_list_2)
        contact_a = partner_a.mailing_contact_ids
        contact_b = partner_b.mailing_contact_ids
        # Comprobar que los contactos están asociados a sus listas.
        self.assertIn(self.mailing_list_1, contact_a.list_ids)
        self.assertIn(self.mailing_list_2, contact_b.list_ids)
        # Recuperar la suscripción del primer contacto de marketing.
        subscription = self.env["mailing.subscription"].search(
            [
                ("contact_id", "=", contact_a.id),
                ("list_id", "=", self.mailing_list_1.id),
            ]
        )
        self.assertEqual(len(subscription), 1)
        # Marcar la suscripción como excluida.
        subscription.write({"opt_out": True})
        # Comprobar que la exclusión existe antes de fusionar.
        self.assertTrue(subscription.opt_out)
        self.assertEqual(subscription.list_id, self.mailing_list_1)
        # Fusionar ambos partners conservando el segundo como destino.
        wizard = self.env["base.partner.merge.automatic.wizard"].create({})
        wizard._merge(
            (partner_a | partner_b).ids,
            dst_partner=partner_b,
        )
        # Refrescar la caché después de la fusión.
        self.env.invalidate_all()
        # Comprobar que se conserva un único contacto de marketing.
        contacts = self.env["mailing.contact"].search(
            [("partner_id", "=", partner_b.id)]
        )
        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts, contact_b)
        # Comprobar que se conservan ambas listas.
        self.assertEqual(
            contacts.list_ids,
            self.mailing_list_1 | self.mailing_list_2,
        )
        # Comprobar que se mantiene la exclusión de la primera lista.
        subscription = self.env["mailing.subscription"].search(
            [
                ("contact_id", "=", contacts.id),
                ("list_id", "=", self.mailing_list_1.id),
            ]
        )
        self.assertEqual(len(subscription), 1)
        self.assertTrue(subscription.opt_out)
