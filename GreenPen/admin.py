from django.contrib import admin
from GreenPen.forms import MarkRecordForm
from GreenPen.models import Student, Mark, Syllabus, Question

class MarkAdmin(admin.ModelAdmin):
    form = MarkRecordForm

admin.site.register(Student)
admin.site.register(Mark, MarkAdmin)
admin.site.register(Syllabus)
admin.site.register(Question)
