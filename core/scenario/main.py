from simulator.env import Environment

from scenario.plot.plot_network import plot_network
from scenario.plot.plot_solution import plot_nominal_solution, plot_model_solution, plot_model_solution_by_demand

from simulator.solver.gurobi.solver import solve_basic_resilient_rsa
from simulator.solver.greedy.solver import solve_greedy_resilient_rsa

def main(args):
    env = Environment(args.instance_file)

    print("[INFO] Instance loaded")
    print(f"    name            : {env.name}")
    print(f"    nodes           : {len(env.nodes)}")
    print(f"    links           : {len(env.links)}")
    print(f"    demands         : {len(env.demands)}")
    print(f"    nominal path    : {len(env.nominal_paths)}")
    print(f"    plot type       : {args.plot_type}")
    print(f"    failure links   : {env.failure_links}")
    print(f"    affected K_Z    : {env.affected_demands}")

    if args.plot_type == "topology":
        plot_network(
            env=env,
            output_path=args.figure_file,
        )
    elif args.plot_type == "solution":
        plot_nominal_solution(
            env=env,
            output_path=args.figure_file,
        )
    elif args.plot_type == "solve":
        solve_basic_resilient_rsa(
            env=env,
            output_path=args.solution_file,
        )
    elif args.plot_type == "solve_greedy":
        solve_greedy_resilient_rsa(
            env=env,
            solution_path=args.solution_file,
        )
    elif args.plot_type == "result":
        plot_model_solution(
            env=env,
            solution_path=args.solution_file,
            output_path=args.figure_file,
        )
    elif args.plot_type == "result_by_demand":
        plot_model_solution_by_demand(
            env=env,
            solution_path=args.solution_file,
            output_dir=args.figure_dir,
        )
    else:
        raise ValueError(f"Unknown plot type: {args.plot_type}")
