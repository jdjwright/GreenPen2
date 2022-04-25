from GreenPen.models import StudentSyllabusAssessmentRecord

def repair_most_recent_StudentSyllabusAssessmentRecord():
    """
    If somehow more than one studentsyllabusassessmentrecord is created
    and marked as 'most recent', this will repair it:
    """
    rs = StudentSyllabusAssessmentRecord.objects.filter(most_recent=True)
    for r in rs:
        others = rs.filter(student=r.student,
                           exam_assessment=r.exam_assessment,
                           teacher_assessment=r.teacher_assessment,
                           self_assessment=r.self_assessment,
                           syllabus_point=r.syllabus_point)
        count = others.count()
        if count > 1:
            try:
                o = others.order_by('order').last()
                others.update(most_recent=False)
                o.most_recent=True
                print("fixed for " + str(r.pk))
            except:
                raise ProcessLookupError
