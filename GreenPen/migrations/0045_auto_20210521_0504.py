# Generated by Django 3.1.7 on 2021-05-21 05:04

import GreenPen.validators
import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('GreenPen', '0044_resource_exam'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gquizexam',
            name='master_form_url',
            field=models.URLField(help_text='This must be the URL for the Google Form containing your questions', validators=[GreenPen.validators.validate_g_form]),
        ),
        migrations.AlterField(
            model_name='gquizexam',
            name='master_response_sheet_url',
            field=models.URLField(help_text='This must be the URL for the Google Sheet containing your responses', null=True, validators=[GreenPen.validators.validate_g_sheet]),
        ),
        migrations.AlterField(
            model_name='resource',
            name='exam',
            field=models.ForeignKey(blank=True, help_text="If you've made a Google Self-Assessed quiz, add it to GreenPen first and then link it here.", null=True, on_delete=django.db.models.deletion.SET_NULL, to='GreenPen.gquizexam'),
        ),
        migrations.AlterField(
            model_name='resource',
            name='url',
            field=models.URLField(blank=True, help_text='If creating a Google Quiz, this should be a link to edit the quiz on Google Forms.', null=True),
        ),
        migrations.AlterField(
            model_name='sitting',
            name='date',
            field=models.DateTimeField(default=datetime.datetime(2021, 5, 21, 5, 4, 25, 126316)),
        ),
    ]
