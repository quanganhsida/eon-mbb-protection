from time import perf_counter

from gurobipy import GRB

from simulator.solver.gurobi.model import build_resilient_rsa_model
from simulator.solver.gurobi.output import extract_solution, save_json


def solve_basic_resilient_rsa(env, output_path: str):
    model, data, variables = build_resilient_rsa_model(env)

    model.Params.TimeLimit = 1800
    model.Params.OutputFlag = 1

    start_time = perf_counter()
    model.optimize()
    running_time = perf_counter() - start_time

    if model.Status not in [GRB.OPTIMAL, GRB.TIME_LIMIT] or model.SolCount == 0:
        print(f"[ERROR] Optimization ended with status: {model.Status}")

        result = {
            "instance": env.name,
            "solver": "gurobi",
            "status": int(model.Status),
            "status_text": get_gurobi_status_text(model.Status),
            "message": "No feasible solution extracted.",
            "running_time": running_time,
        }

        save_json(result, output_path)
        return result

    solution = extract_solution(
        model=model,
        data=data,
        variables=variables,
        env=env,
    )

    result = {
        "instance": env.name,
        "solver": "gurobi",
        "status": int(model.Status),
        "status_text": get_gurobi_status_text(model.Status),
        "objective_value": model.ObjVal,
        "running_time": running_time,
        "failure_links": env.failure_links,
        "affected_demands_KZ": env.affected_demands,
        **solution,
    }

    save_json(result, output_path)

    print("[SOLUTION] Basic resilient RSA")
    print(f"    affected K_Z    : {env.affected_demands}")
    print(f"    K_prime         : {solution['migrated_demands_K_prime']}")
    print(f"    migration_order : {solution['migration_order_text']}")
    print(f"    migrated_paths  : {solution['migrated_paths']}")
    print(f"    running_time    : {running_time:.4f} seconds")

    return result


def get_gurobi_status_text(status):
    """
    Convert Gurobi status code into readable text.
    """

    status_map = {
        GRB.OPTIMAL: "OPTIMAL",
        GRB.INFEASIBLE: "INFEASIBLE",
        GRB.UNBOUNDED: "UNBOUNDED",
        GRB.INF_OR_UNBD: "INF_OR_UNBD",
        GRB.TIME_LIMIT: "TIME_LIMIT",
    }

    return status_map.get(status, f"STATUS_{status}")
