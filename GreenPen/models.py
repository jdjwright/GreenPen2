from django.db import models
from django.utils import timezone
from django.db.models import Q, Sum, Avg, QuerySet
from django.db.models.signals import m2m_changed, post_save
from django.contrib.auth.models import User, Group
from mptt.models import MPTTModel, TreeForeignKey, TreeManyToManyField
from mptt.querysets import TreeQuerySet
import datetime
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import IntegrityError, transaction
from django.urls import reverse
from GreenPen.settings import CALENDAR_START_DATE, CALENDAR_END_DATE, ACADEMIC_YEARS
from django.db.models import Max
from .validators import validate_g_form, validate_g_sheet
from ckeditor.fields import RichTextField
from .exceptions import MarkScoreError, AlreadyImportingScoreError
import gspread
import re
from django.dispatch import receiver
from django_pandas.io import read_frame
import pandas as pd
from django.utils.html import mark_safe
import dash_html_components as html
import dash_bootstrap_components as dbc


class Person(models.Model):
    user = models.OneToOneField(User, blank=True, null=True, on_delete=models.CASCADE, unique=True)

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
    on_role = models.BooleanField(default=True)

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
        return str(self.title) + " " + str(self.full_name()) + " (" + str(self.staff_code) + ")"


class Subject(models.Model):
    name = models.CharField(max_length=200, blank=False, null=False, unique=True)
    HoDs = models.ManyToManyField(Teacher)

    def __str__(self):
        return self.name


class TeachingGroup(models.Model):
    name = models.CharField(max_length=256, blank=True, null=True)
    sims_name = models.CharField(max_length=256, blank=True, null=True)
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, blank=True, null=True)
    teachers = models.ManyToManyField(Teacher, blank=True)
    students = models.ManyToManyField(Student, blank=True)
    syllabus = TreeForeignKey('Syllabus', blank=True, null=True, on_delete=models.SET_NULL)
    archived = models.BooleanField(blank=True, null=True, default=False)
    year_taught = models.IntegerField(null=True, blank=True, help_text="This is the counter for academic years (e.g. 2020-21), NOT yeargroup!") # To be depreciated
    academic_year = models.ForeignKey('AcademicYear', blank=False, null=True, on_delete=models.SET_NULL)
    rollover_name = models.CharField(max_length=256, blank=True, null=True)
    lessons = models.ManyToManyField('TTSlot', blank=True)
    use_for_exams = models.BooleanField(default=True,
                                        help_text="If you have mutliple identical groups, e.g. same A-level class taught by two different teachers, you will need to create three groups: one for each teacher, and one shared one. Use the teacher groups for timetabling and lesson monitoring, and the shared one for all exams. The'Use for exams' flag should be set for the exam class.")
    linked_groups = models.ManyToManyField('TeachingGroup', blank=True)

    def __str__(self):
        if not self.archived:
            return self.name
        else:
            return self.name + "ARCHIVED"

    def set_linked_students(self):
        """
        Take the linked_grouops for this tg and set the students to be the same as for this one
        """
        for group in self.linked_groups.all():
            group.students.set(self.students.all())

    def find_linked_groups(self):
        """
        In the dev teams school, teaching groups have the convention:
        10A/Ss1 <-- for single groups
        10A/Ss1a <-- for groups taught by multiple teachers. E.g.,
        10A/Ss1a taught by Mr Bloggs
        10A/Ss1b taught by Mrs Amir.

        Since the students in 10A/Ss1 are always the same, we need to
        try to sync them so that all assessments appear together.
        """
        gen_code = re.search(r'^(.*)\D$', self.name)
        if gen_code:
            matches = gen_code.groups()
            groups = TeachingGroup.objects.all().exclude(pk=self.pk).filter(name__startswith=matches[0], archived=False)
            self.linked_groups.set(groups)

            return groups

    def ratings_pc_between_range(self, min_rating, max_rating, sittings=False, students=False, syllabus_pts=False):
        all_records = StudentSyllabusAssessmentRecord.objects.filter(student__in=self.students.all())
        if isinstance(sittings, QuerySet):
            # Have to do it this way to prevent an error of referencing Sittings before
            # using it.
            all_records = all_records.filter(sitting__in=sittings)
        if isinstance(students, QuerySet):
            all_records = all_records.filter(student__in=students)
        if isinstance(syllabus_pts, TreeQuerySet):
            all_records = all_records.filter(syllabus_point__in=syllabus_pts)

        total = all_records.distinct().count()
        if not total:
            return 0
        relevant_records = all_records.filter(rating__gte=min_rating,
                                              rating__lt=max_rating).distinct().count()
        return round(relevant_records / total * 100, 0)


def post_tg_lesson_add(sender, **kwargs):
    """
    This function is tiggered after adding a lesson to a teaching group.
    It creates lessons (class Lesson) so that timetables can be populated
    propertly.
    :param lesson: the instance of the TTSlot assigned to this group
    :return:
    """
    tg = kwargs['instance']
    if 'post_add' in kwargs['action']:
        setup_lessons(teachinggrousp=TeachingGroup.objects.filter(pk=tg.pk))


m2m_changed.connect(post_tg_lesson_add, sender=TeachingGroup.lessons.through)


class Syllabus(MPTTModel):
    text = models.TextField(blank=False, null=False)
    parent = TreeForeignKey('Syllabus', blank=True, null=True, on_delete=models.CASCADE)
    identifier = models.CharField(max_length=20, blank=True, null=True,
                                  help_text='This would be a sub point number, e.g. if this is 1.1.1 Blah blah, enter 1')
    tier = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        ordering = ['identifier']

    class MPTTMeta:
        order_insertion_by = ['identifier']

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

    def cohort_stats(self, students=Student.objects.none(), sittings=False):
        records = StudentSyllabusAssessmentRecord.objects.filter(student__in=students,
                                                                 syllabus_point=self)
        if sittings:
            records = records.filter(sitting__in=sittings)

        else:
            records = records.filter(most_recent=True)

        data = records.aggregate(percentage=Avg('percentage'),
                                 rating=Avg('rating'),
                                 children_0_1=Sum('children_0_1'),
                                 children_1_2=Sum('children_1_2'),
                                 children_2_3=Sum('children_2_3'),
                                 children_3_4=Sum('children_3_4'),
                                 children_4_5=Sum('children_4_5'))
        return data

    def resources(self, users=False):
        resources = Resource.objects.filter(syllabus__in=self.get_descendants(include_self=True))
        return resources

    @property
    def resources_markdown(self):
        string = ""
        for r in self.resources():
            string += r.markdown()
        return string

    @property
    def resources_html(self):
        string = ""
        for r in self.resources():
            string += r.html()
        return mark_safe(string)

    def dash_resources(self, user):
        list = []

        for r in self.resources():
            # Teachers get a link to edit the resource

            if user.groups.filter(name='Teachers').count():
                link = reverse('edit-resource', args=[r.pk])
            elif user.groups.filter(name='Students').count():
                student_pk = Student.objects.get(user=user).pk
                link = r.student_clickable_link(student_pk)
            row = html.Div([
                html.A(target='_blank', href=link, id="resource-" + str(r.pk),
                       children=[html.I(className=r.type.icon)]),
                dbc.Tooltip(r.name, target="resource-" + str(r.pk))
            ])
            list.append(row)
        return list


class ExamType(models.Model):
    """
    Provides a list of exam types
    """
    type = models.CharField(max_length=256, blank=False, null=False)
    eligible_for_self_assessment = models.BooleanField(default=False)

    def __str__(self):
        return self.type


class Exam(models.Model):
    name = models.CharField(max_length=256, blank=False, null=False)
    syllabus = TreeForeignKey('Syllabus', blank=True, null=True, on_delete=models.SET_NULL)
    weighting = models.FloatField(blank=False, null=False, default=1)
    type = models.ForeignKey(ExamType,
                             blank=False,
                             null=True,
                             on_delete=models.SET_NULL)
    year = models.IntegerField(blank=False, null=True,
                               help_text="Year group sitting this exam"
                               )
    mark_scheme_url = models.URLField(blank=True, null=True, help_text="Location of the mark scheme.")

    share_mark_scheme = models.BooleanField(default=False,
                                            help_text="Make this mark scheme available to students.")

    def total_score(self):
        return Question.objects.filter(exam=self).aggregate(Sum('max_score'))['max_score__sum']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('edit-exam', args=[str(self.id)])

    def duplicate(self):
        # Create a new model instance with a new pk but same settings
        # Note: something strange happens with python's copy
        # system, meaning that we have to store the original
        # item, Otherwise, trying to get the questions assosciated
        # with the original will instead give the copy.
        original_pk = self.pk
        new = self
        new.pk = None
        new.save()
        original = Exam.objects.get(pk=original_pk)

        # Now copy questions
        questions = Question.objects.filter(exam=original)
        for question in questions:
            # Duplicate the question:
            original_q_pk = question.pk
            newq = question
            newq.pk = None
            newq.exam = new
            newq.save()
            original_q = Question.objects.get(pk=original_q_pk)
            newq.syllabus_points.set(original_q.syllabus_points.all())

        return new


