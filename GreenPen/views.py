from django.views.generic.list import ListView, View
import os
import threading

import gspread
from django.contrib import messages
from django.contrib.auth.decorators import login_required
# For authenticating views
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.forms import inlineformset_factory
from django.forms import modelformset_factory
from django.http import JsonResponse, HttpResponseForbidden, Http404, HttpResponseRedirect, HttpResponse, \
    HttpResponseBadRequest
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.edit import CreateView
from django.views.generic.edit import UpdateView
from django.views.generic.list import ListView, View

from GreenPen.functions.imports import *
from .decorators import teacher_or_own_only
from .forms import *
from .settings import CURRENT_ACADEMIC_YEAR


def check_teacher(user):
    if user.is_superuser:
        return True
    elif user.groups.filter(name='Teachers').count():
        return True

    else:
        return False


def check_superuser(user=User.objects.all()):
    return user.is_superuser


class TeacherOnlyMixin(UserPassesTestMixin):

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        return self.request.user.groups.filter(name='Teachers').count()


class SuperUserOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        if self.request.user.is_superuser:
            return True
        else:
            return False

class StudentList(TeacherOnlyMixin, ListView):
    model = Student


def splash(request):
    if not request.user.is_authenticated:
        return render(request, 'GreenPen/splash.html')

    if request.user.groups.filter(name='Teachers').count():
        return redirect(reverse('bs-sample'))

    elif request.user.groups.filter(name='Students').count():
        student = Student.objects.get(user=request.user)
        return redirect(reverse('student-dashboard'))


@user_passes_test(check_superuser)
def import_students(request):
    # Deal with getting a CSV file

    if request.method == 'POST':
        csvform = CSVDocForm(request.POST, request.FILES)
        if csvform.is_valid():
            file = csvform.save()
            path = file.document.path
            import_students_from_csv(path)
            os.remove(path)
            file.delete()
            return redirect('/')
    else:
        csvform = CSVDocForm()
    return render(request, 'GreenPen/csv_upload.html', {'csvform': csvform})


@user_passes_test(check_superuser)
def import_classes(request):
    # Deal with getting a CSV file

    if request.method == 'POST':
        csvform = CSVDocForm(request.POST, request.FILES)
        if csvform.is_valid():
            file = csvform.save()
            path = file.document.path
            import_classgroups_from_csv(path)
            os.remove(path)
            file.delete()
            return redirect('/')
    else:
        csvform = CSVDocForm()
    return render(request, 'GreenPen/csv_upload.html', {'csvform': csvform})


@user_passes_test(check_superuser)
def import_syllabus(request):
    # Deal with getting a CSV file

    if request.method == 'POST':
        csvform = CSVDocForm(request.POST, request.FILES)
        if csvform.is_valid():
            file = csvform.save()
            path = file.document.path
            import_syllabus_from_csv_new(path)
            os.remove(path)
            file.delete()
            return redirect('/')
    else:
        csvform = CSVDocForm()
    return render(request, 'GreenPen/csv_upload.html', {'csvform': csvform,
                                                        'title': 'Upload Syllabus'})


@user_passes_test(check_superuser)
def import_questions(request):
    # Deal with getting a CSV file

    if request.method == 'POST':
        csvform = CSVDocForm(request.POST, request.FILES)
        if csvform.is_valid():
            file = csvform.save()
            path = file.document.path
            import_questions_from_csv(path)
            os.remove(path)
            file.delete()
            return redirect('/')
    else:
        csvform = CSVDocForm()
    return render(request, 'GreenPen/csv_upload.html', {'csvform': csvform,
                                                        'title': 'Upload Questions'})


@user_passes_test(check_superuser)
def import_sittings(request):
    # Deal with getting a CSV file

    if request.method == 'POST':
        csvform = CSVDocForm(request.POST, request.FILES)
        if csvform.is_valid():
            file = csvform.save()
            path = file.document.path
            import_sittings_from_csv(path)
            os.remove(path)
            file.delete()
            return redirect('/')
    else:
        csvform = CSVDocForm()
    return render(request, 'GreenPen/csv_upload.html', {'csvform': csvform,
                                                        'title': 'Upload Sittings'})


@user_passes_test(check_superuser)
def import_marks(request):
    # Deal with getting a CSV file

    if request.method == 'POST':
        csvform = CSVDocForm(request.POST, request.FILES)
        if csvform.is_valid():
            file = csvform.save()
            path = file.document.path
            import_marks_from_csv(path)
            os.remove(path)
            file.delete()
            return redirect('/')
    else:
        csvform = CSVDocForm()
    return render(request, 'GreenPen/csv_upload.html', {'csvform': csvform,
                                                        'title': 'Upload Marks'})


@user_passes_test(check_superuser)
def update_classes(request):
    # Deal with getting a CSV file

    if request.method == 'POST':
        csvform = CSVDocForm(request.POST, request.FILES)
        if csvform.is_valid():
            file = csvform.save()
            path = file.document.path
            update_groups(path)
            os.remove(path)
            file.delete()
            return redirect('/')
    else:
        csvform = CSVDocForm()
    return render(request, 'GreenPen/csv_upload.html', {'csvform': csvform,
                                                        'title': 'Upload Marks'})


@user_passes_test(check_superuser)
def update_assignments(request):
    # Deal with getting a CSV file

    if request.method == 'POST':
        csvform = CSVDocForm(request.POST, request.FILES)
        if csvform.is_valid():
            file = csvform.save()
            path = file.document.path
            update_group_assignments(path)
            os.remove(path)
            file.delete()
            return redirect('/')
    else:
        csvform = CSVDocForm()
    return render(request, 'GreenPen/csv_upload.html', {'csvform': csvform,
                                                        'title': 'Upload Marks'})


class StudentAssessmentForPoint(TeacherOnlyMixin, ListView):
    template_name = 'GreenPen/studnet_assessment_list.html'

    def get_queryset(self):
        syllabus = get_object_or_404(Syllabus, pk=self.kwargs['syllabus_pk'])
        student = get_object_or_404(Student, pk=self.kwargs['student_pk'])
        return StudentSyllabusAssessmentRecord.objects.filter(student=student,
                                                              syllabus_point=syllabus)


