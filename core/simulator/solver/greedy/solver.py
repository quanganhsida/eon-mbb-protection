from collections import defaultdict
from time import perf_counter
import random
import networkx as nx

from simulator.solver.greedy.output import (
    build_greedy_solution,
    write_greedy_solution,
)

SEARCH_BATCH_SIZE = 5
MAX_CANDIDATE_PATHS = 50
RANDOM_SEED = 0

def edge_key(u,v):
#     Return an undirected edge key
    return tuple(sorted((u,v)))

def path_to_edges(path):
#     Convert a node path into undirected edge keys
    return {
        edge_key(path[i], path[i + 1])
        for i in range(len(path) - 1)
    }

def get_failure_edges(env):
#     get forecasted failure zone Z
    return {
        edge_key(u, v)
        for u, v in getattr(env, "failure_links", [])
    }

def build_initial_occupation(env):
#     build the current spectrum occupation from nominal solution

    occupation = defaultdict(dict)

    for demand_id_str, nominal in env.nominal_paths.items():
        path       = nominal["path"]
        slot_block = nominal["slot_block"]

        for edge in path_to_edges(path):
            for slot in slot_block:
                occupation[edge][slot] = int(demand_id_str)

    return occupation

def build_working_graph(env, failure_edges):
    """
    Remove the forecasted failure links from the graph.
    """

    graph = env.graph.copy()

    for u, v in failure_edges:
        if graph.has_edge(u, v):
            if graph.is_multigraph():
                keys = list(graph[u][v].keys())
                for key in keys:
                    graph.remove_edge(u, v, key)
            else:
                graph.remove_edge(u, v)

    return graph


def generate_candidate_paths(env, source, target, failure_edges):
    """
    Generate candidate paths using k-shortest paths.
    """

    working_graph = build_working_graph(env, failure_edges)

    try:
        generator = nx.shortest_simple_paths(
            working_graph,
            source,
            target,
            weight="length",
        )
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []

    candidate_paths = []

    for path in generator:
        candidate_paths.append(list(path))

        if len(candidate_paths) >= MAX_CANDIDATE_PATHS:
            break

    return candidate_paths


def get_edge_length(graph, edge):
    """
    Get edge length/latency.
    """

    data = get_edge_data(graph, edge)

    for key in ["length", "latency", "weight"]:
        if key in data:
            return float(data[key])

    return 1.0


def path_length(env, path):
    """
    Compute the length of a path.
    """

    total_length = 0.0

    for edge in path_to_edges(path):
        total_length += get_edge_length(env.graph, edge)

    return total_length

def try_reroute_demand(env, occupation, demand_id, failure_edges):
#     try to reroute demand by testing candidate paths
    source, target = get_demand_source_target(env, demand_id)
    slot_count     = get_demand_slot_count(env, demand_id)

    candidate_paths = generate_candidate_paths(
        env=env,
        source=source,
        target=target,
        failure_edges=failure_edges,
    )

    for rank, path in enumerate(candidate_paths, start=1):
        slot_block = find_first_feasible_slot_block(
            env=env,
            occupation=occupation,
            path=path,
            slot_count=slot_count,
            failure_edges=failure_edges,
        )

        if slot_block is not None:
            crossed_failure_edge = get_crossed_failure_edge(
                env=env,
                demand_id=demand_id,
                failure_edges=failure_edges,
            )
            return {
                "path": path,
                "slot_block": slot_block,
                "candidate_path_rank": rank,
                "failure_link": list(crossed_failure_edge)
                if crossed_failure_edge is not None
                else None,
                "path_length": path_length(env, path),
            }

    return None

def get_crossed_failure_edge(env, demand_id, failure_edges):
#     Identify which failure link affects this demand

    nominal = get_nominal_lightpath(env, demand_id)
    nominal_edges = path_to_edges(nominal["path"])

    for failure_edge in failure_edges:
        if failure_edge in nominal_edges:
            return failure_edge

    return None

def find_first_feasible_slot_block(env, occupation, path, slot_count, failure_edges):
#     Search the first feasible slot block on a candidate path
    path_edges = path_to_edges(path)

    if not path_edges:
        return None

    max_start = min(
        get_edge_capacity(env, edge)
        for edge in path_edges
    ) - slot_count + 1

    for start_slot in range(1, max_start + 1):
        slot_block = list(range(start_slot, start_slot + slot_count))

        if is_slot_block_free(
            env=env,
            occupation=occupation,
            path=path,
            slot_block=slot_block,
            failure_edges=failure_edges,
        ):
            return slot_block

    return None

def is_slot_block_free(env, occupation, path, slot_block, failure_edges):
#     check spectrum satisfy EON constrains

    path_edges = path_to_edges(path)

    for edge in path_edges:
        if edge in failure_edges:
            return False

        edge_capacity = get_edge_capacity(env, edge)

        for slot in slot_block:
            if slot > edge_capacity:
                return False

            if occupation[edge].get(slot) is not None:
                return False

    return True

def get_edge_capacity(env, edge):
#     Get the number of avail slots on an edge

    data = get_edge_data(env.graph, edge)

    for key in ["slices", "capacity", "num_slots", "nbSlices", "nb_slices"]:
        if key in data:
            return int(data[key])


    max_slot = 0

    for item in env.nominal_paths.values():
        if item.get("slot_block"):
            max_slot = max(max_slot, max(item["slot_block"]))

    return max_slot + 100


