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
    students = models.ManyToManyField(Student) # Depreciated
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

DAYS = (
    ('Monday', 'Monday'),
    ('Tuesday', 'Tuesday'),
    ('Wednesday', 'Wednesday'),
    ('Thursday', 'Thursday'),
    ('Friday', 'Friday'),
)

PERIODS = (
    (1, 1),
    (2, 2),
    (3, 3),
    (4, 4),
)

RESOURCE_TYPES = (
    ('Presentation', 'Presentation'),
    ('Worksheet', 'Worksheet'),
    ('Test', 'Test'),
    ('Mark Scheme', 'Mark Scheme'),
    ('Web Page', 'Web Page'),
    ('Google Drive', 'Google Drive'),
)


def get_year_from_date(date):
    for n in range(len(CALENDAR_START_DATE)):
        if CALENDAR_START_DATE[n] <= date <= CALENDAR_END_DATE[n]:
            return n
    # we'll only reach this if no date matches; this occurs
    # in the gap between school years.
    return len(CALENDAR_START_DATE) - 1  # since lists start at 0 and len is an absolute number!


# def generate_week_grid(teacher, week_number):
#     start_date = get_monday_date_from_weekno(week_number)
#     next_week = week_number + 1
#     if week_number is not 0:
#         last_week = week_number - 1
#     else:
#         last_week = 0
#
#     current_date = start_date
#     weekgrid = []
#     for day in DAYS:
#
#         # Check if the day is suspended.
#         suspensions = LessonSuspension.objects.filter(date=current_date)
#         if suspensions.exists():
#             # There is at least one suspension on this day
#             if suspensions.filter(whole_school=True).exists():
#                 if suspensions.filter(all_day=True).exists():
#                     # Get the first suspension TODO: add constraints so there's only one
#                     suspension = suspensions.filter(all_day=True)[0]
#
#                     # fill the day row with the suspension objects
#                     weekgrid.append([day[0], suspension, suspension, suspension, suspension])
#                     current_date = current_date + datetime.timedelta(days=1)
#                     continue
#
#         dayrow = [day[0]]
#
#         for period in PERIODS:
#             # Check if that period is whole-school suspended:
#             check = suspensions.filter(period=period[0]).filter(whole_school=True)
#             if check.exists():
#                 dayrow.append(check[0])  # See above: May like to change to a get.
#                 current_date = current_date + datetime.timedelta(days=1)
#                 continue
#
#             try:
#                 timetabled_lesson = TimetabledLesson.objects.get(lesson_slot__day=day[0],
#                                                                  classgroup__groupteacher=teacher,
#                                                                  lesson_slot__period=period[0])
#             except TimetabledLesson.DoesNotExist:
#                 dayrow.append("Free")
#                 timetabled_lesson = "Free"
#
#             if timetabled_lesson != "Free":
#                 check = suspensions.filter(period=period[0], classgroups=timetabled_lesson.classgroup)
#                 if check.exists():
#                     dayrow.append(check)
#                     continue
#
#                 else:
#                     lesson, created = Lesson.objects.get_or_create(lessonslot=timetabled_lesson, date=current_date)
#                     dayrow.append(lesson)
#
#         weekgrid.append(dayrow)
#         current_date = current_date + datetime.timedelta(days=1)
#
#     return weekgrid


def check_suspension(date, period, classgroup):
    # Check if the whole school is suspended that day:
    day_suspensions = LessonSuspension.objects.filter(date=date)
    suspensions = day_suspensions.filter(whole_school=True, all_day=True).count()
    if suspensions:
        return True

    # Check if whole school is suspended that period
    suspensions = day_suspensions.filter(period=period, whole_school=True).count()
    if suspensions:
        return True

    # check if classgroup is suspended all day
    suspensions = day_suspensions.filter(all_day=True, classgroups=classgroup).count()
    if suspensions:
        return True

    # Check if classgroup is suspended for that period.
    suspensions = day_suspensions.filter(period=period, classgroups=classgroup).count()
    if suspensions:
        return True

    return False


