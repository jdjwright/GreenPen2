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
        try:
            return self.user.first_name
        except AttributeError:
            return "Unknown first"

    def last_name(self):
        try:
            return self.user.last_name
        except AttributeError:
            return "Unknown last"

    def email(self):
        try:
            return self.user.email
        except AttributeError:
            return "Unknown email"

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
            aggregate(Sum('attempted_plus_children'))['attempted_plus_children__sum']
        total_correct = StudentSyllabusAssessmentRecord.objects. \
            filter(student__in=students,
                   syllabus_point=self,
                   most_recent=True). \
            aggregate(Sum('correct_plus_children'))['correct_plus_children__sum']
        if total_correct:
            return round(total_correct / total_attempted * 100, 0)
        else:
            return 0


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
            set_assessment_record_chain(record, record.sitting)


class StudentSyllabusAssessmentRecord(models.Model):
    syllabus_point = TreeForeignKey(Syllabus, on_delete=models.CASCADE, blank=False, null=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, blank=False, null=False)
    sitting = models.ForeignKey(Sitting, blank=False, null=False, on_delete=models.CASCADE)
    order = models.IntegerField(blank=False, null=False, default=0)

    attempted_this_level = models.FloatField(blank=False,
                                             null=False,
                                             default=0,
                                             help_text='total marks tried for this point only')
    correct_this_level = models.FloatField(blank=False, null=False,
                                           default=0,
                                           help_text='total marks scored for this point only')
    attempted_plus_children = models.FloatField(blank=False, null=False,
                                                default=0,
                                                help_text='total marks tried for this point and children')
    correct_plus_children = models.FloatField(blank=False, null=False,
                                              default=0,
                                              help_text='total marks scored for this point and children')

    percentage = models.FloatField(blank=False, null=False, default=0)
    rating = models.FloatField(blank=False, null=False, default=0)
    children_0_1 = models.IntegerField(blank=False, null=False, default=0, help_text='total children rated 0-1')
    children_1_2 = models.IntegerField(blank=False, null=False, default=0, help_text='total children rated 1-2')
    children_2_3 = models.IntegerField(blank=False, null=False, default=0, help_text='total children rated 2-3')
    children_3_4 = models.IntegerField(blank=False, null=False, default=0, help_text='total children rated 3-4')
    children_4_5 = models.IntegerField(blank=False, null=False, default=0, help_text='total children rated 4-5')

    most_recent = models.BooleanField(blank=True, null=True, default=False)

    class Meta:
        unique_together = [('student', 'sitting', 'syllabus_point'),
                           ('student', 'syllabus_point', 'order')]

    @property
    def percentage_correct(self):
        if self.attempted_this_level:
            return round(self.correct_this_level / self.attempted_this_level * 100, 0)
        else:
            return 0

    def __str__(self):
        return str(self.student) + " " + str(self.syllabus_point) + " <" + str(self.percentage_correct) + ">"

    def set_calculated_fields(self):
        """ These need to be stored to speed up reports via database aggregation """

        self.percentage = round(self.correct_plus_children / self.attempted_plus_children * 100, 0)
        self.rating = self.percentage * 0.02

        # Set the children elements
        relevant_children = StudentSyllabusAssessmentRecord.objects.filter(student=self.student,
                                                                           most_recent=True,
                                                                           syllabus_point__in=self.syllabus_point.
                                                                           get_descendants())
        self.children_0_1 = relevant_children.filter(rating__lte=1).count()
        self.children_1_2 = relevant_children.filter(rating__lte=2).count()
        self.children_2_3 = relevant_children.filter(rating__lte=3).count()
        self.children_3_4 = relevant_children.filter(rating__lte=4).count()
        self.children_4_5 = relevant_children.filter(rating__lte=5).count()
        self.save()


