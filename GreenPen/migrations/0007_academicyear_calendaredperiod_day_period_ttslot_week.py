# Generated by Django 3.0.7 on 2020-08-13 07:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('GreenPen', '0006_auto_20200813_0554'),
    ]

    operations = [
        migrations.CreateModel(
            name='AcademicYear',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('order', models.IntegerField()),
                ('current', models.BooleanField(default=False)),
                ('first_monday', models.DateTimeField(help_text='This must be the first MONDAY in the school calendar year. Use suspensions if the term does not start on that monday.')),
                ('total_weeks', models.IntegerField(help_text='This must be the total number of weeks. If you end with a partial number of weeks, count the partial one as a full week and use suspensions on the remaining lessons')),
            ],
        ),
        migrations.CreateModel(
            name='Day',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.IntegerField(help_text='The number of days from monday (e.g. Monday = 0, Tuesday = 1...')),
                ('name', models.CharField(max_length=10)),
                ('year', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='GreenPen.AcademicYear')),
            ],
            options={
                'ordering': ['order'],
                'unique_together': {('order', 'name')},
            },
        ),
        migrations.CreateModel(
            name='Period',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.IntegerField()),
                ('name', models.CharField(max_length=5, null=True)),
                ('year', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='GreenPen.AcademicYear')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='Week',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField()),
                ('year', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='GreenPen.AcademicYear')),
            ],
            options={
                'ordering': ['number'],
            },
        ),
        migrations.CreateModel(
            name='TTSlot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.IntegerField()),
                ('day', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='GreenPen.Day')),
                ('period', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='GreenPen.Period')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='CalendaredPeriod',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.IntegerField()),
                ('tt_slot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='GreenPen.TTSlot')),
                ('week', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='GreenPen.Week')),
                ('year', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='GreenPen.AcademicYear')),
            ],
        ),
    ]
