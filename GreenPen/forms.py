from dal import autocomplete
from GreenPen.models import Mark, Student
from django import forms


class MarkRecordForm(forms.ModelForm):
    student = forms.ModelChoiceField(
        queryset=Student.objects.all(),
        widget=autocomplete.ModelSelect2(url='student-autocomplete')
    )

    class Meta:
        model = Mark
        fields = ('__all__')
