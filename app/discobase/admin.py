from django.contrib import admin

from discobase.models import (
    Artist,
    Country,
    Dump,
    TrxCredit,
    Genre,
    Label,
    Record,
    RecordFormat,
    Song,
)


class RecordAdmin(admin.ModelAdmin):
    """Customize record list view in the admin panel."""

    model = Record
    list_display = (
        "id",
        "title",
        "purchase_date",
        "is_digitized",
    )

    # TODO: show many to many fields, maybe like this:
    # C:\Users\r2d4\OneDrive\code\projects\22-05_django_books\books\admin.py
    # or read the docs, see nimbus section for link

    # fields = []  # to change the order
    # fieldsets = [('SECTION X', {'fields':['artist', 'xy']}),]
    list_display_links = ("id", "title")
    list_filter = ("genre",)  # TODO how to filter on artist or label ...
    list_editable = ("purchase_date",)  # more for demo purposes ...
    search_fields = (
        "title",
        # "genre",  -- TODO throwing errors, cannot query in the pk ;-)
        # "record_format",
    )
    list_per_page = 50


admin.site.register(Record, RecordAdmin)


class TrxCreditAdmin(admin.ModelAdmin):
    """Customize trx_credit list view in the admin panel."""

    model = TrxCredit
    list_display = (
        "id",
        "trx_date",
        "trx_type",
        "record",
    )

    list_per_page = 50


admin.site.register(TrxCredit, TrxCreditAdmin)


class SongAdmin(admin.ModelAdmin):
    """Customize trx_credit list view in the admin panel."""

    model = TrxCredit
    list_display = (
        "id",
        "record",
        "title",
        "is_favourite",
    )
    search_fields = (
        # "record",  # TODO throwing errors
        "title"
    )

    list_per_page = 100


admin.site.register(Song, SongAdmin)

# TODO ...
admin.site.register([Artist, Country, Dump, Genre, Label, RecordFormat])
