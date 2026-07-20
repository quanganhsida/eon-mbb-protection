from collections import defaultdict
from time import perf_counter
import random
import networkx as nx

from simulation.solver.greedy.output import (
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

def try_reroute_demand(env, occupation, demand_id, failure_edges):
#     try to reroute demand by testing candidate paths
    source, target = get_demand_source_target(env, demand_id)
    slot_count     = get_demand_slot_count(env, demand_id)

def get_demand_slot_count(env, demand_id):
#     get the number of required slots

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

    if isinstance(demands, dict):
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
        result = try_reroute_demand()
