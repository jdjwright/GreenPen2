from django.db import models
from django.utils import timezone
from django.db.models import Q, Sum, Avg, QuerySet
from django.db.models.signals import m2m_changed, post_save
from django.contrib.auth.models import User
from mptt.models import MPTTModel, TreeForeignKey, TreeManyToManyField
from mptt.querysets import TreeQuerySet
import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.urls import reverse
from GreenPen.settings import CALENDAR_START_DATE, CALENDAR_END_DATE, ACADEMIC_YEARS
from django.db.models import Max


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
        return str(self.title) + " " + str(self.full_name()) + " (" + str(self.staff_code) + ")"


class Subject(models.Model):
    name = models.CharField(max_length=200, blank=False, null=False, unique=True)
    HoDs = models.ManyToManyField(Teacher)

    def __str__(self):
        return self.name


class TeachingGroup(models.Model):
    name = models.CharField(max_length=256, blank=True, null=True)
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, blank=True, null=True)
    teachers = models.ManyToManyField(Teacher)
    students = models.ManyToManyField(Student)
    syllabus = TreeForeignKey('Syllabus', blank=True, null=True, on_delete=models.SET_NULL)
    archived = models.BooleanField(blank=True, null=True, default=False)
    year_taught = models.IntegerField(null=True, blank=True)
    rollover_name = models.CharField(max_length=256, blank=True, null=True)
    lessons = models.ManyToManyField('TTSlot')

    def __str__(self):
        return self.name

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

    def cohort_stats(self, students=Student.objects.none()):
        records = StudentSyllabusAssessmentRecord.objects.filter(student__in=students,
                                                                 syllabus_point=self,
                                                                 most_recent=True)
        data = records.aggregate(percentage=Avg('percentage'),
                                 rating=Avg('rating'),
                                 children_0_1=Sum('children_0_1'),
                                 children_1_2=Sum('children_1_2'),
                                 children_2_3=Sum('children_2_3'),
                                 children_3_4=Sum('children_3_4'),
                                 children_4_5=Sum('children_4_5'))
        return data


class Exam(models.Model):
    name = models.CharField(max_length=256, blank=False, null=False)
    syllabus = TreeForeignKey('Syllabus', blank=True, null=True, on_delete=models.SET_NULL)
    weighting = models.FloatField(blank=False, null=False, default=1)

    def total_score(self):
        return Question.objects.filter(exam=self).aggregate(Sum('max_score'))['max_score__sum']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('edit-exam', args=[str(self.id)])


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


def new_question_created(sender, instance, **kwargs):
    for sitting in Sitting.objects.filter(exam__question=instance):
        sync_marks_with_sittings(sitting)


post_save.connect(new_question_created, sender=Question)


class Sitting(models.Model):
    exam = models.ForeignKey(Exam, blank=False, null=False, on_delete=models.CASCADE)
    date = models.DateField(blank=False, null=False, default=datetime.date.today)
    students = models.ManyToManyField(Student)  # Depreciated
    resets_ratings = models.BooleanField(blank=True, null=True, default=False)
    group = models.ForeignKey(TeachingGroup, blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return str(self.exam) + " " + str(self.date) + "(" + str(self.pk) + ")"

    def avg_percent(self):
        student_marks = Mark.objects.filter(sitting=self,
                                            score__isnull=False)
        if student_marks.count():
            data = student_marks.aggregate(scored=Sum('score'), total=Sum('question__max_score'))
            return int(data['scored'] / data['total'] * 100)
        else:
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

    def avg_syllabus_rating(self, syllabus=Syllabus.objects.none()):
        """
        Calculate the average rating for the cohort taking this exam.
        Optionally, restrict it to just a single syllabus point.
        """
        ratings = StudentSyllabusAssessmentRecord.objects.filter(sitting=self,
                                                                 syllabus_point=syllabus,
                                                                 rating__isnull=False)
        if ratings.count():
            return round(ratings.aggregate(avg=Avg('rating'))['avg'], 1)
        else:
            return 'none'

    def student_total(self, student=Student.objects.none()):
        marks = Mark.objects.filter(sitting=self,
                                    student=student)
        return marks.aggregate(total=Sum('score'))['total']


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
                other.save()
                competitor.save()
        most_recent_competitor = competitors[0]
        if instance.pk == most_recent_competitor.pk:  # Don't use just == as might have changed flags
            newer_reset_reqd = False
        else:
            newer_reset_reqd = True
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

    record.attempted_plus_children = data['question__max_score__sum'] + float(
        children_data['attempted_this_level__sum'] or 0)
    record.correct_plus_children = data['score__sum'] + float(children_data['correct_this_level__sum'] or 0)

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


def student_mark_changed(sender, instance=Mark.objects.none(), **kwargs):
    if instance.score is not None:
        instance.set_student_syllabus_assessment_records()


post_save.connect(student_mark_changed, sender=Mark)


class CSVDoc(models.Model):
    description = models.CharField(max_length=255, blank=True)
    document = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)


## Models for calendaring

class AcademicYear(models.Model):
    name = models.CharField(max_length=30)
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

    class Meta:
        ordering = ['order']

    @property
    def date(self):
        start_date = self.year.first_monday
        return start_date + datetime.timedelta(weeks=self.week.number,
                                               days=self.tt_slot.day.order)

    @property
    def day(self):
        return self.tt_slot.day.name

    @property
    def period(self):
        return self.tt_slot.period.name

    def __str__(self):
        return str(self.date) + " P" + self.tt_slot.period.name


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
                                                   week=week)
            i +=1


class Lesson(models.Model):
    teachinggroup = models.ForeignKey(TeachingGroup, null=False, on_delete=models.CASCADE)
    title = models.CharField(max_length=256, blank=True, null=True)
    order = models.FloatField(null=False)
    description = models.TextField(null=True, blank=True)
    requirements = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ['teachinggroup', 'order']