from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx


def edge_key(u, v):
    return tuple(sorted((u, v)))


def get_scenario3_layout():
    """
    Fixed layout for the small Scenario 3 toy instance.
    """
    return {
        "s": (0.0, 1.0),
        "a": (1.2, 2.1),
        "b": (3.8, 2.1),
        "t": (5.0, 1.0),
        "c": (2.5, 1.0),
        "d": (2.5, -0.1),
    }


def get_layout(env):
    """
    Use fixed layout for Scenario 3.
    Use spring layout for Orange / larger topologies.
    """
    node_set = set(env.nodes)

    if node_set == {"s", "a", "b", "t", "c", "d"}:
        return get_scenario3_layout()

    return nx.spring_layout(
        env.graph,
        seed=7,
        k=1.2,
        iterations=300,
    )


def plot_network(env, output_path: str):
    """
    Plot network topology.
    """

    graph = env.graph
    pos = get_layout(env)

    failure_links = getattr(env, "failure_links", [])
    failure_edges = {edge_key(u, v) for u, v in failure_links}

    all_edges = {edge_key(u, v) for u, v in graph.edges()}
    ordinary_edges = list(all_edges - failure_edges)

    fig, ax = plt.subplots(figsize=(13, 9))

    # Ordinary topology edges.
    nx.draw_networkx_edges(
        graph,
        pos,
        ax=ax,
        edgelist=ordinary_edges,
        edge_color="gray",
        width=1.0,
        alpha=0.85,
    )

    # Forecasted failure links, if available.
    if failure_edges:
        nx.draw_networkx_edges(
            graph,
            pos,
            ax=ax,
            edgelist=list(failure_edges),
            edge_color="red",
            width=3.2,
            alpha=1.0,
        )

    # Nodes.
    nx.draw_networkx_nodes(
        graph,
        pos,
        ax=ax,
        node_size=180,
        node_color="tab:blue",
        edgecolors="black",
        linewidths=0.5,
    )

    # Node labels.
    nx.draw_networkx_labels(
        graph,
        pos,
        ax=ax,
        font_size=8,
        font_color="black",
    )

    title = env.name.replace("_", " ")

    if failure_edges:
        title = f"{title} topology with selected failure zone"
    else:
        title = f"{title} topology"

#     ax.set_title(title, fontsize=14)
    ax.axis("off")

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    plt.tight_layout()
    plt.savefig(output_file, bbox_inches="tight")
    plt.close()

    print(f"[OK] Topology figure saved to: {output_file}")