def syllabus_record_created(sender, instance, created, **kwargs):
    """ Ensure that there's only ever one 'most recent' record, and that is set by the date of assessment. """
    if created:
        competitors = StudentSyllabusAssessmentRecord.objects.filter(syllabus_point=instance.syllabus_point,
                                                                     student=instance.student).order_by(
                                                                                                '-sitting__date')
        # This should order with most recent first
        # TODO: Remove - debug statement
        total_records = competitors.count()
        # Save computation if it's just us:
        if total_records == 1:
            instance.most_recent = True
            instance.order = total_records
            instance.save()
            return instance

        else:
            i = total_records
            for competitor in competitors:
                competitor.most_recent = False
                competitor.order = i
                i += -1
                competitor.save()
            most_recent_competitor = competitors[0]
            if most_recent_competitor == instance:
                instance.most_recent = True
                instance.order = total_records
                instance.save()
            most_recent_competitor.most_recent = True
            most_recent_competitor.order = total_records
            most_recent_competitor.save()
            return instance


def set_assessment_record_chain(record=StudentSyllabusAssessmentRecord.objects.none(), sitting=Sitting.objects.none()):
    """ This is used to set an assessment record for a given sitting for a student. Note that this shouldn't be
    used for all sittings, as we'd end up with lots of identical scores."""

    # Hold old values in memory to use to re-set parents:
    try:
        previous_record = StudentSyllabusAssessmentRecord.objects.get(student=record.student,
                                                                  syllabus_point=record.syllabus_point,
                                                                  order=record.order - 1)
        old_attempted_plus_children = previous_record.attempted_plus_children
        old_correct_plus_children = previous_record.correct_plus_children
    except ObjectDoesNotExist:
        old_attempted_plus_children = 0
        old_correct_plus_children = 0



    # 1. Set the levels for the current assessment record
    # - Find all marks for this level (and ONLY this level) after the last reset point. We want ones scored after
    #   the last reset, and not after this sitting.
    # - Store these marks in 'level_totals'.

    marks = Mark.objects.filter(question__syllabus_points=record.syllabus_point,
                                student=record.student,
                                sitting__date__lte=sitting.date)
    if marks.filter(sitting__resets_ratings=True).count():
        last_relevant_sitting = marks.filter(sitting__resets_ratings=True).order_by('-sitting__date')[0]
        marks = marks.filter(sitting__date__gte=last_relevant_sitting.sitting.date)

    data = marks.aggregate(Sum('question__max_score'), Sum('score'))
    record.attempted_this_level = data['question__max_score__sum']
    record.correct_this_level = data['score__sum']

    # 2. Get total marks at this level by adding on children totals (use just children and their whole tree totals)
    children_data = StudentSyllabusAssessmentRecord.objects.filter(student=record.student,
                                                                   syllabus_point__in=record.syllabus_point.get_descendants()). \
        aggregate(Sum('attempted_plus_children'), Sum('correct_plus_children'))

    record.attempted_plus_children = data['question__max_score__sum'] + float(
        children_data['attempted_plus_children__sum'] or 0)
    record.correct_plus_children = data['score__sum'] + float(children_data['correct_plus_children__sum'] or 0)

    # Set calculated fields:
    record.save()
    record.set_calculated_fields()

    # 3. Iterate up through parents. Take parent old score, and add the difference between my previous totals
    #    and my new total.

    delta_attempted = record.attempted_plus_children - old_attempted_plus_children
    delta_correct = record.correct_plus_children - old_correct_plus_children
    for parent in record.syllabus_point.get_ancestors():

        # Need to get the last record since this may have been from a previous sitting.
        # If we didn't do this, we'd always start with 0 as our attempted_plus_children etc.

        previous, created = StudentSyllabusAssessmentRecord.objects.get_or_create(student=record.student,
                                                                         syllabus_point=parent,
                                                                         most_recent=True,
                                                                         defaults={'sitting': record.sitting,
                                                                                   'attempted_plus_children': delta_attempted,
                                                                                   'correct_plus_children': delta_correct})
        if created:
            previous.set_calculated_fields()
            return
        else:
            student_record, created = StudentSyllabusAssessmentRecord.objects.get_or_create(student=record.student,
                                                                                   syllabus_point=parent,
                                                                                   sitting=record.sitting)
            student_record.attempted_plus_children =previous.attempted_plus_children + delta_attempted
            student_record.correct_plus_children = previous.correct_plus_children + delta_correct
            student_record.set_calculated_fields()



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
