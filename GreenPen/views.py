from GreenPen.models import Student
from django.views.generic.list import ListView, View

from django.shortcuts import redirect, render, get_object_or_404
from GreenPen.functions.imports import *
from .forms import CSVDocForm
import os

# For authenticating views
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin



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


class StudentAssessmentForPoint(TeacherOnlyMixin, ListView):

    template_name = 'GreenPen/studnet_assessment_list.html'

    def get_queryset(self):
        syllabus = get_object_or_404(Syllabus, pk=self.kwargs['syllabus_pk'])
        student = get_object_or_404(Student, pk=self.kwargs['student_pk'])
        return StudentSyllabusAssessmentRecord.objects.filter(student=student,
                                                              syllabus_point=syllabus)