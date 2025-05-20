from django.shortcuts import render
from django.db.models import Avg, Count, Min, Max, StdDev
from study.models import QuizResponse
from scipy import stats
import numpy as np
import logging
from collections import Counter

logger = logging.getLogger(__name__)


def get_score_distribution(scores_list):
    if not scores_list:
        return [0] * 11
    counts = Counter(int(s) for s in scores_list if s is not None)
    distribution = [counts.get(i, 0) for i in range(11)]
    return distribution

def statistics_view(request):
    total_responses = QuizResponse.objects.count()
    all_scores_qs = QuizResponse.objects.values_list("score", flat=True)
    all_scores = [float(s) for s in all_scores_qs if s is not None]

    if all_scores:
        average_score = np.mean(all_scores)
        min_score = np.min(all_scores)
        max_score = np.max(all_scores)
        q1_overall = np.percentile(all_scores, 25)
        median_overall = np.percentile(all_scores, 50)
        q3_overall = np.percentile(all_scores, 75)
        std_dev_overall = np.std(all_scores, ddof=1) if len(all_scores) > 1 else (0.0 if len(all_scores) == 1 else np.nan)
    else:
        average_score = np.nan
        min_score = np.nan
        max_score = np.nan
        q1_overall = np.nan
        median_overall = np.nan
        q3_overall = np.nan
        std_dev_overall = np.nan

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

    for group_stats in responses_by_treatment_group:
        group_scores_qs = QuizResponse.objects.filter(
            participant__treatment_group=group_stats["participant__treatment_group"]
        ).values_list("score", flat=True)
        group_scores = [float(s) for s in group_scores_qs if s is not None]

        if group_scores:
            group_stats["q1_score"] = np.percentile(group_scores, 25)
            group_stats["median_score"] = np.percentile(group_scores, 50)
            group_stats["q3_score"] = np.percentile(group_scores, 75)
        else:
            group_stats["q1_score"] = np.nan
            group_stats["median_score"] = np.nan
            group_stats["q3_score"] = np.nan


    group1_scores_qs = QuizResponse.objects.filter(
        participant__treatment_group=1
    ).values_list("score", flat=True)
    group2_scores_qs = QuizResponse.objects.filter(
        participant__treatment_group=2
    ).values_list("score", flat=True)

    group1_scores = [float(s) for s in group1_scores_qs if s is not None]
    group2_scores = [float(s) for s in group2_scores_qs if s is not None]

    overall_score_distribution = get_score_distribution(all_scores)
    group1_score_distribution = get_score_distribution(group1_scores)
    group2_score_distribution = get_score_distribution(group2_scores)

    t_statistic = None
    p_value = None
    df = None
    cohens_d = None
    confidence_interval = None
    alpha = 0.05

    if len(group1_scores) >= 2 and len(group2_scores) >= 2:
        ttest_result = stats.ttest_ind(
            group1_scores, group2_scores, equal_var=False, alternative="greater"
        )
        t_statistic = ttest_result.statistic
        p_value = ttest_result.pvalue
        df = ttest_result.df

        n1, n2 = len(group1_scores), len(group2_scores)
        mean1, mean2 = np.mean(group1_scores), np.mean(group2_scores)
        var1, var2 = np.var(group1_scores, ddof=1), np.var(group2_scores, ddof=1)

        if var1 > 0 or var2 > 0: # Ensure s_pooled is not NaN or zero if means are different
            s_pooled_numerator = (n1 - 1) * var1 + (n2 - 1) * var2
            s_pooled_denominator = n1 + n2 - 2
            if s_pooled_denominator > 0:
                 s_pooled = np.sqrt(s_pooled_numerator / s_pooled_denominator)
                 if s_pooled > 0: # Avoid division by zero if s_pooled is 0
                    cohens_d = (mean1 - mean2) / s_pooled
                 else: # If pooled std dev is 0, effect size is undefined or infinite if means differ
                    cohens_d = np.inf if mean1 != mean2 else 0 
            else: # Should not happen if n1,n2 >=2
                cohens_d = np.nan
        elif mean1 == mean2: # Both variances are zero and means are equal
             cohens_d = 0
        else: # Both variances are zero but means differ (unlikely with real data)
             cohens_d = np.inf


        se_diff_squared = (var1 / n1) + (var2 / n2)
        if se_diff_squared > 0:
            se_diff = np.sqrt(se_diff_squared)
            confidence_interval = stats.t.interval(
                1 - alpha,
                df,
                loc=(mean1 - mean2),
                scale=se_diff,
            )
        else:
            confidence_interval = (np.nan, np.nan)


    logger.info("=== STUDY STATISTICS ===")
    logger.info(f"Total Responses: {total_responses}")
    logger.info(f"Average Score: {average_score if not np.isnan(average_score) else 'N/A'}")
    logger.info(f"Overall Std Dev: {std_dev_overall if not np.isnan(std_dev_overall) else 'N/A'}")

    context = {
        "total_responses": total_responses,
        "average_score": average_score,
        "min_score": min_score,
        "max_score": max_score,
        "q1_overall": q1_overall,
        "median_overall": median_overall,
        "q3_overall": q3_overall,
        "std_dev_overall": std_dev_overall,
        "responses_by_treatment_group": responses_by_treatment_group,
        "t_statistic": t_statistic,
        "p_value": p_value,
        "df": df,
        "confidence_interval": confidence_interval,
        "cohens_d": cohens_d,
        "alpha": alpha,
        "group1_count": len(group1_scores),
        "group2_count": len(group2_scores),
        "group1_mean": np.mean(group1_scores) if group1_scores else np.nan,
        "group2_mean": np.mean(group2_scores) if group2_scores else np.nan,
        "group1_std": np.std(group1_scores, ddof=1) if len(group1_scores) > 1 else (0.0 if len(group1_scores) == 1 else np.nan),
        "group2_std": np.std(group2_scores, ddof=1) if len(group2_scores) > 1 else (0.0 if len(group2_scores) == 1 else np.nan),
        "overall_score_distribution": overall_score_distribution,
        "group1_score_distribution": group1_score_distribution,
        "group2_score_distribution": group2_score_distribution,
    }
    return render(request, "analytics/statistics.html", context)
