from django.test import TestCase
from GreenPen.models import Student, Teacher, Subject, TeachingGroup, Syllabus, Exam, Question, Mark, Sitting, StudentSyllabusAssessmentRecord
from django.contrib.auth.models import User
import datetime


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

        self.assertEqual(StudentSyllabusAssessmentRecord.objects.filter(student=skinner_student,
                         syllabus_point=q1.syllabus_points.all()[0]).count(), 1)

        # And ensure that the parents are recorded, too

        self.assertEqual(StudentSyllabusAssessmentRecord.objects.filter(student=skinner_student,
                                                                        syllabus_point=q1.syllabus_points.all()[
                                                                            0].parent).count(), 1)

    def test_mark_summary_records(self):
        bloggs_teacher, tubbs_teacher, skinner_student, chalke_student, potions, herbology, hb1 = set_up_class()
        q1, q2 = setUpQuestion()
        sitting, created = Sitting.objects.get_or_create(exam=q1.exam,
                                                         date=datetime.date.today()-datetime.timedelta(days=1))

        # needed to set with a date before today so that the refresh test will be later.

        m1_skinner, created = Mark.objects.get_or_create(student=skinner_student,
                                                         question=q1,
                                                         sitting=sitting,
                                                         score=3)  # 100 %

        self.assertEqual(StudentSyllabusAssessmentRecord.objects.get(student=skinner_student,
                                                                     syllabus_point=Syllabus.objects.get(text='first child'),
                                                                     most_recent=True).percentage,
                         100)

        # Check that the parent of this will include this in their percentage:

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

        # Now we'll create a new exam and sitting that re-sets the assessment record:

        exam2, created = Exam.objects.get_or_create(name='rest exam')
        sitting2, created = Sitting.objects.get_or_create(exam=exam2,
                                                          resets_ratings=True,
                                                          )
        sitting.students.add(Student.objects.get(pk=skinner_student.pk))

        q3, created = Question.objects.get_or_create(exam=exam2,
                                           number='1',
                                           order=1,
                                           max_score=4)
        q3.syllabus_points.add(Syllabus.objects.get(text='first child'))

        m3_skinner, created = Mark.objects.get_or_create(student=skinner_student,
                                                         question=q3,
                                                         sitting=sitting2,
                                                         score=4)  # 100%

        self.assertEqual(Syllabus.objects.
                         get(text='first child').
                         percent_correct(students=Student.objects.filter(pk=skinner_student.pk)),
                         100)  # The previous sitting should have re-set the work.

        self.assertEqual(Syllabus.objects.
                         get(text='first child').
                         percent_correct(students=Student.objects.filter(user__email__contains='school.com')),
                         71)  # skinner is 4/4 from q3 ONLY, chalke is 1/3 from q2 ONLY, so avg = 5/7 = 83%


        # Test that it works for sub-points:

        q4 = Question.objects.create(exam=exam2,
                                     order=2,
                                     number='2',
                                     max_score=5)
        q4.syllabus_points.add(Syllabus.objects.get(text='first grandchild'))

        m4_skinner, created = Mark.objects.get_or_create(student=skinner_student,
                                                         question=q4,
                                                         sitting=sitting2,
                                                         score=2)

        # Check working for grandchild:

        self.assertEqual(Syllabus.objects.get(text='first grandchild').
                         percent_correct(students=Student.objects.filter(pk=skinner_student.pk)),
                         40) # 2/5 = 40%

        # Check that this has included the parent too
        self.assertEqual(Syllabus.objects.get(text='first child').
                         percent_correct(students=Student.objects.filter(pk=skinner_student.pk)),
                         67)  # 4/4 + 2/5 = 6/9 = 67%

        # Just for fun, let's re-check that we can still reset scores with a new test:

        exam3 = Exam.objects.create(name='exam3')
        sitting3 = Sitting.objects.create(exam=exam3,
                                          date=datetime.date.today()+datetime.timedelta(days=1),
                                          resets_ratings=True)
        # This exam is one day ahead, so should become the only source of truth

        q5 = Question.objects.create(exam=exam3,
                                     max_score=10,
                                     number='1',
                                     order=1)
        q5.syllabus_points.add(Syllabus.objects.get(text='first grandchild'))

        m5, created = Mark.objects.get_or_create(student=skinner_student,
                                                 sitting=sitting3,
                                                 question=q5,
                                                 score=3)

        # Should only have re-set grandchildren:

        self.assertEqual(Syllabus.objects.get(text='first grandchild').
                         percent_correct(students=Student.objects.filter(pk=skinner_student.pk)),
                         30) # 3/10 = 30%

        # Should not have re-set the parent, so we should get:
        self.assertEqual(Syllabus.objects.get(text='first child').
                         percent_correct(students=Student.objects.filter(pk=skinner_student.pk)),
                         50)  # 4/4 + 3/10 = 7/14 = 50%


class StudentSyllabusAssessmentRecordTestCase(TestCase):

    def test_most_recent_upates(self):
        setUpSyllabus()

        # Start with creating a single record:
        student = Student.objects.create()
        exam = Exam.objects.create()
        q = Question.objects.create(max_score=3,
                                    order=1,
                                    number='1',
                                    exam=exam)

        q.syllabus_points.add(Syllabus.objects.get(text='first child'))
        sitting = Sitting.objects.create(exam=exam,
                                         date=datetime.date.today() - datetime.timedelta(days=10))
        mark = Mark.objects.create(student=student,
                                   question=q,
                                   sitting=sitting,
                                   score=1)

        # Should have been created and be most recent:
        record = StudentSyllabusAssessmentRecord.objects.get(student=student,
                                                             sitting=sitting,
                                                             syllabus_point=Syllabus.objects.get(text='first child'))
        # for debug:
        records = list(StudentSyllabusAssessmentRecord.objects.all())
        self.assertEqual(record.most_recent, True)

        # Now add a competitor from a day later:
        s2 = Sitting.objects.create(exam=exam,
                                    date=datetime.date.today())

        m2 = Mark.objects.create(student=student,
                                 question=q,
                                 sitting=s2,
                                 score=2)

        # Old record shuld no longer be most recent:
        old_record = StudentSyllabusAssessmentRecord.objects.get(student=student,
                                                             sitting=sitting,
                                                             syllabus_point=Syllabus.objects.get(text='first child'))
        self.assertEqual(old_record.most_recent, False)

        # Sitting of most recent should be s2:

        record = StudentSyllabusAssessmentRecord.objects.get(student=student,
                                                             sitting=s2,
                                                             syllabus_point=Syllabus.objects.get(text='first child'))
        self.assertEqual(record.sitting.date, s2.date)
        self.assertEqual(record.most_recent, True)

        # Add one more to be certain:

        s3 = Sitting.objects.create(exam=exam,
                                    date=datetime.date.today() + datetime.timedelta(days=10))
        m3 = Mark.objects.create(sitting=s3,
                                 question=q,
                                 student=student,
                                 score=3)

        # Check the old two are  no longer most recent
        oldest_record = StudentSyllabusAssessmentRecord.objects.get(student=student,
                                                                 sitting=sitting,
                                                                 syllabus_point=Syllabus.objects.get(
                                                                     text='first child'))
        self.assertEqual(oldest_record.most_recent, False)

        old_record = StudentSyllabusAssessmentRecord.objects.get(student=student,
                                                                 sitting=s2,
                                                                 syllabus_point=Syllabus.objects.get(
                                                                     text='first child'))
        self.assertEqual(old_record.most_recent, False)

        newest = StudentSyllabusAssessmentRecord.objects.get(student=student,
                                                                 sitting=s3,
                                                                 syllabus_point=Syllabus.objects.get(
                                                                     text='first child'))
        self.assertEqual(newest.most_recent, True)

    def test_add_sitting_when_newer_exist(self):
        """ This is necessary to check behaviour when importing exams or if students
        enter exam data after another exam."""
        student = Student.objects.create()

        # - Root
        #   - First child
        #     - First grandchild
        #     - Second grandchile
        #   - Second child
        #     - Third grandchild
        #     - Fourth grandchild

        r = Syllabus.objects.create(text='r')
        c1 = Syllabus.objects.create(parent=r, text='c1')
        g1 = Syllabus.objects.create(parent=c1, text='g1')
        g2 = Syllabus.objects.create(parent=c1, text='g2')
        c2 = Syllabus.objects.create(parent=r, text='c2')
        g3 = Syllabus.objects.create(parent=c2, text='g3')
        g4 = Syllabus.objects.create(parent=c2, text='g4')

        # Add a future exam and sitting:
        e1 = Exam.objects.create()
        s_future = Sitting.objects.create(date=datetime.date.today() + datetime.timedelta(days=1),
                                          exam=e1)
        s_today = Sitting.objects.create(exam=e1)

        q1 = Question.objects.create(exam=e1,
                                     order=1,
                                     number='1',
                                     max_score=5)
        q1.syllabus_points.add(g1)

        m1 = Mark.objects.create(student=student,
                                 question=q1,
                                 sitting=s_future,
                                 score=5)

        record = StudentSyllabusAssessmentRecord.objects.get(most_recent=True,
                                                             syllabus_point=g1,
                                                             student=student)

        self.assertEqual(record.rating, 5)

        # Now add a past exam:

        m2 = Mark.objects.create(student=student,
                                 question=q1,
                                 sitting=s_today,
                                 score=0)
        # Check that a new record has been created:
        self.assertEqual(StudentSyllabusAssessmentRecord.objects.filter(student=student,
                                                                        syllabus_point=g1).count(), 2)
        # refresh from db:
        record = StudentSyllabusAssessmentRecord.objects.get(most_recent=True,
                                                             syllabus_point=g1,
                                                             student=student)

        self.assertEqual(record.rating, 2.5)

        # We should also have one other assessment record:
        self.assertEqual(record.order, 2)

        older = StudentSyllabusAssessmentRecord.objects.get(syllabus_point=g1,
                                                            student=student,
                                                            order=1)
        self.assertEqual(older.rating, 0)



class CollectRatingsTestCase(TestCase):
    def test_ratings(self):
        student = Student.objects.create()

        # - Root
        #   - First child
        #     - First grandchild
        #     - Second grandchile
        #   - Second child
        #     - Third grandchild
        #     - Fourth grandchild

        r = Syllabus.objects.create(text='r')
        c1 = Syllabus.objects.create(parent=r, text='c1')
        g1 = Syllabus.objects.create(parent=c1, text='g1')
        g2 = Syllabus.objects.create(parent=c1, text='g2')
        c2 = Syllabus.objects.create(parent=r, text='c2')
        g3 = Syllabus.objects.create(parent=c2, text='g3')
        g4 = Syllabus.objects.create(parent=c2, text='g4')

        # Give a 3/5 rating for g1:

        exam1 = Exam.objects.create()
        q1 = Question.objects.create(exam=exam1,
                                     max_score=5,
                                     order=1,
                                     number='1')
        q1.syllabus_points.add(g1)

        sitting1 = Sitting.objects.create(exam=exam1)

        m1 = Mark.objects.create(student=student,
                                 sitting=sitting1,
                                 question=q1,
                                 score=3)
        #                              Attempted    Scored rting    0-1 1-2 2-3  3-4  4-5
        # - Root                         5             3     3       0    0   3   0    0
        #   - First child                5             3     3       0    0   2   0    0
        #     - First grandchild         5             3     3       0    0   1   0    0
        # all other levels do not exist

        # Get the student record:
        record = StudentSyllabusAssessmentRecord.objects.get(student=student,
                                                             syllabus_point=g1,
                                                             most_recent=True)

        # Check  rating is correct
        self.assertEqual(record.rating, 3)

        # Check totals are correct:

        self.assertEqual(record.correct_this_level, 3)
        self.assertEqual(record.attempted_this_level, 5)

        # Check rating for parent is correct:

        parent = StudentSyllabusAssessmentRecord.objects.get(student=student,
                                                             syllabus_point=c1,
                                                             sitting=sitting1)

        self.assertEqual(parent.correct_this_level, 0)
        self.assertEqual(parent.attempted_this_level, 0)
        self.assertEqual(parent.correct_plus_children, 3)
        self.assertEqual(parent.attempted_plus_children, 5)

        self.assertEqual(parent.children_3_4, 0)
        self.assertEqual(parent.children_0_1, 0)
        self.assertEqual(parent.children_1_2, 0)
        self.assertEqual(parent.children_2_3, 2)
        self.assertEqual(parent.children_4_5, 0)

        # And check rating for grandparent is correct:

        parent = StudentSyllabusAssessmentRecord.objects.get(student=student,
                                                             syllabus_point=r,
                                                             sitting=sitting1)
        self.assertEqual(parent.correct_this_level, 0)
        self.assertEqual(parent.attempted_this_level, 0)
        self.assertEqual(parent.correct_plus_children, 3)
        self.assertEqual(parent.attempted_plus_children, 5)

        self.assertEqual(parent.children_3_4, 0)
        self.assertEqual(parent.children_0_1, 0) # g2, c2, g3, g4
        self.assertEqual(parent.children_1_2, 0)
        self.assertEqual(parent.children_2_3, 3) # Parent and child
        self.assertEqual(parent.children_4_5, 0)

        # Add a second to the same:
        q2 = Question.objects.create(exam=exam1,
                                     max_score=5,
                                     order=2,
                                     number='2')
        q2.syllabus_points.add(g1)

        m2 = Mark.objects.create(student=student,
                                 sitting=sitting1,
                                 question=q2,
                                 score=4)

        #                              Attempted    Scored    0-1 1-2 2-3  3-4  4-5
        # - Root                         10            7       0    0   0   3    0
        #   - First child                10            7       0    0   0   2    0
        #     - First grandchild         10            7       0    0   0   1    0
        # Lower levels don't have records created yet.
        # Now, Q1=3/5, Q2 = 4/5, total = 7/10 = rating 3.5

        # Get the student record again (need to refresh database!)
        record = StudentSyllabusAssessmentRecord.objects.get(student=student,
                                                             syllabus_point=g1,
                                                             most_recent=True)

        # Check  rating is correct
        self.assertEqual(record.rating, 3.5)

        self.assertEqual(record.correct_this_level, 7)
        self.assertEqual(record.attempted_this_level, 10)
        self.assertEqual(record.correct_plus_children, 7)
        self.assertEqual(record.attempted_plus_children, 10)

        # Check rating for parent is correct:

        parent = StudentSyllabusAssessmentRecord.objects.get(student=student,
                                                             syllabus_point=c1,
                                                             sitting=sitting1)

        self.assertEqual(parent.correct_this_level, 0)
        self.assertEqual(parent.attempted_this_level, 0)
        self.assertEqual(parent.correct_plus_children, 7)
        self.assertEqual(parent.attempted_plus_children, 10)

        self.assertEqual(parent.children_3_4, 2)
        self.assertEqual(parent.children_0_1, 0)
        self.assertEqual(parent.children_1_2, 0)
        # Todo: remove debug statement
        records = list(StudentSyllabusAssessmentRecord.objects.all())
        self.assertEqual(parent.children_2_3, 0)
        self.assertEqual(parent.children_4_5, 0)

        # And check rating for grandparent is correct:

        parent = StudentSyllabusAssessmentRecord.objects.get(student=student,
                                                             syllabus_point=r,
                                                             sitting=sitting1)
        self.assertEqual(parent.children_3_4, 3) # Parent and child
        self.assertEqual(parent.children_0_1, 0)
        self.assertEqual(parent.children_1_2, 0)
        self.assertEqual(parent.children_2_3, 0)
        self.assertEqual(parent.children_4_5, 0)

        self.assertEqual(parent.correct_this_level, 0)
        self.assertEqual(parent.attempted_this_level, 0)
        self.assertEqual(parent.correct_plus_children, 7)
        self.assertEqual(parent.attempted_plus_children, 10)

        # Add in a different rating for grandchild2:
        q3 = Question.objects.create(exam=exam1,
                                     max_score=5,
                                     order=3,
                                     number='3')
        q3.syllabus_points.add(g2)

        m3 = Mark.objects.create(student=student,
                                 sitting=sitting1,
                                 question=q3,
                                 score=1) # Rating = 1

        #                              Attempted    Scored rtin   0-1 1-2 2-3  3-4  4-5
        # - Root                         15            8    2.7   1    1   2   1    0
        #   - First child                15            8    2.7   1    0   1   1    0
        #     - First grandchild         10            7    3.5   0    0   0   1    0
        #     - Second grandchile        5             1     1    1    0   0   0    0
        # All others do not exist yet

        record = StudentSyllabusAssessmentRecord.objects.get(student=student,
                                                             syllabus_point=g2,
                                                             most_recent=True)

        self.assertEqual(record.rating, 1)



        # Check rating for parent is correct:

        parent = StudentSyllabusAssessmentRecord.objects.get(student=student,
                                                             syllabus_point=c1,
                                                             sitting=sitting1)
        records = list(StudentSyllabusAssessmentRecord.objects.all())
        self.assertEqual(parent.children_3_4, 1)
        self.assertEqual(parent.children_0_1, 1)
        self.assertEqual(parent.children_1_2, 0)
        self.assertEqual(parent.children_2_3, 1)
        self.assertEqual(parent.children_4_5, 0)

        # Parent rating should now be 1/5 + 3/5 + 4/5 = 8/15 = 2.66666666
        self.assertEqual(round(parent.rating,1), 2.7)

        # And check rating for grandparent is correct:

        parent = StudentSyllabusAssessmentRecord.objects.get(student=student,
                                                             syllabus_point=r,
                                                             sitting=sitting1)
        self.assertEqual(parent.children_3_4, 1)  # Parent and child
        self.assertEqual(parent.children_0_1, 1)
        self.assertEqual(parent.children_1_2, 0)
        self.assertEqual(parent.children_2_3, 2)
        self.assertEqual(parent.children_4_5, 0)

        # Let's try adding on on the parent level:

        q4 = Question.objects.create(number='3',
                                     order=3,
                                     exam=exam1,
                                     max_score=12)

        q4.syllabus_points.add(c1)

        m4 = Mark.objects.create(student=student,
                                 question=q4,
                                 score=3,
                                 sitting=sitting1)


        #  Child records should be unchanged:
        record = StudentSyllabusAssessmentRecord.objects.get(student=student,
                                                             syllabus_point=g2,
                                                             most_recent=True)

        self.assertEqual(record.rating, 1)

        # Record for this level should change:
        record = StudentSyllabusAssessmentRecord.objects.get(student=student,
                                                             syllabus_point=c1,
                                                             most_recent=True)


        # Percentage should be ating should now be 1/5 + 3/5 + 4/5 + 3/12= 11/27 = 41.%, rating 2.04
        # Rating should be calculated using self and children:

        self.assertEqual(round(record.rating, 1), 2.1) # Weird python rounding problems somewhere!
        self.assertEqual(record.percentage, 41.0)


class SyllabusReportingTestCase(TestCase):
    def test_reports(self):
        s1 = Student.objects.create()
        s2 = Student.objects.create()

        # - Root
        #   - First child
        #     - First grandchild
        #     - Second grandchild
        #   - Second child
        #     - Third grandchild
        #     - Fourth grandchild

        r = Syllabus.objects.create(text='r')
        c1 = Syllabus.objects.create(parent=r, text='c1')
        g1 = Syllabus.objects.create(parent=c1, text='g1')
        g2 = Syllabus.objects.create(parent=c1, text='g2')
        c2 = Syllabus.objects.create(parent=r, text='c2')
        g3 = Syllabus.objects.create(parent=c2, text='g3')
        g4 = Syllabus.objects.create(parent=c2, text='g4')

        # Give a 3/5 rating for g1:

        exam1 = Exam.objects.create()
        q1 = Question.objects.create(exam=exam1,
                                     max_score=5,
                                     order=1,
                                     number='1')
        q1.syllabus_points.add(g1)

        sitting1 = Sitting.objects.create(exam=exam1)

        m1_s1 = Mark.objects.create(student=s1,
                                 sitting=sitting1,
                                 question=q1,
                                 score=3)
        m1_s2 = Mark.objects.create(student=s2,
                                 sitting=sitting1,
                                 question=q1,
                                 score=5)

        #                              Att   Corr    Rtg     0-1  1-2  2-3  3-4  4-5
        # - Root                       10     8       4      0    0    3    0    3
        #   - First child              10     8       4      0    0    2    0    2
        #     - First grandchild       10     8       5      0    0    1    0    1
        #     - Second grandchild      n/a
        #   - Second child
        #     - Third grandchild
        #     - Fourth grandchild

        stats = g1.cohort_stats(Student.objects.all())

        # Test G1 reports corretly:
        self.assertEqual(g1.cohort_stats(Student.objects.all())['percentage'], 80)
        self.assertEqual(g1.cohort_stats(Student.objects.all())['rating'], 4.0)
        self.assertEqual(g1.cohort_stats(Student.objects.all())['children_0_1'], 0)
        self.assertEqual(g1.cohort_stats(Student.objects.all())['children_1_2'], 0)
        self.assertEqual(g1.cohort_stats(Student.objects.all())['children_2_3'], 1)
        self.assertEqual(g1.cohort_stats(Student.objects.all())['children_3_4'], 0)
        self.assertEqual(g1.cohort_stats(Student.objects.all())['children_4_5'], 1)

        #Check that parents are reported correctly:
        stats = c1.cohort_stats(Student.objects.all())
        self.assertEqual(c1.cohort_stats(Student.objects.all())['percentage'], 80)
        self.assertEqual(c1.cohort_stats(Student.objects.all())['rating'], 4.0)
        self.assertEqual(c1.cohort_stats(Student.objects.all())['children_0_1'], 0)
        self.assertEqual(c1.cohort_stats(Student.objects.all())['children_1_2'], 0)
        self.assertEqual(c1.cohort_stats(Student.objects.all())['children_2_3'], 2)
        self.assertEqual(c1.cohort_stats(Student.objects.all())['children_3_4'], 0)
        self.assertEqual(c1.cohort_stats(Student.objects.all())['children_4_5'], 2)

        # Check that grandparents are reported correctly:
        # NB: This will be 2 for each, since there is one rating at child and one at
        # grandchild.

        self.assertEqual(r.cohort_stats(Student.objects.all())['percentage'], 80)
        self.assertEqual(r.cohort_stats(Student.objects.all())['rating'], 4.0)
        self.assertEqual(r.cohort_stats(Student.objects.all())['children_0_1'], 0)
        self.assertEqual(r.cohort_stats(Student.objects.all())['children_1_2'], 0)
        self.assertEqual(r.cohort_stats(Student.objects.all())['children_2_3'], 3)
        self.assertEqual(r.cohort_stats(Student.objects.all())['children_3_4'], 0)
        self.assertEqual(r.cohort_stats(Student.objects.all())['children_4_5'], 3)

        # Create a different score on a different group:
        q2 = Question.objects.create(exam=exam1,
                                     max_score=9,
                                     order=2,
                                     number='2') #
        q2.syllabus_points.add(g3)

        m2_s1 = Mark.objects.create(student=s1,
                                    sitting=sitting1,
                                    question=q2,
                                    score=4) # 44%, 2.2 rating
        m2_s2 = Mark.objects.create(student=s2,
                                    sitting=sitting1,
                                    question=q2,
                                    score=1) # 11%, 0.6 rating

        #                              Att   Corr    Rtg     0-1  1-2  2-3  3-4  4-5
        # - Root                       28     13     2.31    3    0    5    0    3
        #   - First child              10     8       4      0    0    2    0    2
        #     - First grandchild       10     8       5      0    0    1    0    1
        #     - Second grandchild      n/a
        #   - Second child             18     5       1.3    2    0    2    0    0
        #     - Third grandchild       18     5       1.3    1    0    1    0    0
        #     - Fourth grandchild

        stats = g3.cohort_stats(Student.objects.all())
        self.assertEqual(stats['percentage'], 27.5)
        self.assertEqual(stats['rating'], 1.375)
        self.assertEqual(stats['children_0_1'], 1)
        self.assertEqual(stats['children_1_2'], 0)
        self.assertEqual(stats['children_2_3'], 1)
        self.assertEqual(stats['children_3_4'], 0)
        self.assertEqual(stats['children_4_5'], 0)

        # And for parent:
        stats = c2.cohort_stats(Student.objects.all())
        self.assertEqual(stats['percentage'], 27.5)
        self.assertEqual(stats['rating'], 1.375)
        self.assertEqual(stats['children_0_1'], 2)
        self.assertEqual(stats['children_1_2'], 0)
        self.assertEqual(stats['children_2_3'], 2)
        self.assertEqual(stats['children_3_4'], 0)
        self.assertEqual(stats['children_4_5'], 0)

        # And for root:

        stats = r.cohort_stats(Student.objects.all())
        self.assertEqual(stats['percentage'], 46.5) #13/28
        self.assertEqual(stats['rating'], 2.325)
        self.assertEqual(stats['children_0_1'], 2)
        self.assertEqual(stats['children_1_2'], 0)
        self.assertEqual(stats['children_2_3'], 6)
        self.assertEqual(stats['children_3_4'], 0)
        self.assertEqual(stats['children_4_5'], 2)

        # Now test for a new assessment

        e2 = Exam.objects.create()
        q3 = Question.objects.create(exam=e2,
                                     max_score=4,
                                     order=1,
                                     number=1)
        q3.syllabus_points.add(g4)
        sitting = Sitting.objects.create(exam=e2,
                                         date=datetime.date.today() + datetime.timedelta(days=1))

        m3_s1 = Mark.objects.create(question=q3,
                                    student=s1,
                                    score=3,
                                    sitting=sitting) # 75% 3.5 rating

        stats = g4.cohort_stats(Student.objects.all())
        self.assertEqual(stats['percentage'], 75)
        self.assertEqual(stats['rating'], 3.75)
        self.assertEqual(stats['children_0_1'], 0)
        self.assertEqual(stats['children_1_2'], 0)
        self.assertEqual(stats['children_2_3'], 0)
        self.assertEqual(stats['children_3_4'], 1)
        self.assertEqual(stats['children_4_5'], 0)

        # Now test for a new assessment

        e4 = Exam.objects.create()
        q4 = Question.objects.create(exam=e4,
                                     max_score=4,
                                     order=1,
                                     number=1)
        q4.syllabus_points.add(g4)
        sitting = Sitting.objects.create(exam=e4,
                                         date=datetime.date.today() + datetime.timedelta(days=2))

        m3_s1 = Mark.objects.create(question=q4,
                                    student=s1,
                                    score=4,
                                    sitting=sitting)  # 100% 5 rating

        stats = g4.cohort_stats(Student.objects.all())
        self.assertEqual(stats['percentage'], 88)
        self.assertEqual(stats['rating'], 4.4)
        self.assertEqual(stats['children_0_1'], 0)
        self.assertEqual(stats['children_1_2'], 0)
        self.assertEqual(stats['children_2_3'], 0)
        self.assertEqual(stats['children_3_4'], 0)
        self.assertEqual(stats['children_4_5'], 1)

