from django.shortcuts import render
from django.db.models import Avg, Count, Min, Max, StdDev
from study.models import QuizResponse
from scipy import stats
import numpy as np
import logging

logger = logging.getLogger(__name__)


def statistics_view(request):
    total_responses = QuizResponse.objects.count()
    all_scores_qs = QuizResponse.objects.values_list("score", flat=True)
    all_scores = [float(s) for s in all_scores_qs if s is not None]

    average_score = np.mean(all_scores)
    min_score = np.min(all_scores)
    max_score = np.max(all_scores)
    q1_overall = np.percentile(all_scores, 25)
    median_overall = np.percentile(all_scores, 50)
    q3_overall = np.percentile(all_scores, 75)
    std_dev_overall = np.std(all_scores, ddof=1) if len(all_scores) > 1 else np.nan

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

        group_stats["q1_score"] = np.percentile(group_scores, 25)
        group_stats["median_score"] = np.percentile(group_scores, 50)
        group_stats["q3_score"] = np.percentile(group_scores, 75)

    group1_scores_qs = QuizResponse.objects.filter(
        participant__treatment_group=1
    ).values_list("score", flat=True)
    group2_scores_qs = QuizResponse.objects.filter(
        participant__treatment_group=2
    ).values_list("score", flat=True)

    group1_scores = [float(s) for s in group1_scores_qs if s is not None]
    group2_scores = [float(s) for s in group2_scores_qs if s is not None]

    ttest_result = None
    confidence_interval = None
    p_value = None
    t_statistic = None
    df = None
    cohens_d = None
    alpha = 0.05

    if len(group1_scores) >= 2 and len(group2_scores) >= 2:
        ttest_result = stats.ttest_ind(
            group1_scores, group2_scores, equal_var=False, alternative="greater"
        )
        t_statistic = ttest_result.statistic
        p_value = ttest_result.pvalue
        df = ttest_result.df

        n1 = len(group1_scores)
        n2 = len(group2_scores)
        mean1 = np.mean(group1_scores)
        mean2 = np.mean(group2_scores)
        var1 = np.var(group1_scores, ddof=1)
        var2 = np.var(group2_scores, ddof=1)

        print(f"Cohen's d calculation: n1={n1}, n2={n2}")
        print(f"Cohen's d calculation: mean1={mean1}, mean2={mean2}")
        print(f"Cohen's d calculation: var1={var1}, var2={var2}")

        term1_numerator_pooled_s = (n1 - 1) * var1
        term2_numerator_pooled_s = (n2 - 1) * var2
        print(
            f"Cohen's d calculation: term1_numerator_pooled_s ( (n1-1)*var1 ) = {term1_numerator_pooled_s}"
        )
        print(
            f"Cohen's d calculation: term2_numerator_pooled_s ( (n2-1)*var2 ) = {term2_numerator_pooled_s}"
        )

        pooled_s_numerator = term1_numerator_pooled_s + term2_numerator_pooled_s
        pooled_s_denominator = n1 + n2 - 2
        print(
            f"Cohen's d calculation: pooled_s_numerator={pooled_s_numerator}, pooled_s_denominator={pooled_s_denominator}"
        )

        s_pooled = np.sqrt(pooled_s_numerator / pooled_s_denominator)
        print(f"Cohen's d calculation: s_pooled={s_pooled}")

        mean_difference = mean1 - mean2
        print(
            f"Cohen's d calculation: mean_difference (mean1 - mean2) = {mean_difference}"
        )

        cohens_d = mean_difference / s_pooled
        print(f"Cohen's d calculation: cohens_d={cohens_d}")

        confidence_level = 1 - alpha

        se_diff_squared = (var1 / n1) + (var2 / n2)
        se_diff = np.sqrt(se_diff_squared)

        confidence_interval = stats.t.interval(
            confidence_level,
            df,
            loc=(mean1 - mean2),
            scale=se_diff,
        )

    print("\n=== STUDY STATISTICS ===")
    print(f"Total Responses: {total_responses}")
    print(f"Average Score: {average_score} / 10")
    print(f"Min Score: {min_score} / 10")
    print(f"Max Score: {max_score} / 10")
    print(f"Q1 Score: {q1_overall} / 10")
    print(f"Median Score: {median_overall} / 10")
    print(f"Q3 Score: {q3_overall} / 10")
    print(
        f"Std Dev Score: {std_dev_overall:.2f}"
        if not np.isnan(std_dev_overall)
        else "Std Dev Score: N/A"
    )

    print("\n--- Statistics by Treatment Group ---")
    for group_stats in responses_by_treatment_group:
        group_num = group_stats["participant__treatment_group"]
        print(f"  Group {group_num}:")
        print(f"    Count: {group_stats['count']}")
        avg_s = group_stats["avg_score"]
        print(f"    Average Score: {avg_s:.2f}")
        print(f"    Min Score: {group_stats['min_score']}")
        print(f"    Max Score: {group_stats['max_score']}")
        std_s = group_stats["std_dev_score"]
        print(f"    Std Dev Score: {std_s:.2f}")
        q1_s = group_stats["q1_score"]
        median_s = group_stats["median_score"]
        q3_s = group_stats["q3_score"]
        print(f"    Q1 Score: {q1_s:.2f}")
        print(f"    Median Score: {median_s:.2f}")
        print(f"    Q3 Score: {q3_s:.2f}")

    print("\n--- T-Test Results (Group 1 vs Group 2, H1: Group 1 > Group 2) ---")
    if t_statistic is not None and p_value is not None:
        print(f"  T-statistic: {t_statistic:.3f}")
        print(f"  P-value: {p_value:.3f}")
        print(f"  Degrees of Freedom: {df:.2f}")
        print(f"  Cohen's d: {cohens_d:.3f}")
        if confidence_interval is not None and confidence_interval[0] is not None:
            print(
                f"  95% CI for difference in means (Group 1 - Group 2): ({confidence_interval[0]:.3f}, {confidence_interval[1]:.3f})"
            )
        else:
            print("  95% CI for difference in means: Not calculable or not available")
        print("  Alpha: 0.05")
        if p_value < 0.05:
            print(
                "  Result: Statistically significant, reject null hypothesis. Evidence suggests Group 1 scores are greater than Group 2 scores."
            )
        else:
            print(
                "  Result: Not statistically significant, fail to reject null hypothesis. No strong evidence that Group 1 scores are greater than Group 2 scores."
            )
    else:
        print("  T-Test not performed (insufficient data in one or both groups).")
    print("========================\n")

    logger.info("=== STUDY STATISTICS ===")
    logger.info(f"Total Responses: {total_responses}")
    logger.info(f"Average Score: {average_score:.2f} / 10")
    logger.info(
        f"Overall Std Dev: {std_dev_overall:.2f}"
        if not np.isnan(std_dev_overall)
        else "Overall Std Dev: N/A"
    )

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
        "group1_mean": np.mean(group1_scores),
        "group2_mean": np.mean(group2_scores),
        "group1_std": np.std(group1_scores, ddof=1),
        "group2_std": np.std(group2_scores, ddof=1),
    }
    return render(request, "analytics/statistics.html", context)
