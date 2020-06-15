from dal import autocomplete
from GreenPen.models import Mark, Student, CSVDoc, Question
from django import forms


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
            #'number': forms.TextInput(attrs={'class': 'form-control'}),
            #'max_score': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    class Media:
        js = (
            'https://code.jquery.com/jquery-3.2.1.min.js',
        )