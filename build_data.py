"""
Build the aggregated data files that power the dashboard.

Re-runs the exact computations from assignment1.ipynb (same filters, same
outlier rules, same random seeds and sampling order) and exports ONLY
aggregated results:

  data/summary.json   - every statistic, table and test result shown in the app
  data/bootstrap.npz  - bootstrap replicate statistics (means, t, F, medians);
                        these are resampled summary statistics, not survey rows

No individual survey response is written out. The salary-vs-age view is
exported as 2-D bin counts, and box plots as five-number summaries.

Usage (run locally, never on the deployed app):
    python build_data.py /path/to/clean_stackoverflow_data.csv
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

OUT = Path(__file__).parent / "data"
SAL = "ConvertedCompYearly"


def box_summary(values):
    """Tukey box-plot summary (matches seaborn's 1.5*IQR whiskers)."""
    v = np.asarray(values, dtype=float)
    q1, med, q3 = np.percentile(v, [25, 50, 75])
    iqr = q3 - q1
    lo_lim, hi_lim = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    inside = v[(v >= lo_lim) & (v <= hi_lim)]
    return {
        "q1": q1, "median": med, "q3": q3,
        "lowerfence": inside.min(), "upperfence": inside.max(),
        "n_outliers_high": int((v > hi_lim).sum()),
        "n_outliers_low": int((v < lo_lim).sum()),
        "min": v.min(), "max": v.max(), "n": int(v.size),
    }


def records(frame):
    return json.loads(frame.to_json(orient="records"))


def main(csv_path):
    df = pd.read_csv(csv_path)
    out = {"meta": {"rows": int(df.shape[0]), "columns": int(df.shape[1]),
                    "bootstrap_reps": 10000}}
    arrays = {}

    # ------------------------------------------------------------------ Q1
    q1_df = df.copy()
    q1_df.loc[~q1_df["JobSat"].between(0, 10), "JobSat"] = np.nan
    q1_df.loc[~q1_df["Age"].between(18, 100), "Age"] = np.nan

    job_sat = (
        q1_df.groupby("DevType")
        .agg(mean_satisfaction=("JobSat", "mean"), respondent_count=("JobSat", "count"))
        .sort_values("mean_satisfaction", ascending=False)
        .reset_index()
    )
    job_sal = (
        q1_df.groupby("DevType")
        .agg(mean_salary=(SAL, "mean"), median_salary=(SAL, "median"),
             respondent_count=(SAL, "count"), max_salary=(SAL, "max"))
    )
    job_sal["mean_median_ratio"] = job_sal["mean_salary"] / job_sal["median_salary"]
    job_sal = job_sal.sort_values("mean_salary", ascending=False).reset_index()

    age_salary = q1_df[["Age", SAL]].dropna()
    age_edges = np.arange(18, 102, 2)                 # 2-year age bins
    log_edges = np.arange(2.0, 7.65, 0.1)             # log10(USD) bins
    counts, _, _ = np.histogram2d(age_salary["Age"], np.log10(age_salary[SAL]),
                                  bins=[age_edges, log_edges])
    age_band = pd.cut(age_salary["Age"], bins=[17, 24, 34, 44, 54, 64, 100],
                      labels=["18-24", "25-34", "35-44", "45-54", "55-64", "65+"])
    band_stats = (age_salary.groupby(age_band, observed=True)[SAL]
                  .agg(n="count", p25=lambda s: s.quantile(.25), median="median",
                       p75=lambda s: s.quantile(.75), mean="mean").reset_index()
                  .rename(columns={"Age": "band"}))

    out["q1"] = {
        "cleaning": {
            "age_missing_after": int(q1_df["Age"].isna().sum()),
            "jobsat_missing_after": int(q1_df["JobSat"].isna().sum()),
        },
        "job_satisfaction": records(job_sat),
        "job_salary": records(job_sal),
        "age_salary": {
            "n": int(len(age_salary)),
            "age_edges": age_edges.tolist(),
            "log_edges": np.round(log_edges, 2).tolist(),
            "counts": counts.astype(int).tolist(),
            "bands": records(band_stats),
        },
    }

    # ------------------------------------------------------------------ Q2a
    q2_df = df[df["RemoteWork"].isin(["Hybrid", "Remote"])].copy()
    hybrid_salary = q2_df.loc[q2_df["RemoteWork"] == "Hybrid", SAL]
    remote_salary = q2_df.loc[q2_df["RemoteWork"] == "Remote", SAL]

    g = q2_df.groupby("RemoteWork")[SAL]
    q2_stats = g.agg(count="count", mean="mean", median="median", std="std",
                     min="min", max="max")
    pct = g.quantile([0.25, 0.75, 0.95, 0.99]).unstack()
    pct.columns = ["Q1", "Q3", "P95", "P99"]
    q2_stats = q2_stats.join(pct)

    thresholds = g.quantile(0.99)
    q2_temp = q2_df.copy()
    q2_temp["p99_threshold"] = q2_temp["RemoteWork"].map(thresholds)
    q2_temp["is_extreme"] = q2_temp[SAL] > q2_temp["p99_threshold"]
    trimmed_stats = (q2_temp.loc[~q2_temp["is_extreme"]].groupby("RemoteWork")[SAL]
                     .agg(["count", "mean", "median", "std"]))
    removed = q2_temp.groupby("RemoteWork")["is_extreme"].sum()

    q2_clean = q2_temp.loc[~q2_temp["is_extreme"]]
    hybrid_clean = q2_clean.loc[q2_clean["RemoteWork"] == "Hybrid", SAL].to_numpy()
    remote_clean = q2_clean.loc[q2_clean["RemoteWork"] == "Remote", SAL].to_numpy()

    # ------------------------------------------------------------------ Q2b
    n_r, n_h = len(remote_clean), len(hybrid_clean)
    mean_r, mean_h = np.mean(remote_clean), np.mean(hybrid_clean)
    var_r, var_h = np.var(remote_clean, ddof=1), np.var(hybrid_clean, ddof=1)
    variance_ratio = max(var_r, var_h) / min(var_r, var_h)
    lev_stat, lev_p = stats.levene(remote_clean, hybrid_clean, center="median")

    se_diff = np.sqrt(var_r / n_r + var_h / n_h)
    t_stat = (mean_r - mean_h) / se_diff
    df_welch = ((var_r / n_r + var_h / n_h) ** 2
                / ((var_r / n_r) ** 2 / (n_r - 1) + (var_h / n_h) ** 2 / (n_h - 1)))
    p_value = 2 * stats.t.sf(abs(t_stat), df_welch)
    welch_scipy = stats.ttest_ind(remote_clean, hybrid_clean, equal_var=False)

    pooled_var = ((n_r - 1) * var_r + (n_h - 1) * var_h) / (n_r + n_h - 2)
    pooled_std = np.sqrt(pooled_var)
    se_pooled = pooled_std * np.sqrt(1 / n_r + 1 / n_h)
    t_pooled = (mean_r - mean_h) / se_pooled
    df_pooled = n_r + n_h - 2
    p_pooled = 2 * stats.t.sf(abs(t_pooled), df_pooled)
    student_scipy = stats.ttest_ind(remote_clean, hybrid_clean, equal_var=True)

    # ------------------------------------------------------------------ Q2c
    rng = np.random.default_rng(42)
    B = 10000
    boot_remote, boot_hybrid, boot_diffs = np.empty(B), np.empty(B), np.empty(B)
    for b in range(B):
        rs = rng.choice(remote_clean, size=len(remote_clean), replace=True)
        hs = rng.choice(hybrid_clean, size=len(hybrid_clean), replace=True)
        boot_remote[b] = rs.mean()
        boot_hybrid[b] = hs.mean()
        boot_diffs[b] = boot_remote[b] - boot_hybrid[b]
    boot_se = boot_diffs.std(ddof=1)
    standardized = (boot_diffs - boot_diffs.mean()) / boot_se

    # ------------------------------------------------------------------ Q2d
    rng = np.random.default_rng(123)
    remote_null = remote_clean - remote_clean.mean()
    hybrid_null = hybrid_clean - hybrid_clean.mean()
    boot_t = np.empty(B)
    for b in range(B):
        rs = rng.choice(remote_null, size=len(remote_null), replace=True)
        hs = rng.choice(hybrid_null, size=len(hybrid_null), replace=True)
        se = np.sqrt(np.var(rs, ddof=1) / len(rs) + np.var(hs, ddof=1) / len(hs))
        boot_t[b] = (rs.mean() - hs.mean()) / se
    p_boot_t = (np.sum(np.abs(boot_t) >= abs(t_stat)) + 1) / (B + 1)

    # ------------------------------------------------------------------ Q2e
    observed_diff = mean_r - mean_h
    t_crit = stats.t.ppf(1 - 0.05 / 2, df_welch)
    welch_ci = (observed_diff - t_crit * se_diff, observed_diff + t_crit * se_diff)
    boot_ci = np.percentile(boot_diffs, [2.5, 97.5])

    # ------------------------------------------------------------------ Q2f
    m_stat, m_p, grand_median, table = stats.median_test(remote_clean, hybrid_clean)
    rng_median = np.random.default_rng(2026)
    obs_med_diff = np.median(remote_clean) - np.median(hybrid_clean)
    remote_null = remote_clean - np.median(remote_clean)
    hybrid_null = hybrid_clean - np.median(hybrid_clean)
    boot_med_null = np.empty(B)
    for b in range(B):
        rs = rng_median.choice(remote_null, size=len(remote_null), replace=True)
        hs = rng_median.choice(hybrid_null, size=len(hybrid_null), replace=True)
        boot_med_null[b] = np.median(rs) - np.median(hs)
    p_boot_median = (np.sum(np.abs(boot_med_null) >= abs(obs_med_diff)) + 1) / (B + 1)

    original_test = stats.ttest_ind(remote_salary, hybrid_salary, equal_var=False)

    out["q2"] = {
        "counts": {"Hybrid": int(len(hybrid_salary)), "Remote": int(len(remote_salary))},
        "descriptive": records(q2_stats.reset_index()),
        "box": {"Remote": box_summary(remote_salary), "Hybrid": box_summary(hybrid_salary)},
        "p99_thresholds": {k: float(v) for k, v in thresholds.items()},
        "trimmed": records(trimmed_stats.reset_index()),
        "removed": {k: int(v) for k, v in removed.items()},
        "box_trimmed": {"Remote": box_summary(remote_clean), "Hybrid": box_summary(hybrid_clean)},
        "assumptions": {
            "var_r": var_r, "var_h": var_h, "sd_r": np.sqrt(var_r), "sd_h": np.sqrt(var_h),
            "variance_ratio": variance_ratio, "levene_stat": lev_stat, "levene_p": lev_p,
        },
        "welch": {
            "n_r": n_r, "n_h": n_h, "mean_r": mean_r, "mean_h": mean_h,
            "mean_diff": observed_diff, "se_diff": se_diff, "t": t_stat,
            "df": df_welch, "p": p_value,
            "scipy_t": float(welch_scipy.statistic), "scipy_p": float(welch_scipy.pvalue),
        },
        "student": {
            "pooled_var": pooled_var, "pooled_std": pooled_std, "se_pooled": se_pooled,
            "t": t_pooled, "df": df_pooled, "p": p_pooled,
            "scipy_t": float(student_scipy.statistic), "scipy_p": float(student_scipy.pvalue),
        },
        "bootstrap": {
            "B": B, "seed": 42,
            "remote_mean": boot_remote.mean(), "hybrid_mean": boot_hybrid.mean(),
            "diff_mean": boot_diffs.mean(), "se": boot_se,
            "std_mean": standardized.mean(), "std_sd": standardized.std(ddof=1),
        },
        "boot_ttest": {"seed": 123, "observed_t": t_stat, "p": p_boot_t,
                       "max_abs_boot_t": float(np.abs(boot_t).max())},
        "ci": {"welch": list(welch_ci), "bootstrap": boot_ci.tolist(), "t_crit": t_crit},
        "mood": {
            "stat": m_stat, "p": m_p, "grand_median": grand_median,
            "table": np.asarray(table).tolist(),
            "median_r": np.median(remote_clean), "median_h": np.median(hybrid_clean),
            "pct_above_r": table[0][0] / n_r, "pct_above_h": table[0][1] / n_h,
            "obs_median_diff": obs_med_diff, "boot_p": p_boot_median, "seed": 2026,
            "max_abs_boot": float(np.abs(boot_med_null).max()),
        },
        "sensitivity": {
            "original_diff": remote_salary.mean() - hybrid_salary.mean(),
            "original_t": float(original_test.statistic),
            "original_p": float(original_test.pvalue),
        },
    }
    arrays.update(q2_boot_remote=boot_remote, q2_boot_hybrid=boot_hybrid,
                  q2_boot_diffs=boot_diffs, q2_boot_t=boot_t,
                  q2_boot_median_null=boot_med_null)

    # ------------------------------------------------------------------ Q3a
    order = ["Bachelor's degree", "Master's degree", "Professional degree"]
    q3_df = df[df["Country"].isin(["United States of America", "Canada"])
               & df["EdLevel"].isin(order)].copy()
    describe = q3_df.groupby("EdLevel")[SAL].describe().reset_index()
    perc = q3_df.groupby("EdLevel")[SAL].quantile([0, .25, .5, .75, .95, .99, 1.0]).unstack()
    perc.columns = ["Min", "Q1", "Median", "Q3", "P95", "P99", "Max"]
    q3_df["salary_p99"] = q3_df.groupby("EdLevel")[SAL].transform(lambda x: x.quantile(0.99))
    q3_clean = q3_df[q3_df[SAL] <= q3_df["salary_p99"]].copy()
    agg = ["count", "mean", "median", "std"]
    orig_q3 = q3_df.groupby("EdLevel")[SAL].agg(agg).reset_index()
    trim_q3 = q3_clean.groupby("EdLevel")[SAL].agg(agg).reset_index()
    removed_q3 = (q3_df.groupby("EdLevel").size() - q3_clean.groupby("EdLevel").size())

    # ------------------------------------------------------------------ Q3b
    def grp(frame, level):
        return frame.loc[frame["EdLevel"] == level, SAL].dropna().to_numpy()

    bachelor, master, professional = (grp(q3_clean, lvl) for lvl in order)
    f_stat, p_anova = stats.f_oneway(bachelor, master, professional)
    lev3_stat, lev3_p = stats.levene(bachelor, master, professional, center="median")
    f_orig, p_orig = stats.f_oneway(*(grp(q3_df, lvl) for lvl in order))

    # ------------------------------------------------------------------ Q3c
    rng_q3 = np.random.default_rng(123)
    groups = {"Bachelor's": bachelor, "Master's": master, "Professional": professional}
    boot_means = {}
    for name, values in groups.items():
        bm = np.empty(B)
        for b in range(B):
            bm[b] = rng_q3.choice(values, size=len(values), replace=True).mean()
        boot_means[name] = bm
    pairs = {
        "Master's − Bachelor's": boot_means["Master's"] - boot_means["Bachelor's"],
        "Professional − Bachelor's": boot_means["Professional"] - boot_means["Bachelor's"],
        "Professional − Master's": boot_means["Professional"] - boot_means["Master's"],
    }

    # ------------------------------------------------------------------ Q3d
    rng_anova = np.random.default_rng(123)
    grand_mean = np.concatenate([bachelor, master, professional]).mean()
    centered = [v - v.mean() + grand_mean for v in [bachelor, master, professional]]
    boot_f = np.empty(B)
    for b in range(B):
        samples = [rng_anova.choice(v, size=len(v), replace=True) for v in centered]
        boot_f[b] = stats.f_oneway(*samples).statistic
    p_boot_anova = (np.sum(boot_f >= f_stat) + 1) / (B + 1)

    out["q3"] = {
        "n_total": int(len(q3_df)),
        "by_level": {k: int(v) for k, v in q3_df["EdLevel"].value_counts().items()},
        "by_country": {k: int(v) for k, v in q3_df["Country"].value_counts().items()},
        "describe": records(describe),
        "percentiles": records(perc.reset_index()),
        "box": {lvl: box_summary(grp(q3_df, lvl)) for lvl in order},
        "original": records(orig_q3),
        "trimmed": records(trim_q3),
        "removed": {k: int(v) for k, v in removed_q3.items()},
        "anova": {"F": f_stat, "p": p_anova},
        "groups": {name: {"n": len(v), "mean": v.mean(), "std": v.std(ddof=1),
                          "var": np.var(v, ddof=1)} for name, v in groups.items()},
        "levene": {"stat": lev3_stat, "p": lev3_p},
        "sensitivity": {"F_original": f_orig, "p_original": p_orig},
        "bootstrap": {
            name: {"mean": bm.mean(), "se": bm.std(ddof=1),
                   "ci": np.percentile(bm, [2.5, 97.5]).tolist(),
                   "observed": groups[name].mean()}
            for name, bm in boot_means.items()
        },
        "pairs": {name: {"mean": d.mean(), "sd": d.std(ddof=1),
                         "ci": np.percentile(d, [2.5, 97.5]).tolist()}
                  for name, d in pairs.items()},
        "boot_anova": {"seed": 123, "observed_F": f_stat, "p": p_boot_anova,
                       "max_boot_F": float(boot_f.max())},
    }
    arrays.update(q3_boot_bachelor=boot_means["Bachelor's"],
                  q3_boot_master=boot_means["Master's"],
                  q3_boot_professional=boot_means["Professional"],
                  q3_boot_f=boot_f)

    # ------------------------------------------------------------------ write
    OUT.mkdir(exist_ok=True)

    def default(o):
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        raise TypeError(type(o))

    (OUT / "summary.json").write_text(json.dumps(out, default=default, indent=1))
    np.savez_compressed(OUT / "bootstrap.npz", **arrays)
    print(f"Wrote {OUT/'summary.json'} and {OUT/'bootstrap.npz'}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python build_data.py /path/to/clean_stackoverflow_data.csv")
    main(sys.argv[1])
