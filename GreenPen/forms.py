from dal import autocomplete
from GreenPen.models import Mark, Student, CSVDoc, Question, Syllabus, Exam, TeachingGroup, Lesson, Mistake
from django import forms
from mptt.forms import TreeNodeChoiceField
from .widgets import TreeSelect
from jstree.widgets import JsTreeWidget, JsTreeSingleWidget
from django.urls import reverse
import datetime
import json


class MarkRecordForm(forms.ModelForm):
    student = forms.ModelChoiceField(
        queryset=Student.objects.all(),
        widget=autocomplete.ModelSelect2(url='student-autocomplete')
    )

    class Meta:
        model = Mark
        fields = ('__all__')


class CSVDocForm(forms.ModelForm):
    class Meta:
        model = CSVDoc
        fields = ('description', 'document',)


class SetQuestions(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['number', 'max_score', 'syllabus_points', 'order', 'id']
        widgets = {
            'syllabus_points': autocomplete.ModelSelect2Multiple(url='syllabus-autocomplete',
                                                                 forward=['points'],
                                                                 ),
            'exam': forms.HiddenInput(),
            'id': forms.HiddenInput(),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            # 'number': forms.TextInput(attrs={'class': 'form-control'}),
            # 'max_score': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    class Media:
        js = (
            'https://code.jquery.com/jquery-3.2.1.min.js',
        )


class EditMark(forms.ModelForm):

    class Meta:
        model = Mark
        fields = ['score', 'mistakes', 'student_notes']
        widgets = {
            'mistakes': JsTreeWidget(url='syllabus', result_hidden=True)
        }


class SyllabusChoiceForm(forms.Form):
    qs = Syllabus.objects.all()
    points = TreeNodeChoiceField(queryset=qs,
                                 widget=JsTreeWidget(url=False, result_hidden=False),
                                 level_indicator='')

    def _get_level_indicator(self, obj):
        return ''


class AddExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        exclude = []
        widgets = {
            'syllabus': JsTreeSingleWidget(url='/syllabus/json/', result_hidden=False),

        }


class TeachingGroupRollover(forms.ModelForm):
    class Meta:
        models = TeachingGroup
        fields = ['name', 'rollover_name']
        widgets = {'name': forms.TextInput(attrs={'readonly': 'readonly'})}


class NewSittingForm(forms.Form):
    group = forms.ModelChoiceField(TeachingGroup.objects.filter(archived=False))
    date = forms.DateField(widget=forms.SelectDateWidget)


class LessonChangeForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'description', 'requirements']


class SuspendDaysForm(forms.Form):
    start_date = forms.DateField(widget=forms.SelectDateWidget, initial=datetime.date.today)
    end_date = forms.DateField(widget=forms.SelectDateWidget, initial=datetime.date.today)
    whole_school = forms.BooleanField(required=False)
    teaching_groups = forms.ModelMultipleChoiceField(queryset=TeachingGroup.objects.filter(archived=False), required=False)
    reason = forms.CharField(max_length=256)
