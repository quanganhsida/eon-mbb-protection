import csv
import json
import re
from pathlib import Path
from util import get_orange_prepare_args
from collections import defaultdict, deque


DEMAND_PATTERN = re.compile(
    r"#(?P<id>\d+)\.\s+"
    r"(?P<source>\d+)\s+--\s+(?P<target>\d+)\."
    r".*?nbSlices C:\s+(?P<slots>\d+)"
)

PATH_ARC_PATTERN = re.compile(
    r"\((?P<u>\d+)--(?P<v>\d+),\s*(?P<last_slot>\d+)\)"
)


def read_links(link_file: Path):
    nodes = set()
    links = []

    with link_file.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")

        for row in reader:
            u = int(row["Origin"])
            v = int(row["Destination"])

            nodes.add(u)
            nodes.add(v)

            links.append(
                {
                    "id": int(row["Index"]),
                    "u": u,
                    "v": v,
                    "length": float(row["length"]),
                    "slots": int(row["slices"]),
                }
            )

    return sorted(nodes), links


def extract_section(lines, start_marker, stop_markers):
    start = None

    for i, line in enumerate(lines):
        if start_marker in line:
            start = i + 1
            break

    if start is None:
        return []

    end = len(lines)

    for j in range(start, len(lines)):
        if any(marker in lines[j] for marker in stop_markers):
            end = j
            break

    return lines[start:end]


def parse_demands(lines):
    """
    Reconstruct the path by append each nominal path but have not in ordered yet.
    """
    demand_section = extract_section(
        lines=lines,
        start_marker="--- The Demands ---",
        stop_markers=[
            "Time taken by optimization",
            "Total time taken",
        ],
    )

    demands = []

    for line in demand_section:
        match = DEMAND_PATTERN.search(line)

        if not match:
            continue

        demands.append(
            {
                "id": int(match.group("id")),
                "source": int(match.group("source")),
                "target": int(match.group("target")),
                "slots": int(match.group("slots")),
            }
        )

    return demands

def reconstruct_path_from_edges(arcs, source, target):
    """
    Reconstruct a COMPLETE source-target path from unordered edges.
    """

    adjacency = defaultdict(list)

    for u, v, _last_slot in arcs:
        adjacency[u].append(v)
        adjacency[v].append(u)

    queue = deque([source])
    parent = {source: None}

    while queue:
        u = queue.popleft()

        if u == target:
            break

        for v in adjacency[u]:
            if v not in parent:
                parent[v] = u
                queue.append(v)

    if target not in parent:
        raise ValueError(
            f"Cannot reconstruct path from {source} to {target}."
            f"Arcs = {arcs}"
        )

    path = []
    current = target

    while current is not None:
        path.append(current)
        current = parent[current]

    path.reverse()

    return path

def parse_slice_occupation(lines, demands):
    demand_by_id = {
        demand["id"]: demand
        for demand in demands
    }

    section = extract_section(
        lines=lines,
        start_marker="--- Slice occupation ---",
        stop_markers=[
            "Displaying OSNR",
            "Displaying data",
            "Output demands",
            "--- The Demands ---",
        ],
    )

    nominal_paths = {}
    current_demand = None
    current_arcs = []

    def flush_current():
        nonlocal current_demand, current_arcs, nominal_paths

        if current_demand is None or not current_arcs:
            return

        demand = demand_by_id[current_demand]
        source = demand["source"]
        target = demand["target"]

        path = reconstruct_path_from_edges(
            arcs=current_arcs,
            source=source,
            target=target,
        )

        last_slot = current_arcs[0][2]

        nominal_paths[str(current_demand)] = {
            "path": path,
            "last_slot": last_slot,
            "slot_block": [],
        }

    for raw_line in section:
        line = raw_line.strip()

        if not line:
            continue

        if line.startswith("For demand"):
            flush_current()

            current_demand = int(
                line.replace("For demand", "")
                .replace(":", "")
                .strip()
            )
            current_arcs = []
            continue

        match = PATH_ARC_PATTERN.search(line)

        if match and current_demand is not None:
            u = int(match.group("u"))
            v = int(match.group("v"))
            last_slot = int(match.group("last_slot"))
            current_arcs.append((u, v, last_slot))

    flush_current()

    return nominal_paths


