# Generated by Django 4.0.4 on 2022-07-17 18:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('discobase', '0017_rename_cover_record_cover_image_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='song',
            name='position',
            field=models.CharField(max_length=20),
        ),
    ]