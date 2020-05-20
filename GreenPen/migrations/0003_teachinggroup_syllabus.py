# Generated by Django 3.0.6 on 2020-05-20 02:25

from django.db import migrations
import django.db.models.deletion
import mptt.fields


class Migration(migrations.Migration):

    dependencies = [
        ('GreenPen', '0002_syllabus'),
    ]

    operations = [
        migrations.AddField(
            model_name='teachinggroup',
            name='syllabus',
            field=mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='GreenPen.Syllabus'),
        ),
    ]
