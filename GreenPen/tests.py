from django.test import TestCase
from GreenPen.models import Student, Teacher, Subject, TeachingGroup, Syllabus, Exam, Question, Mark, Sitting, StudentSyllabusAssessmentRecord
from django.contrib.auth.models import User


class StudentTestCase(TestCase):
    def setUp(self):
        bloggs_user = User.objects.create(first_name="Joe",
                                          last_name="Bloggs",
                                          email='joe@school.com',
                                          username='joe@school.com')

        Student.objects.create(user=bloggs_user,
                               tutor_group='10Y',
                               year_group=10)

        tubbs_user = User.objects.create(first_name="Timmy",
                                         last_name="Tubbs",
                                         email='tubbs@school.com',
                                         username='tubbs@school.com')

        Student.objects.create(user=tubbs_user,
                               tutor_group='10X',
                               year_group=10)

    def test_student_defult_str(self):
        """Students are printed with full name"""
        joe_bloggs = Student.objects.get(user__email='joe@school.com')
        timmy_tubbs = Student.objects.get(user__email='tubbs@school.com')
        self.assertEqual(str(joe_bloggs), 'Joe Bloggs 10Y')
        self.assertEqual(str(timmy_tubbs), 'Timmy Tubbs 10X')


class TeacherTestCase(TestCase):
    def setUp(self):
        bloggs_user = User.objects.create(first_name="Joe",
                                          last_name="Bloggs",
                                          email='joe@school.com',
                                          username='joe@school.com')

        Teacher.objects.create(user=bloggs_user,
                               staff_code='JBL',
                               title='Mrs')

        tubbs_user = User.objects.create(first_name="Timmy",
                                         last_name="Tubbs",
                                         email='tubbs@school.com',
                                         username='tubbs@school.com')

        Teacher.objects.create(user=tubbs_user,
                               staff_code='TTB',
                               title='Mr')

    def test_teacher_defalt_str(self):
        """Students are printed with full name"""
        joe_bloggs = Teacher.objects.get(user__email='joe@school.com')
        timmy_tubbs = Teacher.objects.get(user__email='tubbs@school.com')
        self.assertEqual(str(joe_bloggs), 'Mrs Joe Bloggs (JBL)')
        self.assertEqual(str(timmy_tubbs), 'Mr Timmy Tubbs (TTB)')


class SubjectTestCase(TestCase):
    def setUp(self):
        set_up_class()

    def test_hods_reporting(self):
        ''' Joe Bloggs is head of Herbology '''
        herbology = Subject.objects.get(name='Herbology')
        self.assertQuerysetEqual(herbology.HoDs.order_by('pk').all(),
                                 map(repr, Teacher.objects.order_by('pk').filter(user__username="joe@school.com")))

        # They are join heads of Potions
        potions = Subject.objects.get(name='Potions')
        self.assertQuerysetEqual(potions.HoDs.order_by('pk').all(),
                                 map(repr, Teacher.objects.order_by('pk').all()))

    def test_student_list(self):
        teaching_group = TeachingGroup.objects.get(name='10A/Hb1')
        student = Student.objects.filter(user__username='chalke@school.com')

        self.assertQuerysetEqual(teaching_group.students.all(), map(repr, student))

    def test_teacher_list(self):
        teaching_group = TeachingGroup.objects.get(name='10A/Hb1')
        teacher = Teacher.objects.filter(user__username='joe@school.com')
        self.assertQuerysetEqual(teaching_group.teachers.all(), map(repr, teacher))

    def test_correct_student_lists(self):
        # For testing that HoDs can see students:

        # HOD
        hod_user = User.objects.create(username='hod',
                                       first_name='hod',
                                       last_name='hod')
        hod = Teacher.objects.create(user=hod_user,
                                     staff_code='HOD',
                                     title='Mrs')
        # Teacher
        teacher_user = User.objects.create(username='teacher',
                                           first_name='teacher',
                                           last_name='teacher')
        teacher = Teacher.objects.create(user=teacher_user,
                                         staff_code='TEA',
                                         title='Mr')

        subject = Subject.objects.create(name='charms')
        subject.HoDs.add(hod)
        teaching_group = TeachingGroup.objects.create(name='11Ch/Ax', subject=subject)
        teaching_group.teachers.add(teacher)

        # Create some students
        s1_user = User.objects.create(username='s1', first_name='s1', last_name='s1')
        s1 = Student.objects.create(user=s1_user, tutor_group='10B', year_group=10)

        # Assign to the class
        teaching_group.students.add(s1)

        # Teacher should see them as teacher
        self.assertQuerysetEqual(teacher.taught_students().all(), map(repr, Student.objects.filter(user=s1_user)))
        # HOD should also see them
        self.assertQuerysetEqual(hod.taught_students().all(), map(repr, Student.objects.filter(user=s1_user)))

    def test_syllabus_printed(self):
        setUpSyllabus()
        hb1 = TeachingGroup.objects.get(name='10A/Hb1')
        hb1.syllabus = Syllabus.objects.get(text='root')

        self.assertEqual(str(hb1.syllabus), '1: root')
        self.assertQuerysetEqual(hb1.syllabus.get_descendants(include_self=True),
                                 map(repr, Syllabus.objects.get(text='root').get_descendants(include_self=True)))


