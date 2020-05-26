from GreenPen.models import *
from django.contrib.auth.models import User, Group
import csv


def import_students_from_csv(path):
    with open(path, newline='') as csvfile:
        students = csv.reader(csvfile, delimiter=',', quotechar='"')
        student_auth_group, created = Group.objects.get_or_create(name='Students')
        # Skip headers
        next(students, None)
        for row in students:
            print('Creating student ' + row[0] + " " + row[1])
            user, created = User.objects.get_or_create(username=row[3])
            user.email = row[2]
            user.first_name = row[0]
            user.last_name = row[1]
            user.save()
            user.groups.add(student_auth_group)
            student, created = Student.objects.get_or_create(user=user)
            student.year = row[5]
            student.student_id = row[4]
            student.save()


def import_classgroups_from_csv(path):
    with open(path, newline='') as csvfile:
        classes = csv.reader(csvfile, delimiter=',', quotechar='"')
        # Skip headers
        next(classes, None)
        teacher_auth_group, created = Group.objects.get_or_create(name='Teachers')
        for row in classes:
            print('Adding ' + row[0])
            teachinggroup, created = TeachingGroup.objects.get_or_create(name=row[0])
            teacher_user, created = User.objects.get_or_create(email=row[2], defaults={'username': row[2],
                                                                                       'first_name': 'Unknown',
                                                                                       'last_name': 'Teacher'})
            teacher_user.groups.add(teacher_auth_group)
            teacher, created = Teacher.objects.get_or_create(user=teacher_user)
            teachinggroup.teachers.add(teacher)
            student = Student.objects.get(student_id=row[3])
            teachinggroup.students.add(student)


def import_syllabus_from_csv(path):
    with open(path, newline='') as csvfile:
        points = csv.reader(csvfile, delimiter=',', quotechar='"')
        # Skip headers
        next(points, None)

        for row in points:
            print('Adding ' + row[1])
            if row[3]:
                parent = Syllabus.objects.get_or_create(id=row[3])
            pt, created = Syllabus.objects.get_or_create(id=row[0])
            pt.text = row[1]
            pt.identifier = row[2]
            if row[3]:
                pt.parent = Syllabus.objects.get_or_create(id=row[3])[0]
            pt.save()


def import_questions_from_csv(path):
    with open(path, newline='') as csvfile:
        qs = csv.reader(csvfile, delimiter=',', quotechar='"')
        # Skip headers
        next(qs, None)

        for row in qs:
            print('Adding ' + row[1])
            exam, created = Exam.objects.get_or_create(id=row[0],
                                                       defaults={'name': row[1]})

            question, created = Question.objects.get_or_create(id=row[2],
                                                               defaults={'number': row[3],
                                                                         'order': row[4],
                                                                         'max_score': row[6],
                                                                         'exam': exam})

            question.syllabus_points.add(Syllabus.objects.get_or_create(pk=row[5])[0])


def import_sittings_from_csv(path):
    with open(path, newline='') as csvfile:
        qs = csv.reader(csvfile, delimiter=',', quotechar='"')
        # Skip headers
        next(qs, None)

        for row in qs:
            print('Adding ' + row[1])
            exam, created = Exam.objects.get_or_create(pk=row[0])
            sitting, created = Sitting.objects.get_or_create(pk=row[1],
                                                             defaults={'date': row[3],
                                                                       'exam': exam})
            sitting.students.add(Student.objects.get_or_create(student_id=row[2])[0])


def import_marks_from_csv(path):
    with open(path, newline='') as csvfile:
        qs = csv.reader(csvfile, delimiter=',', quotechar='"')
        # Skip headers
        next(qs, None)

        for row in qs:
            print('Adding ' + row[1])
            try:
                float(row[2])
            except ValueError:
                continue
            mark, created = Mark.objects.get_or_create(question_id=row[0],
                                                       student=Student.objects.get(student_id=row[1]),
                                                       sitting_id=row[3])
            mark.score = row[2]
            mark.student_notes = row[4]
            mark.save()
