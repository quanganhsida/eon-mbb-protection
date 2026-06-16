import json
from pathlib import Path
from collections import defaultdict, deque


def edge_key(u,v):
    return tuple(sorted((u, v)))

def reconstruct_path(selected_arcs, source, target):
    """
    Reconstruct a path from selected directed arcs.
    """

    next_node = {}

    for u, v in selected_arcs:
        next_node[u] = v

    path = [source]
    current = source
    visited = {source}

    while current != target:
        if current not in next_node:
            break

        current = next_node[current]

        if current in visited:
            break

        path.append(current)
        visited.add(current)

    return path

def save_json(data, output_path: str):
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"[OK] Result saved to: {output_file}")

def compute_migration_order(migrated_demands, precedence_relations):
    """
    Convert precedence relations into a migration order.

    A precedence relation [k, h] means:
        k must be migrated before h.
    """

    nodes = set(migrated_demands)

    graph = defaultdict(list)
    indegree = {k: 0 for k in nodes}

    for k, h in precedence_relations:
        if k in nodes and h in nodes:
            graph[k].append(h)
            indegree[h] += 1

    queue = deque(sorted([k for k in nodes if indegree[k] == 0]))
    order = []

    while queue:
        k = queue.popleft()
        order.append(k)

        for h in sorted(graph[k]):
            indegree[h] -= 1

            if indegree[h] == 0:
                queue.append(h)

    if len(order) != len(nodes):
        raise ValueError(
            f"Cycle detected in precedence relations: {precedence_relations}"
        )

    return order


def format_migration_order(order):
    """
    Format migration order as a readable string.
    """
    return " -> ".join(map(str, order))

def get_nominal_paths(data, env=None):
    """
    Retrieve nominal paths from env or data.
    """
    if env is not None and hasattr(env, "nominal_paths"):
        return env.nominal_paths

    if "nominal_paths" in data:
        return data["nominal_paths"]

    return {}


def get_affected_demands(data, env=None):
    """
    Retrieve K_Z from env or data.
    """
    if env is not None:
        if hasattr(env, "K_Z"):
            return set(env.K_Z)
        if hasattr(env, "affected_demands"):
            return set(env.affected_demands)

    if "K_Z" in data:
        return set(data["K_Z"])

    if "affected_demands_KZ" in data:
        return set(data["affected_demands_KZ"])

    return set()


def is_really_migrated(k, migrated, nominal_paths, affected_demands):
    """
    A demand is kept in K' if:
      - it is directly affected by the failure zone, or
      - its path changes, or
      - its slot block changes.
    """

    if k in affected_demands:
        return True

    k_str = str(k)

    if k_str not in nominal_paths:
        return True

    nominal = nominal_paths[k_str]

    nominal_path = nominal["path"]
    nominal_slots = nominal["slot_block"]

    migrated_path = migrated["path"]
    migrated_slots = migrated["slot_block"]

    return (
        migrated_path != nominal_path
        or migrated_slots != nominal_slots
    )

def extract_solution(model, data, variables, env=None):
    x = variables["x"]
    p = variables["p"]

    K = data["K"]
    A = data["A"]
    Sk = data["Sk"]
    o = data["o"]
    d = data["d"]
    b = data["b"]

    nominal_paths = get_nominal_paths(data, env)
    affected_demands = get_affected_demands(data, env)

    candidate_paths = {}

    for k in K:
        selected = []

        for s in Sk[k]:
            arcs_s = [
                a
                for a in A
                if x[k, a, s].X > 0.5
            ]

            if arcs_s:
                selected.append((s, arcs_s))

        if not selected:
            continue

        # one selected starting slot
        start_slot, selected_arcs = selected[0]

        path = reconstruct_path(
            selected_arcs=selected_arcs,
            source=o[k],
            target=d[k],
        )

        slot_block = list(range(start_slot, start_slot + b[k]))

        candidate_paths[str(k)] = {
            "path": path,
            "start_slot": start_slot,
            "last_slot": start_slot + b[k] - 1,
            "slot_block": slot_block,
            "selected_arcs": [
                [u, v]
                for u, v in selected_arcs
            ],
        }

    migrated_paths = {}

    for k_str, migrated in candidate_paths.items():
        k = int(k_str)

        if is_really_migrated(
            k=k,
            migrated=migrated,
            nominal_paths=nominal_paths,
            affected_demands=affected_demands,
        ):
            migrated_paths[k_str] = migrated

    migrated_demands = sorted(
        int(k)
        for k in migrated_paths.keys()
    )

    precedence_relations = []

    for k in K:
        for h in K:
            if k != h and p[k, h].X > 0.5:
                if k in migrated_demands and h in migrated_demands:
                    precedence_relations.append([k, h])

    migration_order = compute_migration_order(
        migrated_demands=migrated_demands,
        precedence_relations=precedence_relations,
    )

    return {
        "migrated_demands_K_prime": migrated_demands,
        "migrated_paths": migrated_paths,
        "precedence_relations": precedence_relations,
        "migration_order": migration_order,
        "migration_order_text": format_migration_order(migration_order),
    }
