from django.shortcuts import render
from django.db.models import Avg, Count, Min, Max
from study.models import QuizResponse, Participant

def statistics_view(request):
    total_responses = QuizResponse.objects.count()
    average_score = QuizResponse.objects.aggregate(Avg('score'))['score__avg']
    min_score = QuizResponse.objects.aggregate(Min('score'))['score__min']
    max_score = QuizResponse.objects.aggregate(Max('score'))['score__max']

    responses_by_treatment_group = (
        QuizResponse.objects.values('participant__treatment_group')
        .annotate(
            count=Count('id'),
            avg_score=Avg('score'),
            min_score=Min('score'),
            max_score=Max('score')
        )
        .order_by('participant__treatment_group')
    )

    context = {
        'total_responses': total_responses,
        'average_score': average_score if average_score is not None else 0,
        'min_score': min_score if min_score is not None else 0,
        'max_score': max_score if max_score is not None else 0,
        'responses_by_treatment_group': responses_by_treatment_group,
    }
    return render(request, 'analytics/statistics.html', context)
