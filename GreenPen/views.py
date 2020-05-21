from GreenPen.models import Student
from django.views.generic.list import ListView
from django.shortcuts import redirect, render
from GreenPen.functions.imports import import_students_from_csv, import_classgroups_from_csv
from .forms import CSVDocForm
import os


class StudentList(ListView):
    model = Student


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