# Generated by Django 3.0.7 on 2020-08-12 09:25

from django.db import migrations, models
import django.db.models.deletion
import mptt.fields


class Migration(migrations.Migration):

    dependencies = [
        ('GreenPen', '0004_teachinggroup_rollover_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(blank=True, max_length=20, null=True)),
                ('lesson_title', models.CharField(blank=True, max_length=200, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('requirements', models.TextField(blank=True, null=True)),
                ('homework', models.TextField(blank=True, null=True)),
                ('homework_due', models.DateField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('sequence', models.IntegerField(blank=True)),
                ('date', models.DateField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='LessonSlot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.CharField(choices=[('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'), ('Thursday', 'Thursday'), ('Friday', 'Friday')], max_length=10)),
                ('period', models.IntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4)])),
                ('year', models.IntegerField(choices=[(0, '2018-19'), (1, '2019-20'), (2, '2020-21')])),
            ],
            options={
                'unique_together': {('day', 'period', 'year')},
            },
        ),
        migrations.CreateModel(
            name='TimetabledLesson',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lesson_slot', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='GreenPen.LessonSlot')),
                ('teachinggroup', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='GreenPen.TeachingGroup')),
            ],
            options={
                'unique_together': {('teachinggroup', 'lesson_slot')},
            },
        ),
        migrations.CreateModel(
            name='LessonSuspension',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('whole_school', models.BooleanField(default=True)),
                ('date', models.DateField()),
                ('reason', models.CharField(max_length=200, null=True)),
                ('all_day', models.BooleanField(default=False)),
                ('period', models.IntegerField(blank=True, choices=[(1, 1), (2, 2), (3, 3), (4, 4)], null=True)),
                ('teachinggroups', models.ManyToManyField(blank=True, to='GreenPen.TeachingGroup')),
            ],
        ),
        migrations.CreateModel(
            name='LessonResources',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('resource_type', models.CharField(choices=[('Presentation', 'Presentation'), ('Worksheet', 'Worksheet'), ('Test', 'Test'), ('Mark Scheme', 'Mark Scheme'), ('Web Page', 'Web Page'), ('Google Drive', 'Google Drive')], max_length=100, null=True)),
                ('resource_name', models.CharField(max_length=100, null=True)),
                ('link', models.URLField(null=True)),
                ('students_can_view_before', models.BooleanField(default=False)),
                ('students_can_view_after', models.BooleanField(default=False)),
                ('available_to_all_classgroups', models.BooleanField(default=False)),
                ('lesson', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='GreenPen.Lesson')),
                ('syllabus_points', mptt.fields.TreeManyToManyField(to='GreenPen.Syllabus')),
            ],
        ),
        migrations.AddField(
            model_name='lesson',
            name='lessonslot',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='GreenPen.TimetabledLesson'),
        ),
        migrations.AddField(
            model_name='lesson',
            name='syllabus_points',
            field=mptt.fields.TreeManyToManyField(blank=True, to='GreenPen.Syllabus'),
        ),
        migrations.AddField(
            model_name='lesson',
            name='teachinggroup',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='GreenPen.TeachingGroup'),
        ),
        migrations.AlterUniqueTogether(
            name='lesson',
            unique_together={('lessonslot', 'date'), ('teachinggroup', 'sequence')},
        ),
    ]
