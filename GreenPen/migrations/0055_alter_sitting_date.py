# Generated by Django 3.2.8 on 2021-10-25 06:05

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('GreenPen', '0054_auto_20211025_0458'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sitting',
            name='date',
            field=models.DateField(default=datetime.date.today),
        ),
    ]
