from django.db.models.signals import post_save
from django.dispatch import receiver
from django.views.generic import ListView

from discobase.models import TrxCredit, Record


class RecordListView(ListView):
    model = Record
    contect_object_name = "record_list"
    queryset = Record.objects.filter(is_active="True")


@receiver(post_save, sender=Record)
def record_post_save(sender, instance, created, update_fields, **kwargs):
    """Listen to a record post_save() signal and if a
    record is created, trigger a purchase trx creation.
    """
    if created:
        create_purchase_trx(instance)


def create_purchase_trx(record):
    """Create a purchase trx based on the attributes
    of the newly created record.
    """
    trx_value = record.credit_value
    if not TrxCredit.objects.exists():
        credit_saldo = 0
    else:
        credit_saldo = TrxCredit.objects.order_by("-id").get().credit_saldo

    _ = TrxCredit.objects.create(
        trx_date=record.purchase_date,
        trx_type="Purchase",
        trx_value=trx_value,
        credit_saldo=credit_saldo + trx_value,
        record_id=record.id,
    )
