from django.contrib import admin
from GreenPen.forms import MarkRecordForm
from GreenPen.models import Student, Mark

class MarkAdmin(admin.ModelAdmin):
    form = MarkRecordForm

admin.site.register(Student)
admin.site.register(Mark, MarkAdmin)