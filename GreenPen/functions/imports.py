from GreenPen.models import *
from GreenPen.settings import CURRENT_ACADEMIC_YEAR
from django.contrib.auth.models import User, Group
import csv


def import_students_from_csv(path):
    student_list = []
    with open(path, newline='') as csvfile:
        students = csv.reader(csvfile, delimiter=',', quotechar='"')
        student_auth_group, created = Group.objects.get_or_create(name='Students')
        # Skip headers
        next(students, None)
        for row in students:
            print('Creating student ' + row[0] + " " + row[1])
            user, created = User.objects.get_or_create(username=row[2])
            user.email = row[2]
            user.first_name = row[0]
            user.last_name = row[1]
            user.save()
            user.groups.add(student_auth_group)
            student, created = Student.objects.get_or_create(student_id=row[3])
            student.year = row[5]
            student.user = user
            student.tutor_group = row[6]
            student.save()

            student_list.append(student)

        return student_list


def import_classgroups_from_csv(path):
    classgroup_pks = []

    # Start by removing all students from the classgroups
    tgs = TeachingGroup.objects.filter(archived=False)
    for tg in tgs:
        tg.students.clear()

    with open(path, newline='') as csvfile:
        classes = csv.reader(csvfile, delimiter=',', quotechar='"')
        # Skip headers
        next(classes, None)
        teacher_auth_group, created = Group.objects.get_or_create(name='Teachers')

        last_group_name = False

        for row in classes:
            print('Adding ' + row[0])

            if last_group_name != row[0]:
                subject, created = Subject.objects.get_or_create(name=row[1])
                teachinggroup, created = TeachingGroup.objects.filter(archived=False).get_or_create(name=row[0], defaults={
                    'subject': subject,
                    'year_taught': row[7]})
                teacher_user, created = User.objects.get_or_create(email=row[2], defaults={'username': row[2],
                                                                                           'first_name': row[3],
                                                                                           'last_name': row[4],
                                                                                           })
                teacher_user.groups.add(teacher_auth_group)
                teacher, created = Teacher.objects.get_or_create(user=teacher_user, defaults={'staff_code': row[5],
                                                                                              'title': row[6]})
                teachinggroup.teachers.add(teacher)
            student, created = Student.objects.get_or_create(student_id=row[8])
            if created:
                print("Error in student lists - caused by ID" + str(row[8]))
                student.delete()
                continue
            teachinggroup.students.add(student)
            classgroup_pks.append(teachinggroup.pk)

            last_group_name = row[0]

        return classgroup_pks


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
            teacher_user, created = User.objects.get_or_create(email=row[5], defaults={'username': row[5],
                                                                                       'first_name': row[3],
                                                                                       'last_name': row[2]})
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


