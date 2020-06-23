from GreenPen.models import Student
from django.views.generic.list import ListView, View
from django.http import JsonResponse
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


def sample(request):
    def scatter():
        x1 = [1, 2, 3, 4]
        y1 = [30, 35, 25, 45]

        trace = go.Scatter(
            x=x1,
            y=y1
        )
        layout = dict(
            title='Simple Graph',
            xaxis=dict(range=[min(x1), max(x1)]),
            yaxis=dict(range=[min(y1), max(y1)])
        )

        fig = go.Figure(data=[trace], layout=layout)

        plot_div = plot(fig, output_type='div', include_plotlyjs=False)

        return plot_div
    
    def simple_sunburst():
        points = ['Syllabus', 'Sub 1', 'sub2', 'sub3', 'sub1_text1', 'sub2_text1', 'sub2_text2']
        parent = ['', 'Syllabus', 'Syllabus', 'Syllabus', 'Sub 1', 'Sub 2', 'Sub 2']
        value = ['5', '1', '1', '1', '1', '1', '1']

        burst = go.Sunburst(
            labels=points,
            parents=parent,
            values=value
        )

        fig = go.Figure(go.Sunburst(
            labels=["Eve", "Cain", "Seth", "Enos", "Noam", "Abel", "Awan", "Enoch", "Azura"],
            parents=["", "Eve", "Eve", "Seth", "Seth", "Eve", "Eve", "Awan", "Eve"],
            values=[65, 14, 12, 10, 2, 6, 6, 4, 4],
            branchvalues="total",
        ))
        fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))
        plot_div = plot(fig, output_type='div', include_plotlyjs=False)
        return plot_div

    def syllabus_sunburst():
        students = Student.objects.all()
        points = Syllabus.objects.get(pk=2).get_descendants(include_self=True)
        labels = [point.text for point in points]
        parents = [point.parent.text for point in points]
        parents[0] = ""
        values = [point.cohort_stats(students)['rating'] for point in points]

        fig = go.Figure(go.Sunburst(
            labels=labels,
            parents=parents,
            #values=values,
            marker=dict(colors=values,
                        colorscale='RdYlGn',
                        cmid=2.5),
            hovertemplate='<b>{% label %}</b><br>Average rating: {% label %}',
            maxdepth=3

        ))
        fig.update_layout(margin=dict(t=0, l=0, r=0, b=0),
                          uniformtext=dict(minsize=10, mode='hide'))
        plot_div = plot(fig, output_type='div', include_plotlyjs=False)
        return plot_div

    context = {
        'plot1': scatter(),
        'plot2': simple_sunburst(),
        'plot3': syllabus_sunburst(),
    }
    
    
    return render(request, 'GreenPen/plotly_test.html', context)
