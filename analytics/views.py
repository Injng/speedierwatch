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

    average_score = np.mean(all_scores) if all_scores else None
    min_score = np.min(all_scores) if all_scores else None
    max_score = np.max(all_scores) if all_scores else None
    q1_overall = np.percentile(all_scores, 25) if all_scores else None
    median_overall = np.percentile(all_scores, 50) if all_scores else None  # Median
    q3_overall = np.percentile(all_scores, 75) if all_scores else None

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

    # Add Q1, Median, Q3 to each group
    for group_stats in responses_by_treatment_group:
        group_scores_qs = QuizResponse.objects.filter(
            participant__treatment_group=group_stats["participant__treatment_group"]
        ).values_list("score", flat=True)
        group_scores = [float(s) for s in group_scores_qs if s is not None]

        group_stats["q1_score"] = (
            np.percentile(group_scores, 25) if group_scores else None
        )
        group_stats["median_score"] = (
            np.percentile(group_scores, 50) if group_scores else None
        )
        group_stats["q3_score"] = (
            np.percentile(group_scores, 75) if group_scores else None
        )

    group1_scores_qs = QuizResponse.objects.filter(
        participant__treatment_group=1
    ).values_list("score", flat=True)
    group2_scores_qs = QuizResponse.objects.filter(
        participant__treatment_group=2
    ).values_list("score", flat=True)

    # Convert to list of floats for scipy
    group1_scores = [float(s) for s in group1_scores_qs if s is not None]
    group2_scores = [float(s) for s in group2_scores_qs if s is not None]

    ttest_result = None
    confidence_interval = None
    p_value = None
    t_statistic = None
    df = None  # degrees of freedom
    cohens_d = None  # Add Cohen's d variable

    if len(group1_scores) >= 2 and len(group2_scores) >= 2:
        # Perform Welch\'s t-test (equal_var=False) for independent samples, one-tailed (alternative=\'greater\')
        ttest_result = stats.ttest_ind(
            group1_scores, group2_scores, equal_var=False, alternative="greater"
        )
        t_statistic = ttest_result.statistic
        p_value = ttest_result.pvalue

        # Calculate confidence interval for the difference in means
        n1 = len(group1_scores)
        n2 = len(group2_scores)
        mean1 = np.mean(group1_scores)
        mean2 = np.mean(group2_scores)
        var1 = np.var(group1_scores, ddof=1)  # ddof=1 for sample variance
        var2 = np.var(group2_scores, ddof=1)

        # Calculate Cohen's d effect size
        # For unequal variances, we use pooled standard deviation with Welch's correction
        # Formula: d = (mean1 - mean2) / sqrt((var1 + var2) / 2)
        if n1 > 1 and n2 > 1:
            # Calculate pooled standard deviation
            pooled_std = np.sqrt((var1 + var2) / 2)
            # Calculate Cohen's d
            if pooled_std > 0:  # Avoid division by zero
                cohens_d = (mean1 - mean2) / pooled_std
            else:
                cohens_d = np.nan

        # Degrees of freedom for Welch\'s t-test (Satterthwaite approximation)
        if n1 > 1 and n2 > 1:  # df calculation requires n > 1
            df_num = (var1 / n1 + var2 / n2) ** 2
            df_den_term1 = (var1 / n1) ** 2 / (n1 - 1) if n1 > 1 else 0
            df_den_term2 = (var2 / n2) ** 2 / (n2 - 1) if n2 > 1 else 0
            if df_den_term1 + df_den_term2 > 0:
                df = df_num / (df_den_term1 + df_den_term2)
            else:
                df = n1 + n2 - 2  # Fallback or handle as appropriate

            if df > 0:  # t.ppf requires df > 0
                # Standard error of the difference in means
                se_diff = np.sqrt(var1 / n1 + var2 / n2)
                alpha = 0.05
                # For a one-sided "greater" test, the CI is (lower_bound, infinity)
                # We are interested in mean1 - mean2.
                # The critical t-value for a 95% CI (alpha=0.05)
                # t_crit_one_sided = stats.t.ppf(1 - alpha, df)
                # lower_bound_one_sided = (mean1 - mean2) - t_crit_one_sided * se_diff
                # confidence_interval_one_sided = (lower_bound_one_sided, float(\'inf\'))

                # For display, a two-sided 95% CI is often preferred.
                t_crit_two_sided = stats.t.ppf(1 - alpha / 2, df)
                margin_of_error = t_crit_two_sided * se_diff
                confidence_interval = (
                    (mean1 - mean2) - margin_of_error,
                    (mean1 - mean2) + margin_of_error,
                )
            else:  # df <=0
                confidence_interval = (None, None)  # Cannot compute CI
        else:  # n1 <=1 or n2 <=1
            df = None
            confidence_interval = (None, None)

    # Print statistics to the terminal/log
    print("\n=== STUDY STATISTICS ===")
    print(f"Total Responses: {total_responses}")
    print(
        f"Average Score: {average_score if average_score is not None else 'N/A'}{' / 10' if average_score is not None else ''}"
    )
    print(
        f"Min Score: {min_score if min_score is not None else 'N/A'}{' / 10' if min_score is not None else ''}"
    )
    print(
        f"Max Score: {max_score if max_score is not None else 'N/A'}{' / 10' if max_score is not None else ''}"
    )
    print(
        f"Q1 Score: {q1_overall if q1_overall is not None else 'N/A'}{' / 10' if q1_overall is not None else ''}"
    )
    print(
        f"Median Score: {median_overall if median_overall is not None else 'N/A'}{' / 10' if median_overall is not None else ''}"
    )
    print(
        f"Q3 Score: {q3_overall if q3_overall is not None else 'N/A'}{' / 10' if q3_overall is not None else ''}"
    )

    print("\n--- Statistics by Treatment Group ---")
    for group_stats in responses_by_treatment_group:
        group_num = group_stats["participant__treatment_group"]
        print(f"  Group {group_num}:")
        print(f"    Count: {group_stats['count']}")
        avg_s = group_stats["avg_score"]
        print(
            f"    Average Score: {avg_s:.2f}"
            if avg_s is not None
            else "    Average Score: N/A"
        )
        print(f"    Min Score: {group_stats['min_score']}")
        print(f"    Max Score: {group_stats['max_score']}")
        std_s = group_stats["std_dev_score"]
        print(
            f"    Std Dev Score: {std_s:.2f}"
            if std_s is not None
            else "    Std Dev Score: N/A"
        )
        q1_s = group_stats["q1_score"]
        median_s = group_stats["median_score"]
        q3_s = group_stats["q3_score"]
        print(f"    Q1 Score: {q1_s:.2f}" if q1_s is not None else "    Q1 Score: N/A")
        print(
            f"    Median Score: {median_s:.2f}"
            if median_s is not None
            else "    Median Score: N/A"
        )
        print(f"    Q3 Score: {q3_s:.2f}" if q3_s is not None else "    Q3 Score: N/A")

    print("\n--- T-Test Results (Group 1 vs Group 2, H1: Group 1 > Group 2) ---")
    if t_statistic is not None and p_value is not None:
        print(f"  T-statistic: {t_statistic:.3f}")
        print(f"  P-value: {p_value:.3f}")
        print(
            f"  Degrees of Freedom: {df:.2f}"
            if df is not None
            else "  Degrees of Freedom: N/A"
        )
        print(
            f"  Cohen's d: {cohens_d:.3f}"
            if cohens_d is not None
            else "  Cohen's d: N/A"
        )
        if confidence_interval and confidence_interval[0] is not None:
            print(
                f"  95% CI for difference in means (Group 1 - Group 2): ({confidence_interval[0]:.3f}, {confidence_interval[1]:.3f})"
            )
        else:
            print("  95% CI for difference in means: Not calculable")
        print("  Alpha: 0.05")  # Corrected: Not an f-string as it has no placeholders
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

    # Log statistics as well (for server logs)
    logger.info("=== STUDY STATISTICS ===")
    logger.info(f"Total Responses: {total_responses}")
    logger.info(
        f"Average Score: {average_score if average_score is not None else 0:.2f} / 10"
    )
    # ... (add more logging if desired) ...

    context = {
        "total_responses": total_responses,
        "average_score": average_score if average_score is not None else None,
        "min_score": min_score if min_score is not None else None,
        "max_score": max_score if max_score is not None else None,
        "q1_overall": q1_overall,
        "median_overall": median_overall,
        "q3_overall": q3_overall,
        "responses_by_treatment_group": responses_by_treatment_group,
        "t_statistic": t_statistic,
        "p_value": p_value,
        "df": df,
        "confidence_interval": confidence_interval,
        "cohens_d": cohens_d,
        "alpha": 0.05,  # Standard alpha level
        "group1_count": len(group1_scores),
        "group2_count": len(group2_scores),
        "group1_mean": np.mean(group1_scores) if len(group1_scores) > 0 else None,
        "group2_mean": np.mean(group2_scores) if len(group2_scores) > 0 else None,
        "group1_std": np.std(group1_scores, ddof=1) if len(group1_scores) > 1 else None,
        "group2_std": np.std(group2_scores, ddof=1) if len(group2_scores) > 1 else None,
    }
    return render(request, "analytics/statistics.html", context)
