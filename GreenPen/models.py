from django.db import models
from django.utils import timezone
from django.db.models import Q, Sum, Avg
from django.db.models.signals import m2m_changed, post_save
from django.contrib.auth.models import User
from mptt.models import MPTTModel, TreeForeignKey, TreeManyToManyField
import datetime


class Person(models.Model):
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)

    def first_name(self):
        return self.user.first_name

    def last_name(self):
        return self.user.last_name

    def email(self):
        return self.user.email

    def full_name(self):
        return self.first_name() + " " + self.last_name()

    class Meta:
        abstract = True


class Student(Person):
    tutor_group = models.CharField(max_length=5, blank=True, null=True)
    year_group = models.IntegerField(blank=True, null=True)
    student_id = models.IntegerField(blank=True, null=True, unique=True)

    def __str__(self):
        if self.tutor_group:
            return self.full_name() + " " + self.tutor_group
        else:
            return self.full_name()


class Teacher(Person):
    title = models.CharField(max_length=50, blank=True, null=True)
    staff_code = models.CharField(max_length=5, blank=True, null=True)

    def taught_students(self):
        return Student.objects.filter(Q(teachinggroup__teachers=self) | Q(teachinggroup__subject__HoDs=self))

    def __str__(self):
        return self.title + " " + self.full_name() + " (" + self.staff_code + ")"


class Subject(models.Model):
    name = models.CharField(max_length=200, blank=False, null=False, unique=True)
    HoDs = models.ManyToManyField(Teacher)

    def __str__(self):
        return self.name


class TeachingGroup(models.Model):
    name = models.CharField(max_length=256, blank=True, null=True)
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, blank=False, null=True)
    teachers = models.ManyToManyField(Teacher)
    students = models.ManyToManyField(Student)
    syllabus = TreeForeignKey('Syllabus', blank=True, null=True, on_delete=models.SET_NULL)
    archived = models.BooleanField(blank=True, null=True, default=False)

    def __str__(self):
        return self.name


class Syllabus(MPTTModel):
    text = models.TextField(blank=False, null=False)
    parent = TreeForeignKey('Syllabus', blank=True, null=True, on_delete=models.CASCADE)
    identifier = models.CharField(max_length=20, blank=True, null=True,
                                  help_text='This would be a sub point number, e.g. if this is 1.1.1 Blah blah, enter 1')

    def __str__(self):
        string = ''
        for ancestor in self.get_ancestors():
            if ancestor.identifier:
                string = string + ancestor.identifier + "."
        if self.identifier:
            string = string + self.identifier
        if string != '':
            string = string + ": "
        string = string + self.text
        return string

    def percent_correct(self, students=Student.objects.all()):
        total_attempted = StudentSyllabusAssessmentRecord.objects. \
            filter(student__in=students,
                   syllabus_point__in=self.get_descendants(include_self=True),
                   most_recent=True). \
            aggregate(Sum('total_marks_attempted'))['total_marks_attempted__sum']
        total_correct = StudentSyllabusAssessmentRecord.objects. \
            filter(student__in=students,
                   syllabus_point__in=self.get_descendants(include_self=True),
                   most_recent=True). \
            aggregate(Sum('total_marks_correct'))['total_marks_correct__sum']
        return round(total_correct / total_attempted * 100, 0)


class Exam(models.Model):
    name = models.CharField(max_length=256, blank=False, null=False)
    syllabus = TreeForeignKey('Syllabus', blank=True, null=True, on_delete=models.SET_NULL)
    weighting = models.FloatField(blank=False, null=False, default=1)

    def total_score(self):
        return Question.objects.filter(exam=self).aggregate(Sum('max_score'))['max_score__sum']

    def __str__(self):
        return self.name


class Question(models.Model):
    exam = models.ForeignKey(Exam, blank=False, null=False, on_delete=models.CASCADE)
    order = models.FloatField(blank=False, null=False)
    number = models.CharField(max_length=10, blank=False, null=False)
    max_score = models.FloatField(blank=True, null=True)
    syllabus_points = TreeManyToManyField(Syllabus)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.number


def new_question_created(sender, instance, **kwargs):
    for sitting in Sitting.objects.filter(exam__question=instance):
        sync_marks_with_sittings(sitting)


post_save.connect(new_question_created, sender=Question)