def get_edge_data(graph, edge):
#     Return edge attributes for simple graphs and multigraphs

    u, v = edge

    if not graph.has_edge(u, v):
        return {}

    data = graph.get_edge_data(u, v)

    if data is None:
        return {}

#     Simple graph case
    if "length" in data or "slices" in data:
        return data

#     Multigraph case
    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, dict):
                return value

    return {}


def get_demand_slot_count(env, demand_id):
#     get the number of required slots

    demand = get_demand_record(env, demand_id)

    if demand is not None:
        for key in ["slots", "num_slots", "nbSlices", "nb_slices", "width"]:
            if key in demand:
                return int(demand[key])

    nominal = get_nominal_lightpath(env, demand_id)
    return len(nominal["slot_block"])

def get_demand_source_target(env, demand_id):
#     get source and target of a demand
    demand = get_demand_record(env, demand_id)

    if demand is not None:
        source = (
            demand.get("source")
            or demand.get("origin")
            or demand.get("src")
            or demand.get("o")
        )

        target = (
            demand.get("target")
            or demand.get("destination")
            or demand.get("dst")
            or demand.get("t")
        )

        if source is not None and target is not None:
            return source, target

    nominal      = get_nominal_lightpath(env, demand_id)
    nominal_path = nominal["path"]

    return nominal_path[0], nominal_path[-1]

def get_demand_record(env, demand_id):
#     find demand data in env.demands

    demands = getattr(env, "demands", None)

    if demands is None:
        return None

    if isinstance(demands, dict):
        return demands.get(str(demand_id), demands.get(demand_id))

    if isinstance(demands, list):
        for demand in demands:
            current_id = (
                demand.get("id")
                or demand.get("demand_id")
                or demand.get("index")
            )

            if str(current_id) == str(demand_id):
                return demand

    return None

def get_nominal_lightpath(env, demand_id):
#     get the nominal lightpath of a demand.
    demand_id_str = str(demand_id)
    return env.nominal_paths[demand_id_str]

def reserve_lightpath(occupation, demand_id, path, slot_block):
#     Reserve the migrated lightpath

    for edge in path_to_edges(path):
        for slot in slot_block:
            occupation[edge][slot] = int(demand_id)

def release_nominal_lightpath(env, occupation, demand_id):
#     Release the nominal lightpath only the migrated one is established

    nominal = get_nominal_lightpath(env, demand_id)
    path = nominal["path"]
    slot_block = nominal["slot_block"]

    for edge in path_to_edges(path):
        for slot in slot_block:
            if occupation[edge].get(slot) == int(demand_id):
                del occupation[edge][slot]


def solve_greedy_resilient_rsa(env, solution_path: str):
#     1. Take the affected demands K_Z.
#     2. Generate an order of migration randomly.
#     3. While rerouting set is not empty:
#         - Consider the first demand in the order;
#         - Compute candidate shortest paths;
#         - Search a feasible spectrum assignment;
#         - Establish the migrated lightpath iff it is feasible;
#         - Then remove the nominal lightpath.

    start_time = perf_counter()

#     get affected demands from failure zone
    affected_demands = list(getattr(env, "affected_demands", []))
    failure_edges    = get_failure_edges(env)

#      gen migration order randomly
    migration_order = affected_demands[:]
    random.Random(RANDOM_SEED).shuffle(migration_order)

#     build the current occupation from nominal solution
    occupation = build_initial_occupation(env)

    migrated_paths = {}
    failed_demands = []

#     reroute demands one by one
    for demand_id in migration_order:
        result = try_reroute_demand(
            env=env,
            occupation=occupation,
            demand_id=demand_id,
            failure_edges=failure_edges,
        )

        if result is None:
            failed_demands.append(demand_id)
            print(f"[WARNING] Greedy could not reroute demand {demand_id}.")
            continue


#         Make-before-break
#         first reserve the migrated lightpath
        reserve_lightpath(
            occupation=occupation,
            demand_id=demand_id,
            path=result["path"],
            slot_block=result["slot_block"],
        )

#         Then release the old nominal lightpath
        release_nominal_lightpath(
            env=env,
            occupation=occupation,
            demand_id=demand_id
        )

        migrated_paths[str(demand_id)] = result

        print(
            f"[OK] Greedy rerouted demand {demand_id}: "
            f"path={result['path']}, "
            f"S={result['slot_block']}"
        )

    running_time = perf_counter() - start_time


#     Define final status
    if not affected_demands:
        status = "NO_AFFECTED_DEMAND"
        message = "No demand is affected by the failure zone."
    elif failed_demands:
        status = "PARTIAL"
        message = f"Greedy successfully rerouted all affected demands."
    else:
        status = "FEASIBLE"
        message = "Greedy successfully rerouted all affected demands."


#     build output
    solution = build_greedy_solution(
        env=env,
        status=status,
        migrated_paths=migrated_paths,
        migration_order=migration_order,
        running_time=running_time,
        message=message,
    )

    solution["failed_demands"] = failed_demands
    solution["search_batch_size"] = SEARCH_BATCH_SIZE
    solution["max_candidate_paths"] = MAX_CANDIDATE_PATHS
    solution["random_seed"] = RANDOM_SEED


#     Write JSON solution
    write_greedy_solution(
        solution=solution,
        solution_path=solution_path
    )

    return solution
