from gurobipy import GRB, Model, quicksum

def edge_key(u, v):
    return tuple(sorted((u, v)))

def path_to_edges(path):
    edges = []

    for i in range(len(path) - 1):
        u = path[i]
        v = path[i + 1]
        edges.append(edge_key(u, v))

    return edges

def build_directed_arcs(links):
    arcs = []
    arc_to_edge = {}

    for link in links:
        u = link["u"]
        v = link["v"]

        a1 = (u,v)
        a2 = (v,u)

        arcs.append(a1)
        arcs.append(a2)

        e = edge_key(u,v)
        arc_to_edge[a1] = e
        arc_to_edge[a2] = e

    return arcs, arc_to_edge

def build_delta_sets(nodes, arcs):
    delta_out = {v: [] for v in nodes}
    delta_in  = {v: [] for v in nodes}

    for a in arcs:
        u, v = a
        delta_out[u].append(a)
        delta_in[v].append(a)

    return delta_out, delta_in

def build_nominal_occupancy(env, physical_edges, S):
    """
    w[(k,e,t)] = 1 if nominal path of demand k occupies physical edge e at slot t.
    """
    w = {}

    for k_str, nominal in env.nominal_paths.items():
        k = int(k_str)
        path = nominal["path"]
        slot_block = nominal["slot_block"]
        nominal_edges = path_to_edges(path)

        for e in physical_edges:
            for t in S:
                w[(k, e, t)] = 0

        for e in nominal_edges:
            for t in slot_block:
                w[(k, e, t)] = 1

    return w

def extract_input(env):
    V = list(env.nodes)
    K = [d["id"] for d in env.demands]

    o = {d["id"]: d["source"] for d in env.demands}
    d = {d["id"]: d["target"] for d in env.demands}
    b = {d["id"]: d["slots"] for d in env.demands}

    Cmax = max(link["slots"] for link in env.links)
    S = list(range(1, Cmax + 1))

    Sk = {
        k: list(range(1, Cmax - b[k] + 2))
        for k in K
    }

    A, arc_to_edge = build_directed_arcs(env.links)
    E = sorted(set(arc_to_edge.values()))

    delta_out, delta_in = build_delta_sets(V, A)

    latency = {
            (link["u"], link["v"]): link.get("length", 1)
            for link in env.links
    }

    for link in env.links:
        latency[(link["v"], link["u"])] = link.get("length", 1)

    Z = {
        edge_key(u, v)
        for u,v in env.failure_links
    }

    KZ = list(env.affected_demands)

    w = build_nominal_occupancy(env, E , S)

    return {
        "V": V,
        "K": K,
        "A": A,
        "E": E,
        "S": S,
        "Sk": Sk,
        "o": o,
        "d": d,
        "b": b,
        "Cmax": Cmax,
        "delta_out": delta_out,
        "delta_in": delta_in,
        "latency": latency,
        "arc_to_edge": arc_to_edge,
        "Z": Z,
        "KZ": KZ,
        "w": w,
    }

