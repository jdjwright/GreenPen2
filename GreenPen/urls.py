"""GreenPen URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth.views import LogoutView, LoginView
from django.urls import path, include
from GreenPen.autocomplete import *
from GreenPen.views import *
from GreenPen.dash_apps.finished_apps import TeacherDashboard, StudentDashboard

urlpatterns = [
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('', splash, name='splash'),
    path('admin/', admin.site.urls),
    path('syllabus/json/<int:syllabus_pk>', send_syllabus_children, name='ajax-syllabus-children'),
    path('syllabus/json/', load_syllabus_points, name='json_syllabus_points'),
    path('syllabus/json/exam/<int:exam_pk>/', load_syllabus_points_exam, name='load_syllabus_points_exam'),
    path('students/', StudentList.as_view(), name='student_list'),
    path('uploadstudents', import_students, name='import_students'),
    path('uploadclasses', import_classes, name='import_classes'),
    path('uploadsyllabus', import_syllabus),
    path('uploadquestions', import_questions),
    path('uploadsittings', import_sittings),
    path('uploadmarks', import_marks),
    path('updateclasses', update_classes),
    path('updateassignments', update_assignments),
    path('student-autocomplete', StudentComplete.as_view(), name='student-autocomplete'),
    path('syllabus-autocomplete', SyllabusComplete.as_view(), name='syllabus-autocomplete'),
    path('mistake-autocomplete', MistakeAutoComplete.as_view(), name='mistake-autocomplete'),
    path('rating-records/<int:syllabus_pk>/<int:student_pk>', StudentAssessmentForPoint.as_view(), name='student-assessment-record'),
    path('exam', ExamListView.as_view(), name='exam-list'),
    path('exam/add', AddExam.as_view(), name='add-exam'),
    path('exam/add-google', AddGoogleExam.as_view(), name='add-google-exam'),
    path('exam/<int:exam>/edit', EditExamQsView.as_view(), name='edit-exam'),
    path('exam/<int:exam>/duplicate', duplicate_exam, name='duplicate-exam'),
    path('exam/<int:exam_pk>/new-sitting', new_sitting, name='new-sitting'),
    path('student/dashboard', student_dashboard, name='student-dashboard'),
    path('student/<int:student_pk>/exams',student_exam_view, name='student-exam-list'),
    path('student/exams', student_exam_entry, name='student-exam-list-entry'),
    path('bs', teacher_dashboard, name='bs-sample'),
    path('django_plotly_dash/', include('django_plotly_dash.urls')),
    path('sitting/<int:sitting_pk>/results', exam_result_view, name='exam-results'),
    path('sitting/<int:sitting_pk>/alpresults', alp_result_view, name='alp-exam-results'),
    path('sitting/<int:sitting_pk>/delete', confirm_delete_sitting, name='delete-sitting1'),
    path('sitting/<int:sitting_pk>/confirm_delete', delete_sitting, name='delete-sitting2'),
    path('sitting/<int:sitting_pk>/import_scores', import_sitting_scores, name='import_scores'),
    path('marks/<int:mark_pk>', input_mark, name='input_mark'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('login/', LoginView.as_view(), name='login'),
    path('auth/', include('social_django.urls', namespace='social')),
    path('rollover/1', year_rollover_part1, name='rollover1'),
    path('rollover/2', year_rollover_part2, name='rollover2'),
    path('timetable', timetable_splash, name='tt_splash'),
    path('timetable/<int:start_slot_pk>/<int:teacher_pk>', timetable_overview, name='tt_overview'),
    path('lesson/<int:lesson_pk>/<int:return_pk>', change_lesson, name='edit_lesson'),
    path('timetable/suspend', suspend_days, name='suspend_days'),
    path('mistake_json', load_mistake_children, name='mistake_json'),
    path('mistake_json/<int:mark_pk>', load_mistake_children, name='mistake_json_mark'),
  ]
