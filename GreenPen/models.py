from django.db import models
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

    def __str__(self):
        return self.full_name() + " " + self.tutor_group


class Teacher(Person):
    title = models.CharField(max_length=50, blank=True, null=True)
    staff_code = models.CharField(max_length=5, blank=True, null=True)

    def taught_students(self):
        return Student.objects.filter(Q(teachinggroup__teachers=self) | Q(teachinggroup__subject__HoDs=self))

    def __str__(self):
        return self.title + " " + self.full_name() + " (" + self.staff_code + ")"


class Subject(models.Model):
    name = models.CharField(max_length=50, blank=False, null=False, unique=True)
    HoDs = models.ManyToManyField(Teacher)

    def __str__(self):
        return self.name


class TeachingGroup(models.Model):
    name = models.CharField(max_length=20, blank=True, null=True)
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, blank=False, null=True)
    teachers = models.ManyToManyField(Teacher)
    students = models.ManyToManyField(Student)
    syllabus = TreeForeignKey('Syllabus', blank=True, null=True, on_delete=models.SET_NULL)


class Syllabus(MPTTModel):
    text = models.TextField(blank=False, null=False)
    parent = TreeForeignKey('Syllabus', blank=True, null=True, on_delete=models.CASCADE)
    identifier = models.CharField(max_length=20, blank=False, null=True,
                                  help_text='This would be a sub point number, e.g. if this is 1.1.1 Blah blah, enter 1')

    def __str__(self):
        string = ''
        for ancestor in self.get_ancestors():
            string = string + ancestor.identifier + "."
        string = string + self.identifier + ": " + self.text
        return string

    def percent_correct(self, students=Student.objects.all()):
        total_attempted = StudentSyllabusRecord.objects. \
            filter(student__in=students,
                   syllabus_point__in=self.get_descendants(include_self=True)). \
            aggregate(Sum('total_marks_attempted'))['total_marks_attempted__sum']
        total_correct = StudentSyllabusRecord.objects. \
            filter(student__in=students,
                   syllabus_point__in=self.get_descendants(include_self=True)). \
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
    number = models.CharField(max_length=10, blank=False, null=False, unique=True)
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
    sitting = models.ForeignKey(Sitting, on_delete=models.CASCADE, blank=False, null=False)
    score = models.FloatField(blank=True, null=True)

    class Meta:
        unique_together = ['student', 'question', 'sitting']


class StudentSyllabusRecord(models.Model):
    syllabus_point = TreeForeignKey(Syllabus, on_delete=models.CASCADE, blank=False, null=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, blank=False, null=False)
    total_marks_attempted = models.FloatField(blank=True, null=True)
    total_marks_correct = models.FloatField(blank=True, null=True)

    class Meta:
        unique_together = ['student', 'syllabus_point']

    @property
    def percentage_correct(self):
        return round(self.total_marks_correct / self.total_marks_attempted * 100, 0)

    def __str__(self):
        return str(self.student) + " " + str(self.syllabus_point) + " <" + str(self.percentage_correct) + ">"


def student_mark_changed(sender, instance=Mark.objects.all(), **kwargs):
    for point in instance.question.syllabus_points.all():
        record, created = StudentSyllabusRecord.objects.get_or_create(student=instance.student,
                                                                      syllabus_point=point)
        record.total_marks_correct = Mark.objects.filter(student=instance.student,
                                                         question__syllabus_points=point).aggregate(Sum('score'))[
            'score__sum']
        record.total_marks_attempted = Mark.objects.filter(student=instance.student,
                                                           question__syllabus_points=point).aggregate(
            Sum('question__max_score'))['question__max_score__sum']
        record.save()


post_save.connect(student_mark_changed, sender=Mark)
