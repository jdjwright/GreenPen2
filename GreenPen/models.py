from django.db import models
from django.utils import timezone
from django.db.models import Q, Sum, Avg
from django.db.models.signals import m2m_changed, post_save
from django.contrib.auth.models import User
from mptt.models import MPTTModel, TreeForeignKey, TreeManyToManyField
import datetime
from django.core.exceptions import ObjectDoesNotExist


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
                   syllabus_point=self,
                   most_recent=True). \
            aggregate(Sum('total_marks_attempted'))['total_marks_attempted__sum']
        total_correct = StudentSyllabusAssessmentRecord.objects. \
            filter(student__in=students,
                   syllabus_point=self,
                   most_recent=True). \
            aggregate(Sum('total_marks_correct'))['total_marks_correct__sum']
        if total_correct:
            return round(total_correct / total_attempted * 100, 0)
        else:
            return 0


    def set_student_records(self, sitting):
        # Set this level's records:

        record, created = StudentSyllabusAssessmentRecord.objects.get(student=student,
                                                                      sitting=sitting)



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
            record, created = StudentSyllabusAssessmentRecord.objects.get_or_create(student=self.student,
                                                                           syllabus_point=point,
                                                                           sitting=self.sitting)


class StudentSyllabusAssessmentRecord(models.Model):
    syllabus_point = TreeForeignKey(Syllabus, on_delete=models.CASCADE, blank=False, null=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, blank=False, null=False)
    sitting = models.ForeignKey(Sitting, blank=True, null=True, on_delete=models.CASCADE)

    attempted_this_level = models.FloatField(blank=True, null=True, help_text='total marks tried for this point only')
    correct_this_level = models.FloatField(blank=True, null=True, help_text='total marks scored for this point only')
    attempted_plus_children = models.FloatField(blank=True, null=True, help_text='total marks tried for this point and children')
    correct_plus_children = models.FloatField(blank=True, null=True, help_text='total marks scored for this point and children')

    percentage = models.FloatField(blank=True, null=True)
    rating = models.FloatField(blank=True, null=True)
    children_0_1 = models.IntegerField(blank=True, null=True, help_text='total children rated 0-1')
    children_1_2 = models.IntegerField(blank=True, null=True, help_text='total children rated 1-2')
    children_2_3 = models.IntegerField(blank=True, null=True, help_text='total children rated 2-3')
    children_3_4 = models.IntegerField(blank=True, null=True, help_text='total children rated 3-4')
    children_4_5 = models.IntegerField(blank=True, null=True, help_text='total children rated 4-5')

    most_recent = models.BooleanField(blank=True, null=True, default=False)

    @property
    def percentage_correct(self):
        return round(self.total_marks_correct / self.total_marks_attempted * 100, 0)

    def __str__(self):
        return str(self.student) + " " + str(self.syllabus_point) + " <" + str(self.percentage_correct) + ">"


def syllabus_record_created(sender, instance, created, **kwargs):
    """ Ensure that there's only ever one 'most recent' record, and that is set by the date of assessment. """
    if created:
        competitors = StudentSyllabusAssessmentRecord.objects.filter(syllabus_point=instance.syllabus_point,
                                                                     student=instance.student).order_by('-sitting__date')
        # This should order with most recent first

        # Save computation if it's just us:
        if competitors.count() == 1:
            instance.most_recent = True
            instance.save()
            return instance

        else:
            for competitor in competitors:
                competitor.most_recent = False
                competitor.save()
            competitors[0].most_recent = True
            competitors[0].save()
            return instance


def set_assessment_record_chain(record=StudentSyllabusAssessmentRecord.objects.none(), sitting=Sitting.objects.none()):
    """ This is used to set an assessment record for a given sitting for a student. Note that this shouldn't be
    used for all sittings, as we'd end up with lots of identical scores."""

    # Hold old values in memory to use to re-set parents:
    old_rating = record.rating
    old_attempted_plus_children = record.attempted_plus_children
    old_correct_plus_children = record.correct_plus_children

    # 1. Set the levels for the current assessment record
    # - Find all marks for this level (and ONLY this level) after the last reset point. We want ones scored after
    #   the last reset, and not after this sitting.
    # - Store these marks in 'level_totals'.

    marks = Mark.objects.filter(question__syllabus_points=record.syllabus_point,
                             student=record.student,
                                sitting__date__lte=sitting.date)
    if marks.filter(sitting__resets_ratings=True).count():
        last_relevant_sitting = marks.filter(sitting__rests_ratings=True).order_by('-sitting__date')[0]
        marks = marks.filter(sitting__date__gte=last_relevant_sitting.sitting.date)

    data = marks.aggregate(Sum('question__max_score'), Sum('score'))
    record.attempted_this_level = data['question__max_score__sum']
    record.correct_this_level = data['score__sum']

    # 2. Get total marks at this level by adding on children totals (use just children and their whole tree totals)
    children_data = StudentSyllabusAssessmentRecord.objects.filter(student=record.student,
                                                                   syllabus_point__in=record.syllabus_point.get_descendants()).\
        aggregate(Sum('attempted_plus_children'), Sum('correct_plus_children'))

    record.attempted_plus_children = data['question__max_score__sum'] + children_data['attempted_plus_children__sum']
    record.correct_plus_children = data['score__sum'] + children_data['correct_plus_children__sum']

    # 3. Iterate up through parents. Take parent old score, and add the difference between my previous totals and my new total.

    delta_attempted = record.attempted_plus_children - old_attempted_plus_children
    delta_correct = record.correct_plus_children - old_correct_plus_children

    for parent in record.syllabus_point.get_ancestors():
        student_record = StudentSyllabusAssessmentRecord.objects.get_or_create(student=record.student,
                                                                               syllabus_point=parent,
                                                                               most_recent=True)
        student_record.attempted_plus_children += delta_attempted
        student_record.correct_plus_children += delta_correct
        student_record.save()

    record.save()

post_save.connect(syllabus_record_created, sender=StudentSyllabusAssessmentRecord)


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
