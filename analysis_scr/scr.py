from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import t as t_dist
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import os
import re

base_path = "../results/"
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
dataset_nums = ["1k", "10k", "100k"]

UNIT_TO_MS = {
    "ns": 1e-6,
    "us": 1e-3,
    "μs": 1e-3,
    "ms": 1.0,
    "s": 1e3,
}

def choose_display_unit(values):
    max_val = max(values)

    if max_val < 1e-3:
        return "ns", 1e6
    elif max_val < 1:
        return "μs", 1e3
    else:
        return "ms", 1

def parse_with_unit(value):
    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        value = value.strip()

        match = re.match(r"([-+]?\d*\.?\d+)\s*([a-zA-Zμ]*)", value)
        if not match:
            return float("nan")

        num = float(match.group(1))
        unit = match.group(2) or "ms"

        if unit not in UNIT_TO_MS:
            raise ValueError(f"Unknown unit: {unit}")

        return num * UNIT_TO_MS[unit]

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
                "mean": parse_with_unit(row["Mean"]),
                "error": parse_with_unit(row["Error"]),
                "std": parse_with_unit(row["StdDev"])
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

    n1 = df["n_A"].iloc[0]
    n2 = df["n_B"].iloc[0]

    def pooled_std(row):
        s1, s2 = row["std_A"], row["std_B"]
        return np.sqrt(
            ((row["n_A"] - 1)*s1**2 + (row["n_B"] - 1)*s2**2) /
            (row["n_A"] + row["n_B"] - 2)
        )

    df["pooled_std"] = df.apply(pooled_std, axis=1)

    # t-student test
    df["t_stat"] = (
        df["mean_A"] - df["mean_B"]
    ) / (df["pooled_std"] * np.sqrt(2 / df["n_A"]))

    df["df"] = df["n_A"] + df["n_B"] - 2

    # p-value
    df["p_value"] = df.apply(
        lambda r: 2 * t_dist.sf(abs(r["t_stat"]), r["df"])
        if not np.isnan(r["t_stat"]) else np.nan,
        axis=1
    )

    df["winner"] = np.where(df["mean_A"] < df["mean_B"], "A", "B")

    def hedges_g(row):
        s_p = row["pooled_std"]
        if s_p == 0:
            return np.nan

        d = (row["mean_A"] - row["mean_B"]) / s_p

        n = row["n_A"] + row["n_B"]
        correction = 1 - (3 / (4*n - 9))

        return d * correction

    df["effect_size"] = df.apply(hedges_g, axis=1)

    def significance(row):
        if np.isnan(row["p_value"]):
            return "invalid"

        stat_sig = row["p_value"] < 0.05
        practical_sig = abs(row["effect_size"]) > 0.2  # small effect threshold

        if stat_sig and practical_sig:
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


