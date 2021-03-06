from GreenPen.models import Student, Question
from django.views.generic.list import ListView, View
from django.views.generic.edit import UpdateView
from django.http import JsonResponse, HttpResponseForbidden, Http404, HttpResponseRedirect
from django.forms import modelformset_factory
from django.views.generic.edit import CreateView
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render, get_object_or_404, reverse
from django.forms import inlineformset_factory
from GreenPen.functions.imports import *
from .forms import *
from .settings import CURRENT_ACADEMIC_YEAR
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .widgets import *
import os
import threading
import gspread

from plotly.offline import plot
import plotly.graph_objects as go

# For authenticating views
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin


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
            import_syllabus_from_csv(path)
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

    exam_form = AddExamForm()
    parent_form = SyllabusChoiceForm()
    parent_form.fields['points'].widget.set_url('/syllabus/json/')

    def get(self, request, *args, **kwargs):

        exam = get_object_or_404(Exam, pk=self.kwargs['exam'])
        exam_form = AddExamForm(instance=exam)
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

        exam = get_object_or_404(Exam, pk=self.kwargs['exam'])

        form = self.form(request.POST, instance=exam)

        exam_form = AddExamForm(request.POST, instance=exam)
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
                success_message = "Exam save succeffully. <a href='" + reverse('new-sitting', args=(
                exam.pk,)) + "'>Click here to create a sitting for it</a>."
                messages.success(request, success_message)
                return redirect('edit-exam', exam.pk)

        # Some eror occured.
        # We need to sort the form so that it's in the correct order,
        # otherwise newly-added questions will always be at the bottom.
        # Key function to provide sort value

        form.forms.sort(key=sort_order_func)
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


@user_passes_test(check_superuser)
def year_rollover_part1(request):
    # Deal with getting a CSV file
    RolloverFormSet = modelformset_factory(TeachingGroup, TeachingGroupRollover, extra=0)
    qs = TeachingGroup.objects.filter(archived=False, year_taught=CURRENT_ACADEMIC_YEAR)
    rollover_form = RolloverFormSet(queryset=qs)

    if request.method == 'POST':
        rollover_form = RolloverFormSet(request.POST, queryset=qs)
        if rollover_form.is_valid():
            rollover_form.save()

            # Now change the group names
            for group in TeachingGroup.objects.filter(archived=False, year_taught=CURRENT_ACADEMIC_YEAR):
                if group.rollover_name:
                    group.name = group.rollover_name
                    group.rollover_name = False
                    group.year_taught = CURRENT_ACADEMIC_YEAR + 1
                    group.save()

                else:
                    group.archived = True
                    group.save()

            return redirect(reverse('rollover2'))

    return render(request, 'GreenPen/rollover_part_1.html', {'rollover_form': rollover_form,
                                                             'title': 'Upload Marks'})


@user_passes_test(check_superuser)
def year_rollover_part2(request):
    # Deal with getting a CSV file

    if request.method == 'POST':
        csvform = CSVDocForm(request.POST, request.FILES)
        if csvform.is_valid():
            file = csvform.save()
            path = file.document.path
            import_groups_from_sims(path)
            os.remove(path)
            file.delete()
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
    current_week = CalendaredPeriod.objects.get(date=week_commencing, tt_slot__period=first_period)

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
def load_syllabus_points(request):
    parent_id = request.GET.get('id')
    try:
        parent_id = int(parent_id)
        parent = Syllabus.objects.get(pk=parent_id)
        children = Syllabus.objects.filter(parent=parent)
    except ValueError:
        children = Syllabus.objects.filter(level=0)

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
        if exam.syllabus:
            if child in exam_ancestors:
                undetermined = True
                opened = True

            if child == exam_syllabus:
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
