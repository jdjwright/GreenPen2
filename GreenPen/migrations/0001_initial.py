# Generated by Django 3.0.6 on 2020-05-29 04:51

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import mptt.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CSVDoc',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(blank=True, max_length=255)),
                ('document', models.FileField(upload_to='documents/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Exam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('weighting', models.FloatField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tutor_group', models.CharField(blank=True, max_length=5, null=True)),
                ('year_group', models.IntegerField(blank=True, null=True)),
                ('student_id', models.IntegerField(blank=True, null=True, unique=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Syllabus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('identifier', models.CharField(blank=True, help_text='This would be a sub point number, e.g. if this is 1.1.1 Blah blah, enter 1', max_length=20, null=True)),
                ('lft', models.PositiveIntegerField(editable=False)),
                ('rght', models.PositiveIntegerField(editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(editable=False)),
                ('parent', mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='GreenPen.Syllabus')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Teacher',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=50, null=True)),
                ('staff_code', models.CharField(blank=True, max_length=5, null=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TeachingGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=256, null=True)),
                ('archived', models.BooleanField(blank=True, default=False, null=True)),
                ('students', models.ManyToManyField(to='GreenPen.Student')),
                ('subject', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='GreenPen.Subject')),
                ('syllabus', mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='GreenPen.Syllabus')),
                ('teachers', models.ManyToManyField(to='GreenPen.Teacher')),
            ],
        ),
        migrations.AddField(
            model_name='subject',
            name='HoDs',
            field=models.ManyToManyField(to='GreenPen.Teacher'),
        ),
        migrations.CreateModel(
            name='StudentSyllabusManualTeacherRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('rating', models.FloatField(blank=True, null=True)),
                ('comment', models.TextField(blank=True, null=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='GreenPen.Student')),
                ('syllabus_point', mptt.fields.TreeForeignKey(on_delete=django.db.models.deletion.CASCADE, to='GreenPen.Syllabus')),
            ],
        ),
        migrations.CreateModel(
            name='StudentSyllabusManualStudentRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('rating', models.FloatField(blank=True, null=True)),
                ('comment', models.TextField(blank=True, null=True)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='GreenPen.Student')),
                ('syllabus_point', mptt.fields.TreeForeignKey(on_delete=django.db.models.deletion.CASCADE, to='GreenPen.Syllabus')),
            ],
        ),
        migrations.CreateModel(
            name='Sitting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=datetime.date.today)),
                ('resets_ratings', models.BooleanField(blank=True, default=False, null=True)),
                ('exam', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='GreenPen.Exam')),
                ('students', models.ManyToManyField(to='GreenPen.Student')),
            ],
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.FloatField()),
                ('number', models.CharField(max_length=10)),
                ('max_score', models.FloatField(blank=True, null=True)),
                ('exam', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='GreenPen.Exam')),
                ('syllabus_points', mptt.fields.TreeManyToManyField(to='GreenPen.Syllabus')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.AddField(
            model_name='exam',
            name='syllabus',
            field=mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='GreenPen.Syllabus'),
        ),
        migrations.CreateModel(
            name='StudentSyllabusAssessmentRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.IntegerField(default=0)),
                ('attempted_this_level', models.FloatField(default=0, help_text='total marks tried for this point only')),
                ('correct_this_level', models.FloatField(default=0, help_text='total marks scored for this point only')),
                ('attempted_plus_children', models.FloatField(default=0, help_text='total marks tried for this point and children')),
                ('correct_plus_children', models.FloatField(default=0, help_text='total marks scored for this point and children')),
                ('percentage', models.FloatField(default=0)),
                ('rating', models.FloatField(default=0)),
                ('children_0_1', models.IntegerField(default=0, help_text='total children rated 0-1')),
                ('children_1_2', models.IntegerField(default=0, help_text='total children rated 1-2')),
                ('children_2_3', models.IntegerField(default=0, help_text='total children rated 2-3')),
                ('children_3_4', models.IntegerField(default=0, help_text='total children rated 3-4')),
                ('children_4_5', models.IntegerField(default=0, help_text='total children rated 4-5')),
                ('most_recent', models.BooleanField(blank=True, default=False, null=True)),
                ('sitting', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='GreenPen.Sitting')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='GreenPen.Student')),
                ('syllabus_point', mptt.fields.TreeForeignKey(on_delete=django.db.models.deletion.CASCADE, to='GreenPen.Syllabus')),
            ],
            options={
                'unique_together': {('student', 'sitting', 'syllabus_point'), ('student', 'syllabus_point', 'order')},
            },
        ),
        migrations.CreateModel(
            name='Mark',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.FloatField(blank=True, null=True)),
                ('student_notes', models.TextField(blank=True, null=True)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='GreenPen.Question')),
                ('sitting', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='GreenPen.Sitting')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='GreenPen.Student')),
            ],
            options={
                'unique_together': {('student', 'question', 'sitting')},
            },
        ),
    ]
