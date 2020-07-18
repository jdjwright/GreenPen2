from django.contrib import admin
from GreenPen.forms import MarkRecordForm
from GreenPen.models import Student, Mark, Syllabus, Question, TeachingGroup

class MarkAdmin(admin.ModelAdmin):
    form = MarkRecordForm

admin.site.register(Student)
admin.site.register(Mark, MarkAdmin)
admin.site.register(Syllabus)
admin.site.register(Question)
admin.site.register(TeachingGroup)