class Question(models.Model):
    exam = models.ForeignKey(Exam, blank=False, null=False, on_delete=models.CASCADE)
    order = models.FloatField(blank=False, null=False)
    number = models.CharField(max_length=10, blank=False, null=False)
    max_score = models.FloatField(blank=False, null=True)
    syllabus_points = TreeManyToManyField(Syllabus, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.number

    def average(self, cohort=Student.objects.all(), sittings=False):
        if not sittings:
            sittings = Sitting.objects.all()
        marks = Mark.objects.filter(question=self, student__in=cohort, sitting__in=sittings)
        avg = marks.aggregate(Avg('score'))
        return avg['score__avg']

    def average_pc(self, cohort=Student.objects.all(), sittings=False):
        avg = self.average(cohort, sittings)
        if self.max_score and avg:
            return round(avg / self.max_score * 100, 0)


def new_question_created(sender, instance, **kwargs):
    for sitting in Sitting.objects.filter(exam__question=instance):
        sync_marks_with_sittings(sitting)


post_save.connect(new_question_created, sender=Question)


class Sitting(models.Model):
    exam = models.ForeignKey(Exam, blank=False, null=False, on_delete=models.CASCADE)
    date = models.DateTimeField(blank=False, null=False, default=datetime.datetime.now())
    students = models.ManyToManyField(Student)
    resets_ratings = models.BooleanField(blank=True, null=True, default=False)
    group = models.ForeignKey(TeachingGroup, blank=True, null=True, on_delete=models.SET_NULL)
    imported = models.BooleanField(default=True, help_text='Set to true after results have been imported.')

    class Meta:
        permissions = [
            ('create_any_sitting', "Can create a sitting for any classgroup"),
        ]

    def __str__(self):
        return str(self.exam) + " - " + str(self.group) + " " + str(self.date.date())

    def avg_percent(self):
        student_marks = Mark.objects.filter(sitting=self,
                                            score__isnull=False)
        if student_marks.count():
            data = student_marks.aggregate(scored=Sum('score'), total=Sum('question__max_score'))
            if data['total']:
                return int(data['scored'] / data['total'] * 100)

        return "No scores"

    def avg_pc_badge_class(self):
        if self.avg_percent() == "No scores":
            return "badge-secondary"
        if self.avg_percent() < 20:
            return "badge-danger"
        elif self.avg_percent() < 40:
            return "badge-warning"
        elif self.avg_percent() < 60:
            return "badge-info"
        elif self.avg_percent() < 80:
            return "badge-primary"
        elif self.avg_percent() <= 100:
            return "badge-success"
        else:
            return "badge-secondary"

    def avg_syllabus_rating(self, syllabus=Syllabus.objects.none(), students=Student.objects.all()):
        """
        Calculate the average rating for the cohort taking this exam.
        Optionally, restrict it to just a single syllabus point.
        """
        ratings = StudentSyllabusAssessmentRecord.objects.filter(sitting=self,
                                                                 syllabus_point=syllabus,
                                                                 rating__isnull=False,
                                                                 student__in=students)
        if ratings.count():
            return round(ratings.aggregate(avg=Avg('rating'))['avg'], 1)
        else:
            return False

    def student_total(self, student=Student.objects.none()):
        marks = Mark.objects.filter(sitting=self,
                                    student=student)
        return marks.aggregate(total=Sum('score'))['total']

    def student_qs(self):
        if self.students.count():
            return self.students.all()
        else:
            return Student.objects.filter(teachinggroup=self.group)

    def get_generic_teaching_group(self):
        """
        IF creating a whole-school self-assessment task,
        this function will return the teaching group associated with
        all students taking that exam.
        """

        if self.group:
            # Dont' over-write explicity let groups
            return self.group

        else:
            student = self.students.first()
            year = student.year_group
            subject = self.exam.syllabus.get_ancestors(include_self=True).get(level=2)
            group, created = TeachingGroup.objects.get_or_create(name="Year " + str(year) + " " + subject.text,
                                                                 defaults={
                                                                     'year_taught': year,
                                                                     'syllabus': subject,

                                                                 })
            group.students.add(*self.students.all())
            return group


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


class Mistake(MPTTModel):
    mistake_type = models.CharField(blank=False, null=False, max_length=256)
    parent = TreeForeignKey('Mistake', blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.mistake_type

    def cohort_totals(self, cohort=Student.objects.all(), syllabus=Syllabus.objects.all(),
                      sittings=Sitting.objects.all()):
        return round(Mark.objects.filter(mistakes=self,
                                         student__in=cohort,
                                         sitting__in=sittings,
                                         question__syllabus_points__in=syllabus).count(), 1)


class Mark(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, blank=False, null=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, blank=False, null=False)
    score = models.FloatField(blank=True, null=True)
    sitting = models.ForeignKey(Sitting, blank=False, null=True, on_delete=models.CASCADE)
    mistakes = TreeManyToManyField(Mistake, blank=True)
    student_notes = RichTextField(blank=True, null=True)

    class Meta:
        unique_together = ['student', 'question', 'sitting']

    def save(self, *args, **kwargs):
        super(Mark, self).save(*args, **kwargs)
        if self.score is not None:
            self.set_student_syllabus_assessment_records()

    def pc(self):
        if self.question.max_score and self.score:
            return round(self.score / self.question.max_score * 100, 0)

    def score_class(self):
        pc = self.pc()
        if pc == 0:
            return "danger"
        if not pc:
            return ""
        if pc < 20:
            return "danger"
        elif pc < 40:
            return "warning"
        elif pc < 60:
            return "info"
        elif pc < 80:
            return "primary"
        elif pc <= 100:
            return "success"
        else:
            return "secondary"

    def set_student_syllabus_assessment_records(self):
        for point in self.question.syllabus_points.all():
            record, created = StudentSyllabusAssessmentRecord.objects.get_or_create(student=self.student,
                                                                                    syllabus_point=point,
                                                                                    sitting=self.sitting)
            # Here be dragons! When we create a record, logic in the background then sets
            # it to the most recent. HOWEVER, we've loaded this into memory, so the instance
            # that gets sent to set_assessment_record_chain is the OLD one, without
            # the correct 'most recent' flag.
            record = StudentSyllabusAssessmentRecord.objects.get(student=self.student,
                                                                 syllabus_point=point,
                                                                 sitting=self.sitting)
            set_assessment_record_chain(record)
            # If the record chain was not the most recent, we also need to re-set
            # the records that came after it:
            if not record.most_recent:
                for newerrec in StudentSyllabusAssessmentRecord.objects.filter(student=self.student,
                                                                               syllabus_point=point,
                                                                               sitting__date__gte=record.sitting.date):
                    set_assessment_record_chain(newerrec)

    def get_absolute_url(self):
        return reverse('edit-mark', kwargs={'pk': self.pk})

    def get_previous(self):
        if self.question.order > 1:
            previous_q = Question.objects.get(exam=self.sitting.exam,
                                              order=self.question.order - 1)
            return Mark.objects.get(student=self.student,
                                    sitting=self.sitting,
                                    question=previous_q)
        else:
            return False


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

        # Avoid divide by zero error.
        if not self.attempted_plus_children:
            return
        self.percentage = round(self.correct_plus_children / self.attempted_plus_children * 100, 0)
        self.rating = self.percentage * 0.05

        # Set the children elements
        # Need to include self so that we can aggregate ratings for cohorts (e.g. if we
        # are at the last node (leaf node) we need to know how many got a rating of 2;
        # therefore include self here.,
        # Need to save self, otherwise won't appear in the searched records:
        self.save()
        relevant_children = StudentSyllabusAssessmentRecord.objects.filter(student=self.student,
                                                                           most_recent=True,
                                                                           syllabus_point__in=self.syllabus_point.
                                                                           get_descendants(include_self=True))
        self.children_0_1 = relevant_children.filter(rating__lte=1).count()
        self.children_1_2 = relevant_children.filter(rating__lte=2, rating__gt=1).count()
        self.children_2_3 = relevant_children.filter(rating__lte=3, rating__gt=2).count()
        self.children_3_4 = relevant_children.filter(rating__lte=4, rating__gt=3).count()
        self.children_4_5 = relevant_children.filter(rating__lte=5, rating__gt=4).count()
        self.save()


def fix_student_assessment_record_order(students=Student.objects.all(), points=Syllabus.objects.all()):
    """
    Used to repair orders if they become corrupt
    :return:
    """

    i = 0
    total = students.count()
    for student in students:
        for point in points:
            rerun = False
            competitors = StudentSyllabusAssessmentRecord.objects.filter(student=student,
                                                                         syllabus_point=point). \
                order_by('-order').distinct()

            # Firstly, set orders to something that cannot clash:
            for competitor in competitors:
                competitor.order = competitors[0].order + competitor.order + 1
                competitor.save()
            # Refresh from db:
            competitors = StudentSyllabusAssessmentRecord.objects.filter(student=student,
                                                                         syllabus_point=point). \
                order_by('-order').distinct()

            # Re-do order correctly:
            i = competitors.count() + 1
            for competitor in competitors:
                competitor.order = i
                competitor.save()
                i = i - 1


def syllabus_record_created(sender, instance, created, **kwargs):
    """ Ensure that there's only ever one 'most recent' record, and that is set by the date of assessment. """
    if created:
        competitors = StudentSyllabusAssessmentRecord.objects.filter(syllabus_point=instance.syllabus_point,
                                                                     student=instance.student).order_by(
            '-sitting__date')
        # This should order with most recent first

        total_comps = competitors.count()
        i = total_comps  # maximum order number
        j = 1  # used for duplicate competior order number; needs to increment after a clash.
        # We can run into trouble here if we set a compeitor when another already has that order.

        for competitor in competitors:
            competitor.most_recent = False
            competitor.order = i
            i += -1
            try:
                with transaction.atomic():
                    competitor.save()
            except IntegrityError:  # This occurs if we try to write a new order number when another has it.
                other = competitors.get(order=competitor.order)
                other.order = (total_comps + j)
                j += 1
                try:
                    with transaction.atomic():
                        other.save()
                        competitor.save()
                except IntegrityError:
                    # This occurs if our ordering has somehow become corrupted.
                    fix_student_assessment_record_order(students=Student.objects.filter(pk=other.student.pk),
                                                        points=Syllabus.objects.filter(pk=other.syllabus_point.pk))

        # Refresh from db to check correct competitors:
        competitors = StudentSyllabusAssessmentRecord.objects.filter(syllabus_point=instance.syllabus_point,
                                                                     student=instance.student).order_by(
            '-sitting__date')
        most_recent_competitor = competitors[0]
        if instance.pk == most_recent_competitor.pk:  # Don't use just == as might have changed flags
            newer_reset_reqd = False
        else:
            newer_reset_reqd = True
        # Make sure none are most recent:
        most_recents = competitors.filter(most_recent=True)
        for competitor in most_recents:
            competitor.most_recent = False
            competitor.save()
        most_recent_competitor.most_recent = True
        most_recent_competitor.save()

        # Refresh from DB so that we don't send back the old instance with the wrong date and order:
        instance = StudentSyllabusAssessmentRecord.objects.get(pk=instance.pk)

        return instance, newer_reset_reqd


def set_assessment_record_chain(record=StudentSyllabusAssessmentRecord.objects.none()):
    """ This is used to set an assessment record for a given sitting for a student. Note that this shouldn't be
    used for all sittings, as we'd end up with lots of identical scores."""

    # Hold old values in memory to use to re-set parents:
    # We need to check if there was a previous value from a different sitting. However,
    # we also need to be aware that the previous record may be from this same sitting, so
    # need to test if we're the only one:

    # Be careful here; if we're working with a chain that occured BEFORE another assessment
    # (e.g. a student forgot to add an assessment score and has just put it in)
    # then the retrieval of the preivious one could fail.
    total_records = StudentSyllabusAssessmentRecord.objects.filter(student=record.student,
                                                                   syllabus_point=record.syllabus_point,
                                                                   ).count()
    if StudentSyllabusAssessmentRecord.objects.filter(student=record.student,
                                                      syllabus_point=record.syllabus_point).count() <= 1:
        old_attempted_plus_children = record.attempted_plus_children
        old_correct_plus_children = record.correct_plus_children
    else:
        try:
            previous_record = StudentSyllabusAssessmentRecord.objects.get(student=record.student,
                                                                          syllabus_point=record.syllabus_point,
                                                                          order=record.order - 1)
            old_attempted_plus_children = previous_record.attempted_plus_children
            old_correct_plus_children = previous_record.correct_plus_children
        except ObjectDoesNotExist:
            old_attempted_plus_children = record.attempted_plus_children
            old_correct_plus_children = record.correct_plus_children
    # 1. Set the levels for the current assessment record
    # - Find all marks for this level (and ONLY this level) after the last reset point. We want ones scored after
    #   the last reset, and not after this sitting.
    # - Store these marks in 'level_totals'.

    marks = Mark.objects.filter(question__syllabus_points=record.syllabus_point,
                                student=record.student,
                                sitting__date__lte=record.sitting.date)
    if marks.filter(sitting__resets_ratings=True).count():
        last_relevant_sitting = marks.filter(sitting__resets_ratings=True).order_by('-sitting__date')[0]
        marks = marks.filter(sitting__date__gte=last_relevant_sitting.sitting.date)

    data = marks.aggregate(Sum('question__max_score'), Sum('score'))
    record.attempted_this_level = data['question__max_score__sum']
    record.correct_this_level = data['score__sum']

    # 2. Get total marks at this level by adding on children totals (use just children and their whole tree totals)
    children_data = StudentSyllabusAssessmentRecord.objects.filter(student=record.student,
                                                                   syllabus_point__in=record.syllabus_point.get_descendants(),
                                                                   most_recent=True). \
        aggregate(Sum('attempted_this_level'), Sum('correct_this_level'))

    record.attempted_plus_children = float(data['question__max_score__sum'] or 0) + float(
        children_data['attempted_this_level__sum'] or 0)
    record.correct_plus_children = float(data['score__sum'] or 0) + float(children_data['correct_this_level__sum'] or 0)

    # Set calculated fields:
    record.save()
    record.set_calculated_fields()

    # 3. Iterate up through parents. Take parent old score, and add the difference between my previous totals
    #    and my new total.

    delta_attempted = record.attempted_plus_children - old_attempted_plus_children
    delta_correct = record.correct_plus_children - old_correct_plus_children
    parents = list(record.syllabus_point.get_ancestors(ascending=True))
    for parent in parents:

        # Need to get the last record since this may have been from a previous sitting.
        # If we didn't do this, we'd always start with 0 as our attempted_plus_children etc.
        # THIS IS WRONG; previous should be closest by date.
        previous, created = StudentSyllabusAssessmentRecord.objects.get_or_create(student=record.student,
                                                                                  syllabus_point=parent,
                                                                                  most_recent=True,
                                                                                  defaults={'sitting': record.sitting,
                                                                                            'attempted_plus_children': delta_attempted,
                                                                                            'correct_plus_children': delta_correct})
        if created:
            previous = StudentSyllabusAssessmentRecord.objects.get(student=record.student,
                                                                   syllabus_point=parent,
                                                                   most_recent=True)
            previous.set_calculated_fields()
            continue
        else:
            # Todo: remove debug statement
            student_record, created = StudentSyllabusAssessmentRecord.objects.get_or_create(student=record.student,
                                                                                            syllabus_point=parent,
                                                                                            sitting=record.sitting)
            # Here be dragons again! We need to refresh the db because we have to automatically set the order.
            student_record = StudentSyllabusAssessmentRecord.objects.get(student=record.student,
                                                                         syllabus_point=parent,
                                                                         sitting=record.sitting)
            student_record.attempted_plus_children = previous.attempted_plus_children + delta_attempted
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


@receiver(post_save, sender=Mark)
def student_mark_changed(sender, instance=Mark.objects.none(), **kwargs):
    if instance.score is not None:
        instance.set_student_syllabus_assessment_records()


# post_save.connect(student_mark_changed, sender=Mark)


class CSVDoc(models.Model):
    description = models.CharField(max_length=255, blank=True)
    document = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)


class ResourceType(models.Model):
    name = models.CharField(max_length=256, blank=False, null=False)
    icon = models.CharField(max_length=256, blank=False, null=True, help_text="Enter a font-awesome string here.")

    def __str__(self):
        return self.name


class Resource(models.Model):
    name = models.CharField(max_length=256, blank=False, null=False)
    open_to_all = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, blank=False, null=True, on_delete=models.SET_NULL)
    created = models.DateTimeField(blank=False, null=False, default=datetime.datetime.now)
    url = models.URLField(blank=True, null=True,
                          help_text='If creating a Google Quiz, this should be a link to edit the quiz on Google Forms.')
    syllabus = TreeManyToManyField(Syllabus, blank=False)
    allowed_groups = models.ManyToManyField(TeachingGroup, blank=True)
    type = models.ForeignKey(ResourceType,
                             blank=False,
                             null=True,
                             on_delete=models.CASCADE,
                             )
    exam = models.ForeignKey('GQuizExam',
                             blank=True,
                             null=True,
                             on_delete=models.SET_NULL,
                             help_text="If you've made a Google Self-Assessed quiz, add it to GreenPen first and then link it here.")

    def __str__(self):
        return self.name

    def can_view(self, user=User.objects.none):
        if self.open_to_all:
            return True

        # Allow teachers to see all
        if Group.objects.filter(user=user).count():
            return True

        allowed_students = User.objects.filter(student__teachinggroup__in=self.allowed_groups)
        if allowed_students.filter(user=user):
            return True

        return False

    def icon(self):
        return self.type.icon

    def get_absolute_url(self):
        return reverse('edit-resource', args=(self.pk,))

    def html(self, student_pk=False):
        string = '<a href="' + self.student_clickable_link(student_pk=student_pk)
        string += '" data-toggle="tooltip" title="' + self.name + '">' + self.type.icon + '</a>'
        return mark_safe(string)

    def markdown(self):
        return "[" + self.name + "](" + mark_safe(self.url) + ")"

    def student_clickable_link(self, student_pk):
        if self.exam:
            if student_pk:
                return reverse('create_self_assessment_sitting',
                               kwargs={'student_pk': student_pk,
                                       'exam_pk': self.exam.pk})
        else:
            return self.url


