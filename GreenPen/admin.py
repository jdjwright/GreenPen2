from django.contrib import admin
from GreenPen.forms import MarkRecordForm
from GreenPen.models import *

class MarkAdmin(admin.ModelAdmin):
    form = MarkRecordForm

admin.site.register(Student)
admin.site.register(Mark, MarkAdmin)
admin.site.register(Syllabus)
admin.site.register(Question)
admin.site.register(TeachingGroup)
admin.site.register(Sitting)
admin.site.register(Teacher)

reigster_list = [AcademicYear, Day, Period, Week, TTSlot, CalendaredPeriod, Lesson, Suspension]
for item in reigster_list:
    admin.site.register(item)