def set_up_class():
    bloggs1_user, created = User.objects.get_or_create(first_name="Joe",
                                                       last_name="Bloggs",
                                                       email='joe@school.com',
                                                       username='joe@school.com')

    bloggs_teacher, created = Teacher.objects.get_or_create(user=bloggs1_user,
                                                            staff_code='JBL',
                                                            title='Mrs')

    tubbs1_user, created = User.objects.get_or_create(first_name="Timmy",
                                                      last_name="Tubbs",
                                                      email='tubbs@school.com',
                                                      username='tubbs@school.com')

    tubbs_teacher, created = Teacher.objects.get_or_create(user=tubbs1_user,
                                                           staff_code='TTB',
                                                           title='Mr')

    student1_user, created = User.objects.get_or_create(first_name="Simon",
                                                        last_name="Skinner",
                                                        email='skinner@school.com',
                                                        username='skinner@school.com')

    skinner_student, created = Student.objects.get_or_create(user=student1_user,
                                                             tutor_group='10Y',
                                                             year_group=10)

    student2_user, created = User.objects.get_or_create(first_name="Sarah",
                                                        last_name="Chalke",
                                                        email='chalke@school.com',
                                                        username='chalke@school.com')

    chalke_student, created = Student.objects.get_or_create(user=student2_user,
                                                            tutor_group='10X',
                                                            year_group=10)

    herbology, created = Subject.objects.get_or_create(name='Herbology')
    herbology.HoDs.add(bloggs_teacher)

    potions, created = Subject.objects.get_or_create(name='Potions')
    potions.HoDs.add(bloggs_teacher, tubbs_teacher)

    hb1, created = TeachingGroup.objects.get_or_create(name='10A/Hb1',
                                                       subject=herbology,
                                                       )
    hb1.teachers.add(bloggs_teacher)
    hb1.students.add(chalke_student)

    return bloggs_teacher, tubbs_teacher, skinner_student, chalke_student, potions, herbology, hb1


class SyllabusTestCase(TestCase):

    def setUp(self):
        setUpSyllabus()

    def test_str(self):
        root_1_2 = Syllabus.objects.get(text='second grandchild')
        self.assertEqual(str(root_1_2), '1.1.2: second grandchild')



def setUpSyllabus():
    root, created = Syllabus.objects.get_or_create(text='root',
                                                   identifier='1')
    root_1, created = Syllabus.objects.get_or_create(text='first child',
                                                     parent=root,
                                                     identifier='1')
    root_2, created = Syllabus.objects.get_or_create(text='second child',
                                                     parent=root,
                                                     identifier='2')
    root_1_1, created = Syllabus.objects.get_or_create(text='first grandchild',
                                                       parent=root_1,
                                                       identifier='1')
    root_1_2, created = Syllabus.objects.get_or_create(text='second grandchild',
                                                       parent=root_1,
                                                       identifier='2')

    return root


def setUpExam():
    exam, created = Exam.objects.get_or_create(name='exam 1',
                                               syllabus=setUpSyllabus())
    return exam


class ExamTestCase(TestCase):
    def test_str(self):
        exam = setUpExam()
        self.assertEqual(str(exam), 'exam 1')

    def test_max_score(self):
        exam = setUpExam()
        q1, q2 = setUpQuestion()

        self.assertEqual(exam.total_score(), 5)


def setUpQuestion():
    exam = setUpExam()
    setUpSyllabus()

    q1, created = Question.objects.get_or_create(exam=exam,
                                                 order=1,
                                                 number='1a',
                                                 max_score=3)
    q1.syllabus_points.add(Syllabus.objects.get(text='first child'))
    q2, created = Question.objects.get_or_create(exam=exam,
                                                 order=2,
                                                 number='1b',
                                                 max_score=2)
    q2.syllabus_points.add(Syllabus.objects.get(text='second child'))

    return q1, q2


class QuestionTestCase(TestCase):
    def test_ordering(self):
        q1, q2 = setUpQuestion()
        q3 = Question.objects.create(exam=q1.exam,
                                     order=1.4,
                                     number='1ai',
                                     max_score=1)

        self.assertQuerysetEqual(Question.objects.filter(exam=q1.exam),
                                 map(repr, Question.objects.filter(exam=q1.exam).order_by('order')))


