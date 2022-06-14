from datetime import datetime

from django.db import models
from django.core.exceptions import ValidationError


def validate_credit_trx(value):
    if value in ["Addition", "Initial Load", "Purchase", "Removal"]:
        return value
    else:
        raise ValidationError("Not a valid credit trx type.")


def validate_rating_value(value):
    # TODO: the validation makes this field required somehow
    return value
    # if value in range(1, 6) or value is None:
    #     return value
    # else:
    #     raise ValidationError("Rating value not between 1 and 5.")


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
    is_active = models.BooleanField(default=True)
    credit_value = models.IntegerField(choices=[(1, 1), (0, 0)], default=1)
    rating = models.SmallIntegerField(
        validators=[validate_rating_value], null=True, default=None
    )
    review = models.TextField(blank=True)
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

    @property
    def artists_str(self):
        """NOTE: This probably needs an additional db query, when called."""
        return " / ".join([x.artist_name for x in self.artists.all()])

    @property
    def labels_str(self):
        """NOTE: This probably needs an additional db query, when called."""
        return " / ".join([x.label_name for x in self.labels.all()])


class TrxCredit(models.Model):
    # id = models.AutoField(primary_key=True)
    trx_date = models.DateField()
    trx_type = models.CharField(max_length=50, validators=[validate_credit_trx])
    trx_value = models.SmallIntegerField()
    credit_saldo = models.SmallIntegerField()
    record = models.ForeignKey(
        Record, on_delete=models.SET_NULL, related_name="trx_credit", null=True
    )
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
