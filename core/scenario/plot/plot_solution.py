from pathlib import Path
import json

import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.lines import Line2D


def get_scenario3_layout():
    """
    Fixed layout for Scenario 3.
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
    Used spring layout for Orange
    """
    node_set = set(env.nodes)

    if node_set == {"s", "a", "b", "t", "c", "d"}:
        return get_scenario3_layout()

    return nx.spring_layout(
        env.graph,
        seed=7,
        k=1.5,
        iterations=500,
    )

def path_to_edges(path):
    """
    Convert a node path into undirected edge tuples.
    """
    edges = []

    for i in range(len(path) - 1):
        u = path[i]
        v = path[i + 1]
        edges.append(tuple(sorted((u, v))))

    return edges


def collect_nominal_edges(env):
    """
    Collect all physical edges used by nominal paths.
    """
    nominal_edges = set()

    for demand_id in env.nominal_paths:
        path = env.nominal_paths[demand_id]["path"]

        for edge in path_to_edges(path):
            nominal_edges.add(edge)

    return nominal_edges


def build_note_text(env):
    """
    Build a note block for the nominal/failure figure.
    """
    lines = []
    lines.append("Nominal solution")

    for demand_id in sorted(env.nominal_paths.keys(), key=int):
        nominal = env.nominal_paths[demand_id]
        path = nominal["path"]
        slot_block = nominal["slot_block"]

        lines.append(
#             f"P{demand_id}: {' -> '.join(path)}, "
            f"P{demand_id}: {' -> '.join(map(str, path))}, "
            f"S={slot_block}"
        )

    if getattr(env, "failure_links", []):
        lines.append("")
        lines.append(f"Forecasted failure link(s): {env.failure_links}")

    if getattr(env, "affected_demands", []):
        lines.append(f"Directly affected demands K_Z: {env.affected_demands}")

    return "\n".join(lines)


def plot_nominal_solution(env, output_path: str):
    """
    Plot nominal solution and forecasted failure link.

    Style:
    - ordinary topology edges: black, thin
    - nominal paths: royalblue, dashed
    - forecasted failure link: red, bold
    """

    graph = env.graph
    pos = get_scenario3_layout()

    fig, ax = plt.subplots(figsize=(9, 5.8))

    all_edges = {tuple(sorted((u, v))) for (u, v) in graph.edges()}

    nominal_edges = collect_nominal_edges(env)

    failure_links = getattr(env, "failure_links", [])
    failure_edges = {tuple(sorted((u, v))) for (u, v) in failure_links}

    ordinary_edges = list(all_edges - nominal_edges - failure_edges)
    nominal_edges_to_draw = list(nominal_edges - failure_edges)

    # Ordinary physical topology edges.
    nx.draw_networkx_edges(
        graph,
        pos,
        ax=ax,
        edgelist=ordinary_edges,
        edge_color="black",
        width=1.2,
    )

    # Nominal paths.
    nx.draw_networkx_edges(
        graph,
        pos,
        ax=ax,
        edgelist=nominal_edges_to_draw,
        edge_color="royalblue",
        width=3.0,
        style="dashed",
    )

    # Forecasted failure edge.
    if failure_edges:
        nx.draw_networkx_edges(
            graph,
            pos,
            ax=ax,
            edgelist=list(failure_edges),
            edge_color="red",
            width=4.8,
            style="solid",
        )

    # Nodes.
    nx.draw_networkx_nodes(
        graph,
        pos,
        ax=ax,
        node_size=320,
        node_color="lightskyblue",
        edgecolors="black",
        linewidths=0.8,
    )

    special_nodes = [node for node in ["s", "t"] if node in graph.nodes]

    if special_nodes:
        nx.draw_networkx_nodes(
            graph,
            pos,
            ax=ax,
            nodelist=special_nodes,
            node_size=520,
            node_color="cornflowerblue",
            edgecolors="black",
            linewidths=1.0,
        )

    nx.draw_networkx_labels(
        graph,
        pos,
        ax=ax,
        font_size=11,
        font_weight="bold",
        font_color="black",
    )

    ax.set_title("Solution", fontsize=13)
    ax.axis("off")

    legend_handles = [
        Line2D([0], [0], color="black", lw=1.2, label="Ordinary topology edge"),
        Line2D([0], [0], color="royalblue", lw=3.0, linestyle="--", label="Nominal path"),
    ]

    if failure_edges:
        legend_handles.append(
            Line2D([0], [0], color="red", lw=4.8, linestyle="-", label="Forecasted failure link")
        )

    ax.legend(
        handles=legend_handles,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.16),
        ncol=2,
        fontsize=9,
        frameon=False,
    )

    note_text = build_note_text(env)

    fig.text(
        0.12,
        0.02,
        note_text,
        ha="left",
        va="bottom",
        fontsize=9,
        family="monospace",
    )

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    plt.tight_layout(rect=[0, 0.10, 1, 1])
    plt.savefig(output_file, bbox_inches="tight")
    plt.close()

    print(f"[OK] Scenario 3 nominal solution saved to: {output_file}")