## Models for calendaring

class AcademicYear(models.Model):
    name = models.CharField(max_length=30, help_text='E.g. "2020-21')
    order = models.IntegerField(null=False)
    current = models.BooleanField(default=False)
    first_monday = models.DateField(
        help_text='This must be the first MONDAY in the school calendar year. Use suspensions if the term does not start on that monday.',
        null=False)
    total_weeks = models.IntegerField(null=False,
                                      help_text='This must be the total number of weeks. If you end with a partial number of weeks, count the partial one as a full week and use suspensions on the remaining lessons')

    def __str__(self):
        return self.name


class Day(models.Model):
    order = models.IntegerField(blank=False, null=False,
                                help_text='The number of days from monday (e.g. Monday = 0, Tuesday = 1...')
    name = models.CharField(null=False, max_length=10)
    year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, null=False)

    class Meta:
        unique_together = [('order', 'name')]
        ordering = ['order']

    def __str__(self):
        return self.name


class Period(models.Model):
    order = models.IntegerField(null=False)
    name = models.CharField(max_length=5, null=True)
    year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, null=False)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order']


class TTSlot(models.Model):
    day = models.ForeignKey(Day, null=False, on_delete=models.CASCADE)
    period = models.ForeignKey(Period, null=False, on_delete=models.CASCADE)
    order = models.IntegerField(null=False)
    year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, null=False, default=1)

    def __str__(self):
        return self.day.name + " P" + self.period.name

    class Meta:
        ordering = ['order']