class ClassAssessmentForPoint(TeacherOnlyMixin, ListView):
    template_name = 'GreenPen/class_assessment_list.html'

    def get_queryset(self):
        syllabus = get_object_or_404(Syllabus, pk=self.kwargs['syllabus_pk'])
        group = get_object_or_404(TeachingGroup, pk=self.kwargs['group_pk'])
        return StudentSyllabusAssessmentRecord.objects.filter(student__in=group.students.all(),
                                                              syllabus_point=syllabus).order_by(
            'sitting__date'
        )


class EditExamQsView(TeacherOnlyMixin, View):
    template_name = 'GreenPen/exam_details.html'

    form = inlineformset_factory(Exam, Question,
                                 form=SetQuestions,
                                 extra=1,
                                 can_order=True,
                                 can_delete=True,
                                 )

    parent_form = SyllabusChoiceForm()
    parent_form.fields['points'].widget.set_url('/syllabus/json/')

    def get_exam_instance(self):
        try:
            exam = GQuizExam.objects.get(pk=self.kwargs['exam'])
        except ObjectDoesNotExist:
            try: exam = Exam.objects.get(pk=self.kwargs['exam'])

            except ObjectDoesNotExist:
                raise Http404("No exams matching that URL found")

        return exam


    def get_form_type(self, exam, post=False):
        """
        There are two different types of exam-form: one for paper-based exams
        (models.Exam), and one for Google Form auto-marked exams
        (model.GQuizExam).
        This function returns the correct form for editing each type.
        """

        if GQuizExam.objects.filter(pk=exam.pk).count():
            # This means our exam is also a GQuizExam instance
            if post:
                return AddGoogleExamForm(post, instance=exam)
            else:
                return AddGoogleExamForm(instance=exam)

        else:
            if post:
                return AddExamForm(post, instance=exam)
            else:
                return AddExamForm(instance=exam)

    def get(self, request, *args, **kwargs):

        exam = self.get_exam_instance()
        exam_form = self.get_form_type(exam)
        # Add an extra blank if we have no questions added:
        if Question.objects.filter(exam=exam).count():
            extra = 0
        else:
            extra = 1
        formset_factory = inlineformset_factory(Exam, Question,
                                                form=SetQuestions,
                                                extra=extra,
                                                can_order=True,
                                                can_delete=True,
                                                )
        form = formset_factory(instance=exam)

        # Set syllabus tree widget URL
        exam_form.fields['syllabus'].widget.set_url(reverse('load_syllabus_points_exam', args=[exam.pk]))
        return render(request, self.template_name, {'form': form,
                                                    'exam_form': exam_form})

    def post(self, request, *args, **kwargs):

        def sort_order_func(subform):
            return subform.cleaned_data['ORDER']


        exam = self.get_exam_instance()
        form = self.form(request.POST, instance=exam)

        exam_form = self.get_form_type(exam, post=request.POST)
        if exam_form.is_valid():
            if form.is_valid():
                # Sort the forms by order:
                form.forms.sort(key=sort_order_func)
                order = 1
                for subform in form.forms:
                    # Possible hack:
                    # If we have deleted a dynamically-created form, we will
                    # now need to skip it, otherwise we get an index error.
                    if not len(subform.cleaned_data):
                        continue

                    if subform.cleaned_data['DELETE']:
                        try:
                            subform.cleaned_data['id'].delete()
                            continue
                        except (ObjectDoesNotExist, AttributeError):
                            # Occurs if we are deleting a non-saved deleted form; skip
                            continue

                    question = subform.save(commit=False)
                    question.order = order
                    order += 1
                    question.save()
                    subform.save_m2m()
                    # Don't forget that m2m relations aren't automatically saved!

                exam_form.save()

                # Now we need to update sittings if the exam type is self-assessed.

                if isinstance(exam, GQuizExam):
                    if exam.type.eligible_for_self_assessment:
                        # Find all sittings and change their URL
                        sittings = GQuizSitting.objects.filter(exam=exam)
                        sittings.update(scores_sheet_url=exam_form.cleaned_data['master_response_sheet_url'])

                        # Create or edit a resource for it:
                        try:
                            resource, created = Resource.objects.get_or_create(exam=exam,
                                                                  name=exam.name,
                                                                  defaults={
                                                                      'created_by': request.user,
                                                                      'url': exam.master_form_url,
                                                                      'type': ResourceType.objects.get_or_create(name='Self-paced Quiz')[0],
                                                                  })
                            if created:
                                resource.syllabus.set(Syllabus.objects.filter(question__exam=exam))

                            success_message = "Exam saved succeffully. A new resource has been automatically created for it <a href='{link}'>here</a>".format(link=reverse('edit-resource', args=[resource.pk]))

                        except MultipleObjectsReturned:
                            success_message = "Your exam has been saved successfully, however there are multiple self-assessment resource with the same exam and name linked, so we couldn't create the resource automatically. Please create a new resource <a href={link}>here</a>.".format(reverse('add_resource'))
                    else:
                        success_message = "Exam saved succeffully. <a href='" + reverse('new-sitting', args=(
                            exam.pk,)) + "'>Click here to create a sitting for it</a>."


                messages.success(request, success_message)

                return redirect('edit-exam', exam.pk)
            else:
                form.forms.sort(key=sort_order_func)

        # Some eror occured.
        # We need to sort the form so that it's in the correct order,
        # otherwise newly-added questions will always be at the bottom.
        # Key function to provide sort value


        messages.warning(request, "One or more errors occured, please check below.")
        return render(request, self.template_name, {'form': form,
                                                    'exam_form': exam_form})


class ExamListView(TeacherOnlyMixin, ListView):
    queryset = Exam.objects.none()

    def get_queryset(self):
        if self.request.user.groups.filter(name='Teachers'):
            self.template_name = 'GreenPen/exam_list_teacher.html'
            return Exam.objects.all()

        elif self.request.user.groups.filter(name='Students'):
            self.template_name = 'GreenPen/exam_list.html'
            return Exam.objects.filter(sitting__students__user=self.request.user)

        else:
            raise PermissionDenied


