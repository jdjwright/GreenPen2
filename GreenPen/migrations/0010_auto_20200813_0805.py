# Generated by Django 3.0.7 on 2020-08-13 08:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('GreenPen', '0009_ttslot_year'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='calendaredperiod',
            options={'ordering': ['order']},
        ),
        migrations.AddField(
            model_name='teachinggroup',
            name='lessons',
            field=models.ManyToManyField(to='GreenPen.TTSlot'),
        ),
    ]
