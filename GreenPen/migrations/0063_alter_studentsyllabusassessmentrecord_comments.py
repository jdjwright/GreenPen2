# Generated by Django 3.2.8 on 2021-11-11 02:17

import ckeditor.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('GreenPen', '0062_auto_20211110_0801'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentsyllabusassessmentrecord',
            name='comments',
            field=ckeditor.fields.RichTextField(blank=True, null=True),
        ),
    ]