def duplicate_exam(request, exam):
    exam = get_object_or_404(Exam, pk=exam)
    new_exam = exam.duplicate()
    new_exam.name = "Copy of " + new_exam.name
    new_exam.save()
    messages.success(request, new_exam.name + " created.")
    return redirect('edit-exam', new_exam.pk)


class AddExam(TeacherOnlyMixin, CreateView):
    template_name = 'GreenPen/add-exam.html'
    form_class = AddExamForm
    model = Exam

    # Need to make form name consistent for template:
    def get_context_data(self, **kwargs):
        context = super(AddExam, self).get_context_data(**kwargs)
        context["exam_form"] = context["form"]
        return context


class AddGoogleExam(TeacherOnlyMixin, CreateView):
    template_name = 'GreenPen/add-google-exam.html'
    form_class = AddGoogleExamForm
    model = GQuizExam

    # Need to make form name consistent for template:
    def get_context_data(self, **kwargs):
        context = super(AddGoogleExam, self).get_context_data(**kwargs)
        context["exam_form"] = context["form"]
        return context

    @transaction.atomic
    def form_valid(self, form):
        if not test_gc_sheets_questions(form.cleaned_data['master_response_sheet_url'], self.request):
            return self.get(self, form=form)
        self.object = form.save()
        self.object.import_questions()

        messages.success(self.request, "Exam created and questions imported. <strong>Important: </strong>Remember that questions worth 0 marks (e.g. student names) have still been imported - check carefully before assigning syllabus points!")
        return HttpResponseRedirect(self.get_success_url())


def test_gq_sheets_url(url, request):
    gc = gspread.service_account()
    try:
        ss = gc.open_by_url(url)
    except (gspread.exceptions.NoValidUrlKeyFound, gspread.exceptions.SpreadsheetNotFound):
        messages.error(request, "Google Sheets URL not valid; did you use the Forms URL instead?")
        return False
    except gspread.exceptions.APIError:
        messages.error(request, "An error occured. Check that you've run stage '1. Grant access to GreenPen'. If this persists, we may have overloaded Google's servers. Try again in 100 seconds.")
        return False
    return ss


def test_gc_sheets_questions(url, request):

    ss = test_gq_sheets_url(url, request)
    if not ss:
        return False

    try:
        qs = ss.worksheet("Questions").get_all_records()
        return qs
    except gspread.exceptions.APIError:
        messages.error(request, "An error occured. Check that you've run stage '1. Grant access to GreenPen'. If this persists, we may have overloaded Google's servers. Try again in 100 seconds.")
        return False
    except gspread.exceptions.WorksheetNotFound:
        messages.error(request, "Worksheet 'Questions' not found. Did you run 2. Extract  Questions?")
        return False


def test_gc_sheets_responses(url, request):

    ss = test_gq_sheets_url(url, request)
    if not ss:
        return False

    try:
        qs = ss.worksheet("Scores").get_all_records()
        return qs
    except gspread.exceptions.APIError:
        messages.error(request, "An error occured. Check that you've run stage '1. Grant access to GreenPen'. If this persists, we may have overloaded Google's servers. Try again in 100 seconds.")
        return False
    except gspread.exceptions.WorksheetNotFound:
        messages.error(request, "Worksheet 'Scores' not found. Did you run 3. Extract  scores from Form?")
        return False



def send_syllabus_children(request, syllabus_pk):
    points = Syllabus.objects.get(pk=syllabus_pk).get_children()

    return JsonResponse({'points': points})


@login_required
def sitting_splash(request, sitting_pk):
    if is_teacher(request.user):
        return redirect('exam-results', args=(sitting_pk,))
    if is_student(request.user):
        return redirect()

@user_passes_test(check_teacher)
def exam_result_view(request, sitting_pk):
    context = {}
    sitting = Sitting.objects.get(pk=sitting_pk)

    try:
        if sitting.gquizsitting.importing:
            messages.warning(request, "Scores for this exam are currently importing. Please check back in a few minutes.")
    except Sitting.DoesNotExist:
        # Will occur if this is not a Google Quiz subclass.
        pass
    context['sitting'] = sitting
    students = sitting.group.students.all().order_by('user__last_name')
    context['students'] = students
    marks = []

    # Build 2D array in the stucture:
    # Question number |  Student 1 score | Student 2 score .....
    # ...
    # Total           | Student 1 total  | Student 2 total
    for question in sitting.exam.question_set.all().order_by('order'):
        row = []
        row.append(question)
        for student in students:
            try:
                row.append(Mark.objects.get(sitting=sitting,
                                            student=student,
                                            question=question,
                                            ))
            except ObjectDoesNotExist:
                # creating lots of marks can overload the server,
                # so we will only create the first mark for each student.
                if question.order == 1:
                    row.append(Mark.objects.create(sitting=sitting,
                                                   student=student,
                                                   question=question))

                row.append('')
        # Iterated through all scores, so lets add the average.
        row.append(question.average_pc(cohort=sitting.student_qs(), sittings=Sitting.objects.filter(pk=sitting.pk)))
        marks.append(row)

    lastrow = ['Total']
    for student in students:
        lastrow.append(sitting.student_total(student))
    context['lastrow'] = lastrow
    context['marks'] = marks

    return render(request, 'GreenPen/exam_results.html', context)


@user_passes_test(check_teacher)
def alp_result_view(request, sitting_pk):
    context = {}
    sitting = Sitting.objects.get(pk=sitting_pk)
    context['sitting'] = sitting
    students = sitting.group.students.all().order_by('user__last_name')
    context['students'] = students
    questions = sitting.exam.question_set.all()
    context['questions'] = questions
    marks = []

    # Build 2D array in the stucture:
    #          |           |  Q1 num   | Q2
    # stu name | stu total |  Q1 score | Q2 score
    #
    for student in sitting.group.students.all():
        row = []
        row.append(student)
        row.append(sitting.student_total(student))
        for question in questions:
            try:
                row.append(Mark.objects.get(sitting=sitting,
                                            student=student,
                                            question=question,
                                            ))
            except ObjectDoesNotExist:
                # creating lots of marks can overload the server,
                # so we will only create the first mark for each student.
                if question.order == 1:
                    row.append(Mark.objects.create(sitting=sitting,
                                                   student=student,
                                                   question=question))

        marks.append(row)

    context['marks'] = marks

    return render(request, 'GreenPen/alp_exam_results.html', context)