class Week(models.Model):
    year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, null=False)
    number = models.IntegerField(null=False)

    class Meta:
        ordering = ['number']

    def __str__(self):
        return self.year.name + " wek " + str(self.number)


class CalendaredPeriod(models.Model):
    year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    order = models.IntegerField(null=False)
    tt_slot = models.ForeignKey(TTSlot, null=False, on_delete=models.CASCADE)
    week = models.ForeignKey(Week, null=False, on_delete=models.CASCADE)
    date = models.DateField(null=True)

    class Meta:
        ordering = ['order']

    def set_date(self, automatic=True):
        start_date = self.year.first_monday
        self.date = start_date + datetime.timedelta(weeks=self.week.number,
                                                    days=self.tt_slot.day.order)
        if automatic:
            self.save()
        else:
            return self.date

    @property
    def day(self):
        return self.tt_slot.day.name

    @property
    def period(self):
        return self.tt_slot.period.name

    def __str__(self):
        return str(self.date) + " P" + self.tt_slot.period.name

    def save(self, *args, **kwargs):
        self.set_date(automatic=False)
        super(CalendaredPeriod, self).save(*args, **kwargs)


def set_up_slots(academic_year=AcademicYear.objects.none()):
    # Create weekly slots
    i = 0

    for day in Day.objects.filter(year=academic_year):
        for period in Period.objects.filter(year=academic_year):
            TTSlot.objects.get_or_create(order=i,
                                         day=day,
                                         period=period,
                                         year=academic_year)
            i += 1

    # Set up weekly slots
    i = 0
    for week_num in range(academic_year.total_weeks):
        week, created = Week.objects.get_or_create(year=academic_year,
                                                   number=week_num)
        for slot in TTSlot.objects.filter(year=academic_year):
            CalendaredPeriod.objects.get_or_create(year=academic_year,
                                                   order=i,
                                                   tt_slot=slot,
                                                   week=week,
                                                   date=academic_year.first_monday + datetime.timedelta(
                                                       weeks=week.number,
                                                       days=slot.day.order))
            i += 1


