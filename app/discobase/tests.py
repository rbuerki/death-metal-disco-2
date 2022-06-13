from datetime import date, timedelta

from django.test import TestCase

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
from discobase import views


class DiscobaseModelTests(TestCase):
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


# VIEWS

#     def test_book_listing(self):
#         self.assertEqual(f"{self.book.title}", "Harry Potter")
#         self.assertEqual(f"{self.book.author}", "JK Rowling")
#         self.assertEqual(f"{self.book.price}", "25.00")

#     def test_book_list_view(self):
#         response = self.client.get(reverse("book_list"))
#         self.assertEqual(response.status_code, 200)
#         self.assertContains(response, "Harry Potter")
#         self.assertTemplateUsed(response, "books/book_list.html")

#     def test_book_detail_view(self):
#         response = self.client.get(self.book.get_absolute_url())
#         no_response = self.client.get("/books/12345/")
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(no_response.status_code, 404)
#         self.assertContains(response, "Harry Potter")
#         self.assertContains(response, "An excellent review.")
#         self.assertTemplateUsed(response, "books/book_detail.html")
