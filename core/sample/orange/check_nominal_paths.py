import argparse
import json
from pathlib import Path


def edge_key(u, v):
    return tuple(sorted((u, v)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance_file", required=True)
    args = parser.parse_args()

    instance = json.loads(Path(args.instance_file).read_text())

    graph_edges = {
        edge_key(link["u"], link["v"])
        for link in instance["links"]
    }

    demands = {
        demand["id"]: demand
        for demand in instance["demands"]
    }

    nominal_paths = instance["nominal_paths"]

    has_error = False

    for demand_id_str, nominal in nominal_paths.items():
        demand_id = int(demand_id_str)
        demand = demands[demand_id]

        source = demand["source"]
        target = demand["target"]
        path = nominal["path"]

        if path[0] != source or path[-1] != target:
            has_error = True
            print(f"[ERROR] Demand {demand_id}: wrong endpoints")
            print(f"        source-target = {source} -> {target}")
            print(f"        path          = {path}")

        for i in range(len(path) - 1):
            e = edge_key(path[i], path[i + 1])

            if e not in graph_edges:
                has_error = True
                print(f"[ERROR] Demand {demand_id}: non-topology edge {e}")
                print(f"        path = {path}")

    if not has_error:
        print("[OK] All nominal paths are valid.")
    else:
        print("[RESULT] Some nominal paths are invalid.")


if __name__ == "__main__":
    main()