class Suspension(models.Model):
    date = models.DateField(null=False)
    period = models.ForeignKey(Period, null=False, on_delete=models.CASCADE)
    reason = models.CharField(blank=True, null=True, max_length=256)
    teachinggroups = models.ManyToManyField(TeachingGroup, blank=True)
    whole_school = models.BooleanField(null=True)
    slot = models.ForeignKey(CalendaredPeriod, null=True, on_delete=models.CASCADE)

    def set_slot(self, automatic=True):
        try:
            self.slot = CalendaredPeriod.objects.get(date=self.date, tt_slot__period=self.period)
            if automatic:
                self.save()
            return self.slot
        except ObjectDoesNotExist:
            # This occurs if we try to suspend a non-teaching day.
            return False

    def save(self, *args, **kwargs):
        if not self.set_slot(automatic=False):
            # This occurs if we are trying to suspend a non-teaching day
            pass
        if self.whole_school:
            # Assign self to a correct slot
            self.set_slot(automatic=False)
            super(Suspension, self).save(*args, **kwargs)

            # Re-organise lessons affected by this suspension:

            affected_lessons = Lesson.objects.filter(slot=self.slot)

            # We'll need to re-slot these lessons. The recuersion that checks
            # for clashing peers should magically make all the other lessons in the series
            # re-time too.:
            for lesson in affected_lessons:
                lesson.save()  # Save automatically calls 'set_slot'.

        else:
            super(Suspension, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # find the classes affected by this:
        # todo: remove debug filter
        tgs = list(TeachingGroup.objects.filter(lessons=self.slot.tt_slot))
        # Find lessons affected by this suspension:
        tt_lessons = Lesson.objects.filter(slot__date__gte=self.date,
                                           teachinggroup__in=tgs)

        if not self.whole_school:
            tt_lessons = tt_lessons.filter(teachinggroup__in=self.teachinggroups.all())
        list(tt_lessons)  # This shouldn't be required, but for some reason
        # either PyCharm or docker refuses to evaluate the qs without it.
        super(Suspension, self).delete(*args, **kwargs)
        for lesson in tt_lessons:
            lesson.save()


def class_suspended(sender, **kwargs):
    suspension = kwargs['instance']
    if 'post_add' in kwargs['action']:
        classgroups = suspension.teachinggroups.all()
        if classgroups.count():
            affected_lessons = Lesson.objects.filter(teachinggroup__in=classgroups,
                                                     slot__date=suspension.date,
                                                     slot__tt_slot__period=suspension.period)

            for lesson in affected_lessons:
                lesson.save()

    elif 'post_remove' in kwargs['action']:
        print('1')
        # find the classes affected by this:
        # todo: remove debug filter
        tgs = list(TeachingGroup.objects.filter(lessons=suspension.slot.tt_slot))
        # Find lessons affected by this suspension:
        tt_lessons = Lesson.objects.filter(slot__date__gte=suspension.date,
                                           teachinggroup__in=tgs)

        # Exclude any that are still suspended.
        tt_lessons = tt_lessons.exclude(teachinggroup__in=suspension.teachinggroups.all())
        # list(tt_lessons) # This shouldn't be required, but for some reason
        # either PyCharm or docker refuses to evaluate the qs without it.

        for lesson in tt_lessons:
            lesson.save()

    elif 'post_clear' in kwargs['action']:
        print('2')
        # find the classes affected by this:
        # todo: remove debug filter
        tgs = list(TeachingGroup.objects.filter(lessons=suspension.slot.tt_slot))
        # Find lessons affected by this suspension:
        tt_lessons = Lesson.objects.filter(slot__date__gte=suspension.date,
                                           teachinggroup__in=tgs)

        # Exclude any that are still suspended.
        tt_lessons = tt_lessons.exclude(teachinggroup=suspension.teachinggroups.all())
        list(tt_lessons)  # This shouldn't be required, but for some reason
        # either PyCharm or docker refuses to evaluate the qs without it.

        for lesson in tt_lessons:
            lesson.save()


m2m_changed.connect(class_suspended, sender=Suspension.teachinggroups.through)


class Lesson(models.Model):
    teachinggroup = models.ForeignKey(TeachingGroup, null=False, on_delete=models.CASCADE)
    title = models.CharField(max_length=256, blank=True, null=True)
    order = models.FloatField(null=False)
    description = models.TextField(null=True, blank=True)
    requirements = models.TextField(null=True, blank=True)
    slot = models.ForeignKey(CalendaredPeriod, blank=True, null=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = ['teachinggroup', 'order']
        ordering = ['order']

    def __set_slot(self, save=False, candidates=False):

        # Find lesson slots for this class
        tt_slots = TTSlot.objects.filter(teachinggroup=self.teachinggroup)

        # Include the candidates in the recursion to prevent mutliple db hits.
        if not candidates:
            # Get a list of all possible lesson slots
            candidates = list(CalendaredPeriod.objects.filter(tt_slot__in=tt_slots). \
                              exclude(suspension__teachinggroups=self.teachinggroup) \
                              .exclude(suspension__whole_school=True))
        # Place this lesson in the [order-th] slot
        try:
            self.slot = candidates[int(self.order)]
        except IndexError:
            # Todo: Add warning message that lessons go past last day of year.
            # Get last item:
            last_slot = CalendaredPeriod.objects.latest('order')
            year = AcademicYear.objects.get(current=True)
            week = Week.objects.latest('number')
            next_week, created = Week.objects.get_or_create(year=year,
                                                            number=week.number + 1)
            # Add an extra week
            for day in Day.objects.filter(year=year):
                for period in Period.objects.filter(year=year):
                    CalendaredPeriod.objects.get_or_create(year=year,
                                                           order=last_slot.order + 1,
                                                           week=next_week,
                                                           tt_slot=TTSlot.objects.get(year=year,
                                                                                      day=day,
                                                                                      period=period))

            # Try again with newly created days:
            candidates = list(CalendaredPeriod.objects.filter(tt_slot__in=tt_slots). \
                              exclude(suspension__teachinggroups=self.teachinggroup) \
                              .exclude(suspension__whole_school=True))
            self.slot = candidates[int(self.order)]
        # Check if this will now clash with another lesson:
        # NB this works because we've not saved yet, so the DB will return only
        # the saved compeitior lesson.
        competitor = list(Lesson.objects.exclude(pk=self.pk).filter(teachinggroup=self.teachinggroup,
                                                                    slot=self.slot))

        if competitor:
            # Recursion goes BRRRRRR
            competitor[0].__set_slot(save=True, candidates=candidates)

        if save:
            self.save(bypass_set_slot=True)

        else:
            return self.slot

    def save(self, bypass_set_slot=False, *args, **kwargs):
        if not bypass_set_slot:
            self.__set_slot(save=False)
        super(Lesson, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        super(Lesson, self).delete(*args, **kwargs)
        # Find the lessons that previously came after this:
        following = Lesson.objects.filter(teachinggroup=self.teachinggroup,
                                          order__gt=self.order)
        for lesson in following:
            lesson.order = lesson.order - 1
            lesson.save()  # will re-apply the ordering


def setup_lessons(teachinggrousp=TeachingGroup.objects.all()):
    current_year = AcademicYear.objects.get(current=True)
    for group in teachinggrousp:
        max_lessons = group.lessons.count() * current_year.total_weeks
        # If we have a group that has been taught over multiple years (.e.g AS to A2),
        # we need to start from the first lesson of last year.
        lessons = Lesson.objects.filter(teachinggroup=group).order_by('order')
        if lessons.count() > 0:
            lesson_number = lessons.last().order
        else:
            lesson_number = 0
        for lesson in range(max_lessons):
            lesson, created = Lesson.objects.get_or_create(teachinggroup=group,
                                                           order=lesson_number)
            lesson.save()  # Required to force a re-slot.
            lesson_number += 1


class GQuizExam(Exam):
    master_form_url = models.URLField(null=False,
                                      blank=False,
                                      validators=[validate_g_form],
                                      help_text="This must be the URL for the Google Form containing your questions")
    master_response_sheet_url = models.URLField(null=True,
                                                blank=False,
                                                validators=[validate_g_sheet],
                                                help_text="This must be the URL for the Google Sheet containing your responses")

    def import_questions(self):
        gc = gspread.service_account()
        ss = gc.open_by_url(self.master_response_sheet_url)
        qs = ss.worksheet("Questions").get_all_records()

        order = 1
        for row in qs:
            question, created = GQuizQuestion.objects.get_or_create(exam=self,
                                                                    order=order,
                                                                    google_id=row['ID'])
            question.text = row['Question Text']
            question.max_score = row['Max Score']
            question.number = row['Question Number']
            question.save()
            order += 1


    def save(self, *args, **kwargs):
        g_sheet_pattern = r'(^https://docs.google.com/spreadsheets/.*/edit?)'
        g_form_patern = r'(^https://docs.google.com/forms/.*)'

        self.master_response_sheet_url = re.search(g_sheet_pattern, self.master_response_sheet_url).group()
        self.master_form_url = re.search(g_form_patern, self.master_form_url).group()
        super(GQuizExam, self).save(*args, **kwargs)


class GQuizQuestion(Question):
    text = RichTextField(blank=True, null=True)
    google_id = models.IntegerField(blank=False, null=False)


class GQuizSittingQuerySet(models.QuerySet):
    def get_closest_to(self, target):
        closest_greater_qs = self.filter(date__gte=target).order_by('date')
        closest_less_qs = self.filter(date__lte=target).order_by('-date')

        try:
            try:
                closest_greater = closest_greater_qs[0]
            except IndexError:
                return closest_less_qs[0]

            try:
                closest_less = closest_less_qs[0]
            except IndexError:
                return closest_greater_qs[0]
        except IndexError:
            raise self.model.DoesNotExist("There is no closest object"
                                          " because there are no objects.")

        if closest_greater.date - target > target - closest_less.date:
            return closest_less
        else:
            return closest_greater


class GQuizSittingManager(models.Manager):
    def get_queryset(self):
        return GQuizSittingQuerySet(model=self.model)

    def get_closest_to(self, target):
        return self.get_queryset().get_closest_to(target)


class GQuizSitting(Sitting):
    scores_sheet_url = models.URLField(blank=False, null=True)
    scores_sheet_key = models.CharField(blank=False, null=True, max_length=1000,
                                        help_text="This is the ID field of the Google Sheet with your answers on it.")
    importing = models.BooleanField(default=False)
    self_assessment = models.BooleanField(default=False,
                                          help_text='Set to yes if this is a student self-assessment attempt')
    order = models.IntegerField(blank=True, null=True,
                                help_text='Used for multiple attempts at same self-assessment quiz')

    objects = GQuizSittingManager()

    def self_assessment_link(self):
        exam = GQuizExam.objects.get(pk=self.exam.pk)
        return "<a href='{url}' target='blank'>{name}</a>".format(url=str(exam.master_form_url), name=str(exam.name))

    def import_scores(self, email=False, timestamp=False):
        """ Use Google API to get the score data.
        If an email is supplied, only process the data for that student.
        """
        if self.importing:
            if not email:
                raise AlreadyImportingScoreError

        self.importing = True
        self.save()
        marks_entered = False

        gc = gspread.service_account()
        ss = gc.open_by_url(self.scores_sheet_url)
        qs = ss.worksheet("Scores").get_all_records()
        # Get the sitting:

        for row in qs:
            if email:
                time_string = str(row['Timestamp'])
                time_string = time_string.replace('T', ' ')
                time_string = re.match(r'(.*)\.', time_string).group()
                time_string = time_string[:-1]
                response_timestamp = datetime.datetime.strptime(time_string, "%Y-%m-%d %H:%M:%S")
                if email != row['Student Email Address']:
                    continue
                # elif timestamp != response_timestamp:
                #     continue
            # We have found at least one row to import
            marks_entered = True

            print(row)
            student = Student.objects.get(user__email=row['Student Email Address'])

            question = GQuizQuestion.objects.get(exam=self.exam,
                                                 google_id=row['ID'])
            try:
                # Check if there's a normal Mark object:
                mark = Mark.objects.get(question=question,
                                        sitting=self,
                                        student=student)
                mark.delete()
            except ObjectDoesNotExist:
                pass

            # Sanity check for max score in case of changed questions.
            if row['Maximum score'] > question.max_score:
                raise MarkScoreError

            mark, created = GQuizMark.objects.get_or_create(question=question,
                                                            sitting=self, student=student)
            mark.score = row['Student Score']
            mark.student_response = row['Student Answer']
            mark.teacher_response = row['Teacher Feedback']
            mark.student_notes = "You were asked: " + str(
                mark.question.gquizquestion.text) + ".<br>You answered: " + str(
                mark.student_response) + "<br><strong>Teacher response:</strong>: " + str(mark.teacher_response)
            mark.save()


        self.importing = False
        self.save()

        return marks_entered

class GQuizMark(Mark):
    student_response = RichTextField(blank=True, null=True)
    teacher_response = RichTextField(blank=True, null=True)


def student_mark_changed(sender, instance=GQuizMark.objects.none(), **kwargs):
    if instance.score is not None:
        instance.set_student_syllabus_assessment_records()


post_save.connect(student_mark_changed, sender=GQuizMark)


def generate_analsysios_df(marks=Mark.objects.none):
    """
    Takes a queryset of student marks and returns and Pandas dataframe
    sorted by student score and question average score.
    """
    df = read_frame(marks, fieldnames=['student', 'question', 'score', 'question__order', 'question__max_score'])
    df['percentage'] = df['score'] / df['question__max_score'] * 100
    scores = df[df.score > -1]
    sheet = pd.pivot_table(scores, values='percentage', index=['question', 'question__order'], columns='student')
    sheet = sheet.sort_values('question__order')
    rs = sheet.reset_index()
    rs = rs.drop(columns='question__order')
    df = rs.set_index('question')

    # add student average
    df.loc['Mean'] = df.mean()

    # Sort by attainment
    df = df.sort_values('Mean', axis=1, ascending=False)

    # Add question average
    df['Average'] = df.mean(axis=1)

    # Sort by question average
    df = df.sort_values('Average', ascending=False)

    #### Hacky! We have to remove and re-insert the mean because otherwise it will be in the wrong place
    df = df.drop('Mean')
    df.loc['Mean'] = df.mean()
    # clean up
    df = df.round()

    return df
