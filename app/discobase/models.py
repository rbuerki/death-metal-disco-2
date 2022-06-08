from datetime import datetime

from django.db import models
from django.core.exceptions import ValidationError


def validate_credit_trx(value):
    if value in ["Addition", "Initial Load", "Purchase", "Removal"]:  # TODO really?
        return value
    else:
        raise ValidationError("Not a valid credit trx type.")


def validate_rating_value(value):
    if value in range(1, 6):
        return value
    else:
        raise ValidationError("Rating value not between 1 and 5.")


class Country(models.Model):
    country_name = models.CharField(max_length=50, unique=True)
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
        RecordFormat, on_delete=models.CASCADE, related_name="records"
    )
    color = models.CharField(max_length=255, blank=True)
    lim_edition = models.CharField(max_length=50, blank=True)
    number = models.CharField(max_length=50, blank=True)
    remarks = models.CharField(max_length=255, blank=True)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, related_name="records")
    artists = models.ManyToManyField(Artist, related_name="records")
    labels = models.ManyToManyField(Label, related_name="records")
    purchase_date = models.DateField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    is_digitized = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    rating = models.SmallIntegerField(validators=[validate_rating_value], null=True)
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["title", "artists"], name="record_unique")
        ]

    def __str__(self):
        return f"{self.title} ({self.artists})"


class CreditTrx(models.Model):
    # id = models.AutoField(primary_key=True)
    trx_date = models.DateField()
    trx_type = models.CharField(max_length=50, validators=[validate_credit_trx])
    credit_value = models.SmallIntegerField()
    credit_saldo = models.SmallIntegerField()
    record = models.ForeignKey(
        Record, on_delete=models.CASCADE, related_name="credit_trx"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __repr__(self):
        return f"{self.trx_type} (value={self.credit_value})"
