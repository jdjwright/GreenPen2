# Generated by Django 3.0.7 on 2020-08-11 05:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('GreenPen', '0003_auto_20200804_1011'),
    ]

    operations = [
        migrations.AddField(
            model_name='teachinggroup',
            name='rollover_name',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]