def plot_multi_benchmark_report(
    dtrps,
    titlePref="",
    titleSuff="",
    importDt=False,
    output_dir="../results/benchmark_plots",
    fmt="png"
):
    import os
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    os.makedirs(output_dir, exist_ok=True)

    n_pairs = len(dtrps)
    n_tasks = len(dtrps[0])

    for i in range(n_tasks):
        fig, ax = plt.subplots(figsize=(9, 5))


        flat_values = []
        for rp in dtrps:
            row = rp.iloc[i]
            flat_values += [
                row["mean_A"], row["mean_B"],
                row["error_A"], row["error_B"]
            ]

        unit, scale = choose_display_unit(flat_values)


        all_means, all_errs = [], []
        y_positions, pair_centers = [], []

        colors = {"n4j": "steelblue", "pst": "orange"}

        inner_gap = 0.85
        group_gap = 2.4
        y = 0

        for p in range(n_pairs):
            row = dtrps[p].iloc[i]

            mean_A = row["mean_A"] * scale
            mean_B = row["mean_B"] * scale
            err_A = row["error_A"] * scale
            err_B = row["error_B"] * scale

            y_A = y
            y_B = y + inner_gap

            y_positions += [y_A, y_B]
            pair_centers.append((y_A + y_B) / 2)

            all_means += [mean_A, mean_B]
            all_errs += [err_A, err_B]

            y += group_gap


        bars = ax.barh(
            y_positions,
            all_means,
            xerr=all_errs,
            capsize=6,
            color=[colors["n4j"], colors["pst"]] * n_pairs
        )


        ax.set_xscale("symlog", linthresh=max(all_means) * 0.01)


        ax.margins(x=0.23, y=0.15)
        ax.set_xlim(left=0)

        for bar, mean, err in zip(bars, all_means, all_errs):

            x = bar.get_width() + err + (bar.get_width() * 0.16)
            y = bar.get_y() + bar.get_height() / 2

            ax.text(
                x,
                y,
                f"{mean:.2f} {unit}",
                ha="left",
                va="center",
                fontsize=9,
                fontweight="bold"
            )


        for idx, center in enumerate(pair_centers):
            ax.text(
                -0.05,
                center,
                dataset_nums[idx],
                transform=ax.get_yaxis_transform(),
                ha="right",
                va="center",
                fontsize=9,
                fontweight="bold",
                alpha=0.85
            )

        for p in range(n_pairs):
            row = dtrps[p].iloc[i]
            base = p * 2

            bar_A = bars[base]
            bar_B = bars[base + 1]

            y_top = max( bar_A.get_y() + bar_A.get_height(), bar_B.get_y() + bar_B.get_height() ) + 0.25

            x_center = 0.5

            if np.isnan(row["p_value"]):
                text = "p-value: n/a"
            else:
                text = f"p-value= {row['p_value']:.2g}, Hedges' g= {row["effect_size"]:.2f}"

            ax.text(
                x_center,
                y_top,
                text,
                transform=ax.get_yaxis_transform(),
                ha="center",
                va="bottom",
                fontsize=9,
                bbox=dict(
                    facecolor="white",
                    edgecolor="none",
                    alpha=0.7,
                    boxstyle="round,pad=0.2"
                )
            )

        for p in range(n_pairs):
            row = dtrps[p].iloc[i]
            base = p * 2

            bar_A = bars[base]
            bar_B = bars[base + 1]

            if row["significance"] == "significant":
                if row["winner"] == "A":
                    bar_A.set_edgecolor("green")
                    bar_A.set_linewidth(2)
                    bar_B.set_edgecolor("red")
                    bar_B.set_linewidth(2)
                else:
                    bar_B.set_edgecolor("green")
                    bar_B.set_linewidth(2)
                    bar_A.set_edgecolor("red")
                    bar_A.set_linewidth(2)

        extra_space = group_gap * 0.5

        ax.set_ylim(-2, y + extra_space)
        ax.set_yticks([])
        ax.set_xlabel(f"Execution time [{unit}]")

        legend_elements = [
            Patch(facecolor=colors["pst"], label="PostgreSQL"),
            Patch(facecolor=colors["n4j"], label="Neo4j"),
            Patch(facecolor="white", edgecolor="green", linewidth=2, label="Faster (significant)"),
            Patch(facecolor="white", edgecolor="red", linewidth=2, label="Slower (significant)")
        ]
            
        ax.legend(handles=legend_elements, loc="lower right", fontsize=7)

        if importDt:
            ax.set_title(f"{titlePref} Data {titleSuff}")
            filename = os.path.join(output_dir, f"import_.{fmt}")
        else:
            ax.set_title(f"{titlePref} {task_strings[i]} {titleSuff}")
            filename = os.path.join(output_dir, f"task_{i+1}.{fmt}")


        plt.subplots_adjust(left=0.12, right=0.88)

        plt.savefig(filename, dpi=300)
        plt.close()

    print(f"Saved {n_tasks} multi-task plots to {output_dir}/")


dtrps = []
for dt in dataset_strings:
    n4j = load_summary_folder(base_path + dt + "/neo4j/results/benchmark_scr.benchmark.queries.N40{}-report.csv", 9)
    pst = load_summary_folder(base_path + dt + "/postgres/results/benchmark_scr.benchmark.queries.Ps0{}-report.csv", 9)
    n4j = n4j.reset_index(drop=True)
    pst = pst.reset_index(drop=True)
    
    if len(n4j) != len(pst):
        raise ValueError("Task count mismatch between environments")

    df = pd.DataFrame({
        "file_A": n4j["file"],
        "file_B": pst["file"],
        "mean_A": n4j["mean"],
        "mean_B": pst["mean"],
        "std_A": n4j["std"],
        "std_B": pst["std"],
        "n_A": n4j["n"],
        "n_B": pst["n"],
        "error_A": n4j["error"],
        "error_B": pst["error"],
    })
    rp = generate_report(df)
    dtrps.append(rp)


plot_multi_benchmark_report(dtrps, titleSuff="Query Mean Execution Time")

dtirps = []
for dt in dataset_strings:
    n4j = load_summary_folder(base_path + dt + "/neo4j/results/benchmark_scr.benchmark.queries.N4Import-report.csv", 1)
    pst = load_summary_folder(base_path + dt + "/postgres/results/benchmark_scr.benchmark.queries.PsImport-report.csv", 1)
    n4j = n4j.reset_index(drop=True)
    pst = pst.reset_index(drop=True)
    
    if len(n4j) != len(pst):
        raise ValueError("Task count mismatch between environments")

    df = pd.DataFrame({
        "file_A": n4j["file"],
        "file_B": pst["file"],
        "mean_A": n4j["mean"],
        "mean_B": pst["mean"],
        "std_A": n4j["std"],
        "std_B": pst["std"],
        "n_A": n4j["n"],
        "n_B": pst["n"],
        "error_A": n4j["error"],
        "error_B": pst["error"],
    })
    rp = generate_report(df)
    dtirps.append(rp)
plot_multi_benchmark_report(dtirps, importDt=True, titleSuff="Mean Import Time")