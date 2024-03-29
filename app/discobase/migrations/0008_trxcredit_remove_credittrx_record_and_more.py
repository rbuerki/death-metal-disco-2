# Generated by Django 4.0.4 on 2022-06-11 11:39

import discobase.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('discobase', '0007_remove_record_lim_edition_remove_record_number'),
    ]

    operations = [
        migrations.CreateModel(
            name='TrxCredit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('trx_date', models.DateField()),
                ('trx_type', models.CharField(max_length=50, validators=[discobase.models.validate_credit_trx])),
                ('trx_value', models.SmallIntegerField()),
                ('credit_saldo', models.SmallIntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='credittrx',
            name='record',
        ),
        migrations.AddField(
            model_name='record',
            name='credit_value',
            field=models.IntegerField(choices=[(1, 1), (0, 0)], default=1),
        ),
        migrations.AlterField(
            model_name='record',
            name='rating',
            field=models.SmallIntegerField(blank=True, validators=[discobase.models.validate_rating_value]),
        ),
        migrations.AddConstraint(
            model_name='record',
            constraint=models.UniqueConstraint(fields=('title', 'year', 'genre'), name='record_unique'),
        ),
        migrations.DeleteModel(
            name='CreditTrx',
        ),
        migrations.AddField(
            model_name='trxcredit',
            name='record',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='credit_trx', to='discobase.record'),
        ),
    ]
