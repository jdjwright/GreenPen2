from GreenPen.models import Student,  Syllabus, StudentSyllabusAssessmentRecord

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