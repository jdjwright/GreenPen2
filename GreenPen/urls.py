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
from django.urls import path
from GreenPen.autocomplete import StudentComplete
from GreenPen.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('students/', StudentList.as_view(), name='student_list'),
    path('uploadstudents', import_students, name='import_students'),
    path('uploadclasses', import_classes, name='import_classes'),
    path('student-autocomplete/', StudentComplete.as_view(), name='student-autocomplete')
]
