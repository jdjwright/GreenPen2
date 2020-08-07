from GreenPen.models import Student
from django.views.generic.list import ListView, View
from django.http import JsonResponse, HttpResponseForbidden
from django.views.generic.edit import CreateView
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render, get_object_or_404, reverse
from django.forms import inlineformset_factory
from GreenPen.functions.imports import *
from .forms import *
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
    elif user.groups.filter(name='Teacher').count():
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

