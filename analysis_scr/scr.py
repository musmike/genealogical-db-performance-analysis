from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import t as t_dist
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import MultipleLocator
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
dataset_nums_short = ["1000", "10000", "100000"]

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

def tukey_upper_filter(values, k=1.5, return_mask=False):
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]

    if arr.size < 4:
        mask = np.ones(arr.size, dtype=bool)
        return (arr, mask) if return_mask else arr

    q1 = np.percentile(arr, 25)
    q3 = np.percentile(arr, 75)
    iqr = q3 - q1

    if iqr == 0:
        mask = np.ones(arr.size, dtype=bool)
        return (arr, mask) if return_mask else arr

    upper_fence = q3 + k * iqr
    mask = arr <= upper_fence
    filtered = arr[mask]

    return (filtered, mask) if return_mask else filtered

def summarize_values(values):
    filtered = tukey_upper_filter(values)
    n = len(filtered)

    if n == 0:
        return {
            "n": 0,
            "mean": np.nan,
            "error": np.nan,
            "std": np.nan,
        }

    mean = np.mean(filtered)

    std = np.std(filtered, ddof=1) if n > 1 else 0.0

    error = std / np.sqrt(n) if n > 1 else 0.0

    return {
        "n": n,
        "mean": mean,
        "error": error,
        "std": std,
    }

def remove_outliers_from_dataframe(df, value_column="mean", k=1.5):
    values = df[value_column].to_numpy(dtype=float)

    finite_mask = np.isfinite(values)
    filtered_values, retained_mask = tukey_upper_filter(
        values[finite_mask], k=k, return_mask=True
    )

    full_mask = np.zeros(len(df), dtype=bool)
    full_mask[np.where(finite_mask)[0]] = retained_mask

    return df.loc[full_mask].reset_index(drop=True)

def load_raw_folder(pattern, n_files, value_column=4):
    if value_column not in (4, 5):
        raise ValueError("value_column must be 4 or 5 (1-based indexing).")

    col_idx = value_column - 1
    results = []

    for i in range(1, n_files + 1):
        path = Path(pattern.format(i))
        if not path.exists():
            continue

        try:
            df = pd.read_csv(path)

            if col_idx >= df.shape[1]:
                raise ValueError(
                    f"{path.name} has only {df.shape[1]} columns; "
                    f"cannot read column {value_column}."
                )

            series = pd.to_numeric(df.iloc[:, col_idx], errors="coerce").dropna()

            if series.empty:
                raise ValueError(
                    f"No numeric values found in column {value_column}."
                )

            values_kb = series.to_numpy(dtype=float) / 1000.0

            stats = summarize_values(values_kb)

            results.append({
                "file": path.name,
                "n": stats["n"],
                "mean": stats["mean"],
                "error": stats["error"],
                "std": stats["std"],
            })

        except Exception as e:
            print(f"Failed to load {path}: {e}")

    return pd.DataFrame(results)

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

    # welch's t-test
    df["t_stat"] = df.apply(welch_t, axis=1)
    df["df"] = df.apply(welch_df, axis=1)

    df["p_value"] = df.apply(
        lambda r: 2 * t_dist.sf(abs(r["t_stat"]), r["df"])
        if np.isfinite(r["t_stat"]) and np.isfinite(r["df"])
        else np.nan,
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
        practical_sig = abs(row["effect_size"]) > 0.2  

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
    importDt=False,
    output_dir="../results/benchmark_plots",
    fmt="png"
):
    import os
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    os.makedirs(output_dir, exist_ok=True)

    def fmt_sig(x):
        if abs(x) < 10:
            return f"{x:.1f}"
        else:
            return f"{x:g}"

    def _plot(font_offset=0, show_stats=True, suffix=""):
        n_pairs = len(dtrps)
        n_tasks = len(dtrps[0])

        for i in range(n_tasks):

            with plt.rc_context({
                "font.size": plt.rcParams["font.size"] + font_offset
            }):

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
                        x, y,
                        f"{mean:.1f}" if mean < 100 else f"{int(mean)}",
                        ha="left",
                        va="center",
                        fontsize=10 + font_offset,
                        fontweight="bold"
                    )

                if show_stats:
                    for p in range(n_pairs):
                        row = dtrps[p].iloc[i]
                        base = p * 2

                        bar_A = bars[base]
                        bar_B = bars[base + 1]

                        y_top = max(
                            bar_A.get_y() + bar_A.get_height(),
                            bar_B.get_y() + bar_B.get_height()
                        ) + 0.25

                        if np.isnan(row["p_value"]):
                            text = "p-value: n/a"
                        else:
                            text = f"p-value= {row['p_value']:.2g}, Hedges' g= {row['effect_size']:.2f}"

                        ax.text(
                            0.5,
                            y_top,
                            text,
                            transform=ax.get_yaxis_transform(),
                            ha="center",
                            va="bottom",
                            fontsize=10 + font_offset,
                            bbox=dict(
                                facecolor="white",
                                edgecolor="none",
                                alpha=0.7,
                                boxstyle="round,pad=0.2"
                            )
                        )

                extra_space = group_gap * 0.5

                ax.set_ylim(-2, y + extra_space)
                ax.set_ylabel("Dataset's number of people")
                ax.set_yticks(pair_centers)
                ax.set_yticklabels(dataset_nums_short)
                ax.set_xlabel(f"Execution time [{unit}]")

                legend_elements = [
                    Patch(facecolor=colors["pst"], label="PostgreSQL"),
                    Patch(facecolor=colors["n4j"], label="Neo4j"),
                ]

                ax.legend(handles=legend_elements, loc="lower right", fontsize=7)

                if importDt:
                    filename = os.path.join(output_dir, f"import_{suffix}.{fmt}")
                else:
                    filename = os.path.join(output_dir, f"task_{i+1}_{suffix}.{fmt}")

                plt.subplots_adjust(left=0.12, right=0.88)
                plt.savefig(filename, dpi=300 + 50 * font_offset)
                plt.close()

    _plot(font_offset=0, show_stats=True, suffix="default")

    _plot(font_offset=2, show_stats=False, suffix="scaled")

    print(f"Saved scaled + default plots to {output_dir}/")


