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