def load_solution(solution_path: str):
    with open(solution_path, "r", encoding="utf-8") as f:
        return json.load(f)


def collect_migrated_edges(solution):
    migrated_edges = set()

    migrated_paths = solution.get("migrated_paths", {})

    for k, item in migrated_paths.items():
        path = item["path"]

        for edge in path_to_edges(path):
            migrated_edges.add(edge)

    return migrated_edges


def build_result_note_text(env, solution):
    lines = []

    lines.append("Model solution")
    lines.append(f"Affected demands K_Z: {solution.get('affected_demands_KZ', [])}")
    lines.append(f"Migrated demands K': {solution.get('migrated_demands_K_prime', [])}")

    migration_order_text = solution.get("migration_order_text", "")

    if not migration_order_text:
        order = solution.get("migration_order", [])
        migration_order_text = " -> ".join(map(str, order))

    if not migration_order_text:
        precedence_relations = solution.get("precedence_relations", [])
        migration_order_text = str(precedence_relations)

    lines.append(f"Migration order: {migration_order_text}")

    lines.append("")
    lines.append("Migrated paths")

    migrated_paths = solution.get("migrated_paths", {})

    for k in sorted(migrated_paths.keys(), key=int):
        item = migrated_paths[k]

        path = item["path"]
        slot_block = item["slot_block"]

        lines.append(
#             f"P{k}: {' -> '.join(path)}, "
            f"P{k}: {' -> '.join(map(str, path))}, "
            f"S={slot_block}"
        )

    return "\n".join(lines)


def plot_model_solution(env, solution_path: str, output_path: str):
    """
    Plot the solution returned by the Gurobi model.
    """

    solution = load_solution(solution_path)

    graph = env.graph
#     pos = get_scenario3_layout()
    pos = get_layout(env)

    fig, ax = plt.subplots(figsize=(9, 6.2))

    all_edges = {tuple(sorted((u, v))) for (u, v) in graph.edges()}

    nominal_edges = collect_nominal_edges(env)

    failure_links = getattr(env, "failure_links", [])
    failure_edges = {tuple(sorted((u, v))) for (u, v) in failure_links}

    migrated_edges = collect_migrated_edges(solution)

    ordinary_edges = list(
        all_edges
        - nominal_edges
        - failure_edges
        - migrated_edges
    )

    nominal_edges_to_draw = list(
        nominal_edges
        - failure_edges
        - migrated_edges
    )

    migrated_edges_to_draw = list(
        migrated_edges
        - failure_edges
    )

    # Ordinary topology edges.
    nx.draw_networkx_edges(
        graph,
        pos,
        ax=ax,
        edgelist=ordinary_edges,
        edge_color="black",
        width=1.2,
    )

    # Nominal paths.
    nx.draw_networkx_edges(
        graph,
        pos,
        ax=ax,
        edgelist=nominal_edges_to_draw,
        edge_color="royalblue",
        width=3.0,
        style="dashed",
    )

    # Migrated paths.
    nx.draw_networkx_edges(
        graph,
        pos,
        ax=ax,
        edgelist=migrated_edges_to_draw,
        edge_color="forestgreen",
        width=4.0,
        style="solid",
    )

    # Forecasted failure edge.
    if failure_edges:
        nx.draw_networkx_edges(
            graph,
            pos,
            ax=ax,
            edgelist=list(failure_edges),
            edge_color="red",
            width=4.8,
            style="solid",
        )

    # Nodes.
    nx.draw_networkx_nodes(
        graph,
        pos,
        ax=ax,
        node_size=320,
        node_color="lightskyblue",
        edgecolors="black",
        linewidths=0.8,
    )

    special_nodes = [node for node in ["s", "t"] if node in graph.nodes]

    if special_nodes:
        nx.draw_networkx_nodes(
            graph,
            pos,
            ax=ax,
            nodelist=special_nodes,
            node_size=520,
            node_color="cornflowerblue",
            edgecolors="black",
            linewidths=1.0,
        )

    nx.draw_networkx_labels(
        graph,
        pos,
        ax=ax,
        font_size=11,
        font_weight="bold",
        font_color="black",
    )

    ax.set_title("Scenario 3: Gurobi solution", fontsize=13)
    ax.axis("off")

    legend_handles = [
        Line2D([0], [0], color="black", lw=1.2, label="Ordinary topology edge"),
        Line2D([0], [0], color="royalblue", lw=3.0, linestyle="--", label="Nominal path"),
        Line2D([0], [0], color="forestgreen", lw=4.0, linestyle="-", label="Migrated path"),
        Line2D([0], [0], color="red", lw=4.8, linestyle="-", label="Forecasted failure link"),
    ]

    ax.legend(
        handles=legend_handles,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.16),
        ncol=2,
        fontsize=9,
        frameon=False,
    )

    note_text = build_result_note_text(env, solution)

    fig.text(
        0.12,
        0.02,
        note_text,
        ha="left",
        va="bottom",
        fontsize=9,
        family="monospace",
    )

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    plt.tight_layout(rect=[0, 0.16, 1, 1])
    plt.savefig(output_file, bbox_inches="tight")
    plt.close()

    print(f"[OK] Scenario 3 model solution saved to: {output_file}")

