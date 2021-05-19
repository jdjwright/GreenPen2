from .models import Student
from django.core.exceptions import PermissionDenied



def teacher_or_own_only(function):
    """display only if viewing student's own work or if requesting user is a teacher"""

    def wrap(request, *args, **kwargs):

        if request.user.groups.filter(name='Teachers').exists():
            return function(request, *args, **kwargs)

        # TODO: check this works
        requested_student = Student.objects.get(pk=kwargs['student_pk'])
        if request.user == requested_student.user:
            return function(request, *args, **kwargs)

        else:
            raise PermissionDenied

    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap