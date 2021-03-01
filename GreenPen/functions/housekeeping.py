from GreenPen.models import Student,  Syllabus, StudentSyllabusAssessmentRecord, Mark, TeachingGroup, Sitting
from django.core.exceptions import ObjectDoesNotExist

def fix_student_assessment_record_order(students=Student.objects.all(), points=Syllabus.objects.all()):
    """
    Used to repair orders if they become corrupt
    :return:
    """

    i = 0
    total = students.count()
    for student in students:
        for point in points:
            competitors = StudentSyllabusAssessmentRecord.objects.filter(student=student,
                                                                         syllabus_point=point).\
                order_by('-order').distinct()
            i = competitors.count() + 1
            for competitor in competitors:
                competitor.order = i
                i = i - 1
                competitor.save()
        complete = round(i/total * 100,0)
        i += 1
        print(str(complete) + "% complete")


def fix_missing_student_ids():
    # delete students without a user:
    Student.objects.filter(user__isnull=True).delete()
    ss = Student.objects.filter(student_id__isnull=True)
    for s in ss:
        u = s.user
        clash_s = Student.objects.filter(user=u)
        if clash_s.count() == 1:
            continue
        if clash_s.count() > 2:
            print("Problems with " + str(u))
        s0 = clash_s[0]
        s1 = clash_s[1]

        m0 = Mark.objects.filter(student=s0)
        m1 = Mark.objects.filter(student=s1)

        if m0.count() == 0:
            s0.delete()

        elif m1.count() == 0:
            s1.delete()

        else:
            print("Both students have marks: " + str(u))


def fix_multiple_group_assignments():
    """
    1. Get a list of all the teaching groups with multiple names
    2. Pick the first one as the reporting group
    3. Re-assign all sittings to the reporting group.
    """
    completed_pks = []
    while True:
        tgs = TeachingGroup.objects.filter(linked_groups__isnull=False).exclude(pk__in=completed_pks)
        if not tgs.count():
            break

        tg = tgs[0]
        possible_pks = [tg.pk]
        completed_pks.append(tg.pk)
        tgs = tg.linked_groups.all()
        for t in tgs:
            completed_pks.append(t.pk)
            possible_pks.append(t.pk)
        try:
            master = tgs.get(use_for_exams=True)
        except (TeachingGroup.DoesNotExist, TeachingGroup.MultipleObjectsReturned):
            master = tgs[0]

        tgs.update(use_for_exams=False)
        master.use_for_exams = True
        master.save()
        # Now fix the assignments
        ss = Sitting.objects.filter(group__pk__in=possible_pks)
        ss.update(group=master)
        print(str(master))