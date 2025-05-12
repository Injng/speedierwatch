from django.shortcuts import render
from django.db.models import Avg, Count, Min, Max, StdDev
from study.models import QuizResponse
from scipy import stats
import numpy as np


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

        # Calculate confidence interval using scipy.stats.t.interval
        n1 = len(group1_scores)
        n2 = len(group2_scores)
        mean1 = np.mean(group1_scores)
        mean2 = np.mean(group2_scores)
        var1 = np.var(group1_scores, ddof=1)
        var2 = np.var(group2_scores, ddof=1)

        # Degrees of freedom using Welch-Satterthwaite equation
        df = ((var1 / n1 + var2 / n2) ** 2) / (
            (var1 / n1) ** 2 / (n1 - 1) + (var2 / n2) ** 2 / (n2 - 1)
        )

        # Standard error of difference between means
        se = np.sqrt(var1 / n1 + var2 / n2)

        # Mean difference
        mean_diff = mean1 - mean2

        # Calculate 95% confidence interval using scipy.stats.t.interval
        alpha = 0.05
        ci_lower, ci_upper = stats.t.interval(1 - alpha, df, loc=mean_diff, scale=se)
        confidence_interval = (ci_lower, ci_upper)

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