class LessonSlot(models.Model):
    day = models.CharField(max_length=10, choices=DAYS, blank=False, null=False)
    period = models.IntegerField(choices=PERIODS, blank=False, null=False)
    year = models.IntegerField(blank=False, null=False, choices=ACADEMIC_YEARS.items())

    class Meta:
        unique_together = ['day', 'period', 'year']

    def __str__(self):
        return self.day + " P" + str(self.period) + " " + str(self.year)

    def dow(self):
        """Return the day of the week"""
        if self.day == "Monday":
            return 0
        if self.day == "Tuesday":
            return 1
        if self.day == "Wednesday":
            return 2
        if self.day == "Thursday":
            return 3
        if self.day == "Friday":
            return 4

    def teachers_lesson(self, teacher):
        """Return the TimetabledLesson assosciated with a teacher"""
        lesson = TimetabledLesson.objects.get(lesson_slot=self, teachinggroup__teachers=teacher)


class TimetabledLesson(models.Model):
    teachinggroup = models.ForeignKey(TeachingGroup, on_delete=models.CASCADE, blank=True, null=True)
    lesson_slot = models.ForeignKey(LessonSlot, on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        unique_together = ['teachinggroup', 'lesson_slot']

    def __str__(self):
        return str(self.teachinggroup) + " " + str(self.lesson_slot)

    def dow(self):
        return self.lesson_slot.day

    def total_lessons(self):
        lessons = int(TimetabledLesson.objects.filter(classgroup=self.teachinggroup).count())
        return lessons

    def order(self):
        all_instances = TimetabledLesson.objects.filter(classgroup=self.teachinggroup)
        return list(all_instances).index(self) + 1


class Lesson(models.Model):
    lessonslot = models.ForeignKey(TimetabledLesson, on_delete=models.CASCADE)
    teachinggroup = models.ForeignKey(TeachingGroup, null=True, blank=False, on_delete=models.SET_NULL)
    status = models.CharField(max_length=20, null=True, blank=True)
    lesson_title = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    requirements = models.TextField(null=True, blank=True)
    homework = models.TextField(null=True, blank=True)
    homework_due = models.DateField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    sequence = models.IntegerField(null=False, blank=True)
    date = models.DateField(null=True, blank=True)
    syllabus_points = TreeManyToManyField(Syllabus, blank=True)

    class Meta:
        unique_together = (("lessonslot", "date"),
                           ("teachinggroup", "sequence"))

    def __str__(self):
        if self.lesson_title:
            return str(self.teachinggroup) + " " + str(self.sequence) + ": " + str(self.lesson_title)

        else:
            return str(self.teachinggroup) + "lesson:  " + str(self.sequence) + " " + str(self.date)

    def resources(self):

        return LessonResources.objects.filter(lesson=self)

    def student_viewable_resources(self):
        # Get the resources set to be viewable at any time
        all_resources = []
        resources = LessonResources.objects.filter(lesson=self, students_can_view_before=True)
        print(all_resources)
        for resource in resources:
            all_resources.append(resource)

        # If it's been taught, get the 'after' resources:

        if self.date < datetime.date.today():
            resources = LessonResources.objects.filter(lesson=self, students_can_view_after=True).exclude(
                students_can_view_before=True)
            for resource in resources:
                all_resources.append(resource)

        return all_resources

    def set_date(self, year):

        """ A slightly complicated method, which must set the date for the current lesson.

        We need to create every lesson for the year.
         1. Set a start date + period
         2. Check if a lesson is suspended
         3. If not suspended, get_or_create the lesson, and set it to the date and period
         4. Move to next eligible lesson and repeat.

         """

        all_lessons = Lesson.objects.filter(lessonslot__teachinggroup=self.lessonslot.teachinggroup).order_by('sequence')

        # Lesson slots where these appear.
        slots = TimetabledLesson.objects.filter(teachinggroup=self.lessonslot.teachinggroup)

        # Find total lessons per week
        lessons_per_week = int(TimetabledLesson.objects.filter(teachinggroup=self.lessonslot.teachinggroup).count())

        # we'll use *week* to track each week we're looking at.

        global week, lesson_of_week, slot_number, current_lesson
        week = 0
        lesson_of_week = 0
        slot_number = 0
        current_lesson = 0
        # Set our starting lesson date:

        dow = slots[0].lesson_slot.dow()
        date = CALENDAR_START_DATE[year] + datetime.timedelta(days=dow)

        days_taught = []
        for slot in slots:
            days_taught.append(slot.lesson_slot.dow())

        def next_lesson(week, lesson_of_week, slot_number):
            if lesson_of_week == (lessons_per_week - 1):  # We just did the last lesson of the week
                week = week + 1
                lesson_of_week = 0

            else:
                lesson_of_week = lesson_of_week + 1

            if slot_number != lessons_per_week - 1:
                slot_number = slot_number + 1

            else:
                slot_number = 0

            date = CALENDAR_START_DATE + datetime.timedelta(days=days_taught[slot_number], weeks=week)

            return week, lesson_of_week, slot_number, date

        while date < CALENDAR_END_DATE[year]:

            # Iteratete this over the slots:

            for slot in slots:
                if check_suspension(date, slot.lesson_slot.period, slot.teachinggroup):
                    # lesson has been suspended
                    week, lesson_of_week, slot_number, date = next_lesson(week, lesson_of_week, slot_number)
                    continue

                else:  # lesson is not suspended
                    lesson, created = Lesson.objects.get_or_create(date=date, lessonslot=slots[slot_number],
                                                                   teachinggroup=slots[slot_number].teachinggroup)
                    # lesson.sequence = current_lesson
                    # current_lesson = current_lesson + 1
                    week, lesson_of_week, slot_number, date = next_lesson(week, lesson_of_week, slot_number)
                    lesson.save

    # def save(self, *args, **kwargs):
    #
    #     super(Lesson, self).save(*args, **kwargs)
    #
    #     return self

    def lesson_resource_icons(self):
        icons = []
        resources = LessonResources.objects.filter(lesson=self)

        for resource in resources:
            icons.append(resource.icon)

        return icons

    def delete(self, *args, **kwargs):
        # We've removed a lesson, so we need to decerement all the following lessons
        following_lessons = Lesson.objects.filter(teachinggroup=self.teachinggroup, sequence__gt=self.sequence).order_by(
            'sequence')
        # Avoid integrity error:
        # Find max sequence
        max = following_lessons.aggregate(Max('sequence'))

        if max['sequence__max'] is not None:
            self.sequence = max['sequence__max'] + 10
            self.save()
            for lesson in following_lessons:
                lesson.sequence = lesson.sequence - 1
                lesson.save()
        super().delete(*args, **kwargs)

    def homework_due_lessons(self):
        lessons_w_homework_due = Lesson.objects.filter(homework_due=self.date, teachinggroup=self.teachinggroup)
        if lessons_w_homework_due.count():
            return lessons_w_homework_due

        else:
            return False

    def next_in_order(self):
        return Lesson.objects.get(teachinggroup=self.teachinggroup,
                                  sequence=self.sequence + 1)


class LessonResources(models.Model):
    lesson = models.ForeignKey(Lesson, blank=True, null=True, on_delete=models.SET_NULL)
    resource_type = models.CharField(max_length=100, choices=RESOURCE_TYPES, null=True, blank=False)
    resource_name = models.CharField(max_length=100, null=True, blank=False)
    link = models.URLField(blank=False, null=True)
    students_can_view_before = models.BooleanField(default=False)
    students_can_view_after = models.BooleanField(default=False)
    available_to_all_classgroups = models.BooleanField(default=False)
    syllabus_points = TreeManyToManyField(Syllabus)

    def __str__(self):
        return self.resource_name

    def editable_icon(self):
        """Link to the form to edit a resource """
        string = "<a href=" + str(reverse('timetable:edit_lesson_resource', args=[self.lesson.pk, self.pk]))
        string = string + ' target="_blank" data-toggle="tooltip" data-placement="top" title="'
        string = string + (str(self.resource_name))
        string = string + '">'

        if self.resource_type == "Presentation":
            string = string + "<i class='fas fa-desktop'>"

        elif self.resource_type == "Web Page":
            string = string + "<i class='fas fa-tablet-alt'>"

        elif self.resource_type == "Worksheet":
            string = string + '<i class="fas fa-newspaper">'

        elif self.resource_type == "Test":
            string = string + "<i class='fas fa-pencil-ruler'>"

        elif self.resource_type == "Google Drive":
            string = string + '<i class="fab fa-google-drive">'

        else:
            string = string + '<i class="fas fa-question-circle">'

        string = string + "</i></a>"

        return string


    def icon(self):
        """ Icon link to the resource itself"""

        string = "<a href=" + str(self.link)
        string = string + ' target="_blank" rel="noopener" data-toggle="tooltip" data-placement="top" title="'
        string = string + (str(self.resource_name))
        string = string + '">'

        if self.resource_type == "Presentation":
            string = string + "<i class='fas fa-desktop'>"

        elif self.resource_type == "Web Page":
            string = string + "<i class='fas fa-tablet-alt'>"

        elif self.resource_type == "Worksheet":
            string = string + '<i class="fas fa-newspaper">'

        elif self.resource_type == "Test":
            string = string + "<i class='fas fa-pencil-ruler'></i>"

        elif self.resource_type == "Google Drive":
            string = string + '<i class="fab fa-google-drive">'

        else:
            string = string + '<i class="fas fa-question-circle">'

        string = string + "</i></a>"

        return string

    def student_viewable(self):
        """ Return True if students should be able to see this resource """
        if self.students_can_view_before:
            return True

        elif self.students_can_view_after:
            if self.lesson.date >= datetime.date.today():
                return True

        else:
            return False

    def set_syllabus_points(self):
        if self.lesson:
            points = self.lesson.syllabus_points.all().order_by('pk')
            for point in points:
                self.syllabus_points.add(point)


class LessonSuspension(models.Model):
    """Store suspensions and missing lessons"""
    whole_school = models.BooleanField(default=True)
    date = models.DateField(blank=False, null=False)
    reason = models.CharField(max_length=200, blank=False, null=True)
    teachinggroups = models.ManyToManyField(TeachingGroup, blank=True)
    all_day = models.BooleanField(default=False)
    period = models.IntegerField(choices=PERIODS, blank=True, null=True)

    def save(self, *args, **kwargs):
        """When we save, we need to update the dates of all affected lessons. """
        super(LessonSuspension, self).save(*args, **kwargs)

        affected_lessons = Lesson.objects.filter(date=self.date)
        for lesson in affected_lessons:
            teachinggroup = lesson.teachinggroup
            year = get_year_from_date(self.date)
            set_classgroups_lesson_dates(teachinggroup)

        return self

    def __str__(self):
        return str(self.date) + " " + self.reason


def check_suspension(date, period, teachinggroup):
    # Check if the whole school is suspended that day:
    day_suspensions = LessonSuspension.objects.filter(date=date)
    suspensions = day_suspensions.filter(whole_school=True, all_day=True).count()
    if suspensions:
        return True

    suspensions = day_suspensions.filter(period=period, whole_school=True).count()
    if suspensions:
        return True

    suspensions = day_suspensions.filter(all_day=True, teachinggroups=teachinggroup).count()
    if suspensions:
        return True

    suspensions = day_suspensions.filter(period=period, teachinggroups=teachinggroup).count()
    if suspensions:
        return True

    return False


def set_classgroups_lesson_dates(classgroup):
    # slots must be ordered for it to work - weirdly this doesn't happen on local!
    slots = TimetabledLesson.objects.filter(teachingggroup=classgroup).order_by('lesson_slot')
    year = classgroup.year_taught

    total_slots = slots.count() - 1  # index 0

    current_week = 0
    current_slot = 0
    current_lesson = 0

    message = False  # Used to return a warning message if lessons overshoot end date

    def next_lesson(current_slot, current_week, reset=False):
        if current_slot == total_slots:
            # Occurs if the last slot we filled was the last of the weeek
            current_slot = 0
            current_week = current_week + 1

        else:
            current_slot = current_slot + 1

        if reset:
            current_slot = 0
            current_week = 0

        return current_slot, current_week

    date = CALENDAR_START_DATE[year]
    # We start at the beginning of the school year
    current_week, current_slot = next_lesson(current_week, current_slot, True)

    while date < CALENDAR_END_DATE[year]:
        # We need to check if the lesson exists:

        try:
            lesson = Lesson.objects.get(sequence=current_lesson, classgroup=classgroup)
        except models.ObjectDoesNotExist:
            lesson = Lesson.objects.create(sequence=current_lesson, classgroup=classgroup,
                                           lessonslot=slots[current_slot])

        date = CALENDAR_START_DATE[year] + datetime.timedelta(weeks=current_week,
                                                              days=slots[current_slot].lesson_slot.dow())

        period = slots[current_slot].lesson_slot.period

        while True:
            # We need to keep trying with this period until we place it
            if check_suspension(date, period, classgroup):
                # lesson is suspended, so skip
                current_slot, current_week = next_lesson(current_slot, current_week)
                date = CALENDAR_START_DATE[year] + datetime.timedelta(weeks=current_week,
                                                                      days=slots[current_slot].lesson_slot.dow())
                continue  # Go back to the start and try again
            else:

                lesson.lessonslot = slots[current_slot]
                lesson.date = date
                current_slot, current_week = next_lesson(current_slot, current_week)

                # Check if a lesson already exists that meets all these criteria:

                try:
                    with transaction.atomic():  # Needed to prevent an error as per https://stackoverflow.com/questions/32205220/cant-execute-queries-until-end-of-atomic-block-in-my-data-migration-on-django-1?rq=1

                        lesson.save()  # Will fail if a lesson already has same date and slot

                except IntegrityError:
                    # All lessons above <current_sequence> must be incremented
                    clashing_lessons = Lesson.objects.filter(sequence__gte=current_lesson,
                                                             classgroup=classgroup).order_by('sequence').reverse()
                    # Must be in reverse order so we don't cause further integrity errors
                    # Note that we don't need to worry about setting correct slots here, as they are about to be re-set
                    for clashing_lesson in clashing_lessons:

                        # clashing_lesson.sequence = clashing_lesson.sequence + 1
                        # This date thing is a horrid hack, but we're about to set a correct date,
                        # and we need to make sure we don't cause further integrity errors

                        # temp bugxix:
                        if clashing_lesson.date:
                            clashing_lesson.date = clashing_lesson.date + datetime.timedelta(weeks=1000)
                        else:
                            clashing_lesson.date = CALENDAR_START_DATE[year] + datetime.timedelta(weeks=1000)
                        clashing_lesson.save()
                    lesson.save()  # Finally save our original lesson

                break  # End loop and get next lesson

        current_lesson = current_lesson + 1

    # re-set our values back to zero for next iteration (why???)

    next_lesson(current_week, current_slot, True)

    # clean up any lessons beyond end date
    overshot_lessons = Lesson.objects.filter(date__gte=CALENDAR_END_DATE[year], classgroup=lesson.classgroup)

    # Delete only unwritten lessons
    overshot_lessons.filter(lesson_title__isnull=True).delete()

    # Check if any are left - this means that some had titles
    if Lesson.objects.filter(date__gte=CALENDAR_END_DATE[year], classgroup=lesson.classgroup).count():
        message = "Warning! Your scheduled lessons extend beyond the last day of term."

    return message