def collect_edges_from_path(path):
    return set(path_to_edges(path))

def build_single_demand_note_text(demand_id, env, solution):
    demand_id_str = str(demand_id)

    nominal  = env.nominal_paths[demand_id_str]
    migrated = solution["migrated_paths"][demand_id_str]

    nominal_path  = nominal["path"]
    nominal_slots = nominal["slot_block"]

    migrated_path  = migrated["path"]
    migrated_slots = migrated["slot_block"]

    migration_order_text = solution.get("migration_order_text", "")

    if not migration_order_text:
        order = solution.get("migration_order", [])
        migration_order_text = " -> ".join(map(str, order))

    affected_demands = solution.get("affected_demands_KZ", env.affected_demands)
    num_affected_demands = len(affected_demands)

    lines = []
    lines.append(f"Demand P{demand_id}")
    lines.append(f"Failure link(s): {env.failure_links}")
    lines.append(f"Affected demands K_Z: {affected_demands}")
    lines.append(f"Number of affected demands: {num_affected_demands}")
    lines.append(f"Migration order: {migration_order_text}")
    lines.append("")
    lines.append(
        f"Nominal path : {' -> '.join(map(str, nominal_path))}, "
        f"S={nominal_slots}"
    )
    lines.append(
        f"Migrated path: {' -> '.join(map(str, migrated_path))}, "
        f"S={migrated_slots}"
    )

    return "\n".join(lines)

