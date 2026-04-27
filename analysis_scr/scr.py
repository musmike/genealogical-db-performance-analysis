from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import t as t_dist
import matplotlib.pyplot as plt
import os

base_path = "../benchmark_scr/artifacts/"
task_strings = ["Lowest Common Ancestor", 
                "Surname and Birth Year Filter",
                "Births per City per Quarter-Century",
                "Ancestor Retrieval",
                "Descendant Retrieval",
                "Youngest Parent",
                "Place Name Update",
                "Insert Family",
                "Delete Family"
                ]

dataset_strings = ["small", "medium", "large"]


def parse_number(value):
    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        value = value.strip()

        # remove common BenchmarkDotNet units
        for unit in [" ms", " ns", " us", " μs", " s"]:
            if value.endswith(unit):
                value = value.replace(unit, "")

        return float(value)

    return float("nan")

def load_summary_folder(pattern, n):
    results = []
    for i in range(1, n+1):
        path = Path(pattern.format(i))
        if not path.exists():
            continue
        try:
            df = pd.read_csv(path)
            row = df.iloc[0]
            results.append({
                "file": path.name,
                "n": int(row["IterationCount"]),
                "mean": parse_number(row["Mean"]),
                "error": parse_number(row["Error"]),
                "std": parse_number(row["StdDev"])
            })
        except Exception as e:
            print(f"Failed to load {path}: {e}")

    return pd.DataFrame(results)

def welch_t(row):
    se = np.sqrt(
        (row["std_A"]**2 / row["n_A"]) +
        (row["std_B"]**2 / row["n_B"])
    )
    return (row["mean_A"] - row["mean_B"]) / se if se != 0 else np.nan

def welch_df(row):
    s1, s2 = row["std_A"], row["std_B"]
    n1, n2 = row["n_A"], row["n_B"]

    num = (s1**2/n1 + s2**2/n2)**2
    den = ((s1**2/n1)**2/(n1-1)) + ((s2**2/n2)**2/(n2-1))

    return num / den

def generate_report(df):
    df = df.copy()

    # t-statistic
    df["t_stat"] = df.apply(welch_t, axis=1)

    # degrees of freedom
    df["df"] = df.apply(welch_df, axis=1)

    # p-value (two-tailed)
    df["p_value"] = df.apply(
        lambda r: 2 * t_dist.sf(abs(r["t_stat"]), r["df"])
        if not np.isnan(r["t_stat"]) else np.nan,
        axis=1
    )
    
    df["winner"] = np.where(df["mean_A"] < df["mean_B"], "A", "B")
    
    def cohens_d(row):
        pooled = np.sqrt((row["std_A"]**2 + row["std_B"]**2) / 2)
        return (row["mean_A"] - row["mean_B"]) / pooled if pooled != 0 else np.nan

    df["cohens_d"] = df.apply(cohens_d, axis=1)

    def significance(row):
        if np.isnan(row["p_value"]):
            return "invalid"
        if row["p_value"] < 0.05:
            return "significant"
        return "not significant"

    df["significance"] = df.apply(significance, axis=1)

    return df

def print_summary(report_df):
    for _, r in report_df.iterrows():
        print(
            f"{r['file_A'][32:-4]} vs {r['file_B'][32:-4]} | "
            f"Δmean={r['mean_A'] - r['mean_B']:.4f} | "
            f"winner={r['winner']} | "
            f"p={r['p_value']:.4g} | "
            f"d={r['cohens_d']:.3f} | "
            f"{r['significance']}"
        )

def plot_benchmark_report(df, titlePref = "", titleSuff="", importDt=False, unit="ms", output_dir="benchmark_plots", fmt="png"):
    os.makedirs(output_dir, exist_ok=True)

    for i, row in df.iterrows():

        fig, ax = plt.subplots(figsize=(6, 4))

        labels = ["Neo4j", "PostgreSQL"]
        means = [row["mean_A"], row["mean_B"]]
        stds = [row["std_A"], row["std_B"]]
        errs = [row["error_A"], row["error_B"]]
        it = row["n_A"]
        upper = means + errs
        bars = ax.barh(
            labels,
            means,
            xerr = errs,
            capsize=6,
            color=["steelblue", "orange"]
        )
        
        for bar, mean, err in zip(bars, means, errs):

            label_x = mean + err + (np.max(upper) * 0.02)  # small padding

            ax.text(
                label_x,
                bar.get_y() + bar.get_height() / 2,
                f"{mean:.3f} {unit}",
                ha="left",
                va="center",
                fontsize=9,
                fontweight="bold"
            )

        # Significance coloring
        if row["significance"] == "significant":
            if row["winner"] == "A":
                bars[0].set_edgecolor("green")
                bars[0].set_linewidth(3)
                bars[1].set_edgecolor("red")
                bars[1].set_linewidth(3)
            else:
                bars[1].set_edgecolor("green")
                bars[1].set_linewidth(3)
                bars[0].set_edgecolor("red")
                bars[0].set_linewidth(3)

        # Labels & title
        if importDt:
            ax.set_title(f"{titlePref} Data Import {titleSuff}")
            filename = os.path.join(output_dir, f"import_.{fmt}")
        else:
            ax.set_title(f"{titlePref} {task_strings[i]} {titleSuff}")
            filename = os.path.join(output_dir, f"task_{i+1}.{fmt}")
        
        ax.set_xlim(0, np.max(upper) * 1.25)
        ax.set_xlabel(f"Execution time [{unit}]")
        ax.margins(y=0.2)

        ax.text(
            0.5, 0.95,
            f"p-value = {row['p_value']:.3g}; Cohen's d = {row['cohens_d']:.2f}",
            transform=ax.transAxes,
            ha="center",
            va="top",
            fontsize=9
        )

        plt.tight_layout()
        plt.savefig(filename, dpi=300)
        plt.close()

    print(f"Saved {len(df)} plots to {output_dir}/")