def import_groups_from_sims(path, rollover=False):
    """
    Take a CSV file from SIMS that includes the class listing for
    all groups, and import the classes, students and teachers from
    that CSV.

    The CSV should be in the following format, with each column (indexe
    from 0):

    0. Group Name ** USED TO ID GROUP **
    1. Teacher Title (Ms, Mrs, Dr..)
    2. Teacher Surname
    3. Teacher forename
    4. Teacher initials
    5. Work email ** USED TO ID TEACHER **
    6. Student surname
    7. Student forename
    8. Student gender
    9. Student email address ** USED TO ID STUDENT **
    10. Student admission number
    11. Student tutor group
    12. Student year group
    13. Rollover group name
    14. Syallbus PK for that class

    This function WILL UPDATE STUDENTS details to what is supplied
    in the CSV (i.e. respect name changes etc),
    but WILL NOT UPDATE STAFF (since these are usually made more centrally).

    Also, this script will REMOVE ALL STUDENTS from each teachingroup
    before re-populating them. This is to keep accurate records as
    students are moved from one class to another.

    """

    # If this is part of a rollover exercise, add these to the next
    # academic year in the `year_taught` field.
    # Otherwise, add them to the current academic year.
    if rollover:
        academic_year_legacy = CURRENT_ACADEMIC_YEAR + 1
    else:
        academic_year_legacy = CURRENT_ACADEMIC_YEAR


    with open(path, newline='') as csvfile:
        students = csv.reader(csvfile, delimiter=',', quotechar='"')
        # Skip headers
        next(students, None)

        # Make sure auth groups exist for adding staff/ students
        teacher_auth_group, created = Group.objects.get_or_create(name='Teachers')
        student_auth_group, created = Group.objects.get_or_create(name='Students')
        academic_year = AcademicYear.objects.get(current=True)
        current_group_name = ''
        for row in students:
            if current_group_name != row[0]:

                # Only create a group and update a teacher once
                current_group_name = row[0]
                current_group, created = TeachingGroup.objects.get_or_create(sims_name=current_group_name,
                                                                             archived=False)

                # Set this group to the new academic year
                current_group.academic_year = academic_year
                current_group.year_taught = academic_year.order

                # Remove old members:
                current_group.students.clear()
                if created:
                    # We've added a new teaching group, so must set up its details:
                    current_group.name = row[0] + " " + current_group.academic_year.name
                    current_group.archived = False
                # Set the rollover name

                current_group.rollover_name = row[13]

                # Set the group syllabus
                if row[14]:
                    current_group.syllabus = Syllabus.objects.get(pk=row[14])
                current_group.save()

                teacher_user, created = User.objects.get_or_create(email=row[5], defaults={'username': row[5]})
                if created:
                    teacher_user.first_name = row[2]
                    teacher_user.last_name = row[3]
                    teacher.save()
                    teacher_auth_group.user_set.add(teacher_user)

                teacher, created = Teacher.objects.get_or_create(user=teacher_user)
                if created:
                    teacher.title = row[1]
                    teacher.staff_code = row[4]
                current_group.teachers.add(teacher)


            # Now we add the students:
            student_user, created = User.objects.get_or_create(email=row[9],
                                                               defaults={'username': row[10]})

            # No 'if created' here, as we want to update for next academic year's data:
            student_user.first_name = row[7]
            student_user.last_name = row[6]
            student_user.username = row[10]
            student_user.save()

            # Sometimes multiple student users have been created. In this instance,
            # we want to keep the pre-existing one so that we still have the
            # assessment data etc.
            try:
                student, created = Student.objects.get_or_create(student_id=row[10])
                student.user = student_user
                student.tutor_group = row[11]
                student.year_group = row[12]
                student.student_id = row[10]
                student.save()
            except IntegrityError:

                clash_user = User.objects.get(student=student)
                student.user = clash_user
                student.user.first_name = row[7]
                student.user.last_name = row[6]
                student.user.username = row[10]

                student_user.delete() # No point keeping the added user.
                student.save()
                print("WARNING: user clash found between {} and {}".format(clash_user, student_user))


            student_auth_group.user_set.add(student.user)
            current_group.students.add(student)

            print("Added " + str(student) + " to group " + str(current_group_name))


def import_syllabus_from_csv_new(path):
    with open(path, newline='') as csvfile:
        points = csv.reader(csvfile, delimiter=',', quotechar='"')
        # Skip headers
        next(points, None)
        home_point = Syllabus.objects.get(text='Garden International School')

        for row in points:
            print('Adding ' + row[9])
            course, created = Syllabus.objects.get_or_create(identifier=row[0],
                                                             defaults={'text': row[0],
                                                                      'parent': home_point,
                                                                      })
            topic, created = Syllabus.objects.get_or_create(parent=course, identifier=row[1],
                                                   defaults={'text': row[2]})
            sub_topic, created = Syllabus.objects.get_or_create(parent=topic, identifier=row[3],
                                                       defaults={'text': row[4]})
            if row[5]=="N/A":
                point, created = Syllabus.objects.get_or_create(parent=sub_topic, identifier=row[8],
                                                       defaults={'text': row[9],
                                                                 'tier': row[7]})
            else:
                sub_sub_topic, created = Syllabus.objects.get_or_create(parent=sub_topic, identifier=row[5],
                                                               defaults={'text': row[6]})
                point, created = Syllabus.objects.get_or_create(parent=sub_sub_topic, identifier=row[8],
                                                       defaults={'text': row[9],
                                                                 'tier': row[7]})


