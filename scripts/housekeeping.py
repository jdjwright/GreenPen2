from GreenPen.models import *


def detect_potential_exam_errors():
    """
    Used to detect exams which have questions that cover multiple
    exam syllabi.
    :return: queryset of exams
    """

    # Start with all our exams:
    exams = Exam.objects.all()

    # Get the subject levels
    subjects = Syllabus.objects.filter(level=2)

    # Iterate over each question, and each exam:

    problem_exams = []
    for exam in exams:

        problem_questions = []
        for question in exam.question_set.all():
            all_top_levels_ids = []
            # Find its syllabus points
            points = question.syllabus_points.all()
            for point in points:
                subject = point.get_ancestors().get(level=2)
                all_top_levels_ids.append(subject.pk)
            # Check for multiple subjects:
            parents = Syllabus.objects.filter(pk__in=all_top_levels_ids).distinct()

            if parents.count() > 1:
                problem_questions.append(question)

        if len(problem_questions):
            problem_exams.append(problem_questions)
    return problem_exams

