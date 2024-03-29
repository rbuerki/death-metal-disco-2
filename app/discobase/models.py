from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.forms import ImageField, IntegerField
from django.urls import reverse
from django.utils.functional import cached_property


def validate_credit_trx(value):
    if value in ["Addition", "Initial Load", "Purchase", "Removal"]:
        return value
    else:
        raise ValidationError("Not a valid credit trx type.")


def validate_rating_value(value):
    if value in range(0, 6) or value is None:
        return value
    else:
        raise ValidationError("Rating value not between 0 and 5.")


class Country(models.Model):
    country_name = models.CharField(max_length=50, unique=True)
    country_code = models.CharField(max_length=2, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.country_name


class Artist(models.Model):
    # id = models.AutoField(primary_key=True)
    artist_name = models.CharField(max_length=255)
    country = models.ForeignKey(
        Country, on_delete=models.CASCADE, related_name="artists"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["artist_name", "country"], name="artist_unique"
            )
        ]

    def __str__(self):
        return f"{self.artist_name} ({self.country})"


class Genre(models.Model):
    # id = models.AutoField(primary_key=True)
    genre_name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.genre_name


class Label(models.Model):
    # id = models.AutoField(primary_key=True)
    label_name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.label_name


class RecordFormat(models.Model):
    # id = models.AutoField(primary_key=True)
    format_name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.format_name


class Record(models.Model):
    # id = models.AutoField(primary_key=True)  # TODO: check if UUID is better
    title = models.CharField(max_length=255)
    year = models.SmallIntegerField(default=datetime.now().year)
    record_format = models.ForeignKey(
        RecordFormat, on_delete=models.CASCADE, related_name="records", default=3
    )
    color = models.CharField(max_length=255, blank=True)
    remarks = models.CharField(max_length=255, blank=True)
    genre = models.ForeignKey(
        Genre, on_delete=models.CASCADE, related_name="records", default=1
    )
    artists = models.ManyToManyField(Artist, related_name="records")
    labels = models.ManyToManyField(Label, related_name="records")
    purchase_date = models.DateField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    is_digitized = models.BooleanField(default=False)
    credit_value = models.IntegerField(choices=[(1, 1), (0, 0)], default=1)
    rating = models.SmallIntegerField(validators=[validate_rating_value], default=0)
    # favourite_song = models.CharField(
    #     max_length=255, blank=True
    # )  # TODO relate to tracklist with condition
    review = models.TextField(blank=True)
    cover_image = models.ImageField(
        upload_to="covers/", default="covers/_placeholder.png"
    )
    discogs_id = models.IntegerField(default=-1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # NOTE: I cannot use m2m fields in the constraint, so this ist the best I can do ...
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["title", "year", "genre"], name="record_unique"
            )
        ]

    def __str__(self):
        return f"{self.artists_str} - {self.title} ({str(self.year)})"

    def get_absolute_url(self):
        return reverse("discobase:record_detail", args=[str(self.pk)])

    def get_discogs_url(self):
        return f"https://www.discogs.com/release/{str(self.discogs_id)}"

    def get_next_records_url(self):
        next_record = Record.objects.filter(id__gt=self.id).order_by("id").first()
        return next_record.get_absolute_url()

    def get_previous_records_url(self):
        prev_record = Record.objects.filter(id__lt=self.id).order_by("-id").first()
        return prev_record.get_absolute_url()

    @cached_property
    def artists_str(self):
        """NOTE: This probably needs an additional db query, when called."""
        return " / ".join([x.artist_name for x in self.artists.all()])

    @cached_property
    def labels_str(self):
        """NOTE: This probably needs an additional db query, when called."""
        return " / ".join([x.label_name for x in self.labels.all()])


class Song(models.Model):
    # id = models.AutoField(primary_key=True)
    record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name="song")
    position = models.CharField(max_length=20)
    title = models.CharField(max_length=255)
    is_favourite = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __repr__(self):
        return f"{self.position} {self.title}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["record", "title"], name="song_unique")
        ]


class TrxCredit(models.Model):
    # id = models.AutoField(primary_key=True)
    trx_date = models.DateField()
    trx_type = models.CharField(max_length=50, validators=[validate_credit_trx])
    trx_value = models.SmallIntegerField()
    credit_saldo = models.SmallIntegerField()
    record = models.ForeignKey(
        Record, on_delete=models.SET_NULL, related_name="trx_credit", null=True
    )
    record_string = models.CharField(max_length=200, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __repr__(self):
        return f"{self.trx_type} (value={self.trx_value})"


class Dump(models.Model):
    # id = models.AutoField(primary_key=True)
    legacy_id = models.SmallIntegerField()
    title = models.CharField(max_length=255)
    year = models.SmallIntegerField()
    record_format = models.CharField(max_length=50)
    color = models.CharField(max_length=255, blank=True)
    remarks = models.CharField(max_length=255, blank=True)
    genre = models.CharField(max_length=50)
    artists = models.CharField(max_length=255)
    labels = models.CharField(max_length=255)
    purchase_date = models.DateField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    rating = models.SmallIntegerField(null=True)
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.artists} - {self.title} ({str(self.year)})"
