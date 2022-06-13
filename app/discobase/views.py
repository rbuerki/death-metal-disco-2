from datetime import date, timedelta

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.views.generic import ListView

from discobase.models import TrxCredit, Record


class RecordListView(ListView):
    model = Record
    contect_object_name = "record_list"
    queryset = Record.objects.filter(is_active="True")


class TrxCreditListView(ListView):
    model = TrxCredit
    contect_object_name = "trxcredit_list"
    queryset = TrxCredit.objects.order_by("-trx_date")


# CREATE PURCHASE TRX


@receiver(post_save, sender=Record)
def record_post_save(sender, instance, created, update_fields, **kwargs) -> None:
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
        credit_saldo = TrxCredit.objects.order_by("-id").get().credit_saldo

    _ = TrxCredit.objects.create(
        trx_date=record.purchase_date,
        trx_type="Purchase",
        trx_value=trx_value * -1,
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
    last_addition_date, days_since_last = get_days_since_last_addition(TrxCredit)

    while days_since_last >= 10:
        trx_date = last_addition_date + timedelta(days=interval_days)

        _ = TrxCredit.objects.create(
            trx_date=trx_date,
            trx_type="Addition",
            trx_value=1,
            credit_saldo=(TrxCredit.objects.order_by("-id").first().credit_saldo + 1),
            record=None,
        )
        last_addition_date, days_since_last = get_days_since_last_addition(TrxCredit)

        # print(f"Creating 'Addition' Trx for: {credit_trx_date}") TODO remove


def get_days_since_last_addition(TrxCredit) -> tuple[date, int]:
    """Return the date of and the number of days since the
    last transaction with type 'Addition' stored in the
    CreditTrx table. This function is called within
    'create_addition_credits'.
    """
    last_addition_date = (
        TrxCredit.objects.filter(trx_type="Addition").order_by("-id").first().trx_date
    )
    days_since_last = (date.today() - last_addition_date).days

    return last_addition_date, days_since_last
