# Generated by Django 3.2.8 on 2021-10-25 06:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('GreenPen', '0056_auto_20211025_0640'),
    ]

    operations = [
        migrations.RenameField(
            model_name='studentsyllabusassessmentrecord',
            old_name='most_recent_examined',
            new_name='most_recent',
        ),
    ]
