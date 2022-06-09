# from django.shortcuts import render
# Create your views here.
from typing import Any

from django.core.exceptions import ValidationError

from discobase.models import (
    Artist,
    Country,
    CreditTrx,
    Genre,
    Label,
    Record,
    RecordFormat,
)


def parse_strings_to_lists(
    insert_data: dict, multi_fields: tuple = ("artists", "countries", "labels")
) -> dict:
    """For data fields with the possibility of multiple entries per record,
    parse the str values to lists in insert_data and return the dict.
    """
    for field in multi_fields:
        field_list = [x.strip() for x in insert_data[field].split(";")]
        insert_data[field] = field_list

    if len(insert_data["artists"]) != len(insert_data["countries"]):
        raise AssertionError("Need the same number of artists and artist countries.")

    return insert_data


def create_new_discobase_entry(insert_data: dict[str, Any]) -> None:
    """Use the information in the passed insert_data to
    create all the necessary new database entries.
    """
    # create artists and countries
    artists = []
    for a, c in zip(insert_data["artists"], insert_data["countries"]):
        country, _ = Country.objects.get_or_create(country_name=c)
        artist, _ = Artist.objects.get_or_create(artist_name=a, country=country)
        artists.append(artist)

    # create labels
    labels = []
    for l_ in insert_data["labels"]:
        label, _ = Label.objects.get_or_create(label_name=l_)
        labels.append(label)

    # create genre
    # TODO: implement predefined choice
    genre, _ = Genre.objects.get_or_create(genre_name=insert_data["genre"])

    # create record_format
    # TODO: implement predefined choice
    record_format, _ = RecordFormat.objects.get_or_create(
        format_name=insert_data["record_format"]
    )

    # create record
    record = Record(
        title=insert_data["title"],
        year=insert_data["year"],
        record_format=record_format,
        color=insert_data["color"],
        lim_edition=insert_data["lim_edition"],
        number=insert_data["number"],
        remarks=insert_data["remarks"],
        genre=genre,
        purchase_date=insert_data["purchase_date"],
        price=insert_data["price"],
        is_digitized=insert_data["is_digitized"],
        is_active=insert_data["is_active"],
        rating=insert_data["rating"],
        review=insert_data["review"],
    )
    record.artists.set(artists)
    record.labels.set(labels)

    # TODO unique constraint not possible one m2m fields! implement custom
    try:
        record.save()
        success = True
    except ValidationError:
        print("Save failed, a record with the same artist(s) and title already exists.")
        success = False

    if success:
        # Create purchase trx
        credit_value = insert_data["trx_value"] * -1
        try:
            credit_saldo = CreditTrx.objects.order_by("-Id")[0].credit_saldo
        except IndexError:
            # In case of initial data_ingestion only
            credit_saldo = 0

        CreditTrx.objects.create(
            trx_date=insert_data["purchase_date"],
            trx_type=insert_data["trx_type"],
            credit_value=credit_value,
            credit_saldo=credit_saldo + credit_saldo,
        )
