import argparse
import csv
import json
from pathlib import Path


def load_json(path):
    """
    Load a JSON file.
    """

    input_file = Path(path)

    if not input_file.exists():
        raise FileNotFoundError(f"File not found: {input_file}")

    with input_file.open("r", encoding="utf-8") as f:
        return json.load(f)


def edge_key(u, v):
    """
    Return an undirected edge key.
    """

    return tuple(sorted((u, v)))


def path_to_edges(path):
    """
    Convert a node path into a list of undirected edges.
    """

    return [
        edge_key(path[i], path[i + 1])
        for i in range(len(path) - 1)
    ]


def build_edge_length_map(instance):
    """
    Build a dictionary edge -> length from the instance.
    """

    edge_length = {}

    for link in instance.get("links", []):
        u = link["u"]
        v = link["v"]
        length = float(link.get("length", 1.0))
        edge_length[edge_key(u, v)] = length

    return edge_length


def compute_path_length(path, edge_length):
    """
    Compute the length of one path.
    """

    total = 0.0

    for edge in path_to_edges(path):
        total += edge_length.get(edge, 1.0)

    return total


def normalize_status(solution):
    """
    Normalize solver status.
    """

    solver = solution.get("solver", "")

    if solver == "greedy":
        return solution.get("status", "UNKNOWN")

    if solver == "gurobi":
        if "status_text" in solution:
            return solution["status_text"]

        status_code = solution.get("status", None)

        gurobi_status = {
            2: "OPTIMAL",
            3: "INFEASIBLE",
            4: "INF_OR_UNBD",
            5: "UNBOUNDED",
            9: "TIME_LIMIT",
        }

        return gurobi_status.get(status_code, f"STATUS_{status_code}")

    return str(solution.get("status", "UNKNOWN"))


def get_slot_block(lightpath):
    """
    Get slot block from a lightpath dictionary.
    """

    if lightpath is None:
        return []

    return list(lightpath.get("slot_block", []))


def get_path(lightpath):
    """
    Get path from a lightpath dictionary.
    """

    if lightpath is None:
        return []

    return list(lightpath.get("path", []))


def classify_migration(nominal, migrated):
    """
    Classify migration type.
    """

    if migrated is None:
        return "not_migrated"

    nominal_path = get_path(nominal)
    migrated_path = get_path(migrated)

    nominal_slots = get_slot_block(nominal)
    migrated_slots = get_slot_block(migrated)

    path_changed = nominal_path != migrated_path
    spectrum_changed = nominal_slots != migrated_slots

    if path_changed and spectrum_changed:
        return "route_and_spectrum"

    if path_changed and not spectrum_changed:
        return "route_only"

    if not path_changed and spectrum_changed:
        return "spectrum_only"

    return "unchanged"


def compute_solution_metrics(instance, solution, solver_name):
    """
    Compute comparable metrics for one solver.
    """

    nominal_paths = instance.get("nominal_paths", {})
    edge_length = build_edge_length_map(instance)

    affected_demands = set(
        int(k)
        for k in solution.get("affected_demands_KZ", [])
    )

    migrated_paths = solution.get("migrated_paths", {})

    migrated_demands = set(
        int(k)
        for k in solution.get("migrated_demands_K_prime", migrated_paths.keys())
    )

    recovered_affected = affected_demands & migrated_demands
    extra_migrations = migrated_demands - affected_demands

    failed_demands = solution.get("failed_demands", [])
    failed_demands = [int(k) for k in failed_demands]

    route_only = 0
    route_and_spectrum = 0
    spectrum_only = 0
    unchanged = 0
    spectrum_changes = 0

    total_path_length = 0.0
    max_used_slot = 0

    for demand_id in sorted(migrated_demands):
        demand_id_str = str(demand_id)

        nominal = nominal_paths.get(demand_id_str)
        migrated = migrated_paths.get(demand_id_str)

        migration_type = classify_migration(nominal, migrated)

        if migration_type == "route_only":
            route_only += 1
        elif migration_type == "route_and_spectrum":
            route_and_spectrum += 1
        elif migration_type == "spectrum_only":
            spectrum_only += 1
        elif migration_type == "unchanged":
            unchanged += 1

        if migrated is not None:
            migrated_slots = get_slot_block(migrated)
            migrated_path = get_path(migrated)

            if nominal is not None:
                if get_slot_block(nominal) != migrated_slots:
                    spectrum_changes += 1

            if migrated_slots:
                max_used_slot = max(max_used_slot, max(migrated_slots))

            total_path_length += compute_path_length(
                path=migrated_path,
                edge_length=edge_length,
            )

    num_affected = len(affected_demands)
    num_migrated = len(migrated_demands)
    num_recovered = len(recovered_affected)

    if num_affected > 0:
        recovery_ratio = num_recovered / num_affected
    else:
        recovery_ratio = 1.0

    if num_migrated > 0:
        average_path_length = total_path_length / num_migrated
    else:
        average_path_length = 0.0

    failure_links = solution.get(
        "failure_links",
        instance.get("failure", {}).get("failed_links", []),
    )

    return {
        "instance": instance.get("name", ""),
        "num_demands": len(instance.get("demands", [])),
        "num_failure_links": len(failure_links),
        "solver": solver_name,
        "status": normalize_status(solution),
        "objective_value": solution.get("objective_value", ""),
        "num_affected_demands": num_affected,
        "num_recovered_affected_demands": num_recovered,
        "recovery_ratio": round(recovery_ratio, 6),
        "num_migrated_demands": num_migrated,
        "extra_migrations": len(extra_migrations),
        "num_failed_demands": len(failed_demands),
        "num_route_only_migrations": route_only,
        "num_route_and_spectrum_migrations": route_and_spectrum,
        "num_spectrum_only_migrations": spectrum_only,
        "num_unchanged_migrations": unchanged,
        "num_spectrum_changes": spectrum_changes,
        "total_migrated_path_length": round(total_path_length, 6),
        "average_migrated_path_length": round(average_path_length, 6),
        "max_used_slot": max_used_slot,
        "running_time": round(float(solution.get("running_time", 0.0)), 6),
        "migration_order": solution.get("migration_order_text", ""),
    }