def plot_multi_benchmark_report(dfs1, dfs2, titlePref="", titleSuff="", importDt=False, unit="ms", output_dir="benchmark_plots", fmt="png"):
    os.makedirs(output_dir, exist_ok=True)
    n_pairs = 3
    for i in range(len(dfs1)):
        fig, ax = plt.subplots(figsize=(8,5))
        all_means = []
        all_errs = []
        y_labels = []

        colors = {"A": "steelblue", "B": "orange"}

        y_positions = []
        pair_centers = []
        y = 0
        spacing = 1.2
        bars1 = []
        bars2 = []
        upper_bounds = []

        for p in range(n_pairs):
            dfa = dfs1[p].iloc[i]
            dfb = dfs2[p].iloc[i]

            mean_a = dfa["mean_A"]
            mean_b = dfb["mean_B"]

            err_a = dfa["error_A"]
            err_b = dfb["error_B"] 

            y_A = y
            y_B = y + 0.5

            y_positions += [y_A, y_B]
            pair_centers.append((y_A + y_B) / 2)
            all_means += [mean_a, mean_b]
            all_errs += [err_a, err_b]
            y_labels += ["A", "B"]
            upper_bounds.append(max(mean_a + err_a, mean_b + mean_b))
            y += spacing

        bars = ax.barh(
            y_positions,
            all_means,
            xerr=all_errs,
            capsize=6,
            color=[colors["A"], colors["B"]] * n_pairs
        )

        for bar, mean, err in zip(bars, all_means, all_errs):

            label_x = mean + err + (max(all_means) * 0.02)

            ax.text(
                label_x,
                bar.get_y() + bar.get_height() / 2,
                f"{mean:.3f} {unit}",
                ha="left",
                va="center",
                fontsize=9,
                fontweight="bold"
            )

        for idx, center in enumerate(pair_centers):
            ax.text(
                -max(all_means) * 0.05,
                center,
                dataset_strings[idx],
                ha="right",
                va="center",
                fontsize=10,
                fontweight="bold"
            )

        for p in range(n_pairs):

            dfA = dfs1[p].iloc[i]
            dfB = dfs2[p].iloc[i]

            base = p * 2

            bars_A = bars[base]
            bars_B = bars[base + 1]

            if dfA["significance"] == "significant":

                if dfA["winner"] == "A":
                    bars_A.set_edgecolor("green")
                    bars_A.set_linewidth(3)
                    bars_B.set_edgecolor("red")
                    bars_B.set_linewidth(3)
                else:
                    bars_B.set_edgecolor("green")
                    bars_B.set_linewidth(3)
                    bars_A.set_edgecolor("red")
                    bars_A.set_linewidth(3)


        max_upper = max(upper_bounds)
        ax.set_xlim(0, max_upper * 1.3)

        ax.set_yticks([])
        ax.set_xlabel(f"Execution time [{unit}]")

        ax.set_title(f"{titlePref} Task {i+1} {titleSuff}")
        ax.margins(y=0.15)

        filename = os.path.join(output_dir, f"task_{i+1}.{fmt}")
        plt.tight_layout()
        plt.savefig(filename, dpi=300)
        plt.close()

    print(f"Saved {len(dfs1)} multi-task plots to {output_dir}/")



df11 = load_summary_folder(base_path + "large/neo4j/results/benchmark_scr.benchmark.queries.N40{}-report.csv", 9)
df12 = load_summary_folder(base_path + "large/postgres/results/benchmark_scr.benchmark.queries.Ps0{}-report.csv", 9)


df11 = df11.reset_index(drop=True)
df12 = df12.reset_index(drop=True)

if len(df11) != len(df12):
    raise ValueError("Task count mismatch between environments")

df1 = pd.DataFrame({
    "file_A": df11["file"],
    "file_B": df12["file"],
    "mean_A": df11["mean"],
    "mean_B": df12["mean"],
    "std_A": df11["std"],
    "std_B": df12["std"],
    "n_A": df11["n"],
    "n_B": df12["n"],
    "error_A": df11["error"],
    "error_B": df12["error"],
})


dfi1 = load_summary_folder(base_path + "large/neo4j/results/benchmark_scr.benchmark.queries.N4Import-report.csv", 1)
dfi2 = load_summary_folder(base_path + "large/postgres/results/benchmark_scr.benchmark.queries.PsImport-report.csv", 1)
dfi = pd.DataFrame({
    "file_A": dfi1["file"],
    "file_B": dfi2["file"],
    "mean_A": dfi1["mean"],
    "mean_B": dfi2["mean"],
    "std_A": dfi1["std"],
    "std_B": dfi2["std"],
    "n_A": dfi1["n"],
    "n_B": dfi2["n"],
    "error_A": dfi1["error"],
    "error_B": dfi2["error"],
})
for _, row in dfi.iterrows():
    print(row)

rp = generate_report(df1)
print_summary(rp)

rpi = generate_report(dfi)
print_summary(rpi)

plot_benchmark_report(rp, titleSuff="Query Mean Execution Time")
plot_benchmark_report(rpi, importDt=True, unit="s", titleSuff="Mean Time")