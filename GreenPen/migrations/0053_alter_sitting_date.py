# Generated by Django 3.2.8 on 2021-10-25 02:05

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('GreenPen', '0052_alter_sitting_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sitting',
            name='date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
