from datetime import date, timedelta

from django.http import HttpResponse
from django.db.models import Q
from django.db.models.signals import m2m_changed, post_delete, post_save, pre_delete
from django.dispatch import receiver
from django.shortcuts import render
from django.views.generic import DetailView, ListView, View

from discobase.charts import make_trxcredit_chart
from discobase.forms import DateForm, SearchForm
from discobase.models import Dump, Record, TrxCredit


class RecordListView(ListView):
    model = Record
    context_object_name = "record_list"
    paginate_by = 50

    def get_queryset(self):
        """Override default queryset by filtering for the
        input from the navbar search window. If there is none
        return all records.
        NOTE: This might slow down the base list page. Maybe I
        should make a separate RecordSearchListView.
        """
        query = self.request.GET.get("q")
        if not query:
            return Record.objects.all()
        else:
            return Record.objects.filter(
                Q(title__icontains=query)
                | Q(artists__artist_name__icontains=query)
                | Q(labels__label_name__icontains=query)
                | Q(record_format__format_name=query)
            )


class TrxCreditListView(ListView):
    model = TrxCredit
    context_object_name = "trxcredit_list"
    queryset = TrxCredit.objects.order_by("-trx_date")


class RecordDetailView(DetailView):
    model = Record
    context_object_name = "record"


# TODO integrate credit_addition_trx
# class TrxCreditView(View):
#     def get(self, request):
#         # <view logic>
#         return HttpResponse('result')


# TODO for testing only
def search_TEMP(request):
    from discobase.choices import format_choices

    context = {"form": SearchForm, "format_choices": format_choices}
    return render(request, "discobase/search_TEMP.html", context)


# DISPLAY CHARTS


def trxcredit_chart(request):
    """Display the credittrx_chart. Start- and end date
    can be adapted by the user (using the DateForm).
    """
    # First, check if an addition trx has to be added
    # TODO This is not very efficient, and if it stays here, then change
    # the function to read from trx directly, so we hit the db only once
    create_addition_credits(TrxCredit)

    trx = (
        TrxCredit.objects.exclude(trx_type="Initial Load")
        .filter(trx_date__year__gte="2021")
        .order_by("trx_date", "trx_type")
    )
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if start_date:
        trx = trx.filter(trx_date__gte=start_date)
    if end_date:
        trx = trx.filter(trx_date__lte=end_date)

    chart = make_trxcredit_chart(trx)
    context = {"chart": chart, "form": DateForm}
    return render(request, "discobase/chart.html", context)


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
        record_string=None,  # it misses the artist part (m2m) in this state, see next
    )


@receiver(m2m_changed, sender=Record.artists.through)
def record_m2m_update_post_save(sender, instance, action, *args, **kwargs) -> None:
    """Listen to a change in the record-artists relation and if
    the record exists in the credit_trx table, update it's record_string.
    (This is a necessary 'update' of the post_save function, to include
    the artist relation, which seems not yet properly set in post_save.)
    """
    if action == "post_add":
        try:
            trx = TrxCredit.objects.get(record_id=instance)
            trx.record_string = str(instance)
            trx.save()
        except ValueError:
            pass


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
            record_string=None,
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


# DUMP RECORD AND CREATE REMOVAL TRX


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
        record_string=str(record),
    )