@user_passes_test(check_teacher)
def teacher_dashboard(request):
    return render(request, 'GreenPen/teacher_dashboard.html')

@user_passes_test(check_teacher)
def exam_analysis_db(request):
    return render(request, 'GreenPen/exam_analysis_db.html')


@login_required()
def student_dashboard(request):
    # Check use is allowed to see this data:

    return render(request, 'GreenPen/teacher_dashboard.html')


def input_mark(request, mark_pk):
    mark = Mark.objects.get(pk=mark_pk)

    # Check teacher of students own mark:
    if request.user.groups.filter(name='Teachers').count():
        pass
    elif request.user == mark.student.user:
        pass
    else:
        raise HttpResponseForbidden

    form = EditMark(instance=mark)
    form.fields['mistakes'].widget.set_url(reverse('mistake_json_mark', args=[mark_pk]))
    prev_q = mark.get_previous()
    if prev_q:
        back_url = reverse('input_mark', args=[mark.get_previous().pk])
    else:
        back_url = False
    if request.method == 'POST':
        form = EditMark(request.POST, instance=mark)
        form.fields['mistakes'].widget.set_url(reverse('mistake_json_mark', args=[mark_pk]))

        if form.is_valid():
            if form.cleaned_data['score'] > mark.question.max_score:
                form.add_error('score', 'Score is higher than max for that question!')
            else:
                form.save()
                try:
                    next_q = Question.objects.get(exam=mark.question.exam,
                                                  order=mark.question.order + 1)
                except ObjectDoesNotExist:
                    next_q = False

                if next_q:
                    next_mark, created = Mark.objects.get_or_create(student=mark.student,
                                                                    sitting=mark.sitting,
                                                                    question=next_q)
                    return redirect('input_mark', mark_pk=next_mark.pk)
                else:
                    return redirect('student-dashboard')

    return render(request, 'GreenPen/input_mark.html', {'mark': mark,
                                                        'form': form,
                                                        'back_url': back_url})

class AcademicYearRollover(CreateView, SuperUserOnlyMixin):
    """
    Start the academic year rollover process by creating the new academic year
    Note that this should not be started until each part is ready to go!

    WARNING: Currently this will also roll over the calendear.
    If you'd like to be able to change your calendar shape for a new
    academic year, please feel free to raise a pull request.
    """
    model = AcademicYear
    success_url = '/rollover/2'
    fields = ['name', 'first_monday', 'total_weeks']

    def form_valid(self, form):
        # Set the order to be the next academic year
        current_academic_year = AcademicYear.objects.get(current=True)
        current_academic_year.current = False
        current_academic_year.save()
        form.instance.order = current_academic_year.order + 1
        form.instance.current = True


        return super().form_valid(form)


@user_passes_test(check_superuser)
def year_rollover_part2(request):

    # Start by creating the timetable for next academic year:

    # Copy the days from previous calendar
    prev_year = list(AcademicYear.objects.all().order_by('order'))[-2]
    curr_year = AcademicYear.objects.get(current=True)
    for new_day in Day.objects.filter(year=prev_year).order_by('order'):
        new_day.pk = None
        new_day.year = curr_year
        try:
            new_day.save()
        except IntegrityError:
            # Means the day alreay exists
            continue

    # Copy periods from last year
    for new_period in Period.objects.filter(year=prev_year).order_by('order'):
        new_period.pk = None
        new_period.year = curr_year
        try:
            new_period.save()
        except IntegrityError:
            # Already exists
            continue

    # Now set up the new calendar
    set_up_slots(curr_year)

    RolloverFormSet = modelformset_factory(TeachingGroup, TeachingGroupRollover, extra=0)
    qs = TeachingGroup.objects.filter(archived=False)
    rollover_form = RolloverFormSet(queryset=qs)
    current_academic_year = AcademicYear.objects.get(current=True)

    if request.method == 'POST':
        rollover_form = RolloverFormSet(request.POST, queryset=qs)
        if rollover_form.is_valid():
            rollover_form.save()

            # Now change the group names
            for group in TeachingGroup.objects.filter(archived=False, year_taught=CURRENT_ACADEMIC_YEAR):
                if group.rollover_name:
                    group.academic_year = current_academic_year
                    group.name = group.rollover_name + " " + group.academic_year.name
                    group.sims_name = group.rollover_name
                    group.rollover_name = False
                    group.year_taught = CURRENT_ACADEMIC_YEAR + 1

                    group.save()

                else:
                    group.archived = True
                    group.name = group.name + " ARCHIVED"
                    group.save()

            return redirect(reverse('rollover3'))
    else:

        return render(request, 'GreenPen/rollover_part_1.html', {'rollover_form': rollover_form,
                                                                 'title': 'Upload Marks'})


@user_passes_test(check_superuser)
def year_rollover_part3(request):
    # Deal with getting a CSV file

    if request.method == 'POST':
        csvform = CSVDocForm(request.POST, request.FILES)
        if csvform.is_valid():
            file = csvform.save()
            path = file.document.path
            import_groups_from_sims(path)
            os.remove(path)
            file.delete()
            messages.success(request, "Completed the rollover!")
            return redirect('/')
    else:
        csvform = CSVDocForm()
    return render(request, 'GreenPen/csv_upload.html', {'csvform': csvform,
                                                        'title': 'Upload Marks'})



