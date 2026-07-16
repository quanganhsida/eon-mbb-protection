from gurobipy import GRB

from simulator.solver.gurobi.model import build_resilient_rsa_model
from simulator.solver.gurobi.output import extract_solution, save_json


def solve_basic_resilient_rsa(env, output_path: str):
    model, data, variables = build_resilient_rsa_model(env)

    model.Params.TimeLimit = 1800
    model.Params.OutputFlag = 1

    model.optimize()

    if model.Status not in [GRB.OPTIMAL, GRB.TIME_LIMIT] or model.SolCount == 0:
        print(f"[ERROR] Optimization ended with status: {model.Status}")

        result = {
            "instance": env.name,
            "status": int(model.Status),
            "message": "No feasible solution extracted.",
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
        "instance"           : env.name,
        "status"             : int(model.Status),
        "objective_value"    : model.ObjVal,
        "failure_links"      : env.failure_links,
        "affected_demands_KZ": env.affected_demands,
        **solution,
    }

    save_json(result, output_path)


    print("[SOLUTION] Basic resilient RSA")
    print(f"    affected K_Z    : {env.affected_demands}")
    print(f"    K_prime         : {solution['migrated_demands_K_prime']}")
    print(f"    migration_order : {solution['migration_order_text']}")
    print(f"    migrated_paths  : {solution['migrated_paths']}")

    return result
