# Generated by Django 3.1.5 on 2021-02-15 09:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('GreenPen', '0027_student_on_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='teachinggroup',
            name='sims_name',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]