def build_resilient_rsa_model(env):
    data = extract_input(env)

    V = data["V"]
    K = data["K"]
    A = data["A"]
    E = data["E"]
    S = data["S"]
    Sk = data["Sk"]
    o = data["o"]
    d = data["d"]
    b = data["b"]
    delta_out = data["delta_out"]
    delta_in = data["delta_in"]
    latency = data["latency"]
    arc_to_edge = data["arc_to_edge"]
    Z = data["Z"]
    KZ = data["KZ"]
    w = data["w"]

    model = Model("Scenario3_basic_resilient_RSA")

    # --------------------------------------------------
    # Variables
    # --------------------------------------------------

    x_index = [
        (k, a, s)
        for k in K
        for a in A
        for s in Sk[k]
    ]

    x = model.addVars(
        x_index,
        vtype=GRB.BINARY,
        name="x",
    )

    p_index = [
        (k,h)
        for k in K
        for h in K
        if k != h
    ]

    p = model.addVars(
        p_index,
        vtype=GRB.BINARY,
        name="p",
    )

    # --------------------------------------------------
    # Helper expressions
    # --------------------------------------------------

    def is_migrated_expr(k):
        return quicksum(
            x[k, a, s]
            for s in Sk[k]
            for a in delta_out[o[k]]
        )

    def migrated_occupancy_expr(k, e, t):
        return quicksum(
            x[k, a, s0]
            for s0 in Sk[k]
            for a in A
            if arc_to_edge[a] == e and s0 <= t <= s0 + b[k] - 1
        )

    # --------------------------------------------------
    # Objective
    # --------------------------------------------------

    f1 = quicksum(
        is_migrated_expr(k)
        for k in K
        if k not in KZ
    )

    f2 = quicksum(
        latency[a] * x[k, a, s]
        for k in K
        for a in A
        for s in Sk[k]
    )

    model.ModelSense = GRB.MINIMIZE

    model.setObjectiveN(
        f1,
        index=0,
        priority=2,
        weight=1,
        name="min_additional_migrations",
    )

    model.setObjectiveN(
        f2,
        index=1,
        priority=1,
        weight=1,
        name="min_total_latency",
    )

    # --------------------------------------------------
    # Constraints
    # --------------------------------------------------

    # Migration activation
    for k in KZ:
        model.addConstr(
            is_migrated_expr(k) == 1,
            name=f"impacted_must_migrate[{k}]",
        )

    for k in K:
        if k not in KZ:
            model.addConstr(
                is_migrated_expr(k) <= 1,
                name=f"optional_migration[{k}]",
            )

    # Avoid forecasted failure zone
    for k in K:
        for a in A:
            if arc_to_edge[a] in Z:
                for s in Sk[k]:
                    model.addConstr(
                        x[k, a, s] == 0,
                        name=f"avoid_failure_zone[{k},{a},{s}]",
                    )

    # Flow constraints
    for k in K:
        for s in Sk[k]:
            source = o[k]
            target = d[k]

            source_out = quicksum(
                x[k,a,s]
                for a in delta_out[source]
            )

            # no incoming flow to source
            model.addConstr(
                quicksum(x[k,a,s] for a in delta_in[source]) == 0,
                name=f"no_in_source[{k},{s}]",
            )

            # no outgoing flow from target
            model.addConstr(
                quicksum(x[k,a,s] for a in delta_out[target]) == 0,
                name=f"no_out_target[{k},{s}]",
            )

            # destination coupling
            model.addConstr(
                quicksum(x[k,a,s] for a in delta_in[target]) == source_out,
                name=f"source_destination_coupling[{k},{s}]",
            )

            # flow conservation at intermediate nodes
            for v in V:
                if v != source and v != target:
                    model.addConstr(
                        quicksum(x[k,a,s] for a in delta_in[v])
                        -
                        quicksum(x[k,a,s] for a in delta_out[v])
                        == 0,
                        name=f"flow_conservation[{k},{a},{v}]",
                    )

    # Non-overlap Constraints
    for e in E:
        for t in S:
            migrated_part = quicksum(
                migrated_occupancy_expr(k, e, t)
                for k in K
            )

            permanent_nominal_part = quicksum(
                (1 - is_migrated_expr(r)) * w.get((r, e, t), 0)
                for r in K
            )

            model.addConstr(
                migrated_part + permanent_nominal_part <= 1,
                name=f"final_non_overlap[{e},{t}]",
            )

    # Precedence
    # induction
    for k in K:
        for h in K:
            if k == h:
                continue

            for e in E:
                for t in S:
                    if w.get((k,e,t), 0) == 1:
                        model.addConstr(
                            p[k,h] >= migrated_occupancy_expr(h, e, t),
                            name=f"precedence_induction[{k},{h},{e},{t}]",
                        )

    # activation
    for k in K:
        for h in K:
            if k == h:
                continue

            model.addConstr(
                p[k,h] <= is_migrated_expr(k),
                name=f"precedence_requires_k_migrated[{k},{h}]",
            )

            model.addConstr(
                p[k,h] <= is_migrated_expr(h),
                name=f"precedence_requires_h_migrated[{k},{h}]",
            )

    # antisymmetry
    for k in K:
        for h in K:
            if k < h:
                model.addConstr(
                    p[k,h] + p[h,k] <= 1,
                    name=f"antisymmetry[{k},{h}]",
                )

    # transitivity
    for k in K:
        for h in K:
            for l in K:
                if len({k, h, l}) == 3:
                    model.addConstr(
                        p[k,h] + p[h,l] - p[k,l] <= 1,
                        name=f"transitivity[{k},{h},{l}]",
                    )

    model.update()

    variables = {
        "x": x,
        "p": p,
    }

    return model, data, variables
