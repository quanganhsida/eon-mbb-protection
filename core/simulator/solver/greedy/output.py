from pathlib import Path
import json


def compute_total_path_length(migrated_paths):
    """
    Compute the total length of all migrated paths.
    """

    total_length = 0.0

    for migrated in migrated_paths.values():
        total_length += float(migrated.get("path_length", 0.0))

    return total_length


def compute_max_used_slot(migrated_paths):
    """
    Compute the maximum slot index used by migrated paths.
    """

    max_used_slot = 0

    for migrated in migrated_paths.values():
        slot_block = migrated.get("slot_block", [])

        if slot_block:
            max_used_slot = max(max_used_slot, max(slot_block))

    return max_used_slot


def build_greedy_solution(
    env,
    status,
    migrated_paths,
    migration_order,
    running_time,
    message="",
):
    """
    Build a Greedy solution dictionary compatible with the Gurobi output format.
    """

    # Basic instance information.
    instance_name = getattr(env, "name", "")
    failure_links = list(getattr(env, "failure_links", []))
    affected_demands = sorted(list(getattr(env, "affected_demands", [])))

    # Demands effectively rerouted by the Greedy heuristic.
    migrated_demands = sorted(
        int(demand_id)
        for demand_id in migrated_paths.keys()
    )

    # Simple metrics for later comparison with the MILP/Gurobi model.
    total_path_length = compute_total_path_length(migrated_paths)
    max_used_slot = compute_max_used_slot(migrated_paths)

    solution = {
        "status": status,
        "solver": "greedy",
        "message": message,
        "instance": instance_name,
        "failure_links": failure_links,
        "affected_demands_KZ": affected_demands,
        "migrated_demands_K_prime": migrated_demands,
        "migration_order": migration_order,
        "migration_order_text": " -> ".join(map(str, migration_order)),
        "migrated_paths": migrated_paths,
        "precedence_relations": [],
        "objective_value": None,
        "total_path_length": total_path_length,
        "max_used_slot": max_used_slot,
        "number_of_affected_demands": len(affected_demands),
        "number_of_migrated_demands": len(migrated_demands),
        "running_time": running_time,
    }

    return solution


def write_greedy_solution(solution, solution_path: str):
    """
    Write the Greedy solution to a JSON file.
    """

    output_file = Path(solution_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8") as f:
        json.dump(solution, f, indent=2)

    print(f"[OK] Greedy solution saved to: {output_file}")