def prepare_three_way_memory_plot_data(pg_df, neo4j_df, neo4j_heap_df):
    min_len = min(len(pg_df), len(neo4j_df), len(neo4j_heap_df))

    rows = []
    for i in range(min_len):
        rows.append({
            "group": f"S{i+1}",
            "pg_mean": pg_df.iloc[i]["mean"],
            "pg_error": pg_df.iloc[i]["error"],
            "neo4j_mean": neo4j_df.iloc[i]["mean"],
            "neo4j_error": neo4j_df.iloc[i]["error"],
            "heap_mean": neo4j_heap_df.iloc[i]["mean"],
            "heap_error": neo4j_heap_df.iloc[i]["error"],
        })

    return pd.DataFrame(rows)


def plot_memory_scenarios_for_dataset(
    pg_df,
    neo4j_df,
    neo4j_heap_df,
    title,
    output_path="../results/benchmark_plots",
    dataset_name=None,
    figsize=(12, 6),
    fmt="png",
    memory_limit_mib=3600
):

    

    def _plot(font_offset=0, suffix=""):
        plot_df = prepare_three_way_memory_plot_data(
            pg_df, neo4j_df, neo4j_heap_df
        )

        if plot_df.empty:
            raise ValueError("No data available for plotting.")

        with plt.rc_context({
            "font.size": plt.rcParams["font.size"] + font_offset
        }):

            pg_means = plot_df["pg_mean"].to_numpy()
            neo_means = plot_df["neo4j_mean"].to_numpy()
            heap_means = plot_df["heap_mean"].to_numpy()

            groups = plot_df["group"].tolist()
            x = np.arange(len(groups))
            width = 0.18

            fig, ax = plt.subplots(figsize=figsize)

            bars_pg = ax.bar(x - width, pg_means, width, color="orange", label="PostgreSQL")
            bars_neo = ax.bar(x, neo_means, width, color="powderblue", label="Neo4j")
            bars_heap = ax.bar(x + width, heap_means, width, color="seagreen", label="Neo4j Heap")
            def add_values(bar_container):
                for bar in bar_container:
                    h = bar.get_height()
                    if np.isnan(h):
                        continue
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        h,
                        f"{h / 1000:.0f}",
                        ha="center",
                        va="bottom",
                        fontsize=9 + font_offset
                    )
            add_values(bars_pg)
            add_values(bars_neo)
            add_values(bars_heap)
            ax.set_xticks(x)
            g_groups = [g[0] + g[2:] for g in groups]
            ax.set_xticklabels(groups)

            ax.set_ylabel("Memory usage [MB]")
            ax.set_xlabel("Scenarios")
            ax.grid(axis="y", alpha=0.3)
            tick_step_kb = 1000 * 1000
            ax.yaxis.set_major_locator(MultipleLocator(tick_step_kb))
            ax.yaxis.set_major_formatter( lambda x, pos: f"{x / 1000:.0f}" )
            ax.legend(
                loc="upper center",
                bbox_to_anchor=(0.5, -0.12),
                ncol=4,
                frameon=True
            )

            plt.tight_layout()

            if output_path:
                os.makedirs(output_path, exist_ok=True)
                name = dataset_name or "memory"
                filename = os.path.join(output_path, f"{name}_{suffix}.{fmt}")
                plt.savefig(filename, dpi=300, bbox_inches="tight")

            plt.close()

    _plot(0, "default")
    _plot(2, "scaled")

    return None