@user_passes_test(check_teacher)
def new_sitting(request, exam_pk):
    exam = Exam.objects.get(pk=exam_pk)
    questions = Question.objects.filter(exam=exam)
    sittingform = NewSittingForm()
    # sittingform.set_group_choices(user=request.user)
    if request.method == 'POST':
        sittingform = NewSittingForm(request.POST)
        if sittingform.is_valid():
            classgroup = sittingform.cleaned_data['group']

            if sittingform.cleaned_data['response_form_url']:
                # Check it's accessible:
                if not test_gc_sheets_responses(sittingform.cleaned_data['response_form_url'], request):
                    return render(request, 'GreenPen/add-sitting.html', {'sittingform': sittingform,
                                                                         'exam': exam})
                sitting = GQuizSitting.objects.create(exam=exam,
                                                      group=classgroup,
                                                      date=sittingform.cleaned_data['date'],
                                                      scores_sheet_url=sittingform.cleaned_data['response_form_url']
                                                      )

                 # Import the questions before we create
                t = threading.Thread(target=sitting.import_scores, daemon=True)
                t.start()
                messages.warning(request, "Started importing questions. Return to the scores page in a few minutes to check they've imported correctly.")

            else:
                sitting = Sitting.objects.create(exam=exam,
                                                 group=classgroup,
                                                 date=sittingform.cleaned_data['date'],
                                                 )
            students = classgroup.students.all()
            for student in students:
                for question in questions:
                    Mark.objects.get_or_create(student=student, question=question, sitting=sitting)
            return redirect(reverse('exam-results', args=[sitting.pk, ]))

        else:
            return render(request, 'GreenPen/add-sitting.html', {'sittingform': sittingform,
                                                                 'exam': exam})

    return render(request, 'GreenPen/add-sitting.html', {'sittingform': sittingform,
                                                         'exam': exam})


def import_sitting_scores(request, sitting_pk):
    sitting = GQuizSitting.objects.get(pk=sitting_pk)
    if sitting.importing:
        messages.error(request, "There is already an import running for this sitting. Please check back later.")
    else:
        t = threading.Thread(target=sitting.import_scores, daemon=True)

        t.start()
        messages.warning(request, "Started importing questions. Return to the scores page in a few minutes to check they've imported correctly.")
    return redirect(reverse('exam-results', args=[sitting.pk, ]))


@user_passes_test(check_teacher)
def confirm_delete_sitting(request, sitting_pk):
    sitting = Sitting.objects.get(pk=sitting_pk)

    return render(request, 'GreenPen/confirm_delete_sitting.html', {'sitting': sitting})


@user_passes_test(check_teacher)
def delete_sitting(request, sitting_pk):
    sitting = Sitting.objects.get(pk=sitting_pk)
    sitting.delete()

    return redirect(reverse('exam-list'))


@login_required
def student_exam_view(request, student_pk):
    student = Student.objects.get(student_id=student_pk)
    if request.user.groups.filter(name='Teachers').count():
        pass
    elif request.user.groups.filter(name='Students').count():
        if student.user == request.user:
            pass
        else:
            raise HttpResponseForbidden
    else:
        raise HttpResponseForbidden

    sittings = Sitting.objects.filter(group__students=student).order_by('date')
    data = []
    for sitting in sittings:
        first_q = sitting.exam.question_set.order_by('order')[0]
        first_mark, created = Mark.objects.get_or_create(student=student,
                                                         sitting=sitting,
                                                         question=first_q)
        row = {'exam': sitting.exam,
               'sitting': sitting,
               'score': sitting.student_total(student),
               'first_mark': first_mark}
        data.append(row)
    return render(request, 'GreenPen/exam_list_student.html', {'student': student,
                                                               'data': data})


def student_exam_entry(request):
    if request.user.groups.filter(name='Students').count():
        student = Student.objects.get(user=request.user)
        return redirect(reverse('student-exam-list', args=[student.student_id, ]))
    else:
        raise Http404


@user_passes_test(check_teacher)
def timetable_splash(request):
    teacher = Teacher.objects.get(user=request.user)

    # Calculate the first day of the week
    today = datetime.date.today()
    week_commencing = today + datetime.timedelta(days=-today.weekday())
    first_period = Period.objects.get(order=1, year=AcademicYear.objects.get(current=True))
    try:
        current_week = CalendaredPeriod.objects.get(date=week_commencing, tt_slot__period=first_period)
    except ObjectDoesNotExist:
        # This happens if we're between calendars, e.g. in the Summer holidays.
        # In this instance, let's go to the closest Monday, trying foward first.
        current_week = CalendaredPeriod.objects.get(order=0, year=AcademicYear.objects.get(current=True))

    return redirect(reverse(timetable_overview, args=[current_week.pk, teacher.pk]))


@user_passes_test(check_teacher)
def timetable_overview(request, start_slot_pk, teacher_pk):
    """
    Dispaly the week grid for a given teacher, starting at the calendar slot corresponding to
    start_slot
    :param request:
    :param start_slot_pk: The PK for the calendar slot to begin the week grid with
    :param teacher_pk: the PK for the teacher who's timetalbe you'd like to see
    :return:
    """
    teacher = Teacher.objects.get(pk=teacher_pk)
    starting_slot = CalendaredPeriod.objects.get(pk=start_slot_pk)

    slots = CalendaredPeriod.objects.filter(date__gte=starting_slot.date,
                                            date__lt=starting_slot.date + datetime.timedelta(weeks=1))
    calendar_items = build_week_grid(starting_slot, teacher)

    try:
        next_week_pk = CalendaredPeriod.objects.get(date=starting_slot.date + datetime.timedelta(weeks=1),
                                                    tt_slot__period=starting_slot.tt_slot.period).pk
    except ObjectDoesNotExist:
        next_week_pk = False

    try:
        last_week_pk = CalendaredPeriod.objects.get(date=starting_slot.date - datetime.timedelta(weeks=1),
                                                    tt_slot__period=starting_slot.tt_slot.period).pk
    except ObjectDoesNotExist:
        last_week_pk = False

    return render(request, 'GreenPen/timetable_overview.html', {'teacher': teacher,
                                                                'calendar_items': calendar_items,
                                                                'next_week_pk': next_week_pk,
                                                                'last_week_pk': last_week_pk,
                                                                'return_pk': start_slot_pk})


@user_passes_test(check_teacher)
def add_tt_lesson(request, slot_pk):
    """
    When a user clicks 'add lesson' on their timetable,
    present a list of the classes they teach. Once the user has
    picked a class, create a lesson for that class in the slot
    given from the pk.
    """
    slot = CalendaredPeriod.objects.get(pk=slot_pk)
    tt_slot = slot.tt_slot
    teacher = Teacher.objects.get(user=request.user)
    groups = TeachingGroup.objects.filter(teachers=teacher, archived=False)

    form = TeachingGroupChoiceForm()
    form.fields['group'].queryset=groups

    if request.method == 'POST':
        form = TeachingGroupChoiceForm(request.POST)
        if form.is_valid():
            group = form.cleaned_data['group']
            group.lessons.add(tt_slot)
            messages.success(request, "Added lesson to your timetable")
            return redirect('tt_splash')
    else:
        return render(request, 'GreenPen/add-lesson-to-tt.html', {'tt_slot': tt_slot,
                                                                  'form': form})


