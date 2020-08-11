from GreenPen.models import Student, Question
from django.views.generic.list import ListView, View
from django.views.generic.edit import UpdateView
from django.http import JsonResponse, HttpResponseForbidden, Http404
from django.forms import modelformset_factory
from django.views.generic.edit import CreateView
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render, get_object_or_404, reverse
from django.forms import inlineformset_factory
from GreenPen.functions.imports import *
from .forms import *
from .settings import CURRENT_ACADEMIC_YEAR
from django.contrib.auth.decorators import login_required
from .widgets import *
import os

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
        return redirect(reverse('student-dashboard', args=[student.pk]))


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
    syllabus_widget = autocomplete.ModelSelect2Multiple(url='syllabus-autocomplete',
                                                                 forward=['points'],
                                                                 )
    setquestionsformset = inlineformset_factory(Exam, Question,
                                                form=SetQuestions,
                                                extra=50,
                                                can_order=False,
                                                can_delete=True)

    parent_form = SyllabusChoiceForm()


    def get(self, request, *args, **kwargs):

        exam = get_object_or_404(Exam, pk=self.kwargs['exam'])

        # # Add an extra blank if we have no questions added:
        # if not exam.question_set.count():
        #     self.setquestionsformset = inlineformset_factory(Exam, Question,
        #                                                 form=SetQuestions,
        #                                                 extra=1,
        #                                                 can_order=False,
        #                                                 can_delete=True)

        form = self.setquestionsformset(instance=exam)
        return render(request, self.template_name, {'form': form,
                                                    'parent_form': self.parent_form})

    def post(self, request, *args, **kwargs):
        exam = get_object_or_404(Exam, pk=self.kwargs['exam'])
        form = self.setquestionsformset(request.POST, instance=exam)
        if form.is_valid():
            # <process form cleaned data>
            for q in form.deleted_forms:
                question = q.cleaned_data['id'].delete()
            form.save()
            return redirect(reverse('edit-exam', args=(exam.pk,)))

        return render(request, self.template_name, {'form': form,
                                                    'parent_form': self.parent_form})


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


class AddExam(TeacherOnlyMixin, CreateView):
    template_name = 'Greenpen/add-exam.html'
    form_class = AddExamForm
    model = Exam


def send_syllabus_children(request, syllabus_pk):
    points = Syllabus.objects.get(pk=syllabus_pk).get_children()

    return JsonResponse({'points': points})



@user_passes_test(check_superuser)
def exam_result_view(request, sitting_pk):
    context = {}
    sitting = Sitting.objects.get(pk=sitting_pk)
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
def teacher_dashboard(request):

    return render(request, 'GreenPen/teacher_dashboard.html')


def student_dashboard(request, student_pk):
    student = get_object_or_404(Student, pk=student_pk)

    # Check use is allowed to see this data:
    if request.user.is_superuser or request.user.groups.filter(name='Teachers').count():
        pass
    elif request.user.groups.filter(name='Students'):
        if student.user != request.user:
            return HttpResponseForbidden

    return render(request, 'Greenpen/student_dashboard.html', {'student': student})


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

    if request.method == 'POST':
        form = EditMark(request.POST, instance=mark)
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
                    return redirect('student-dashboard', student_pk=mark.student.pk)

    return render(request, 'GreenPen/input_mark.html', {'mark': mark,
                                                        'form': form})


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
            sitting = Sitting.objects.create(exam=exam, group=classgroup, date=sittingform.cleaned_data['date'],
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
        return redirect(reverse('student-exam-list', args=[student.student_id,]))
    else:
        raise Http404
