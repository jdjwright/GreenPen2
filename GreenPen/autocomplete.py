from dal import autocomplete

from GreenPen.models import Student, Syllabus, Mistake


class StudentComplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return Student.objects.none()

        qs = Student.objects.all()

        if self.q:
            qs = qs.filter(name__istartswith=self.q)

        return qs


class SyllabusComplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Syllabus.objects.none()

        qs = Syllabus.objects.all()

        if self.forwarded.get('points', None):
            qs = qs.get(pk=self.forwarded.get('points')).get_descendants()

        if self.q:
            qs = qs.filter(text__icontains=self.q)

        return qs


class MistakeAutoComplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Mistake.objects.none()

        qs = Mistake.objects.all()
        if self.q:
            qs = qs.filter(mistake__type__icontains=self.q)
        return qs