class SittingTestCase(TestCase):
    def test_students_marks_created(self):
        sitting = setUpSitting()
        bloggs_teacher, tubbs_teacher, skinner_student, chalke_student, potions, herbology, hb1 = set_up_class()
        sitting.students.add(skinner_student, chalke_student)
        # The setUpQuestions should have added two questions to the test.
        self.assertEqual(Mark.objects.filter(student=skinner_student).count(), 2)

        # Now check that adding a q to exam adds it to the students

    def test_adding_q_adds_mark(self):
        sitting = setUpSitting()
        bloggs_teacher, tubbs_teacher, skinner_student, chalke_student, potions, herbology, hb1 = set_up_class()
        sitting.students.add(skinner_student, chalke_student)
        self.assertEqual(Mark.objects.filter(student=skinner_student).count(), 2)

        # Now add a question
        q3 = Question.objects.create(exam=sitting.exam,
                                     order=4,
                                     number='2',
                                     max_score=5)
        self.assertEqual(Mark.objects.filter(student=skinner_student).count(), 3)


def setUpSitting():
    bloggs_teacher, tubbs_teacher, skinner_student, chalke_student, potions, herbology, hb1 = set_up_class()
    q1, q2 = setUpQuestion()
    sitting, created = Sitting.objects.get_or_create(exam=q1.exam)
    return sitting


class StudentSyllabusPercentTestCase(TestCase):
    def test_records_created(self):
        """ Ensure that a StudentSyllabusAssessmentRecord record is created on mark save."""
        bloggs_teacher, tubbs_teacher, skinner_student, chalke_student, potions, herbology, hb1 = set_up_class()
        q1, q2 = setUpQuestion()
        sitting, created = Sitting.objects.get_or_create(exam=q1.exam)
        self.assertEqual(StudentSyllabusAssessmentRecord.objects.all().count(), 0)

        # Start simple, with a test of whether it works with top-level marks
        m1_skinner, created = Mark.objects.get_or_create(student=skinner_student,
                                                         question=q1,
                                                         sitting=sitting,
                                                         score=3)  # 100 %

        self.assertEqual(StudentSyllabusAssessmentRecord.objects.all().count(), 1)

    def test_percentages_correctly_calculated(self):
        bloggs_teacher, tubbs_teacher, skinner_student, chalke_student, potions, herbology, hb1 = set_up_class()
        q1, q2 = setUpQuestion()
        sitting, created = Sitting.objects.get_or_create(exam=q1.exam)
        m1_skinner, created = Mark.objects.get_or_create(student=skinner_student,
                                                         question=q1,
                                                         sitting=sitting,
                                                         score=3)  # 100 %

        self.assertEqual(StudentSyllabusAssessmentRecord.objects.get(student=skinner_student,
                                                                     syllabus_point=Syllabus.objects.get(text='first child')).percentage_correct,
                         100)
        m2_skinner, creatred = Mark.objects.get_or_create(student=skinner_student,
                                                          question=q2,
                                                          sitting=sitting,
                                                          score=1)  # 50%

        self.assertEqual(Syllabus.objects.
                         get(text='first child').
                         percent_correct(students=Student.objects.filter(pk=skinner_student.pk)),
                         100)

        self.assertEqual(Syllabus.objects.
                         get(text='second child').
                         percent_correct(students=Student.objects.filter(pk=skinner_student.pk)),
                         50)
        m1_chalke, created = Mark.objects.get_or_create(student=chalke_student,
                                                        question=q1,
                                                        sitting=sitting,
                                                        score=1)  # 33 %
        m2_chalke, creatred = Mark.objects.get_or_create(student=chalke_student,
                                                         question=q2,
                                                         sitting=sitting,
                                                         score=1)  # 50%

        self.assertEqual(Syllabus.objects.
                         get(text='first child').
                         percent_correct(students=Student.objects.filter(user__email__contains='school.com')),
                         67)  # student 1 = 3/3, student 2 = 1/3, avg = 2/3 = 67%

        self.assertEqual(Syllabus.objects.
                         get(text='second child').
                         percent_correct(students=Student.objects.filter(user__email__contains='school.com')),
                         50)  # student 1 = 1/2, student 2 = 1/1, avg = 1/2 = 50%.

        q3 = Question.objects.create(exam=q1.exam,
                                     max_score=4,
                                     number='5',
                                     order=5)
        q3.syllabus_points.add(Syllabus.objects.get(text='first grandchild'))

        m3_skinner, created = Mark.objects.get_or_create(student=skinner_student,
                                                         question=q3,
                                                         sitting=sitting,
                                                         score=3)  # 50%
        self.assertEqual(Syllabus.objects.
                         get(text='first child').
                         percent_correct(students=Student.objects.filter(user__email__contains='school.com')),
                         70)  # student 1 Q1 = 3/3, student 2 Q1 = 1/3, student 1 q3 = 3/4 -> Total = 7/10