class Sitting(models.Model):
    exam = models.ForeignKey(Exam, blank=False, null=False, on_delete=models.CASCADE)
    date = models.DateField(blank=False, null=False, default=datetime.date.today)
    students = models.ManyToManyField(Student)
    resets_ratings = models.BooleanField(blank=True, null=True, default=False)


def student_added_to_sitting(sender, instance, action, **kwargs):
    if action == 'post_add':
        sync_marks_with_sittings(instance)


def sync_marks_with_sittings(sitting):
    for student in sitting.students.all():
        for question in sitting.exam.question_set.all():
            Mark.objects.get_or_create(student=student,
                                       question=question,
                                       sitting=sitting)


m2m_changed.connect(student_added_to_sitting, sender=Sitting.students.through)


class Mark(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, blank=False, null=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, blank=False, null=False)
    score = models.FloatField(blank=True, null=True)
    sitting = models.ForeignKey(Sitting, blank=False, null=True, on_delete=models.CASCADE)
    student_notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['student', 'question', 'sitting']

    def set_student_syllabus_assessment_records(self):
        for point in self.question.syllabus_points.all():
            record, created = StudentSyllabusAssessmentRecord.objects.get_or_create(syllabus_point=point,
                                                                                    student=self.student,
                                                                                    sitting=self.sitting,
                                                                                    defaults={'most_recent': True})
            if created:
                previous, created = StudentSyllabusAssessmentRecord.objects.get_or_create(syllabus_point=point,
                                                                                          student=self.student,
                                                                                          most_recent=True)
                previous.most_recent = False

            all_mark_records = Mark.objects.filter(student=self.student,
                                                   question__syllabus_points=point)

            if self.sitting.resets_ratings:
                relevant_records = all_mark_records.filter(sitting__date__gte=self.sitting.date)
            else:
                last_reset = all_mark_records.filter(sitting__resets_ratings=True)
                if last_reset.count():
                    relevant_records = all_mark_records.filter(sitting__date__gte=last_reset.sitting.date)
                else:
                    relevant_records = all_mark_records

            record.total_marks_attempted = relevant_records. \
                aggregate(Sum('question__max_score'))['question__max_score__sum']
            record.total_marks_correct = relevant_records.aggregate(Sum('score'))['score__sum']
            record.percentage = round(record.total_marks_correct / record.total_marks_attempted * 100, 0)
            record.rating = record.percentage * 0.05
            record.save()


class StudentSyllabusAssessmentRecord(models.Model):
    syllabus_point = TreeForeignKey(Syllabus, on_delete=models.CASCADE, blank=False, null=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, blank=False, null=False)
    total_marks_attempted = models.FloatField(blank=True, null=True)
    total_marks_correct = models.FloatField(blank=True, null=True)
    sitting = models.ForeignKey(Sitting, blank=True, null=True, on_delete=models.CASCADE)
    percentage = models.FloatField(blank=True, null=True)
    rating = models.FloatField(blank=True, null=True)
    most_recent = models.BooleanField(blank=True, null=True, default=False)

    @property
    def percentage_correct(self):
        return round(self.total_marks_correct / self.total_marks_attempted * 100, 0)

    def __str__(self):
        return str(self.student) + " " + str(self.syllabus_point) + " <" + str(self.percentage_correct) + ">"


class StudentSyllabusManualStudentRecord(models.Model):
    syllabus_point = TreeForeignKey(Syllabus, on_delete=models.CASCADE, blank=False, null=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, blank=False, null=False)
    created = models.DateTimeField(blank=False, null=False, default=timezone.now)
    rating = models.FloatField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)


class StudentSyllabusManualTeacherRecord(models.Model):
    syllabus_point = TreeForeignKey(Syllabus, on_delete=models.CASCADE, blank=False, null=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, blank=False, null=False)
    created = models.DateTimeField(blank=False, null=False, default=timezone.now)
    rating = models.FloatField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, blank=False, null=True, on_delete=models.SET_NULL)


def student_mark_changed(sender, instance=Mark.objects.none(), **kwargs):
    if instance.score:
        instance.set_student_syllabus_assessment_records()


post_save.connect(student_mark_changed, sender=Mark)


class CSVDoc(models.Model):
    description = models.CharField(max_length=255, blank=True)
    document = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