def plot_single_demand_solution(env, solution, demand_id, output_path):
    """
    Plot one demand solution only
    """

    graph = env.graph
    pos = get_layout(env)

    demand_id_str = str(demand_id)

    nominal = env.nominal_paths[demand_id_str]
    migrated = solution["migrated_paths"][demand_id_str]

    nominal_edges = collect_edges_from_path(nominal["path"])
    migrated_edges = collect_edges_from_path(migrated["path"])

    failure_edges = {
        tuple(sorted((u, v)))
        for u, v in getattr(env, "failure_links", [])
    }

    all_edges = {
        tuple(sorted((u, v)))
        for u, v in graph.edges()
    }

    ordinary_edges = list(
        all_edges - nominal_edges - migrated_edges - failure_edges
    )

    nominal_edges_to_draw = list(
        nominal_edges - failure_edges - migrated_edges
    )

    migrated_edges_to_draw = list(
        migrated_edges - failure_edges
    )

    fig, ax = plt.subplots(figsize=(13, 9))

    # Ordinary topology edges.
    nx.draw_networkx_edges(
        graph,
        pos,
        ax=ax,
        edgelist=ordinary_edges,
        edge_color="gray",
        width=1.0,
        alpha=0.75,
    )

    # Nominal path for this demand.
    if nominal_edges_to_draw:
        nx.draw_networkx_edges(
            graph,
            pos,
            ax=ax,
            edgelist=nominal_edges_to_draw,
            edge_color="royalblue",
            width=3.0,
            style="dashed",
        )

    # Migrated path for this demand.
    if migrated_edges_to_draw:
        nx.draw_networkx_edges(
            graph,
            pos,
            ax=ax,
            edgelist=migrated_edges_to_draw,
            edge_color="forestgreen",
            width=4.0,
            style="solid",
        )

    # Failure edge.
    if failure_edges:
        nx.draw_networkx_edges(
            graph,
            pos,
            ax=ax,
            edgelist=list(failure_edges),
            edge_color="red",
            width=4.8,
            style="solid",
        )

    # Nodes.
    nx.draw_networkx_nodes(
        graph,
        pos,
        ax=ax,
        node_size=180,
        node_color="lightskyblue",
        edgecolors="black",
        linewidths=0.5,
    )

    nx.draw_networkx_labels(
        graph,
        pos,
        ax=ax,
        font_size=8,
        font_color="black",
    )

    ax.axis("off")

    legend_handles = [
        Line2D([0], [0], color="gray", lw=1.0, label="Ordinary topology edge"),
        Line2D([0], [0], color="royalblue", lw=3.0, linestyle="--", label="Nominal path"),
        Line2D([0], [0], color="forestgreen", lw=4.0, linestyle="-", label="Migrated path"),
        Line2D([0], [0], color="red", lw=4.8, linestyle="-", label="Forecasted failure link"),
    ]

    ax.legend(
        handles=legend_handles,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.10),
        ncol=2,
        fontsize=9,
        frameon=False,
    )

    note_text = build_single_demand_note_text(
        demand_id=demand_id,
        env=env,
        solution=solution,
    )

    fig.text(
        0.10,
        0.02,
        note_text,
        ha="left",
        va="bottom",
        fontsize=9,
        family="monospace",
    )

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    plt.tight_layout(rect=[0, 0.12, 1, 1])
    plt.savefig(output_file, bbox_inches="tight")
    plt.close()

    print(f"[OK] Demand {demand_id} solution saved to: {output_file}")


def build_combined_solution_note_text(env, solution, demand_ids):
    """
    Build a unified note block for the combined MBB solution.
    """

    affected_demands = solution.get("affected_demands_KZ", env.affected_demands)

    migration_order_text = solution.get("migration_order_text", "")

    if not migration_order_text:
        order = solution.get("migration_order", [])
        migration_order_text = " -> ".join(map(str, order))

    migrated_paths = solution.get("migrated_paths", {})

    lines = []
    lines.append("Combined MBB solution")
    lines.append(f"Failure link(s): {env.failure_links}")
    lines.append(f"Affected demands K_Z: {affected_demands}")
    lines.append(f"Number of affected demands: {len(affected_demands)}")
    lines.append(f"Migration order: {migration_order_text}")
    lines.append("")
    lines.append("Affected demand paths")

    for demand_id in sorted(demand_ids):
        demand_id_str = str(demand_id)

        if demand_id_str not in env.nominal_paths:
            continue

        if demand_id_str not in migrated_paths:
            continue

        nominal = env.nominal_paths[demand_id_str]
        migrated = migrated_paths[demand_id_str]

        nominal_path = nominal["path"]
        migrated_path = migrated["path"]

        nominal_slots = nominal["slot_block"]
        migrated_slots = migrated["slot_block"]

        lines.append(
            f"P{demand_id} nominal : "
            f"{' -> '.join(map(str, nominal_path))}, "
            f"S={nominal_slots}"
        )

        lines.append(
            f"P{demand_id} migrated: "
            f"{' -> '.join(map(str, migrated_path))}, "
            f"S={migrated_slots}"
        )

    return "\n".join(lines)


