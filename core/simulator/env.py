import json
from pathlib import Path

import networkx as nx

"""
Read instances and build graph
"""

class Environment:
    """
    Environment for a small EON/RSA instance.
    This class only loads:
    - nodes
    - links
    - demands

    It does not use nominal paths yet.
    """

    def __init__(self, instance_path: str):
        self.instance_path = Path(instance_path)
        self.instance = self._load_instance()

        self.name = self.instance["name"]
        self.nodes = self.instance["nodes"]
        self.links = self.instance["links"]
        self.demands = self.instance.get("demands", [])
        self.nominal_paths = self.instance.get("nominal_paths", {})
        self.failure_links = self._load_failure_links()

        self.graph = self._build_graph()

        self.affected_demands = self._identify_affected_demands()

    def _edge_key(self, u, v):
        """
        Return a canonical representation of an undirected edge.
        """
        return tuple(sorted((u,v)))

    def _path_to_edges(self, path):
        edges = set()

        for i in range(len(path) - 1):
            u = path[i]
            v = path[i + 1]
            edges.add(self._edge_key(u, v))

        return edges

    def _identify_affected_demands(self):
        """
        Identify demands whose nominal path intersects the forecasted failure zone.
        K_Z = {k in K | P_k intersects Z}
        """
        if not self.failure_links:
            return []

        failure_edges = {
            self._edge_key(u,v)
            for u, v in self.failure_links
        }

        affected = []

        for demand_id, nominal in self.nominal_paths.items():
            path = nominal["path"]
            path_edges = self._path_to_edges(path)

            if path_edges & failure_edges:
                affected.append(int(demand_id))

        return sorted(affected)

    def _load_failure_links(self):
        failure = self.instance.get("failure", {})
        raw_failed_links = failure.get("failed_links", [])

        failed_links = []

        for item in raw_failed_links:
            if len(item) != 2:
                raise ValueError(
                    f"Invalid failed link format: {item}. "
                    "Each failed link must be [u, v]."
                )

            u, v = item
            failed_links.append([u, v])

        return failed_links

    def _load_instance(self) -> nx.Graph:
        if not self.instance_path.exists():
            raise FileNotFoundError(
                    f"Instance file not found: {self.instance_path}"
            )

        with self.instance_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _build_graph(self) -> nx.Graph():
        graph = nx.Graph()

        for node in self.nodes:
            graph.add_node(node)

        for link in self.links:
            graph.add_edge(
                link["u"],
                link["v"],
                id=link["id"],
                length=link["length"],
                slots=link["slots"],
            )

        return graph
