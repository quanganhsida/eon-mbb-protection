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
    return {
        edge_key(path[i], path[i + 1])
        for i in range(len(path) - 1)
    }
