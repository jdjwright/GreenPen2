from dal import autocomplete

from GreenPen.models import Student


class StudentComplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return Student.objects.none()

        qs = Student.objects.all()

        if self.q:
            qs = qs.filter(name__istartswith=self.q)

        return qs