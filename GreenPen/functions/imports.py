from GreenPen.models import Student, TeachingGroup, Teacher
from django.contrib.auth.models import User
import csv


def import_students_from_csv(path):
    with open(path, newline='') as csvfile:
        students = csv.reader(csvfile, delimiter=',', quotechar='"')
        # Skip headers
        next(students, None)
        for row in students:
            print('Creating student ' + row[0] + " " + row[1])
            user, created = User.objects.get_or_create(username=row[3])
            user.email = row[2]
            user.first_name = row[0]
            user.last_name = row[1]
            user.save()
            student, created = Student.objects.get_or_create(user=user)
            student.year = row[5]
            student.student_id = row[4]
            student.save()


def import_classgroups_from_csv(path):
    with open(path, newline='') as csvfile:
        classes = csv.reader(csvfile, delimiter=',', quotechar='"')
        # Skip headers
        next(classes, None)
        for row in classes:
            print('Adding ' + row[2])
            current_name = row[0]
            teachinggroup, created = TeachingGroup.objects.get_or_create(name=row[0])
            teacher_user, created = User.objects.get_or_create(email=row[1], defaults={'username': row[1]})
            teacher, created = Teacher.objects.get_or_create(user=teacher_user)
            teachinggroup.teachers.add(teacher)
            student = Student.objects.get(student_id=row[2])
            teachinggroup.students.add(student)