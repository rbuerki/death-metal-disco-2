from datetime import date, timedelta

from django.http import HttpResponse
from django.db.models.signals import post_delete, post_save, pre_delete
from django.dispatch import receiver
from django.views.generic import ListView, View

from discobase.models import Dump, Record, TrxCredit


class RecordListView(ListView):
    model = Record
    contect_object_name = "record_list"
    queryset = Record.objects.filter(is_active="True")


class TrxCreditListView(ListView):
    model = TrxCredit
    contect_object_name = "trxcredit_list"
    queryset = TrxCredit.objects.order_by("-trx_date")


# TODO integrate credit_addition_trx
# class TrxCreditView(View):
#     def get(self, request):
#         # <view logic>
#         return HttpResponse('result')


# CREATE PURCHASE TRX ON RECORD INSERT


@receiver(post_save, sender=Record)
def record_post_save(sender, instance, created, **kwargs) -> None:
    """Listen to a record post_save() signal and if a
    record is created, trigger a purchase trx creation.
    """
    if created:
        create_purchase_trx(instance)


def create_purchase_trx(record) -> None:
    """Create a purchase trx based on the attributes
    of the newly created record. This function is called
    everytime a record is saved.
    """
    trx_value = record.credit_value * -1
    if not TrxCredit.objects.exists():
        credit_saldo = 0
    else:
        credit_saldo = TrxCredit.objects.order_by("-id").first().credit_saldo

    _ = TrxCredit.objects.create(
        trx_date=record.purchase_date,
        trx_type="Purchase",
        trx_value=trx_value,
        credit_saldo=credit_saldo + trx_value,
        record=record,
    )


# CREATE REGULAR ADDITION TRX


def create_addition_credits(TrxCredit, interval_days: int = 10) -> None:
    """Every x days a new credit is added (to be spent
    on purchasing new records). This function checks
    the delta in days since the last addition and inserts
    the necessary credit transactions depending on the
    defined interval.
    """
    last_addition_date, days_since_last = get_days_since_last_addition(
        TrxCredit, interval_days
    )

    while days_since_last >= 10:
        trx_date = last_addition_date + timedelta(days=interval_days)

        _ = TrxCredit.objects.create(
            trx_date=trx_date,
            trx_type="Addition",
            trx_value=1,
            credit_saldo=(TrxCredit.objects.order_by("-id").first().credit_saldo + 1),
            record=None,
        )
        last_addition_date, days_since_last = get_days_since_last_addition(
            TrxCredit, interval_days
        )


def get_days_since_last_addition(TrxCredit, interval_days) -> tuple[date, int]:
    """Return the date of and the number of days since the
    last transaction with type 'Addition' stored in the
    CreditTrx table. This function is called within
    'create_addition_credits'.
    """
    if TrxCredit.objects.filter(trx_type="Addition").exists():
        last_addition_date = (
            TrxCredit.objects.filter(trx_type="Addition")
            .order_by("-id")
            .first()
            .trx_date
        )
        days_since_last = (date.today() - last_addition_date).days
    else:
        # Prepare for very first addition trx
        last_addition_date = date.today() - timedelta(days=interval_days)
        days_since_last = 10

    return last_addition_date, days_since_last


# SOFT DELETE RECORD AND CREATE REMOVAL TRX


@receiver(pre_delete, sender=Record)
def record_pre_delete(sender, instance, **kwargs) -> None:
    """Listen to a record pre_delete() signal and tigger
    its transfer into the hollow void of ... the dump.
    """
    send_record_to_dump(instance)


def send_record_to_dump(record) -> None:
    _ = Dump.objects.create(
        legacy_id=record.id,
        title=record.title,
        year=record.year,
        record_format=record.record_format.format_name,
        color=record.color,
        remarks=record.remarks,
        genre=record.genre.genre_name,
        artists=record.artists_str,
        labels=record.labels_str,
        purchase_date=record.purchase_date,
        price=record.price,
        rating=record.rating,
        review=record.review,
    )


@receiver(post_delete, sender=Record)
def record_post_delete(sender, instance, **kwargs) -> None:
    """Listen to a record post_delete() signal and tigger
    the reward of a removal trx credit.
    """
    create_removal_trx(instance)


def create_removal_trx(record) -> None:
    """Create a removal trx based on the attributes
    of the record to be deleted. This function is called
    everytime before a record is deleted.
    """
    trx_value = record.credit_value
    credit_saldo = TrxCredit.objects.order_by("-id").first().credit_saldo

    _ = TrxCredit.objects.create(
        trx_date=date.today(),
        trx_type="Removal",
        trx_value=trx_value,
        credit_saldo=credit_saldo + trx_value,
        record=None,  # 'cause the record don't live here anymore ...
    )
