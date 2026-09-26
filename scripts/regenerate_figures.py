# scripts/regenerate_figures.py

import os
import csv

import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(__file__))
AGG_DIR = os.path.join(ROOT, "logs", "aggregated")
FIG_DIR = os.path.join(ROOT, "results", "figures")
TABLE_DIR = os.path.join(ROOT, "results", "tables")


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def load_summary():
    path = os.path.join(AGG_DIR, "summary_by_condition.csv")
    data = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # convert numerics
            for k in ("success", "mean_risk", "max_risk", "steps"):
                row[k] = float(row[k])
            data.append(row)
    return data


def plot_success_by_condition(summary):
    ensure_dir(FIG_DIR)
    conds = [row["condition"] for row in summary]
    success = [row["success"] for row in summary]

    plt.figure()
    plt.bar(conds, success, color=["gray", "blue", "orange", "green"])
    plt.ylim(0, 1)
    plt.ylabel("Success rate")
    plt.xlabel("Condition")
    plt.title("Task success by condition (A–D)")
    out_path = os.path.join(FIG_DIR, "success_by_condition.png")
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()
    print(f"[INFO] Wrote {out_path}")


def plot_mean_risk_by_condition(summary):
    ensure_dir(FIG_DIR)
    conds = [row["condition"] for row in summary]
    mean_risk = [row["mean_risk"] for row in summary]

    plt.figure()
    plt.bar(conds, mean_risk, color=["gray", "blue", "orange", "green"])
    plt.ylabel("Mean structural risk R_t")
    plt.xlabel("Condition")
    plt.title("Mean structural risk by condition (A–D)")
    out_path = os.path.join(FIG_DIR, "mean_risk_by_condition.png")
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()
    print(f"[INFO] Wrote {out_path}")


def write_main_metrics_table(summary):
    ensure_dir(TABLE_DIR)
    path = os.path.join(TABLE_DIR, "main_metrics_table.md")
    with open(path, "w") as f:
        f.write("| Condition | Success | Mean risk | Max risk | Steps |\n")
        f.write("|-----------|---------|-----------|----------|-------|\n")
        for row in summary:
            f.write(
                f"| {row['condition']} "
                f"| {row['success']:.2f} "
                f"| {row['mean_risk']:.3f} "
                f"| {row['max_risk']:.3f} "
                f"| {int(row['steps'])} |\n"
            )
    print(f"[INFO] Wrote {path}")


def main():
    summary = load_summary()
    plot_success_by_condition(summary)
    plot_mean_risk_by_condition(summary)
    write_main_metrics_table(summary)


if __name__ == "__main__":
    main()