def generate_memory_scenario_plots(
    scenario_count=9,
    output_path="../results/benchmark_plots",
    fmt="png",
    memory_limit_mib=3600
):
    results = {}

    for dt in dataset_strings:
        pth = f"{base_path}{dt}/memory/"


        pg = load_raw_folder(
            pth + "memory_Ps0{}.csv",
            scenario_count,
            value_column=4
        )

        n4 = load_raw_folder(
            pth + "memory_N40{}.csv",
            scenario_count,
            value_column=5
        )

        n4h = load_raw_folder(
            pth + "heap_N40{}.csv",
            scenario_count,
            value_column=4
        )

        title = f"{dt.capitalize() + " Dataset"} Memory Usage by Scenario"

        plot_df = plot_memory_scenarios_for_dataset(
            pg_df=pg,
            neo4j_df=n4,
            neo4j_heap_df=n4h,
            title=title,
            dataset_name=dt,
            output_path=output_path,
            fmt=fmt,
            memory_limit_mib=memory_limit_mib
        )

        results[dt] = plot_df

    return results

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


plot_multi_benchmark_report(dtrps)

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

def plot_disk_usage_comparison(
    output_path="../results/benchmark_plots",
    filename="disk_usage_comparison.png",
    figsize=(9, 6)
):
    import os
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt


    def bytes_to_mib(v):
        return v / (1000.0 * 1000.0)


    fig, axes = plt.subplots(
        1,
        len(dataset_strings),
        figsize=figsize,
        sharey=False
    )



    for i, (ax, size) in enumerate(zip(axes, dataset_strings)):

        disk_dir = os.path.join(
            base_path,
            size,
            "disk"
        )

        neo_path = os.path.join(
            disk_dir,
            "disk_size_neo4j.csv"
        )

        pg_path = os.path.join(
            disk_dir,
            "disk_size_postgres.csv"
        )


        neo_df = pd.read_csv(neo_path)
        pg_df = pd.read_csv(pg_path)


        neo_bytes = pd.to_numeric(
            neo_df.iloc[0, 1],
            errors="coerce"
        )

        pg_bytes = pd.to_numeric(
            pg_df.iloc[0, 1],
            errors="coerce"
        )


        neo_mib = bytes_to_mib(neo_bytes)
        pg_mib = bytes_to_mib(pg_bytes)


        labels = ["PostgreSQL", "Neo4j"]
        values = [pg_mib, neo_mib]
        colors = ["orange", "steelblue"]

        bars = ax.bar(
            labels,
            values,
            color=colors,
            width=0.35
        )


        for bar, value in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value,
                f"{value:.1f}",
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold"
            )


        ax.set_title(f"{size.capitalize()} Dataset")
        if i == 0:
            ax.set_ylabel("Disk usage [MB]")
        ax.grid(axis="y", alpha=0.3)

        ax.set_ylim(top=max(values) * 1.15)


    fig.suptitle(
        "Database Disk Usage Comparison",
        fontsize=16,
        fontweight="bold"
    )

    plt.tight_layout()


    os.makedirs(output_path, exist_ok=True)

    full_output = os.path.join(
        output_path,
        filename
    )

    plt.savefig(
        full_output,
        dpi=300,
        bbox_inches="tight"
    )


    return full_output


plot_multi_benchmark_report(dtirps, importDt=True)

pg_dtmrps = []
neo4j_dtmrps = []
neo4jh_dtmrps = []
for dt in dataset_strings:
    pth = f"{base_path}{dt}/memory/"

    pg = load_raw_folder(
        pth + "memory_Ps0{}.csv",
        9,
        value_column=4
    )

    n4 = load_raw_folder(
        pth + "memory_N40{}.csv",
        9,
        value_column=5
    )

    n4h = load_raw_folder(
        pth + "heap_N40{}.csv",
        9,
        value_column=4
    )
    pg_st = summarize_values(pg["mean"].dropna().to_numpy())
    n4_st = summarize_values(n4["mean"].dropna().to_numpy())
    n4h_st = summarize_values(n4h["mean"].dropna().to_numpy())
    pg_dtmrps.append({
        "file": dt,
        **pg_st
    })
    neo4j_dtmrps.append({
        "file":dt,
        **n4_st
    })
    neo4jh_dtmrps.append({
        "file":dt,
        **n4h_st
    })

pg_df = pd.DataFrame(pg_dtmrps)
n4_df = pd.DataFrame(neo4j_dtmrps)
n4h_df = pd.DataFrame(neo4jh_dtmrps)

generate_memory_scenario_plots()
plot_disk_usage_comparison()