def build_week_grid(start_period=CalendaredPeriod.objects.none(),
                    teacher=Teacher.objects.none()):
    days = Day.objects.filter(year=AcademicYear.objects.get(current=True))
    periods = Period.objects.filter(year=AcademicYear.objects.get(current=True))

    slots = CalendaredPeriod.objects.filter(date__gte=start_period.date,
                                            date__lt=start_period.date + datetime.timedelta(weeks=1))
    row = [period for period in periods]
    #    row = [''] + row
    rows = [row]
    for day in days:
        row = [day]
        for period in periods:
            slot = slots.get(tt_slot__day=day, tt_slot__period=period)

            # Either add all lessons (might double book teachers!) or make false
            lessons = Lesson.objects.filter(slot=slot, teachinggroup__teachers=teacher)
            if not lessons.count():
                lessons = False

            # Add suspensions or make false.
            suspensions = Suspension.objects.filter(slot=slot).filter(Q(teachinggroups__teachers=teacher)
                                                                      | Q(whole_school=True))
            if not suspensions.count():
                suspensions = False
            row.append({'lessons': lessons,
                        'suspensions': suspensions,
                        'slot': slot})
        rows.append(row)

    return rows


@user_passes_test(check_teacher)
def change_lesson(request, lesson_pk, return_pk):
    teacher = Teacher.objects.get(user=request.user)
    lesson = Lesson.objects.get(pk=lesson_pk)
    form = LessonChangeForm(instance=lesson)
    form.fields['syllabus'].widget.set_url(reverse('lesson-syllabus-json', args=[lesson.pk]))
    if request.method == 'POST':
        form = LessonChangeForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            return redirect('tt_overview', start_slot_pk=return_pk, teacher_pk=teacher.pk)
    return render(request, 'GreenPen/lesson_change.html', {'lesson': lesson,
                                                           'form': form})


@user_passes_test(check_superuser)
def suspend_days(request):
    form = SuspendDaysForm()

    if request.method == 'POST':
        form = SuspendDaysForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            whole_school = form.cleaned_data['whole_school']
            teachinggroups = form.cleaned_data['teaching_groups']

            delta = end_date - start_date  # as timedelta

            for i in range(delta.days + 1):
                day = start_date + datetime.timedelta(days=i)
                periods = Period.objects.filter(year=AcademicYear.objects.get(current=True))
                for period in periods:
                    suspension = Suspension.objects.create(date=day,
                                                           whole_school=whole_school,
                                                           reason=form.cleaned_data['reason'],
                                                           period=period)
                    if not whole_school:
                        suspension.teachinggroups.set(teachinggroups)
            return redirect(reverse('tt_splash'))

    return render(request, 'GreenPen/suspend_days.html', {'form': form})


@login_required()
def load_mistake_children(request, mark_pk=False):
    parent_id = request.GET.get('id')
    try:
        parent_id = int(parent_id)
        parent = Mistake.objects.get(pk=parent_id)
        children = Mistake.objects.filter(parent=parent)
    except ValueError:
        children = Mistake.objects.filter(level=0)

    if mark_pk:
        mark = Mark.objects.get(pk=mark_pk)
        mark_mistakes = mark.mistakes.all()
        mistake_ancestors = mark.mistakes.all().get_ancestors(include_self=False)

    data = []
    for child in children:
        if child.parent:
            parent_pk = child.parent.pk
        else:
            parent_pk = '#'
        undetermined = False
        selected = False
        opened = False
        if mark_pk:
            if child in mistake_ancestors:
                undetermined = True
                opened = True
            if child in mark_mistakes:
                selected = True
        data.append({
            'id': child.pk,
            'parent': parent_pk,
            'text': child.mistake_type,
            'children': not child.is_leaf_node(),
            'state': {'selected': selected,
                      'undetermined': undetermined,
                      'opened': opened}
        })
    return JsonResponse(data, safe=False)


@login_required()
def load_syllabus_points(request, resource_pk=False):
    parent_id = request.GET.get('id')
    try:
        parent_id = int(parent_id)
        parent = Syllabus.objects.get(pk=parent_id)
        children = Syllabus.objects.filter(parent=parent)
    except ValueError:
        children = Syllabus.objects.filter(level=0)

    if resource_pk:
        resource = Resource.objects.get(pk=resource_pk)
        resource_syllabus = resource.syllabus.all()
        resouce_syllabus_ancestors = resource.syllabus.all().get_ancestors(include_self=False)

    data = []
    for child in children:
        if child.parent:
            parent_pk = child.parent.pk
        else:
            parent_pk = '#'
        undetermined = False
        selected = False

        data.append({
            'id': child.pk,
            'parent': parent_pk,
            'text': child.text,
            'children': not child.is_leaf_node(),

        })
    return JsonResponse(data, safe=False)


class SyllabusJSONView(View):
    """
        Return all children of a parent.
        Allows for setting indeterminate if a child has been set:
        this is set by the 'get_children' method.
        """

    # Override this to set a different top-level syllabus point for
    # the tree, e.g. for a lesson.
    syllabus = Syllabus.objects.filter(level=0)
    root_level = 0

    def set_syllabus(self, syllabus):
        if syllabus:
            self.syllabus = syllabus

    def set_root_level(self):
        """
        JSTree requires us to set the 'parent_pk' property to '#' for
        root nodes.
        To do this, the function 'get' will need to know whether
        something is at the top level.
        """

        self.root_level = self.syllabus[0].get_level()

    def set_children(self):
        """
        Overide this method to provide inerterminate checkbox
        if a field has children set.
        Returns checked and indeterminate syllabus points as querysets.
        """
        return Syllabus.objects.none(), Syllabus.objects.none()



    def get(self, request, *args, **kwargs):
        self.set_syllabus(False)
        parent_id = self.request.GET.get('id')
        self.set_root_level()
        checked, indeterminate = self.set_children()

        try:
            parent_id = int(parent_id)
            parent = Syllabus.objects.get(pk=parent_id)
            children = Syllabus.objects.filter(parent=parent)
        except ValueError:
            children = self.syllabus

        data = []
        for child in children:
            if child.get_level() == self.root_level:
                parent_pk = '#'
            elif child.parent:
                parent_pk = child.parent.pk
            else:
                parent_pk = '#' # We shouldn't get here, as root level is 0 by default.
            undetermined = False
            selected = False
            opened = False
            if child in indeterminate:
                undetermined = True
                opened = True

            if child in checked:
                selected = True

            data.append({
                'id': child.pk,
                'parent': parent_pk,
                'text': child.text,
                'children': not child.is_leaf_node(),
                'state': {'selected': selected,
                          'undetermined': undetermined,
                          'opened': opened}
            })
        return JsonResponse(data, safe=False)


