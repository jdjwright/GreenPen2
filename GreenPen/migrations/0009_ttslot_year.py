# Generated by Django 3.0.7 on 2020-08-13 07:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('GreenPen', '0008_auto_20200813_0741'),
    ]

    operations = [
        migrations.AddField(
            model_name='ttslot',
            name='year',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='GreenPen.AcademicYear'),
        ),
    ]