def fix_slot_blocks_from_demands(nominal_paths, demands):
    """
    Compute real slot blocks of each demand.
    """
    b = {d["id"]: d["slots"] for d in demands}

    for demand_id_str, nominal in nominal_paths.items():
        demand_id = int(demand_id_str)
        nb_slots = b[demand_id]
        last_slot = nominal["last_slot"]

        nominal["slot_block"] = list(
            range(last_slot - nb_slots + 1, last_slot + 1)
        )

    return nominal_paths


def build_instance_name(execution_file: Path):
    return execution_file.stem.replace(".", "_").replace("-", "_")

# =====================================================================================
def edge_key(u,v):
    return tuple(sorted((u, v)))

# Convert a node path into undirected physical edges.
def path_to_edges(path):
    edges = []

    for i in range(len(path) - 1):
        u = path[i]
        v = path[i+1]
        edges.append(edge_key(u,v))

    return edges

# Automatically select the failure zone.
# Choose the edge crossed by the largest number of nominal paths.
def select_failure_zone(nominal_paths, num_failed_links=1):
    edge_count = {}

    for demand_id, nominal in nominal_paths.items():
        path = nominal["path"]

        for e in path_to_edges(path):
            edge_count[e] = edge_count.get(e,0) + 1

    if not edge_count:
        return []

    ranked_edges = sorted(
        edge_count.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    selected_edges = [
        list(edge)
        for edge, _count in ranked_edges[:num_failed_links]
    ]

    print("[INFO] Automatically selected failure zone:")
    for edge, count in ranked_edges[:num_failed_links]:
        print(f"    edge {edge[0]} -- {edge[1]} crossed by {count} demands.")

    return selected_edges

# Manually select the failure zone
def select_failure_zone_manual(links, failure_edge_u, failure_edge_v):
    u = int(failure_edge_u)
    v = int(failure_edge_v)

    target = edge_key(u, v)

    physical_edges = {
        edge_key(link["u"], link["v"])
        for link in links
    }

    if target not in physical_edges:
        raise ValueError(
            f"Manual failure edge {u} -- {v} does not exist in topology."
        )

    print("[INFO] Manually selected failure zone:")
    print(f"    edge {u} -- {v}")

    return [[u, v]]
# =====================================================================================


# =====================================================================================
# MAIN
# =====================================================================================
def prepare_orange_instance(link_file, execution_file, output_file, num_failed_links=1, failure_edge_u=None, failure_edge_v=None,):
    """
    Gather all informations into a JSON file.
    """
    link_file = Path(link_file)
    execution_file = Path(execution_file)
    output_file = Path(output_file)

    nodes, links = read_links(link_file)

    lines = execution_file.read_text(encoding="utf-8").splitlines()

    demands = parse_demands(lines)
    nominal_paths = parse_slice_occupation(lines, demands)
    nominal_paths = fix_slot_blocks_from_demands(nominal_paths, demands)

    if failure_edge_u is not None and failure_edge_v is not None:
        failed_links = select_failure_zone_manual(
            links=links,
            failure_edge_u=failure_edge_u,
            failure_edge_v=failure_edge_v,
        )
    else:
        failed_links = select_failure_zone(
            nominal_paths=nominal_paths,
            num_failed_links=num_failed_links,
        )

    instance = {
        "name": build_instance_name(execution_file),
        "nodes": nodes,
        "links": links,
        "demands": demands,
        "nominal_paths": nominal_paths,
        "failure": {
            "failed_links": failed_links
        },
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8") as f:
        json.dump(instance, f, indent=2)

    print(f"[OK] Orange instance saved to: {output_file}")
    print(f"     nodes         : {len(nodes)}")
    print(f"     links         : {len(links)}")
    print(f"     demands       : {len(demands)}")
    print(f"     nominal paths : {len(nominal_paths)}")


def main():
    args = get_orange_prepare_args()

    prepare_orange_instance(
        link_file=args.link_file,
        execution_file=args.execution_file,
        output_file=args.output_file,
        num_failed_links=args.num_failed_links,
        failure_edge_u=args.failure_edge_u,
        failure_edge_v=args.failure_edge_v,
    )


if __name__ == "__main__":
    main()
