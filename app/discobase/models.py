from django.db import models
from django.core.exceptions import ValidationError


def validate_credit_trx(value):
    if value in ["Addition", "Initial Load", "Purchase", "Remove"]:  # TODO really?
        return value
    else:
        raise ValidationError("Not a valid credit trx type.")


def validate_rating_value(value):
    if value in range(1, 6):
        return value
    else:
        raise ValidationError("Rating value not between 1 and 5.")


class Country(models.Model):
    country_name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<id={self.id}, name={self.country_name}>"


class Artist(models.Model):
    # id = models.AutoField(primary_key=True)
    artist_name = models.CharField(max_length=255, unique=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<id={self.id}, name={self.artist_name}, country={self.country}>"


class Genre(models.Model):
    # id = models.AutoField(primary_key=True)
    genre_name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<id={self.id}, name={self.genre_name}>"


class Label(models.Model):
    # id = models.AutoField(primary_key=True)
    label_name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<id={self.id}, name={self.label_name}>"


class RecordFormat(models.Model):
    # id = models.AutoField(primary_key=True)
    format_name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<id={self.id}, name={self.name}>"


class Record(models.Model):
    # id = models.AutoField(primary_key=True)  # TODO: check if UUID is better
    title = models.CharField(max_length=255)
    year = models.SmallIntegerField()
    color = models.CharField(max_length=255, blank=True)
    lim_edition = models.CharField(max_length=50, blank=True)
    number = models.CharField(max_length=50, blank=True)
    remarks = models.CharField(max_length=255, blank=True)
    purchase_date = models.DateField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    rating = models.SmallIntegerField(validators=[validate_rating_value], null=True)
    review = models.TextField(blank=True)
    is_digitized = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    genre = models.OneToOneField(Genre, on_delete=models.CASCADE)
    record_format = models.OneToOneField(RecordFormat, on_delete=models.CASCADE)
    artist = models.ManyToManyField(Artist)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # @property
    # def record_id(self):
    #     return self.id

    def __str__(self):
        return f"<id={self.id}, title={self.title}, artist={self.artists}>"


class CreditTrx(models.Model):
    # id = models.AutoField(primary_key=True)
    trx_date = models.DateField()
    trx_type = models.CharField(max_length=50, validators=[validate_credit_trx])
    credit_value = models.SmallIntegerField()
    credit_saldo = models.SmallIntegerField()
    record = models.ForeignKey(Record, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __repr__(self):
        return (
            f"<id={self.id}, "
            f"date={self.trx_date}, "
            f"type={self.trx_type}, "
            f"value={self.credit_value}, "
            f"saldo={self.credit_saldo}, "
            f"record_id={self.record})>"
        )
