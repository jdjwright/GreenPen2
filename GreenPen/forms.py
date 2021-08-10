from dal import autocomplete
from GreenPen.models import Mark, Student, CSVDoc, Question, Syllabus, Exam, TeachingGroup, Lesson, GQuizExam, Resource
from django import forms
from django.contrib.auth.models import User
from mptt.forms import TreeNodeChoiceField
from .widgets import TreeSelect
from jstree.widgets import JsTreeWidget, JsTreeSingleWidget, JSTreeMultipleWidget
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
        fields = ['number', 'max_score', 'syllabus_points', 'id']
        widgets = {
            'syllabus_points': autocomplete.ModelSelect2Multiple(url='syllabus-autocomplete',
                                                                 forward=['syllabus'],
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
                                 widget=JsTreeWidget(url=False, result_hidden=True),
                                 level_indicator='')

    def _get_level_indicator(self, obj):
        return ''


class SyllabusSingleChoiceField(TreeNodeChoiceField):
    widget = JsTreeSingleWidget(url='/syllabus/json', result_hidden=True)

    def clean(self, value):
        # JSTreeWidget produces an array of values, but we only want one
        # Hence we must extract it.
        try:
            value = value[0]
        except IndexError:
            return Syllabus.objects.filter(level=0).first()
        value = super(SyllabusSingleChoiceField, self).clean(value)
        return value


class AddExamForm(forms.ModelForm):
    syllabus = SyllabusSingleChoiceField(queryset=Syllabus.objects.all())
    class Meta:
        model = Exam
        exclude = []
        widgets = {
            'syllabus': JsTreeSingleWidget(url='/syllabus/json/', result_hidden=False),

        }
        # fields = {
        #     'syllabus': SyllabusSingleChoiceField(queryset=Syllabus.objects.all())
        # }
        

class AddResourceForm(forms.ModelForm):

    class Meta:
        model = Resource
        fields = ['name', 'type', 'url', 'syllabus', 'created_by', 'exam']
        widgets = {
            'syllabus': JsTreeWidget(url='/syllabus/json/', result_hidden=True),
            'created_by': forms.HiddenInput()
        }

    def set_additional(self, user):
        self.fields['created_by'] = user


class AddGoogleExamForm(forms.ModelForm):
    syllabus = SyllabusSingleChoiceField(queryset=Syllabus.objects.all())
    class Meta:
        model = GQuizExam
        exclude = []
        widgets = {
            'syllabus': JsTreeSingleWidget(url='/syllabus/json/', result_hidden=False),

        }
        # fields = {
        #     'syllabus': SyllabusSingleChoiceField(queryset=Syllabus.objects.all())
        # }


class TeachingGroupRollover(forms.ModelForm):
    class Meta:
        models = TeachingGroup
        fields = ['name', 'rollover_name']
        widgets = {'name': forms.TextInput(attrs={'readonly': 'readonly'})}


class NewSittingForm(forms.Form):
    group = forms.ModelChoiceField(TeachingGroup.objects.filter(archived=False))
    date = forms.DateField(widget=forms.SelectDateWidget)
    response_form_url = forms.URLField(max_length=1000, required=False, help_text="If importing answers from a Google Form, include the URL  of the response sheet URL here.")

    def set_group_choices(self, user=User.objects.none()):
        """ Restrict the settable groups based upon the user creating the form. """
        tgs = TeachingGroup.objects.filter(archived=False, use_for_exams=True)
        # if not User.has_perm('GreenPen.create_any_sitting'):
        #     tgs = tgs.filter(teachers__user=user)

        self.group.choices = tgs



class LessonChangeForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'description', 'requirements', 'syllabus']
        widgets = {
            'syllabus': JsTreeWidget(url='/syllabus/json/', result_hidden=True),
        }


class SuspendDaysForm(forms.Form):
    start_date = forms.DateField(widget=forms.SelectDateWidget, initial=datetime.date.today)
    end_date = forms.DateField(widget=forms.SelectDateWidget, initial=datetime.date.today)
    whole_school = forms.BooleanField(required=False)
    teaching_groups = forms.ModelMultipleChoiceField(queryset=TeachingGroup.objects.filter(archived=False), required=False)
    reason = forms.CharField(max_length=256)


class CSVDocForm(forms.ModelForm):
    class Meta:
        model = CSVDoc
        fields = ('description', 'document', )


class TeachingGroupChoiceForm(forms.Form):
    group = forms.ModelChoiceField(queryset=TeachingGroup.objects.all())
