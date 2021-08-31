from dal import autocomplete
import json
from django.db.models import Q
from GreenPen.models import Student, Syllabus, Mistake, TeachingGroup, Teacher, Lesson, Resource


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

        if self.forwarded.get('syllabus', None):
            pks = json.loads(self.forwarded.get('syllabus', None))
            qs = qs.filter(pk__in=pks).get_descendants().distinct()

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


class TeachingGroupAutocomplete(autocomplete.Select2QuerySetView):
    qs = TeachingGroup.objects.all()

    def set_qs(self):
        return self.qs

    def get_queryset(self):
        self.qs = self.set_qs()
        if not self.request.user.is_authenticated:
            return TeachingGroup.objects.none()
        if self.q:
            self.qs = self.qs.filter(name__icontains=self.q)

        return self.qs


class TeachingGroupOwnAutocomplete(TeachingGroupAutocomplete):
    def set_qs(self):
        return self.qs.filter(teachers=Teacher.objects.get(user=self.request.user), archived=False)


class LessonAutocomplete(autocomplete.Select2QuerySetView):
    qs = Lesson.objects.none()

    def set_viewable_lessons(self):
        """
        By default, allow teachers to see *all* lessons,
        and student to see any lesson they are taught.
        """
        if self.request.user.groups.filter(name='Teachers').count():
            self.qs = Lesson.objects.all()

        elif self.request.user.groups.filter(name='Students').count():
            self.qs = Lesson.objects.filter(teachinggroup__students=Student.objects.get(user=self.request.user))

    def get_queryset(self):

        self.set_viewable_lessons()

        if self.forwarded.get('teachinggroup', None):
            pks = json.loads(self.forwarded.get('teachinggroup', None))
            self.qs = self.qs.filter(teachinggroup__pk=pks)

        if self.q:
            self.qs = self.qs.filter(title__icontains=self.q)

        return self.qs.exclude(title__isnull=True).order_by('-slot__date')


class ResourceAutocomplete(autocomplete.Select2QuerySetView):
    qs = Resource.objects.none()
    def set_viewable_resources(self):
        """
        By default, allow teachers to see *all* resources,
        and student to see any resource open to them.
        """
        if self.request.user.groups.filter(name='Teachers').count():
            self.qs = Resource.objects.all()

        elif self.request.user.groups.filter(name='Students').count():
            self.qs = Resource.objects.filter(open_to_all=True)

    def get_queryset(self):

        self.set_viewable_resources()

        if self.forwarded.get('syllabus', None):
            pk = json.loads(self.forwarded.get('syllabus', None))[0]
            syllabus_points = Syllabus.objects.get(pk=pk).get_descendants(include_self=True)
            self.qs = self.qs.filter(syllabus__in=syllabus_points)

        if self.q:
            self.qs = self.qs.filter(name__icontains=self.q)

        return self.qs.distinct()