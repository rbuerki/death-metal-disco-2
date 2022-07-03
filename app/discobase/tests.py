from datetime import date, timedelta

from django.test import TestCase
from django.urls import resolve, reverse

from discobase import views
from discobase.forms import DateForm
from discobase.models import (
    Artist,
    Country,
    Dump,
    Genre,
    Label,
    Record,
    RecordFormat,
    TrxCredit,
)


class DiscobaseModelTests(TestCase):
    """These tests don't use the fixture."""

    @classmethod
    def setUpTestData(cls):
        cls.country = Country.objects.create(
            country_name="Switzerland",
            country_code="CH",
        )

        cls.artist = Artist.objects.create(
            artist_name="Raphmadon",
            country=cls.country,
        )

        cls.genre = Genre.objects.create(
            genre_name="Metal of Death",
        )

        cls.label = Label.objects.create(
            label_name="Capsized Duck Records",
        )

        cls.record_format = RecordFormat.objects.create(
            format_name="LP",
        )

        cls.addition_trx = TrxCredit.objects.create(
            trx_date=date.today() - timedelta(days=22),
            trx_type="Addition",
            trx_value=1,
            credit_saldo=1,
            record=None,
        )

        cls.record = Record.objects.create(
            title="Album of Blood",
            year="2022",
            record_format=cls.record_format,
            color="vomit green",
            remarks="limited: 222",
            genre=cls.genre,
            purchase_date="1999-01-01",
            price=20,
        )
        cls.record.artists.set([cls.artist])
        cls.record.labels.set([cls.label])

    def test_objecs_are_created(self):
        """Objects are created with expected relations, including the
        purchase transaction for the inserted record.
        """
        r1 = Record.objects.get(genre__genre_name="Metal of Death")
        r2 = Record.objects.get(record_format__format_name="LP")
        r3 = Record.objects.get(artists__country__country_code="CH")
        r4 = Record.objects.get(labels__label_name="Capsized Duck Records")
        r5 = Record.objects.get(trx_credit__trx_type="Purchase")
        trx_add = TrxCredit.objects.get(trx_type="Addition")
        trx_pur = TrxCredit.objects.get(trx_type="Purchase")
        self.assertTrue(r1 == r2 == r3 == r4 == r5)
        self.assertEqual(trx_add.trx_date, date.today() - timedelta(days=22))
        self.assertEqual(trx_pur.trx_date, date(1999, 1, 1))
        self.assertEqual(trx_pur.credit_saldo, 0)

    def test_create_addition_credits(self):
        """Addition credits are properly created based
        on the existing trx in the database.
        """
        views.create_addition_credits(TrxCredit)
        t1 = TrxCredit.objects.filter(trx_type="Addition").count()
        t2 = TrxCredit.objects.order_by("-id").first().credit_saldo
        t3 = TrxCredit.objects.filter(id=3).get().trx_date
        self.assertEqual(t1, 3)
        self.assertEqual(t2, 2)
        self.assertEqual(t3, date.today() - timedelta(days=12))

    def test_record_removal(self):
        """Shallow copies of records are sent to the dump
        pre-delete and a removal trx is added post-delete.
        """
        r = Record.objects.first()
        r.delete()
        t1 = Dump.objects.order_by("-id").first().title
        t2 = TrxCredit.objects.order_by("-id").first()
        t3 = Record.objects.filter(id=r.id).first()
        trx_pur = TrxCredit.objects.get(trx_type="Purchase")
        self.assertEqual(t1, r.title)
        self.assertEqual(t2.trx_type, "Removal")
        self.assertEqual(t2.trx_value, 1)
        self.assertEqual(t3, None)
        self.assertEqual(trx_pur.record, None)


# TODO see also dj-books p. 187
class DiscobaseViewTests(TestCase):
    """These tests use a fixture."""

    fixtures = [
        "discobase_testdata.json",
    ]
    record = Record.objects.first()

    def test_record_list_view(self):
        response = self.client.get(reverse("discobase:record_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pieces")
        self.assertTemplateUsed("discobase/record_list.html")

    def test_record_detail_view(self):
        response = self.client.get(self.record.get_absolute_url())
        no_response = self.client.get("discobase/records/888888")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(no_response.status_code, 404)
        self.assertContains(response, "Dismember")
        self.assertTemplateUsed("discobase/recod_detail.html")

    def test_trxrecord_list_view(self):
        response = self.client.get(reverse("discobase:trxcredit_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Initial Load")
        self.assertTemplateUsed("discobase/trxcredit_list.html")

    def test_trxrecord_chart_view(self):
        response = self.client.get(reverse("discobase:trxcredit_chart"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Credit Saldo Movement")
        self.assertTemplateUsed("discobase/trxcredit_chart.html")

    def test_trxrecord_chart_form(self):
        form = DateForm()
        self.assertIn("start_date", form.fields)
        self.assertIn("end_date", form.fields)
        # TODO add more ...
