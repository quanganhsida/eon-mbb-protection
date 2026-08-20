import argparse
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


def load_summary(summary_csv):
    """
    Load comparison summary CSV.
    """

    summary_csv = Path(summary_csv)

    if not summary_csv.exists():
        raise FileNotFoundError(f"Summary CSV not found: {summary_csv}")

    data = pd.read_csv(summary_csv)

    return data


def save_bar_plot(data, x_col, y_col, title, ylabel, output_file):
    """
    Save a simple bar plot from the comparison summary.
    """

    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(7, 4))

    data.plot(
        kind="bar",
        x=x_col,
        y=y_col,
        ax=ax,
        legend=False,
    )

    ax.set_title(title)
    ax.set_xlabel("")
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()

    print(f"[OK] Figure saved to: {output_file}")


def save_grouped_migration_plot(data, output_file):
    """
    Plot route-only and route-and-spectrum migrations.
    """

    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    columns = [
        "num_route_only_migrations",
        "num_route_and_spectrum_migrations",
        "num_spectrum_changes",
    ]

    existing_columns = [
        col for col in columns
        if col in data.columns
    ]

    if not existing_columns:
        print("[WARNING] No migration columns found. Skipped.")
        return

    plot_data = data[["solver"] + existing_columns].set_index("solver")

    fig, ax = plt.subplots(figsize=(8, 4))

    plot_data.plot(
        kind="bar",
        ax=ax,
    )

    ax.set_title("Migration types: Gurobi vs Greedy")
    ax.set_xlabel("")
    ax.set_ylabel("Number of demands")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.legend(loc="best")

    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()

    print(f"[OK] Figure saved to: {output_file}")


def plot_all(summary_csv, output_dir, case_name):
    """
    Generate all comparison plots.
    """

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    data = load_summary(summary_csv)

    numeric_columns = [
        "recovery_ratio",
        "num_migrated_demands",
        "extra_migrations",
        "num_failed_demands",
        "max_used_slot",
        "total_migrated_path_length",
        "average_migrated_path_length",
        "running_time",
    ]

    for col in numeric_columns:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce").fillna(0)

    if "recovery_ratio" in data.columns:
        save_bar_plot(
            data=data,
            x_col="solver",
            y_col="recovery_ratio",
            title="Recovery ratio: Gurobi vs Greedy",
            ylabel="Recovery ratio",
            output_file=output_dir / f"{case_name}_recovery_ratio.pdf",
        )

    if "running_time" in data.columns:
        save_bar_plot(
            data=data,
            x_col="solver",
            y_col="running_time",
            title="Running time: Gurobi vs Greedy",
            ylabel="Seconds",
            output_file=output_dir / f"{case_name}_running_time.pdf",
        )

    if "max_used_slot" in data.columns:
        save_bar_plot(
            data=data,
            x_col="solver",
            y_col="max_used_slot",
            title="Maximum used slot: Gurobi vs Greedy",
            ylabel="Slot index",
            output_file=output_dir / f"{case_name}_max_used_slot.pdf",
        )

    if "total_migrated_path_length" in data.columns:
        save_bar_plot(
            data=data,
            x_col="solver",
            y_col="total_migrated_path_length",
            title="Total migrated path length: Gurobi vs Greedy",
            ylabel="Path length",
            output_file=output_dir / f"{case_name}_total_path_length.pdf",
        )

    save_grouped_migration_plot(
        data=data,
        output_file=output_dir / f"{case_name}_migration_types.pdf",
    )


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--summary_csv", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--case_name", required=True)

    return parser.parse_args()


def main():
    args = parse_args()

    plot_all(
        summary_csv=args.summary_csv,
        output_dir=args.output_dir,
        case_name=args.case_name,
    )


if __name__ == "__main__":
    main()
