# Generated by Django 3.2.8 on 2021-10-14 05:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('GreenPen', '0051_auto_20211013_0156'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sitting',
            name='date',
            field=models.DateTimeField(default='django.utils.timezone.now'),
        ),
    ]