def plot_combined_model_solution(env, solution, output_path):
    """
    Plot all directly affected demands K_Z on one single topology.
    """

    graph = env.graph
    pos = get_layout(env)

    migrated_paths = solution.get("migrated_paths", {})
    affected_demands = solution.get("affected_demands_KZ", env.affected_demands)

    valid_demand_ids = []
    nominal_edges = set()
    migrated_edges = set()

    for demand_id in sorted(affected_demands):
        demand_id_str = str(demand_id)

        if demand_id_str not in env.nominal_paths:
            print(f"[WARNING] Demand {demand_id} not found in nominal_paths. Skipped.")
            continue

        if demand_id_str not in migrated_paths:
            print(f"[WARNING] Demand {demand_id} not found in migrated_paths. Skipped.")
            continue

        valid_demand_ids.append(demand_id)

        nominal = env.nominal_paths[demand_id_str]
        migrated = migrated_paths[demand_id_str]

        nominal_edges.update(
            collect_edges_from_path(nominal["path"])
        )

        migrated_edges.update(
            collect_edges_from_path(migrated["path"])
        )

    failure_edges = {
        tuple(sorted((u, v)))
        for u, v in getattr(env, "failure_links", [])
    }

    all_edges = {
        tuple(sorted((u, v)))
        for u, v in graph.edges()
    }

    ordinary_edges = list(
        all_edges - nominal_edges - migrated_edges - failure_edges
    )

    nominal_edges_to_draw = list(
        nominal_edges - failure_edges - migrated_edges
    )

    migrated_edges_to_draw = list(
        migrated_edges - failure_edges
    )

    fig, ax = plt.subplots(figsize=(13, 9))

    # Ordinary topology edges.
    nx.draw_networkx_edges(
        graph,
        pos,
        ax=ax,
        edgelist=ordinary_edges,
        edge_color="gray",
        width=1.0,
        alpha=0.75,
    )

    # Nominal paths of affected demands.
    if nominal_edges_to_draw:
        nx.draw_networkx_edges(
            graph,
            pos,
            ax=ax,
            edgelist=nominal_edges_to_draw,
            edge_color="royalblue",
            width=3.0,
            style="dashed",
        )

    # Migrated paths of affected demands.
    if migrated_edges_to_draw:
        nx.draw_networkx_edges(
            graph,
            pos,
            ax=ax,
            edgelist=migrated_edges_to_draw,
            edge_color="forestgreen",
            width=4.0,
            style="solid",
        )

    # Forecasted failure link(s).
    if failure_edges:
        nx.draw_networkx_edges(
            graph,
            pos,
            ax=ax,
            edgelist=list(failure_edges),
            edge_color="red",
            width=4.8,
            style="solid",
        )

    # Nodes.
    nx.draw_networkx_nodes(
        graph,
        pos,
        ax=ax,
        node_size=180,
        node_color="lightskyblue",
        edgecolors="black",
        linewidths=0.5,
    )

    nx.draw_networkx_labels(
        graph,
        pos,
        ax=ax,
        font_size=8,
        font_color="black",
    )

    ax.set_title("Combined MBB solution for the failure zone", fontsize=13)
    ax.axis("off")

    legend_handles = [
        Line2D([0], [0], color="gray", lw=1.0, label="Ordinary topology edge"),
        Line2D([0], [0], color="royalblue", lw=3.0, linestyle="--", label="Nominal path"),
        Line2D([0], [0], color="forestgreen", lw=4.0, linestyle="-", label="Migrated path"),
        Line2D([0], [0], color="red", lw=4.8, linestyle="-", label="Forecasted failure link"),
    ]

    ax.legend(
        handles=legend_handles,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.10),
        ncol=2,
        fontsize=9,
        frameon=False,
    )

    note_text = build_combined_solution_note_text(
        env=env,
        solution=solution,
        demand_ids=valid_demand_ids,
    )

    fig.text(
        0.10,
        0.02,
        note_text,
        ha="left",
        va="bottom",
        fontsize=9,
        family="monospace",
    )

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    plt.tight_layout(rect=[0, 0.18, 1, 1])
    plt.savefig(output_file, bbox_inches="tight")
    plt.close()

    print(f"[OK] Combined model solution saved to: {output_file}")


def plot_model_solution_by_demand(env, solution_path: str, output_dir: str):
    """
    Unified plotting function for model solution.
    """

    solution = load_solution(solution_path)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Remove old separated demand PDFs to avoid confusion.
    for old_file in output_dir.glob("demand_*_model_solution.pdf"):
        old_file.unlink()

    # Remove old migrated solution PDFs to regenerate cleanly.
    for old_file in output_dir.glob("Migrated_solution_*.pdf"):
        old_file.unlink()

    output_path = output_dir / "Migrated_solution_1.pdf"

    plot_combined_model_solution(
        env=env,
        solution=solution,
        output_path=output_path,
    )
