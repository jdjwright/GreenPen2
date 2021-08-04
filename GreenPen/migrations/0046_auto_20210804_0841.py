# Generated by Django 3.1.7 on 2021-08-04 08:41

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('GreenPen', '0045_auto_20210521_0504'),
    ]

    operations = [
        migrations.AddField(
            model_name='teachinggroup',
            name='academic_year',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='GreenPen.academicyear'),
        ),
        migrations.AlterField(
            model_name='academicyear',
            name='name',
            field=models.CharField(help_text='E.g. "2020-21', max_length=30),
        ),
        migrations.AlterField(
            model_name='sitting',
            name='date',
            field=models.DateTimeField(default=datetime.datetime(2021, 8, 4, 8, 41, 43, 409624)),
        ),
        migrations.AlterField(
            model_name='teachinggroup',
            name='year_taught',
            field=models.IntegerField(blank=True, help_text='This is the counter for academic years (e.g. 2020-21), NOT yeargroup!', null=True),
        ),
    ]