def format_path(path):
    """
    Format path for CSV.
    """

    if not path:
        return ""

    return " -> ".join(map(str, path))


def format_slots(slot_block):
    """
    Format slot block for CSV.
    """

    if not slot_block:
        return ""

    return f"[{min(slot_block)}; {max(slot_block)}]"


def build_by_demand_rows(instance, gurobi_solution, greedy_solution):
    """
    Build per-demand comparison rows.
    """

    nominal_paths = instance.get("nominal_paths", {})

    gurobi_paths = gurobi_solution.get("migrated_paths", {})
    greedy_paths = greedy_solution.get("migrated_paths", {})

    affected_demands = set(
        int(k)
        for k in gurobi_solution.get(
            "affected_demands_KZ",
            greedy_solution.get("affected_demands_KZ", []),
        )
    )

    all_demands = set(affected_demands)

    all_demands.update(int(k) for k in gurobi_paths.keys())
    all_demands.update(int(k) for k in greedy_paths.keys())

    rows = []

    for demand_id in sorted(all_demands):
        demand_id_str = str(demand_id)

        nominal = nominal_paths.get(demand_id_str)
        gurobi = gurobi_paths.get(demand_id_str)
        greedy = greedy_paths.get(demand_id_str)

        rows.append(
            {
                "demand": demand_id,
                "affected": demand_id in affected_demands,
                "nominal_path": format_path(get_path(nominal)),
                "nominal_fs": format_slots(get_slot_block(nominal)),
                "gurobi_path": format_path(get_path(gurobi)),
                "gurobi_fs": format_slots(get_slot_block(gurobi)),
                "gurobi_migration_type": classify_migration(nominal, gurobi),
                "greedy_path": format_path(get_path(greedy)),
                "greedy_fs": format_slots(get_slot_block(greedy)),
                "greedy_migration_type": classify_migration(nominal, greedy),
            }
        )

    return rows


def write_csv(rows, output_file):
    """
    Write rows to CSV.
    """

    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        return

    with output_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] CSV written to: {output_file}")


def write_summary_text(summary_rows, output_file):
    """
    Write a readable text summary.
    """

    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8") as f:
        f.write("Gurobi vs Greedy comparison\n")
        f.write("=" * 32)
        f.write("\n\n")

        for row in summary_rows:
            f.write(f"Solver: {row['solver']}\n")
            f.write(f"  status                       : {row['status']}\n")
            f.write(f"  affected demands |K_Z|       : {row['num_affected_demands']}\n")
            f.write(f"  recovered affected demands   : {row['num_recovered_affected_demands']}\n")
            f.write(f"  recovery ratio               : {row['recovery_ratio']}\n")
            f.write(f"  migrated demands |K'|        : {row['num_migrated_demands']}\n")
            f.write(f"  extra migrations             : {row['extra_migrations']}\n")
            f.write(f"  route-only migrations        : {row['num_route_only_migrations']}\n")
            f.write(f"  route-spectrum migrations    : {row['num_route_and_spectrum_migrations']}\n")
            f.write(f"  spectrum changes             : {row['num_spectrum_changes']}\n")
            f.write(f"  max used slot                : {row['max_used_slot']}\n")
            f.write(f"  total migrated path length   : {row['total_migrated_path_length']}\n")
            f.write(f"  running time                 : {row['running_time']} s\n")
            f.write(f"  migration order              : {row['migration_order']}\n")
            f.write("\n")

    print(f"[OK] Summary written to: {output_file}")


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--instance_file", required=True)
    parser.add_argument("--gurobi_solution_file", required=True)
    parser.add_argument("--greedy_solution_file", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--case_name", required=True)

    return parser.parse_args()


def main():
    args = parse_args()

    instance = load_json(args.instance_file)
    gurobi_solution = load_json(args.gurobi_solution_file)
    greedy_solution = load_json(args.greedy_solution_file)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_rows = [
        compute_solution_metrics(
            instance=instance,
            solution=gurobi_solution,
            solver_name="gurobi",
        ),
        compute_solution_metrics(
            instance=instance,
            solution=greedy_solution,
            solver_name="greedy",
        ),
    ]

    by_demand_rows = build_by_demand_rows(
        instance=instance,
        gurobi_solution=gurobi_solution,
        greedy_solution=greedy_solution,
    )

    summary_csv = output_dir / f"{args.case_name}_comparison_summary.csv"
    by_demand_csv = output_dir / f"{args.case_name}_comparison_by_demand.csv"
    summary_txt = output_dir / f"{args.case_name}_comparison_summary.txt"

    write_csv(summary_rows, summary_csv)
    write_csv(by_demand_rows, by_demand_csv)
    write_summary_text(summary_rows, summary_txt)

    print("[OK] Comparison completed")


if __name__ == "__main__":
    main()
