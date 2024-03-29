# Generated by Django 4.0.4 on 2022-06-08 10:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('discobase', '0004_alter_record_year'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='record',
            name='artist',
        ),
        migrations.RemoveField(
            model_name='record',
            name='label',
        ),
        migrations.AddField(
            model_name='record',
            name='artists',
            field=models.ManyToManyField(related_name='records', to='discobase.artist'),
        ),
        migrations.AddField(
            model_name='record',
            name='labels',
            field=models.ManyToManyField(related_name='records', to='discobase.label'),
        ),
        migrations.AlterField(
            model_name='artist',
            name='country',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='artists', to='discobase.country'),
        ),
        migrations.AlterField(
            model_name='credittrx',
            name='record',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='credit_trx', to='discobase.record'),
        ),
        migrations.AlterField(
            model_name='record',
            name='genre',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='records', to='discobase.genre'),
        ),
        migrations.AlterField(
            model_name='record',
            name='record_format',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='records', to='discobase.recordformat'),
        ),
    ]
