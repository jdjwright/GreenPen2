# Generated by Django 3.2.8 on 2021-10-25 06:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('GreenPen', '0057_rename_most_recent_examined_studentsyllabusassessmentrecord_most_recent'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentsyllabusassessmentrecord',
            name='exam_assessment',
            field=models.BooleanField(default=True),
        ),
    ]
