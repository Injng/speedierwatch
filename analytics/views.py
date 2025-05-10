from django.shortcuts import render
from django.db.models import Avg, Count, Min, Max, StdDev
from study.models import QuizResponse
from scipy import stats


def statistics_view(request):
    total_responses = QuizResponse.objects.count()
    average_score = QuizResponse.objects.aggregate(Avg("score"))["score__avg"]
    min_score = QuizResponse.objects.aggregate(Min("score"))["score__min"]
    max_score = QuizResponse.objects.aggregate(Max("score"))["score__max"]

    responses_by_treatment_group = (
        QuizResponse.objects.values("participant__treatment_group")
        .annotate(
            count=Count("id"),
            avg_score=Avg("score"),
            min_score=Min("score"),
            max_score=Max("score"),
            std_dev_score=StdDev("score"),
        )
        .order_by("participant__treatment_group")
    )

    group1_scores = QuizResponse.objects.filter(
        participant__treatment_group=1
    ).values_list("score", flat=True)
    group2_scores = QuizResponse.objects.filter(
        participant__treatment_group=2
    ).values_list("score", flat=True)

    ttest_result = None
    confidence_interval = None
    p_value = None
    t_statistic = None
    if len(group1_scores) >= 2 and len(group2_scores) >= 2:
        ttest_result = stats.ttest_ind(
            group1_scores, group2_scores, equal_var=False, alternative="greater"
        )
        t_statistic = ttest_result.statistic
        p_value = ttest_result.pvalue
        ci_result = ttest_result.confidence_interval(confidence_level=0.95)
        confidence_interval = (ci_result.low, ci_result.high)

    context = {
        "total_responses": total_responses,
        "average_score": average_score if average_score is not None else 0,
        "min_score": min_score if min_score is not None else 0,
        "max_score": max_score if max_score is not None else 0,
        "responses_by_treatment_group": responses_by_treatment_group,
        "t_statistic": t_statistic,
        "p_value": p_value,
        "confidence_interval": confidence_interval,
        "alpha": 0.05,
        "group1_count": len(group1_scores),
        "group2_count": len(group2_scores),
    }
    return render(request, "analytics/statistics.html", context)
