from GreenPen.models import *
from GreenPen.settings import CURRENT_ACADEMIC_YEAR
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
            teachinggroup, created = TeachingGroup.objects.get_or_create(pk=row[4], defaults={'name': row[0],
                                                                                              'subject': row[5],
                                                                                              'archived': row[1],
                                                                                              'year_taught': row[6]})
            teacher_user, created = User.objects.get_or_create(email=row[2], defaults={'username': row[2],
                                                                                       'first_name': 'Unknown',
                                                                                       'last_name': 'Teacher'})
            teacher_user.groups.add(teacher_auth_group)
            teacher, created = Teacher.objects.get_or_create(user=teacher_user)
            teachinggroup.teachers.add(teacher)
            student, created = Student.objects.get_or_create(student_id=row[3])
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
                                                                       'exam': exam,
                                                                       'group__pk': row[2]})
            sitting.date = row[3]
            sitting.exam = exam
            sitting.group = TeachingGroup.objects.get(pk=row[2])
            sitting.save()

def import_marks_from_csv(path):
    with open(path, newline='') as csvfile:
        qs = csv.reader(csvfile, delimiter=',', quotechar='"')
        # Skip headers
        next(qs, None)

        for row in qs:
            print('Adding ' + str(row))
            try:
                float(row[2])
            except ValueError:
                continue
            try:
                mark, created = Mark.objects.get_or_create(question_id=row[0],
                                                       student=Student.objects.get(student_id=row[1]),
                                                       sitting_id=row[3])
            except:
                print('Failed above' + str(row))
            if mark.score is None:
                mark.score = row[2]
                mark.student_notes = row[4]
                mark.save()


def update_groups(path):
    """
    This updates group information only from the classgorup csv file
    :param path: File path to csv
    :return: nothing
    """

    with open(path, newline='') as csvfile:
        classes = csv.reader(csvfile, delimiter=',', quotechar='"')
        # Skip headers
        next(classes, None)
        teacher_auth_group, created = Group.objects.get_or_create(name='Teachers')
        for row in classes:
            print('Adding ' + row[0])
            teachinggroup, created = TeachingGroup.objects.get_or_create(pk=row[4])
            teachinggroup.name = row[0]
            subject = Syllabus.objects.get(pk=row[5])
            teachinggroup.syllabus = subject
            if row[1] == 'TRUE':
                teachinggroup.archived = True
            teachinggroup.year_taught = row[6]
            teachinggroup.save()
            teacher_user, created = User.objects.get_or_create(email=row[2], defaults={'username': row[2],
                                                                                       'first_name': 'Unknown',
                                                                                       'last_name': 'Teacher'})
            teacher_user.groups.add(teacher_auth_group)
            teacher, created = Teacher.objects.get_or_create(user=teacher_user)
            teachinggroup.teachers.add(teacher)

def update_group_assignments(path):
    with open(path, newline='') as csvfile:
        classes = csv.reader(csvfile, delimiter=',', quotechar='"')
        # Skip headers
        next(classes, None)
        teacher_auth_group, created = Group.objects.get_or_create(name='Teachers')
        for row in classes:
            print('Adding ' + row[0])
            teachinggroup = TeachingGroup.objects.get(pk=row[4])
            teachinggroup.students.add(Student.objects.get(student_id=row[3]))

def import_groups_from_sims(path):
    with open(path, newline='') as csvfile:
        students = csv.reader(csvfile, delimiter=',', quotechar='"')
        # Skip headers
        next(students, None)
        teacher_auth_group, created = Group.objects.get_or_create(name='Teachers')
        current_group_name = ''
        current_group = ''
        for row in students:
            if current_group_name != row[0]:
                # Only create a group and update a teacher once
                current_group_name = row[0]
                current_group, created = TeachingGroup.objects.get_or_create(name=current_group_name,
                                                                    year_taught=CURRENT_ACADEMIC_YEAR + 1)

                teacher, created = Teacher.objects.get_or_create(staff_code=row[9])
                current_group.teachers.add(teacher)
                current_group.save()

            # Now we add the students:
            student, created = Student.objects.get_or_create(student_id=row[15])
            student.tutor_group = row[12]
            student.year_group = row[16]
            student.user, created = User.objects.get_or_create(username=row[15])
            student.user.first_name = row[11]
            student.user.last_name = row[10]
            student.user.email = row[14]
            student.save()
            student.user.save()
            current_group.students.add(student)
            print("Added " + str(student))