@login_required()
def load_syllabus_points_exam(request, exam_pk):
    """
    Loads the syllabus points for a JSTree widget when selecting the
    syllabus section that an exam tests.
    """

    # See if we have a parent loaded. If we are expanding a node, this will be present.
    # if not, we are on the initial load, and it will raise a value error.
    parent_id = request.GET.get('id')
    try:
        parent_id = int(parent_id)
        parent = Syllabus.objects.get(pk=parent_id)
        children = Syllabus.objects.filter(parent=parent)
    except ValueError:
        children = Syllabus.objects.filter(level=0)

    # get the exam, and find what syallbus it's currently set to.
    exam = Exam.objects.get(pk=exam_pk)

    if exam.syllabus:
        exam_syllabus = exam.syllabus
        exam_ancestors = exam_syllabus.get_ancestors(include_self=False)

    # We also want to open the nodes for any points already
    # in the exam

    included_points = Syllabus.objects.filter(question__exam=exam)

    included_ancestors = included_points.get_ancestors(include_self=False)

    #  Build a list of the parent points.
    data = []
    for child in children:
        if child.parent:
            parent_pk = child.parent.pk
        else:
            parent_pk = '#'
        undetermined = False
        selected = False
        opened = False
        li_attr = False
        if exam.syllabus:
            if child in exam_ancestors:
                undetermined = True
                opened = True

            if child == exam_syllabus:
                selected = True

        if child in included_ancestors:
            opened = True
            li_attr = {"class": "jstree-ancestor-checked"}

        if child in included_points:
            li_attr = {"class": "jstree-syllabus-checked"}

        data.append({
            'id': child.pk,
            'parent': parent_pk,
            'text': child.text,
            'children': not child.is_leaf_node(),
            'state': {'selected': selected,
                      'undetermined': undetermined,
                      'opened': opened},
            'li_attr': li_attr
        })
    return JsonResponse(data, safe=False)


def is_teacher(user=User.objects.none()):
    if user.groups.filter(name='Teachers').count():
        return True
    else:
        return False


def is_student(user=User.objects.none()):
    if user.groups.filter(name='Students ').count():
        return True
    else:
        return False


@user_passes_test(check_superuser)
def update_students(request):
    # Deal with getting a CSV file

    if request.method == 'POST':
        csvform = CSVDocForm(request.POST, request.FILES)
        if csvform.is_valid():
            file = csvform.save()
            path = file.document.path

            # Run import students to update all and add new students
            current_students = import_students_from_csv(path)

            # Remove any students no longer registered

            ex_students = Student.objects.all().exclude(pk__in=[s.pk for s in current_students])
            ex_students.update(on_role=False)
            os.remove(path)
            file.delete()
            messages.success(request, 'Updated all students.')
            return redirect(reverse('splash'))
    else:
        csvform = CSVDocForm()
    return render(request, 'GreenPen/upload_csv.html', {'csvform': csvform,
                                                             'upload_message': 'Updating Student list'})


@user_passes_test(check_superuser)
def update_classgroups(request):
    # Deal with getting a CSV file

    if request.method == 'POST':
        csvform = CSVDocForm(request.POST, request.FILES)
        if csvform.is_valid():
            file = csvform.save()
            path = file.document.path

            # Run import students to update all and add new students
            current_tg_pks = import_classgroups_from_csv(path)
            os.remove(path)
            file.delete()
            # Remove any students no longer registered
            for group in TeachingGroup.objects.filter(archived=False):
                linked_groups = group.find_linked_groups()
                if linked_groups:
                    for added in linked_groups:
                        current_tg_pks.append(added.pk)
                group.set_linked_students()
            from GreenPen.functions import housekeeping
            housekeeping.fix_multiple_group_assignments()
            old_tgs = TeachingGroup.objects.all().exclude(archived=False, pk__in=current_tg_pks)
            old_tgs.update(archived=True)

            messages.success(request, 'Updated all classgroups.')
            return redirect(reverse('splash'))
    else:
        csvform = CSVDocForm()
    return render(request, 'GreenPen/upload_csv.html', {'csvform': csvform,
                                                             'upload_message': 'Updating Class Groups'})


class AddResource(TeacherOnlyMixin, CreateView):
    template_name = 'GreenPen/add-resource.html'
    form_class = AddResourceForm
    model = Resource

    def get_initial(self):
        # Get the initial dictionary from the superclass method
        initial = super(AddResource, self).get_initial()
        # Copy the dictionary so we don't accidentally change a mutable dict
        initial = initial.copy()
        initial['created_by'] = self.request.user.pk

        return initial

    def get_form(self):
        form = super(AddResource, self).get_form(self.form_class)
        if self.object:
            form.fields['syllabus'].widget.set_url(reverse('resource-syllabus-json', args=[self.object.pk]))
        else:
            form.fields['syllabus'].widget.set_url(reverse('json_syllabus_points'))
        return form

    def form_valid(self, form):
        form.set_additional(self.request.user)
        messages.success(self.request, "Resource saved successfully. Click <a href='/resources/new'>here</a> to add another")

        return super().form_valid(form)

    def form_invalid(self, form):
        pass

class AddResourceFromLesson(AddResource):
    def form_valid(self, form):
        response = super(AddResource, self).form_valid(form)
        lesson = Lesson.objects.get(pk=self.kwargs['lesson_pk'])
        lesson.resources.add(self.object)
        return response


class EditResource(AddResource, UpdateView):
    def get_initial(self):
        return super(AddResource, self).get_initial()


class ResourceSyllabusJSON(SyllabusJSONView):
    def set_children(self):
        resource_pk = self.kwargs['resource_pk']
        resource = Resource.objects.get(pk=resource_pk)
        checked = resource.syllabus.all()
        indeterminate = checked.get_ancestors(include_self=False)

        return checked, indeterminate


class LessonSyllabusJSON(SyllabusJSONView):

    def set_children(self):
        lesson_pk = self.kwargs['lesson_pk']
        lesson = Lesson.objects.get(pk=lesson_pk)
        checked = lesson.syllabus.all()
        indeterminate = checked.get_ancestors(include_self=False)

        return checked, indeterminate

    def set_syllabus(self, syllabus):
        lesson_pk = self.kwargs['lesson_pk']
        lesson = Lesson.objects.get(pk=lesson_pk)
        self.syllabus = Syllabus.objects.filter(pk=lesson.teachinggroup.syllabus.pk)


class ResourceList(ListView):
    model = Resource
    template_name = 'GreenPen/resource-list.html'


@teacher_or_own_only
def create_self_assessment_sitting(request, exam_pk, student_pk):
    """
    Create a self-assessment sitting of an exam for a student. This can be
    either self-selected if he requesting user is a student, or assigned if the
    requesting user is a teacher.
    """

    student = get_object_or_404(Student, pk=student_pk)
    exam = get_object_or_404(GQuizExam, pk=exam_pk)

    # Check this is a self-assessment exam

    if not exam.type.eligible_for_self_assessment:
        messages.error(request, "You attempted to create a self-assessment quiz using a non-self assesed exam")
        return HttpResponseForbidden()

    # Check if the student has started and not completed an attempt:

    previous_attempts = GQuizSitting.objects.filter(exam=exam,
                                               students=student).order_by('order')

    if previous_attempts.last():
        if not previous_attempts.last().imported:
            messages.warning(request, "Youv'e already started and not completed this quiz. Click  Click {link} to "
                                      "open it.".format(link=previous_attempts.last().self_assessment_link()))

    sitting = GQuizSitting.objects.create(exam=exam,
                                     date=datetime.date.today(),
                                     self_assessment=True,
                                     order=previous_attempts.count() + 1,
                                     imported=False,
                                          scores_sheet_url=exam.master_response_sheet_url)

    sitting.students.add(student)
    sitting.group = sitting.get_generic_teaching_group()
    sitting.save()

    messages.success(request, "Your sitting has been created. Click {link} to open it.".format(link=sitting.self_assessment_link()))
    return redirect('import_student_self_assessment_scores', sitting_pk=sitting.pk, student_pk=student_pk)


def recieve_google_completion_message():
    """
    This code receives a POST request from Google to tell us that a student has
    completed an online assessment, so that we can now retrieve that students'
    answers and update their scores.

    This code will only work with new attempts, so we must be careful to manually
    re-enter the whole thing if a teacher changes answers or the original Google form
    becomes corrupt.

    The POST payload should include the following:

    gapps_id: PK of the teacher who set it up
    gapps_key: alphanumeric password generated at runtime.
    sheet_id; 
    """
    pass


@teacher_or_own_only
def import_student_self_assessment_scores_pt1(request, sitting_pk, student_pk):
    sitting = get_object_or_404(GQuizSitting, pk=sitting_pk)
    student = get_object_or_404(Student, pk=student_pk)

    return render(request, "GreenPen/Import_quiz.html", {'student': student,
                                           'sitting': sitting})


@teacher_or_own_only
def import_student_self_assessment_scores_pt2(request, sitting_pk, student_pk):
    """ We should have recieved a POST from Google, dealt with by
    qquiz_alert. This function should check if the sitting is still listed as
    imported=False. If so,it will add a message to complete the form
    and redirect. Otherwise, the student will be sent to their dashboard
    to view the result.
    """

    sitting = get_object_or_404(GQuizSitting, pk=sitting_pk)
    student = get_object_or_404(Student, pk=student_pk)

    if sitting.imported:
        messages.success(request, "Your quiz has been imported correctly. Please use the timeline chart to filter to only show this quiz.")
        return redirect(reverse('splash'))

    else:
        messages.warning(request, "You either have not yet filled out the Google Quiz, or your quiz is still importing. Please make sure you've completed the link above, or wait a minute for us to catch up! If this error continues, please inform your teacher.")
        return redirect(reverse('import_student_self_assessment_scores', args=[sitting.pk, student_pk]))




@csrf_exempt
def gquiz_alert(request):
    if request.method == 'POST':
        recieved_json = json.loads(request.body)
        sheet_url = recieved_json['form_url']
        student_email = recieved_json['student_email']
        response_timestamp = recieved_json['timestamp']

        remote_add = request.META['REMOTE_ADDR']


        print('Sheet url: ' + sheet_url)
        print('Email: ' + student_email)
        print('Timestamp' + response_timestamp)
        print('remote address:' + remote_add)

        time_string = str(response_timestamp)
        time_string = time_string.replace('T', ' ')
        time_string = re.match(r'(.*)\.', time_string).group()
        time_string = time_string[:-1]
        response_timestamp = datetime.datetime.strptime(time_string, "%Y-%m-%d %H:%M:%S")

        sittings = GQuizSitting.objects.filter(scores_sheet_url=sheet_url)

        if sittings.count() > 1:
            # More than one sitting using the same response sheet.
            # This should only occur for self-assessment quizzes.
            if sittings.count() != sittings.filter(self_assessment=True).count():
                raise IntegrityError("Multiple sittings using the same URL")

            sitting = sittings.filter(students__user__email=student_email).get_closest_to(response_timestamp)
        else:
            sitting = GQuizSitting.objects.get(scores_sheet_url=sheet_url)

        sitting.import_scores(email=student_email, timestamp=response_timestamp)
        print("E:" + student_email +":E")
        print("T:" + str(response_timestamp) +"T")
        sitting.imported = True
        sitting.save()
        return HttpResponse('Success')
    else:
        return HttpResponseBadRequest
